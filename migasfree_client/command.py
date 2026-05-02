# Copyright (c) 2013-2026 Jose Antonio Chavarría <jachavar@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import contextlib
import errno
import functools
import getpass
import gettext
import logging
import logging.config
import logging.handlers
import os
import platform
import shutil
import ssl
import sys
import time
from urllib.parse import urljoin

import requests
from rich.console import Console

from . import mtls, settings, utils
from .devices import Printer, get_available_devices_classes
from .network import get_network_info
from .pms import Pms, get_available_pms
from .url_request import UrlRequest

__author__ = 'Jose Antonio Chavarría <jachavar@gmail.com>'
__license__ = 'GPLv3'
__all__ = ['MigasFreeCommand']

_ = gettext.gettext

LOGGING_CONF = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s',
            'datefmt': '%Y-%m-%dT%H:%M:%S%z',
        },
    },
    'handlers': {
        'stderr': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'stream': 'ext://sys.stderr',
            'level': 'WARNING',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'INFO',
            'formatter': 'simple',
            'filename': settings.LOG_FILE,
            'maxBytes': 10_000_000,
            'backupCount': 5,
        },
    },
    'loggers': {
        'root': {
            'level': 'INFO',
            'handlers': [
                'stderr',
                'file',
            ],
        },
    },
}

try:
    logging.config.dictConfig(LOGGING_CONF)
except (OSError, ValueError):
    sys.stderr.write(_('Failed to configure the log file (%s)\n') % settings.LOG_FILE)
    sys.exit(errno.EACCES)

logger = logging.getLogger('migasfree_client')

# implicit print flush
os.environ['PYTHONUNBUFFERED'] = '1'

sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 1)
sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', 1)


def set_debug_log_level():
    LOGGING_CONF['handlers']['file']['level'] = 'DEBUG'
    LOGGING_CONF['loggers']['root']['level'] = 'DEBUG'
    logging.config.dictConfig(LOGGING_CONF)


def require_sign_keys(method):
    """Decorator to ensure sign keys are valid before method execution."""

    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self._check_sign_keys():
            sys.exit(errno.EPERM)
        return method(self, *args, **kwargs)

    return wrapper


def require_computer_id(method):
    """Decorator to ensure computer_id is set before method execution."""

    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self._computer_id:
            self.get_computer_id()
        return method(self, *args, **kwargs)

    return wrapper


@contextlib.contextmanager
def lock_file_context(cmd, lock_file):
    """Context manager for lock file handling."""
    utils.check_lock_file(cmd, lock_file)
    try:
        yield
    finally:
        utils.remove_file(lock_file)


