# -*- coding: UTF-8 -*-

# Copyright (c) 2013-2025 Jose Antonio Chavarría <jachavar@gmail.com>
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

import os
import sys
import errno
import getpass
import platform
import logging
import logging.config
import logging.handlers
import time
import ssl
import gettext
import shutil
import requests

from rich import print
from rich.console import Console
from urllib.parse import urljoin

from .network import get_network_info
from .pms import Pms, get_available_pms
from .devices import Printer, get_available_devices_classes
from .url_request import UrlRequest

from . import settings, utils

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
            'level': 'WARNING'
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
except (IOError, ValueError):
    print(_('Failed to configure the log file (%s)') % settings.LOG_FILE)
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


class MigasFreeCommand():
    """
    Interface class
    """

    URLS = {
        # command API
        'get_server_info': '/api/v1/public/server/info/',
        'get_project_keys': '/api/v1/public/keys/project/',
        'get_repositories_keys': '/api/v1/public/keys/repositories/',
        'get_computer_id': '/api/v1/safe/computers/id/',
        'upload_computer': '/api/v1/safe/computers/',
        'upload_eot': '/api/v1/safe/eot/',

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

        # label API
        'get_label': '/api/v1/safe/computers/label/',

        # tags API
        'get_assigned_tags': '/api/v1/safe/computers/tags/assigned/',
        'get_available_tags': '/api/v1/safe/computers/tags/available/',
        'upload_tags': '/api/v1/safe/computers/tags/',

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
    REPOS_KEY = 'repositories.pub'

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

    def __init__(self):
        _config_client = utils.get_config(settings.CONF_FILE, 'client')
        if not isinstance(_config_client, dict):
            _config_client = {}

        self.migas_project = os.environ.get(
            'MIGASFREE_CLIENT_PROJECT', utils.get_mfc_project()
        )

        self.PRIVATE_KEY = f'{self.migas_project}.pri'

        self.migas_computer_name = os.environ.get(
            'MIGASFREE_CLIENT_COMPUTER_NAME', utils.get_mfc_computer_name()
        )

        self.migas_server = os.environ.get(
            'MIGASFREE_CLIENT_SERVER',
            _config_client.get('server', 'localhost')
        )

        self.migas_port = os.environ.get(
            'MIGASFREE_CLIENT_PORT',
            _config_client.get('port', '')
        )

        self.migas_protocol = os.environ.get(
            'MIGASFREE_CLIENT_PROTOCOL',
            _config_client.get('protocol', 'http')
        )

        self.migas_auto_update_packages = utils.cast_to_bool(
            os.environ.get(
                'MIGASFREE_CLIENT_AUTO_UPDATE_PACKAGES',
                _config_client.get('auto_update_packages', True)
            ),
            default=True
        )

        self.migas_manage_devices = utils.cast_to_bool(
            os.environ.get(
                'MIGASFREE_CLIENT_MANAGE_DEVICES',
                _config_client.get('manage_devices', True)
            ),
            default=True
        )

        self.migas_upload_hardware = utils.cast_to_bool(
            os.environ.get(
                'MIGASFREE_CLIENT_UPLOAD_HARDWARE',
                _config_client.get('upload_hardware', True)
            ),
            default=True
        )

        self.migas_proxy = os.environ.get(
            'MIGASFREE_CLIENT_PROXY', _config_client.get('proxy', None)
        )
        self.migas_package_proxy_cache = os.environ.get(
            'MIGASFREE_CLIENT_PACKAGE_PROXY_CACHE',
            _config_client.get('package_proxy_cache', None)
        )

        self._debug = utils.cast_to_bool(
            os.environ.get(
                'MIGASFREE_CLIENT_DEBUG',
                _config_client.get('debug', False)
            )
        )
        if self._debug:
            set_debug_log_level()

        _config_packager = utils.get_config(settings.CONF_FILE, 'packager')
        if not isinstance(_config_packager, dict):
            _config_packager = {}

        self.packager_user = os.environ.get(
            'MIGASFREE_PACKAGER_USER', _config_packager.get('user', None)
        )
        self.packager_pwd = os.environ.get(
            'MIGASFREE_PACKAGER_PASSWORD',
            _config_packager.get('password', None)
        )
        self.packager_project = os.environ.get(
            'MIGASFREE_PACKAGER_PROJECT', _config_packager.get('project', None)
        )
        self.packager_store = os.environ.get(
            'MIGASFREE_PACKAGER_STORE', _config_packager.get('store', None)
        )

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
                cert = ssl.get_server_certificate(
                    (self.migas_server, port),
                    ssl.PROTOCOL_SSLv23
                )
                if utils.write_file(settings.CERT_FILE, cert):
                    self.migas_ssl_cert = settings.CERT_FILE
            except ssl.SSLError:
                pass
            except OSError as e:
                _msg = _('Error getting server certificate: %s') % e
                self.operation_failed(_msg)
                sys.exit(errno.ECONNREFUSED)

    def _get_keys_path(self):
        return os.path.join(
            settings.KEYS_PATH,
            utils.sanitize_path(self.migas_server)
        )

    def _init_url_base(self):
        self._url_base = '{}://{}{}'.format(
            self.migas_protocol,
            self.migas_server,
            f':{self.migas_port}' if self.migas_port else ''
        )

    def _init_url_request(self):
        keys_path = self._get_keys_path()
        self._url_request = UrlRequest(
            debug=self._debug,
            proxy=self.migas_proxy,
            project=self.migas_project,
            keys={
                'private': os.path.join(keys_path, self.PRIVATE_KEY),
                'public': os.path.join(keys_path, self.PUBLIC_KEY)
            },
            cert=self.migas_ssl_cert
        )

    def _init_command(self):
        self._ssl_cert()
        self.pms_selection()
        self._init_url_base()
        self._init_url_request()
        self.get_server_info()

    def api_protocol(self):
        return self.migas_protocol

    def api_endpoint(self, path):
        return urljoin(self._url_base, path)

    def _show_message(self, msg):
        print()
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
            _ret, _output, _error = utils.execute(
                os.path.join(path, file_),
                verbose=True,
                interactive=False
            )
            if _ret == 0:
                self.operation_ok()
            else:
                _msg = _('Command %s failed: %s') % (file_, _error)
                self.operation_failed(_msg)
                logger.error(_msg)
                self._write_error(_msg)

    def _check_user_is_root(self):
        if not utils.is_root_user():
            self.operation_failed(
                _('User has insufficient privileges to execute this command')
            )
            sys.exit(errno.EACCES)

    def _check_sign_keys(self, get_computer_id=True):
        keys_path = self._get_keys_path()

        paths = {
            'private': os.path.join(keys_path, self.PRIVATE_KEY),
            'public': os.path.join(keys_path, self.PUBLIC_KEY),
            'repos': os.path.join(keys_path, self.REPOS_KEY),
        }

        all_keys_exist = all(os.path.isfile(path) for path in paths.values())

        if all_keys_exist:
            if get_computer_id and not self._computer_id:
                self.get_computer_id()

            return True  # all OK

        missing_keys = [key for key, path in paths.items() if not os.path.isfile(path)]
        logger.warning('Security keys are not present!!!', ', '.join(missing_keys))
        return self._auto_register()

    def _auto_register(self):
        self._show_message(_('Autoregistering computer...'))

        if self._save_sign_keys(
                self.auto_register_user, self.auto_register_password
        ):
            return self._save_computer(
                self.auto_register_user, self.auto_register_password
            ) != 0

        return False

    def _save_sign_keys(self, user, password):
        exit_on_error = user != self.auto_register_user

        # API keys
        response = self._url_request.run(
            url=self.api_endpoint(self.auto_register_end_point),
            data={
                'username': user,
                'password': password,
                'project': self.migas_project,
                'platform': platform.system(),
                'pms': str(self.pms),
                'architecture': self.pms.get_system_architecture() if self.pms else ''
            },
            safe=False,
            exit_on_error=exit_on_error,
            debug=self._debug
        )
        logger.debug('Response _save_sign_keys: %s', response)

        if isinstance(response, dict) and 'error' in response:
            if 'code' in response['error']:
                self.operation_failed(response['error']['info'])
                logger.error(response['error']['info'])
                if exit_on_error:
                    sys.exit(response['error']['code'])

                return False

            self.operation_failed(response['error'])
            logger.error(response['error'])
            if exit_on_error:
                sys.exit(errno.EPERM)

            return False

        if not self._check_path(self._get_keys_path()):
            sys.exit(errno.ENOTDIR)

        for _file, content in list(response.items()):
            if _file == 'migasfree-server.pub':
                _file = self.PUBLIC_KEY
            if _file == 'migasfree-client.pri':
                _file = self.PRIVATE_KEY
            if _file == 'migasfree-packager.pri':
                _file = self.PRIVATE_KEY

            path_file = os.path.join(self._get_keys_path(), _file)
            logger.debug('Trying writing file: %s', path_file)

            ret = utils.write_file(path_file, str(content))
            if ret:
                print(_('Key %s created!') % path_file)
            else:
                msg = _('Error writing key file!!!')
                self.operation_failed(msg)
                logger.error(msg)
                sys.exit(errno.ENOENT)

        # Repositories key
        return self._save_repos_key()

    def _save_repos_key(self):
        response = self._url_request.run(
            url=self.api_endpoint(self.URLS['get_repositories_keys']),
            safe=False,
            exit_on_error=False,
            debug=self._debug
        )
        logger.debug('Response _save_repos_key: %s', response)

        path = self._get_keys_path()
        if not self._check_path(path):
            return False

        path_file = os.path.join(path, self.REPOS_KEY)
        logger.debug('Trying writing file: %s', path_file)

        ret = utils.write_file(path_file, response)
        if ret:
            if self.pms.import_server_key(path_file):
                print(_('Key %s created!') % path_file)
            else:
                print(_('ERROR: not import key: %s!') % path_file)

            return True

        msg = _('Error writing key file!!!')
        self.operation_failed(msg)
        logger.error(msg)

        return False

    def cmd_register_computer(self, user=None):
        carry_on = utils.query_yes_no(
            _('Have you check config options in this machine (%s)?')
            % settings.CONF_FILE
        )
        if carry_on == 'no':
            msg = _('Check %s file and register again') % settings.CONF_FILE
            self.operation_failed(msg)
            sys.exit(errno.EAGAIN)

        if not self._auto_register():
            sys.stdin = open('/dev/tty')
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

    def _save_computer(self, user, password):
        response = self._url_request.run(
            url=self.api_endpoint(self.URLS['upload_computer']),
            data={
                'uuid': utils.get_hardware_uuid(),
                'name': self.migas_computer_name,
                'ip_address': get_network_info()['ip'],
                'username': user,
                'password': password
            },
            exit_on_error=False,
            debug=self._debug
        )
        logger.debug('Response _save_computer: %s', response)

        if isinstance(response, dict) and 'error' in response:
            if response['error']['code'] == requests.codes.unauthorized:
                self.operation_failed(
                    '{} ({})'.format(
                        response['error']['info'],
                        _('You must register the computer with a valid user')
                    )
                )
                sys.exit(errno.EPERM)

            self.operation_failed(response['error']['info'])
            if response['error']['code'] == requests.codes.not_found:
                sys.exit(errno.ENODATA)

        return response.get('id', 0)  # computer ID

    def get_server_info(self):
        response = self._url_request.run(
            url=self.api_endpoint(self.URLS['get_server_info']),
            safe=False,
            exit_on_error=False,
            debug=self._debug
        )
        logger.debug('Response get_server_info: %s', response)

        if isinstance(response, dict):
            self._server_info = response

    def get_computer_id(self):
        if not os.path.isfile(
            os.path.join(self._get_keys_path(), self.PRIVATE_KEY)
        ):
            return 0

        if not self._url_base:
            self._init_command()

        if self._computer_id:
            return self._computer_id

        response = self._url_request.run(
            url=self.api_endpoint(self.URLS['get_computer_id']),
            data={
                'uuid': utils.get_hardware_uuid(),
                'name': self.migas_computer_name
            },
            exit_on_error=False,
            debug=self._debug
        )
        logger.debug('Response get_computer_id: %s', response)

        if isinstance(response, dict) and 'error' in response:
            if response['error']['code'] == requests.codes.not_found:
                response = self._save_computer(
                    self.auto_register_user, self.auto_register_password
                )
            else:
                self.operation_failed(
                    '{} ({})'.format(
                        response['error']['info'],
                        _('Review keys or register computer again')
                    )
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
            debug=self._debug
        )
        logger.debug('Response end_of_transmission: %s', response)

    def _show_config_options(self):
        conf_file = ''
        if os.path.isfile(settings.CONF_FILE):
            conf_file = settings.CONF_FILE

        print()
        print(_('Config options: %s') % conf_file)
        print('\t%s: %s %s' % (
            _('Project'),
            self.migas_project,
            '(ENV)' if 'MIGASFREE_CLIENT_PROJECT' in os.environ else ''
        ))
        print('\t%s: %s %s' % (
            _('Server'),
            self.migas_server,
            '(ENV)' if 'MIGASFREE_CLIENT_SERVER' in os.environ else ''
        ))
        print('\t%s: %s %s' % (
            _('Protocol'),
            self.migas_protocol,
            '(ENV)' if 'MIGASFREE_CLIENT_PROTOCOL' in os.environ else ''
        ))
        if self.migas_port:
            print('\t%s: %s %s' % (
                _('Port'),
                self.migas_port,
                '(ENV)' if 'MIGASFREE_CLIENT_PORT' in os.environ else ''
            ))
        print('\t%s: %s %s' % (
            _('Auto update packages'),
            self.migas_auto_update_packages,
            '(ENV)' if 'MIGASFREE_CLIENT_AUTO_UPDATE_PACKAGES' in os.environ else ''
        ))
        print('\t%s: %s %s' % (
            _('Manage devices'),
            self.migas_manage_devices,
            '(ENV)' if 'MIGASFREE_CLIENT_MANAGE_DEVICES' in os.environ else ''
        ))
        print('\t%s: %s %s' % (
            _('Upload hardware'),
            self.migas_upload_hardware,
            '(ENV)' if 'MIGASFREE_CLIENT_UPLOAD_HARDWARE' in os.environ else ''
        ))
        print('\t%s: %s %s' % (
            _('Proxy'),
            self.migas_proxy,
            '(ENV)' if 'MIGASFREE_CLIENT_PROXY' in os.environ else ''
        ))
        print('\t%s: %s %s' % (
            _('Package Proxy Cache'),
            self.migas_package_proxy_cache,
            '(ENV)' if 'MIGASFREE_CLIENT_PACKAGE_PROXY_CACHE' in os.environ else ''
        ))
        print('\t%s: %s %s' % (
            _('Debug'),
            self._debug,
            '(ENV)' if 'MIGASFREE_CLIENT_DEBUG' in os.environ else ''
        ))
        print('\t%s: %s %s' % (
            _('Computer name'),
            self.migas_computer_name,
            '(ENV)' if 'MIGASFREE_CLIENT_COMPUTER_NAME' in os.environ else ''
        ))

    def _show_running_options(self):
        print()
        print(_('Running options:'))
        print('\t%s: %s' % (
            _('migasfree server version'), self._server_info.get('version', _('None')))
        )
        print('\t%s: %s' % (_('SSL certificate'), self.migas_ssl_cert))
        if self.migas_ssl_cert is not None \
                and not isinstance(self.migas_ssl_cert, bool) \
                and not os.path.exists(self.migas_ssl_cert):
            print(
                '\t\t%s: %s' % (
                    _('Warning'),
                    _('Certificate does not exist and authentication is not guaranteed')
                )
            )
        print('\t%s: %s' % (_('PMS'), self.pms))
        if self.pms:
            print('\t%s: %s' % (_('Architecture'), self.pms.get_system_architecture()))

    def _write_error(self, msg, append=False):
        if append:
            _mode = 'a'
        else:
            _mode = 'wb'

        if not self._error_file_descriptor:
            self._error_file_descriptor = open(self.ERROR_FILE, _mode, encoding='utf8')

        _text = '{}\n{}\n{}\n\n'.format(
            '-' * 20,
            time.strftime("%Y-%m-%d %H:%M:%S"),
            str(msg)
        )
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

    def cmd_version(self, args=None):
        if hasattr(args, 'quiet') and args.quiet:
            print(utils.get_mfc_release())
        else:
            self._show_config_options()

        sys.exit(utils.ALL_OK)

    def cmd_remove_keys(self, args=None):
        if hasattr(args, 'all') and args.all:
            keys_path = settings.KEYS_PATH
        else:
            keys_path = self._get_keys_path()

        if hasattr(args, 'debug') and args.debug:
            print(_('Trying to remove %s directory') % keys_path)

        try:
            shutil.rmtree(keys_path)
        except shutil.Error:
            if hasattr(args, 'quiet') and not args.quiet:
                print(_('An error occurred while deleting directory %s') % keys_path)
            sys.exit(errno.EPERM)
        except FileNotFoundError:
            if hasattr(args, 'quiet') and not args.quiet:
                print(_('No such directory %s') % keys_path)
            sys.exit(errno.EACCES)

        if hasattr(args, 'quiet') and not args.quiet:
            print(_('Directory %s has been removed') % keys_path)

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