class MigasFreeCommand:
    """
    Interface class
    """

    URLS = {  # noqa: RUF012
        # command API
        'get_server_info': '/api/v1/public/server/info/',
        'get_project_keys': '/api/v1/public/keys/project/',
        'get_repositories_keys': '/api/v1/public/keys/repositories/',
        'get_computer_id': '/api/v1/safe/computers/id/',
        'upload_computer': '/api/v1/safe/computers/',
        'upload_eot': '/api/v1/safe/eot/',
        #
        # sync API
        'get_properties': '/api/v1/safe/computers/properties/',
        'get_fault_definitions': '/api/v1/safe/computers/faults/definitions/',
        'get_repositories': '/api/v1/safe/computers/repositories/',
        'get_mandatory_packages': '/api/v1/safe/computers/packages/mandatory/',
        'get_devices': '/api/v1/safe/computers/devices/',
        'get_hardware_required': '/api/v1/safe/computers/hardware/required/',
        'get_traits': '/api/v1/safe/computers/traits/',
        'upload_errors': '/api/v1/safe/computers/errors/',
        'upload_hardware': '/api/v1/safe/computers/hardware/',
        'upload_attributes': '/api/v1/safe/computers/attributes/',
        'upload_faults': '/api/v1/safe/computers/faults/',
        'upload_software': '/api/v1/safe/computers/software/',
        'upload_devices_changes': '/api/v1/safe/computers/devices/changes/',
        'upload_sync': '/api/v1/safe/synchronizations/',
        'upload_sync_availability': '/manager/v1/public/synchronizations/availability/',
        #
        # label API
        'get_label': '/api/v1/safe/computers/label/',
        #
        # tags API
        'get_assigned_tags': '/api/v1/safe/computers/tags/assigned/',
        'get_available_tags': '/api/v1/safe/computers/tags/available/',
        'upload_tags': '/api/v1/safe/computers/tags/',
        #
        # upload API
        'get_packager_keys': '/api/v1/public/keys/packager/',
        'upload_package': '/api/v1/safe/packages/',
        'upload_set': '/api/v1/safe/packages/set/',
        'create_repository': '/api/v1/safe/packages/repos/',
    }

    CMD = 'migasfree'  # /usr/bin/migasfree
    LOCK_FILE = os.path.join(settings.TMP_PATH, f'{CMD}.pid')
    ERROR_FILE = os.path.join(settings.TMP_PATH, f'{CMD}.err')

    PUBLIC_KEY = 'server.pub'
    PRIVATE_KEY = ''

    APP_ICON = os.path.join('apps', 'migasfree.svg')
    SERVER_ICON = os.path.join('apps', 'migasfree-server-network.svg')

    _url_base = None
    _url_request = None

    _debug = False
    _quiet = False

    pms = None
    devices_class = None

    console = Console(log_path=False)
    error_console = Console(stderr=True, log_path=False, style='bright_red', force_terminal=True)

    auto_register_user = ''
    auto_register_password = ''
    auto_register_end_point = URLS['get_project_keys']
    get_key_repositories_end_point = URLS['get_repositories_keys']

    _computer_id = None
    _error_file_descriptor = None
    _mtls_cert = None
    _mtls_key = None
    _ca_cert = None

    def __init__(self):
        _config_client = utils.get_config(settings.CONF_FILE, 'client')
        if not isinstance(_config_client, dict):
            _config_client = {}

        self.migas_project = os.environ.get('MIGASFREE_CLIENT_PROJECT', utils.get_mfc_project())

        self.PRIVATE_KEY = f'{self.migas_project}.pri'

        self.migas_computer_name = os.environ.get('MIGASFREE_CLIENT_COMPUTER_NAME', utils.get_mfc_computer_name())

        self.migas_server = os.environ.get('MIGASFREE_CLIENT_SERVER', _config_client.get('server', 'localhost'))

        self.migas_port = os.environ.get('MIGASFREE_CLIENT_PORT', _config_client.get('port', ''))

        self.migas_protocol = os.environ.get('MIGASFREE_CLIENT_PROTOCOL', _config_client.get('protocol', 'http'))

        self.migas_auto_update_packages = utils.cast_to_bool(
            os.environ.get('MIGASFREE_CLIENT_AUTO_UPDATE_PACKAGES', _config_client.get('auto_update_packages', True)),
            default=True,
        )

        self.migas_manage_devices = utils.cast_to_bool(
            os.environ.get('MIGASFREE_CLIENT_MANAGE_DEVICES', _config_client.get('manage_devices', True)), default=True
        )

        self.migas_upload_hardware = utils.cast_to_bool(
            os.environ.get('MIGASFREE_CLIENT_UPLOAD_HARDWARE', _config_client.get('upload_hardware', True)),
            default=True,
        )

        self.migas_proxy = os.environ.get('MIGASFREE_CLIENT_PROXY', _config_client.get('proxy'))
        self.migas_package_proxy_cache = os.environ.get(
            'MIGASFREE_CLIENT_PACKAGE_PROXY_CACHE', _config_client.get('package_proxy_cache')
        )

        self._debug = utils.cast_to_bool(os.environ.get('MIGASFREE_CLIENT_DEBUG', _config_client.get('debug', False)))
        if self._debug:
            set_debug_log_level()

        _config_packager = utils.get_config(settings.CONF_FILE, 'packager')
        if not isinstance(_config_packager, dict):
            _config_packager = {}

        self.packager_user = os.environ.get('MIGASFREE_PACKAGER_USER', _config_packager.get('user'))
        self.packager_pwd = os.environ.get('MIGASFREE_PACKAGER_PASSWORD', _config_packager.get('password'))
        self.packager_project = os.environ.get('MIGASFREE_PACKAGER_PROJECT', _config_packager.get('project'))
        self.packager_store = os.environ.get('MIGASFREE_PACKAGER_STORE', _config_packager.get('store'))

        self._server_info = {}

        # http://www.lightbird.net/py-by-example/logging.html
        logger.info('*' * 20)
        logger.info('%s in execution', self.CMD)
        logger.info('Config file: %s', settings.CONF_FILE)
        logger.debug('Config client: %s', _config_client)
        logger.debug('Config packager: %s', _config_packager)

    def _ssl_cert(self):
        self.migas_ssl_cert = False
        if self.migas_protocol == 'https':
            port = self.migas_port if self.migas_port else 443

            if os.path.isfile(settings.CERT_FILE):
                os.remove(settings.CERT_FILE)

            try:
                cert = ssl.get_server_certificate((self.migas_server, port), ssl.PROTOCOL_SSLv23)
                if utils.write_file(settings.CERT_FILE, cert):
                    self.migas_ssl_cert = settings.CERT_FILE
            except ssl.SSLError:
                pass
            except OSError as e:
                _msg = _('Error getting server certificate: %s') % e
                self.operation_failed(_msg)
                sys.exit(errno.ECONNREFUSED)

    def _get_keys_path(self):
        return os.path.join(settings.KEYS_PATH, utils.sanitize_path(self.migas_server))

    def _init_url_base(self):
        self._url_base = '{}://{}{}'.format(
            self.migas_protocol, self.migas_server, f':{self.migas_port}' if self.migas_port else ''
        )

    def _init_mtls(self):
        """Initialize mTLS certificate paths, fetching from server if needed."""
        self._mtls_cert, self._mtls_key, self._ca_cert = mtls.get_mtls_credentials(self.migas_server)

        if self._mtls_cert and self._mtls_key:
            self._update_ca_certificate()
            self._enable_mtls()
            return

        self._fetch_mtls_from_server()

    def _update_ca_certificate(self):
        """Check and update CA certificate from server."""
        logger.info('Checking CA certificate...')
        ca_result = mtls.download_ca_certificate(self._url_base, self.migas_server)

        if ca_result['success']:
            self._ca_cert = ca_result['ca_file']
            if ca_result.get('updated'):
                logger.info('CA certificate updated')
        elif not ca_result.get('not_available'):
            logger.warning('Failed to download CA certificate: %s', ca_result['message'])

    def _enable_mtls(self):
        """Enable mTLS mode: force https protocol and update URL base."""
        self.migas_protocol = 'https'
        self._init_url_base()
        logger.info('mTLS enabled, protocol: https')

    def _fetch_mtls_from_server(self):
        """Attempt to fetch mTLS certificates from server."""
        logger.info('No mTLS credentials found, attempting to fetch from server...')

        url_request = UrlRequest(
            debug=self._debug,
            proxy=self.migas_proxy,
            cert=self.migas_ssl_cert,
        )

        result = mtls.fetch_and_install_mtls_certificate(
            url_request=url_request,
            server=self.migas_server,
            server_url=self._url_base,
            uuid=utils.get_hardware_uuid(),
            project_name=self.migas_project,
        )

        if result['success']:
            self._mtls_cert, self._mtls_key, self._ca_cert = mtls.get_mtls_credentials(self.migas_server)
            self._enable_mtls()
            logger.info('mTLS credentials installed successfully')
        elif not result.get('not_available'):
            logger.warning('Failed to fetch mTLS credentials: %s', result['message'])

    def _init_url_request(self):
        keys_path = self._get_keys_path()
        self._url_request = UrlRequest(
            debug=self._debug,
            proxy=self.migas_proxy,
            project=self.migas_project,
            keys={
                'private': os.path.join(keys_path, self.PRIVATE_KEY),
                'public': os.path.join(keys_path, self.PUBLIC_KEY),
            },
            cert=self.migas_ssl_cert,
            mtls_cert=self._mtls_cert,
            mtls_key=self._mtls_key,
            ca_cert=self._ca_cert,
        )

    def _fetch_mtls_certificates(self):
        """Fetch mTLS and CA certificates from server."""
        # Download CA certificate
        ca_result = mtls.download_ca_certificate(self._url_base, self.migas_server)
        if ca_result['success']:
            self._ca_cert = ca_result['ca_file']
            if ca_result.get('updated'):
                self.operation_ok(_('CA certificate downloaded'))
            else:
                self.operation_ok(_('CA certificate is up to date'))
        elif ca_result.get('not_available'):
            logger.info('CA certificate endpoint not available')
        else:
            self.operation_failed(_('Failed to download CA certificate: %s') % ca_result['message'])

        # Download mTLS certificates
        url_request = UrlRequest(
            debug=self._debug,
            proxy=self.migas_proxy,
            cert=self.migas_ssl_cert,
        )

        result = mtls.fetch_and_install_mtls_certificate(
            url_request=url_request,
            server=self.migas_server,
            server_url=self._url_base,
            uuid=utils.get_hardware_uuid(),
            project_name=self.migas_project,
        )

        if result['success']:
            self._mtls_cert, self._mtls_key, self._ca_cert = mtls.get_mtls_credentials(self.migas_server)
            self.operation_ok(_('mTLS certificates downloaded'))
        elif result.get('not_available'):
            logger.info('mTLS endpoint not available')
        else:
            self.operation_failed(_('Failed to download mTLS certificates: %s') % result['message'])

    def _init_command(self):
        self._ssl_cert()
        self._init_url_base()
        self._init_mtls()
        self.pms_selection()
        self._init_url_request()
        self.get_server_info()

    def api_protocol(self):
        return self.migas_protocol

    def api_endpoint(self, path):
        return urljoin(self._url_base, path)

    def _show_message(self, msg):
        self.console.print()
        self.console.rule(msg)

    def _check_path(self, path):
        if not os.path.isdir(path):
            try:
                os.makedirs(path)
            except OSError:
                _msg = _('Error creating %s directory') % path
                self.operation_failed(_msg)
                logger.error(_msg)
                return False

        return True

    def _execute_path(self, path):
        self._check_path(path)
        files = os.listdir(path)
        for file_ in sorted(files):
            self._show_message(_('Running command %s...') % file_)
            _ret, _output, _error = utils.execute(os.path.join(path, file_), verbose=True, interactive=False)
            if _ret == 0:
                self.operation_ok()
            else:
                _msg = _('Command %s failed: %s') % (file_, _error)
                self.operation_failed(_msg)
                logger.error(_msg)
                self._write_error(_msg)

    def _check_user_is_root(self):
        if not utils.is_root_user():
            self.operation_failed(_('User has insufficient privileges to execute this command'))
            sys.exit(errno.EACCES)

    def _check_sign_keys(self, get_computer_id=True):
        keys_path = self._get_keys_path()

        paths = {
            'private': os.path.join(keys_path, self.PRIVATE_KEY),
            'public': os.path.join(keys_path, self.PUBLIC_KEY),
        }

        all_keys_exist = all(os.path.isfile(path) for path in paths.values())

        if all_keys_exist:
            if get_computer_id and not self._computer_id:
                self.get_computer_id()

            return True  # all OK

        missing_keys = [key for key, path in paths.items() if not os.path.isfile(path)]
        logger.warning('Security keys are not present!!! %s', ', '.join(missing_keys))
        return self._auto_register()

    def _auto_register(self):
        self._show_message(_('Autoregistering computer...'))

        if self._save_sign_keys(self.auto_register_user, self.auto_register_password):
            return self._save_computer(self.auto_register_user, self.auto_register_password) != 0

        return False

    def _handle_keys_error(self, response, exit_on_error):
        """Handle error response from keys API call. Returns True if error was handled."""
        if not (isinstance(response, dict) and 'error' in response):
            return False

        error = response['error']
        if isinstance(error, dict) and 'code' in error:
            error_info = error['info']
            if error['code'] == requests.codes.not_found:
                error_info = _(
                    'Project "{}" not found on server. '
                    'You must create it or review the "Project" parameter '
                    'in the configuration file.'
                ).format(
                    self.migas_project
                )
            self.operation_failed(error_info)
            logger.error(error_info)
            if exit_on_error:
                sys.exit(error['code'])
        else:
            self.operation_failed(error)
            logger.error(error)
            if exit_on_error:
                sys.exit(errno.EPERM)

        return True

    def _get_key_filename(self, original_name):
        """Map server key filename to local key filename."""
        key_mapping = {
            'migasfree-server.pub': self.PUBLIC_KEY,
            'migasfree-client.pri': self.PRIVATE_KEY,
            'migasfree-packager.pri': self.PRIVATE_KEY,
        }
        return key_mapping.get(original_name, original_name)

    def _write_key_file(self, filename, content):
        """Write a key file and handle errors."""
        path_file = os.path.join(self._get_keys_path(), filename)
        logger.debug('Trying writing file: %s', path_file)

        if utils.write_file(path_file, str(content)):
            self.console.print(_('Key %s created!') % path_file)
            return True

        msg = _('Error writing key file!!!')
        self.operation_failed(msg)
        logger.error(msg)
        sys.exit(errno.ENOENT)

    def _save_sign_keys(self, user, password):
        exit_on_error = user != self.auto_register_user

        response = self._url_request.run(
            url=self.api_endpoint(self.auto_register_end_point),
            data={
                'username': user,
                'password': password,
                'project': self.migas_project,
                'platform': platform.system(),
                'pms': str(self.pms),
                'architecture': self.pms.get_system_architecture() if self.pms else '',
            },
            safe=False,
            exit_on_error=exit_on_error,
            debug=self._debug,
        )
        logger.debug('Response _save_sign_keys: %s', response)

        if self._handle_keys_error(response, exit_on_error):
            return False

        if not self._check_path(self._get_keys_path()):
            sys.exit(errno.ENOTDIR)

        for original_name, content in list(response.items()):
            filename = self._get_key_filename(original_name)
            self._write_key_file(filename, content)

        return True

    def cmd_register_computer(self, user=None):
        carry_on = utils.query_yes_no(_('Have you check config options in this machine (%s)?') % settings.CONF_FILE)
        if carry_on == 'no':
            msg = _('Check %s file and register again') % settings.CONF_FILE
            self.operation_failed(msg)
            sys.exit(errno.EAGAIN)

        if not self._auto_register():
            sys.stdin = open('/dev/tty')  # noqa: SIM115
            user = input('{}: '.format(_('User to register computer at server')))
            if not user:
                self.operation_failed(_('Empty user. Exiting %s.') % self.CMD)
                logger.info('Empty user in register computer option')
                sys.exit(errno.EAGAIN)

            password = getpass.getpass('{}: '.format(_('Password')))

            self._show_message(_('Registering computer...'))
            self._save_sign_keys(user, password)
            self._save_computer(user, password)

        self.operation_ok(_('Computer registered at server'))

        self._show_message(_('Fetching mTLS certificates...'))
        self._fetch_mtls_certificates()

    def _save_computer(self, user, password):
        response = self._url_request.run(
            url=self.api_endpoint(self.URLS['upload_computer']),
            data={
                'uuid': utils.get_hardware_uuid(),
                'name': self.migas_computer_name,
                'ip_address': get_network_info()['ip'],
                'username': user,
                'password': password,
            },
            exit_on_error=False,
            debug=self._debug,
        )
        logger.debug('Response _save_computer: %s', response)

        if isinstance(response, dict) and 'error' in response:
            if response['error']['code'] == requests.codes.unauthorized:
                self.operation_failed(
                    '{} ({})'.format(response['error']['info'], _('You must register the computer with a valid user'))
                )
                sys.exit(errno.EPERM)

            if response['error']['code'] == requests.codes.not_found:
                self.operation_failed(
                    _(
                        'Project "{}" not found on server. '
                        'You must create it or review the "Project" parameter '
                        'in the configuration file.'
                    ).format(
                        self.migas_project
                    )
                )
                sys.exit(errno.ENODATA)

            self.operation_failed(response['error']['info'])

        return response.get('id', 0)  # computer ID

    def get_server_info(self):
        response = self._url_request.run(
            url=self.api_endpoint(self.URLS['get_server_info']), safe=False, exit_on_error=False, debug=self._debug
        )
        logger.debug('Response get_server_info: %s', response)

        if isinstance(response, dict):
            self._server_info = response

    def get_computer_id(self):
        if not os.path.isfile(os.path.join(self._get_keys_path(), self.PRIVATE_KEY)):
            return 0

        if not self._url_base:
            self._init_command()

        if self._computer_id:
            return self._computer_id

        response = self._url_request.run(
            url=self.api_endpoint(self.URLS['get_computer_id']),
            data={'uuid': utils.get_hardware_uuid(), 'name': self.migas_computer_name},
            exit_on_error=False,
            debug=self._debug,
        )
        logger.debug('Response get_computer_id: %s', response)

        if isinstance(response, dict) and 'error' in response:
            if response['error']['code'] == requests.codes.not_found:
                response = self._save_computer(self.auto_register_user, self.auto_register_password)
            else:
                self.operation_failed(
                    '{} ({})'.format(response['error']['info'], _('Review keys or register computer again'))
                )
                sys.exit(errno.ENODATA)

        self._computer_id = response
        return self._computer_id

    def end_of_transmission(self):
        if not self._computer_id:
            self.get_computer_id()

        response = self._url_request.run(
            url=self.api_endpoint(self.URLS['upload_eot']),
            data={
                'id': self._computer_id,
            },
            debug=self._debug,
        )
        logger.debug('Response end_of_transmission: %s', response)

    def _show_config_options(self):
        conf_file = settings.CONF_FILE if os.path.isfile(settings.CONF_FILE) else ''

        self.console.print()
        self.console.print(_('Config options: %s') % conf_file)

        # Config options: (label, value, env_var_name, show_if_truthy)
        config_options = [
            (_('Project'), self.migas_project, 'MIGASFREE_CLIENT_PROJECT', True),
            (_('Server'), self.migas_server, 'MIGASFREE_CLIENT_SERVER', True),
            (_('Protocol'), self.migas_protocol, 'MIGASFREE_CLIENT_PROTOCOL', True),
            (_('Port'), self.migas_port, 'MIGASFREE_CLIENT_PORT', bool(self.migas_port)),
            (_('Auto update packages'), self.migas_auto_update_packages, 'MIGASFREE_CLIENT_AUTO_UPDATE_PACKAGES', True),
            (_('Manage devices'), self.migas_manage_devices, 'MIGASFREE_CLIENT_MANAGE_DEVICES', True),
            (_('Upload hardware'), self.migas_upload_hardware, 'MIGASFREE_CLIENT_UPLOAD_HARDWARE', True),
            (_('Proxy'), self.migas_proxy, 'MIGASFREE_CLIENT_PROXY', True),
            (_('Package Proxy Cache'), self.migas_package_proxy_cache, 'MIGASFREE_CLIENT_PACKAGE_PROXY_CACHE', True),
            (_('Debug'), self._debug, 'MIGASFREE_CLIENT_DEBUG', True),
            (_('Computer name'), self.migas_computer_name, 'MIGASFREE_CLIENT_COMPUTER_NAME', True),
        ]

        for label, value, env_var, show in config_options:
            if show:
                env_indicator = '(ENV)' if env_var in os.environ else ''
                self.console.print(f'\t{label}: {value} {env_indicator}')

    def _show_running_options(self):
        self.console.print()
        self.console.print(_('Running options:'))
        self.console.print(
            '\t{}: {}'.format(_('migasfree server version'), self._server_info.get('version', _('None')))
        )
        self.console.print('\t{}: {}'.format(_('SSL certificate'), self.migas_ssl_cert))
        if (
            self.migas_ssl_cert is not None
            and not isinstance(self.migas_ssl_cert, bool)
            and not os.path.exists(self.migas_ssl_cert)
        ):
            self.console.print(
                '\t\t{}: {}'.format(_('Warning'), _('Certificate does not exist and authentication is not guaranteed'))
            )
        self.console.print('\t{}: {}'.format(_('PMS'), self.pms))
        if self.pms:
            self.console.print('\t{}: {}'.format(_('Architecture'), self.pms.get_system_architecture()))

    def _write_error(self, msg, append=False):
        _mode = 'ab' if append else 'wb'

        if not self._error_file_descriptor:
            self._error_file_descriptor = open(self.ERROR_FILE, _mode)  # noqa: SIM115

        _text = '{}\n{}\n{}\n\n'.format('-' * 20, time.strftime('%Y-%m-%d %H:%M:%S'), str(msg))
        _text = bytes(_text, encoding='utf8')

        self._error_file_descriptor.write(_text)

    def _usage_examples(self):
        raise NotImplementedError

    @staticmethod
    def _search_pms():
        cmd_to_find = 'command -v'
        if utils.is_windows():
            cmd_to_find = 'where'

        for item in get_available_pms():
            cmd = f'{cmd_to_find} {item[0]}'
            ret, _, _ = utils.execute(cmd, interactive=False)
            if ret == 0:
                return item[1]

        return None  # if not found

    def pms_selection(self):
        pms_info = self._search_pms()
        logger.debug('PMS info: %s', pms_info)
        if not pms_info:
            return

        self.pms = Pms.factory(pms_info)()

    def _devices_class_selection(self):
        _class = None
        for item in get_available_devices_classes():
            _class = Printer.factory(item[1])(self.migas_server)
            if _class.platform == sys.platform:
                self.devices_class = _class
                return

    def _check_pms(self):
        if not self.pms:
            msg = _('Any PMS was not found. Cannot continue.')
            self.operation_failed(msg)
            logger.critical(msg)
            sys.exit(errno.EINPROGRESS)

    def operation_ok(self, info=''):
        msg = str(info) if info else _('Ok')
        self.console.log(msg, style='green')

    def operation_failed(self, info=''):
        console = self.error_console
        if utils.is_windows():
            console = self.console
            console.style = 'bright_red'

        console.rule(_('Failed'))
        if info:
            console.log(info)

        if utils.is_windows():
            console.style = ''

    def _handle_response(self, response, success_msg=True):
        """Handle API response with standard error checking."""
        if 'error' in response:
            self.operation_failed(response['error']['info'])
            sys.exit(errno.ENODATA)
        if success_msg:
            self.operation_ok()
        return response

    def _handle_response_with_default(self, response, default=None):
        """Handle API response returning default on not_found error."""
        if 'error' in response:
            if response['error']['code'] == requests.codes.not_found:
                self.operation_ok()
                return default
            self.operation_failed(response['error']['info'])
            sys.exit(errno.ENODATA)
        self.operation_ok()
        return response

    def _api_call(
        self,
        url_key,
        data=None,
        exit_on_error=True,
        log_name=None,
        safe=True,
        keys=None,
        upload_files=None,
        message=None,
    ):
        """Make API call with console status and logging."""
        if message:
            self._show_message(message)

        with self.console.status(''):
            response = self._url_request.run(
                url=self.api_endpoint(self.URLS[url_key]),
                data=data or {},
                debug=self._debug,
                exit_on_error=exit_on_error,
                safe=safe,
                keys=keys,
                upload_files=upload_files,
            )
        logger.debug('Response %s: %s', log_name or url_key, response)
        if self._debug:
            self.console.log(f'Response: {response}')

        return response

    def _report_error(self, msg):
        """Report error to console, logger and error file."""
        self.operation_failed(msg)
        logger.error(msg)
        self._write_error(msg)

    def cmd_version(self, args=None):
        if hasattr(args, 'quiet') and args.quiet:
            self.console.print(utils.get_mfc_release())
        else:
            self._show_config_options()

        sys.exit(utils.ALL_OK)

    def cmd_remove_keys(self, args=None):
        is_all = getattr(args, 'all', False)
        is_debug = getattr(args, 'debug', False)
        is_quiet = getattr(args, 'quiet', True)

        keys_path = settings.KEYS_PATH if is_all else self._get_keys_path()

        if is_debug:
            logger.debug(_('Trying to remove %s directory') % keys_path)

        try:
            shutil.rmtree(keys_path)
        except shutil.Error:
            if not is_quiet:
                self.console.print(_('An error occurred while deleting directory %s') % keys_path)
            sys.exit(errno.EPERM)
        except FileNotFoundError:
            if not is_quiet:
                self.console.print(_('No such directory %s') % keys_path)
            sys.exit(errno.EACCES)

        if not is_quiet:
            self.console.print(_('Directory %s has been removed') % keys_path)

        sys.exit(utils.ALL_OK)

    def cmd_import_mtls(self, cert_file):
        """Import mTLS certificate from tar file."""
        self._show_message(_('Importing mTLS certificate...'))

        result = mtls.import_mtls_certificate(cert_file)

        if result['success']:
            self.operation_ok(result['message'])
        else:
            self.operation_failed(result['message'])
            sys.exit(errno.EPERM)

        sys.exit(utils.ALL_OK)

    def run(self, args=None):
        self._init_command()

        if hasattr(args, 'debug') and args.debug:
            self._debug = True
            set_debug_log_level()

        if hasattr(args, 'quiet') and args.quiet:
            self._quiet = True

        if not self._quiet:
            self._show_config_options()
