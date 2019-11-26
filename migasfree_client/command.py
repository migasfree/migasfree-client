# -*- coding: UTF-8 -*-

# Copyright (c) 2013-2019 Jose Antonio Chavarría <jachavar@gmail.com>
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
import pwd
import requests
import logging
import time
import ssl

import gettext
_ = gettext.gettext

try:
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urljoin

from . import (
    settings,
    utils,
    network,
    url_request,
    printcolor
)
from .pms import Pms

__author__ = 'Jose Antonio Chavarría <jachavar@gmail.com>'
__license__ = 'GPLv3'
__all__ = 'MigasFreeCommand'

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s',
    level=logging.INFO,
    filename=settings.LOG_FILE
)
logger = logging.getLogger(__name__)

# implicit print flush
buf_arg = 0
if sys.version_info[0] == 3:
    os.environ['PYTHONUNBUFFERED'] = '1'
    buf_arg = 1

sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buf_arg)
sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', buf_arg)


class MigasFreeCommand(object):
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
    LOCK_FILE = os.path.join(settings.TMP_PATH, '{}.pid'.format(CMD))
    ERROR_FILE = os.path.join(settings.TMP_PATH, '{}.err'.format(CMD))

    PUBLIC_KEY = 'server.pub'
    PRIVATE_KEY = ''
    REPOS_KEY = 'repositories.pub'

    ICON = 'apps/migasfree.svg'
    ICON_COMPLETED = 'actions/migasfree-ok.svg'

    _url_base = None
    _url_request = None

    _debug = False
    _quiet = False

    pms = None

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

        self.PRIVATE_KEY = '{}.pri'.format(self.migas_project)

        self.migas_computer_name = os.environ.get(
            'MIGASFREE_CLIENT_COMPUTER_NAME', utils.get_mfc_computer_name()
        )

        self.migas_server = os.environ.get(
            'MIGASFREE_CLIENT_SERVER',
            _config_client.get('server', 'localhost')
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
            logger.setLevel(logging.DEBUG)

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

        self._ssl_cert()
        self._pms_selection()
        self._init_url_base()
        self._init_url_request()
        self.get_server_info()

    def _ssl_cert(self):
        address = self.migas_server.split(':')
        host = address[0]
        port = int(address[1]) if len(address) == 2 else 80

        if os.path.isfile(settings.CERT_FILE):
            os.remove(settings.CERT_FILE)

        self.migas_ssl_cert = False
        try:
            cert = ssl.get_server_certificate((host, port), ssl.PROTOCOL_SSLv23)
            if utils.write_file(settings.CERT_FILE, cert):
                self.migas_ssl_cert = settings.CERT_FILE
        except:
            pass

    def _init_url_base(self):
        self._url_base = '{}://{}'.format(self.api_protocol(), self.migas_server)

    def _init_url_request(self):
        keys_path = os.path.join(settings.KEYS_PATH, self.migas_server)
        self._url_request = url_request.UrlRequest(
            debug=self._debug,
            proxy=self.migas_proxy,
            project=self.migas_project,
            keys={
                'private': os.path.join(keys_path, self.PRIVATE_KEY),
                'public': os.path.join(keys_path, self.PUBLIC_KEY)
            },
            cert=self.migas_ssl_cert
        )

    def api_protocol(self):
        return 'https' if self.migas_ssl_cert else 'http'

    def api_endpoint(self, path):
        return urljoin(self._url_base, path)

    @staticmethod
    def _show_message(msg):
        print('')
        printcolor.info(str(' ' + msg + ' ').center(76, '*'))

    def _check_path(self, path):
        if not os.path.isdir(path):
            try:
                os.makedirs(path)
            except OSError:
                _msg = _('Error creating %s directory') % path
                self.operation_failed(_msg)
                logging.error(_msg)
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
                logging.error(_msg)
                self._write_error(_msg)

    @staticmethod
    def _check_user_is_root():
        return pwd.getpwuid(os.getuid()).pw_gid == 0

    def _user_is_not_root(self):
        if not self._check_user_is_root():
            self.operation_failed(
                _('User has insufficient privileges to execute this command')
            )
            sys.exit(errno.EACCES)

    def _check_sign_keys(self, get_computer_id=True):
        private_key = os.path.join(
            settings.KEYS_PATH, self.migas_server, self.PRIVATE_KEY
        )
        public_key = os.path.join(
            settings.KEYS_PATH, self.migas_server, self.PUBLIC_KEY
        )
        repos_key = os.path.join(
            settings.KEYS_PATH, self.migas_server, self.REPOS_KEY
        )

        if os.path.isfile(private_key) and \
                os.path.isfile(public_key) and \
                os.path.isfile(repos_key):
            if get_computer_id and not self._computer_id:
                self.get_computer_id()

            return True  # all OK

        logger.warning('Security keys are not present!!!')
        return self._auto_register()

    def _auto_register(self):
        print(_('Autoregistering computer...'))

        if self._save_sign_keys(
            self.auto_register_user, self.auto_register_password
        ):
            return self._save_computer() != 0

    def _save_sign_keys(self, user, password):
        # API keys
        response = self._url_request.run(
            url=self.api_endpoint(self.auto_register_end_point),
            data={
                'username': user,
                'password': password,
                'project': self.migas_project,
                'platform': platform.system(),
                'pms': str(self.pms),
                'architecture': self.pms.get_system_architecture()
            },
            safe=False,
            exit_on_error=(user != self.auto_register_user),
            debug=self._debug
        )
        logger.debug('Response _save_sign_keys: %s', response)

        if isinstance(response, dict) and 'error' in response:
            if response['error']['code'] == errno.ECONNREFUSED:
                sys.exit(errno.ECONNREFUSED)

        if not self._check_path(os.path.join(
                os.path.abspath(settings.KEYS_PATH),
                self.migas_server
        )):
            sys.exit(errno.ENOTDIR)

        for _file, content in list(response.items()):
            if _file == 'migasfree-server.pub':
                _file = self.PUBLIC_KEY
            if _file == 'migasfree-client.pri':
                _file = self.PRIVATE_KEY
            if _file == 'migasfree-packager.pri':
                _file = self.PRIVATE_KEY

            path_file = os.path.join(
                settings.KEYS_PATH, self.migas_server, _file
            )
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
        logger.debug('Response _save_repos_key: {}'.format(response))

        path = os.path.abspath(
            os.path.join(settings.KEYS_PATH, self.migas_server)
        )
        if not self._check_path(path):
            return False

        path_file = os.path.join(path, self.REPOS_KEY)
        logger.debug('Trying writing file: {}'.format(path_file))

        ret = utils.write_file(path_file, response)
        if ret:
            if self.pms.import_server_key(path_file):
                print(_('Key %s created!') % path_file)
            else:
                print(_('ERROR: not import key: %s!') % path_file)
        else:
            msg = _('Error writing key file!!!')
            self.operation_failed(msg)
            logger.error(msg)
            return False

        return True

    def _register_computer(self, user=None):
        carry_on = utils.query_yes_no(
            _('Have you check config options in this machine (%s)?')
            % settings.CONF_FILE
        )
        if carry_on == 'no':
            msg = _('Check %s file and register again') % settings.CONF_FILE
            self.operation_failed(msg)
            sys.exit(errno.EAGAIN)

        if not self._auto_register():
            if not user:
                sys.stdin = open('/dev/tty')
                user = raw_input('%s: ' % _('User to register computer at server'))
                if not user:
                    self.operation_failed(_('Empty user. Exiting %s.') % self.CMD)
                    logger.info('Empty user in register computer option')
                    sys.exit(errno.EAGAIN)

            password = getpass.getpass('%s: ' % _('Password'))
            self._save_sign_keys(user, password)

        self.operation_ok(_('Computer registered at server'))

    def _save_computer(self):
        response = self._url_request.run(
            url=self.api_endpoint(self.URLS['upload_computer']),
            data={
                'uuid': utils.get_hardware_uuid(),
                'name': self.migas_computer_name,
                'ip_address': network.get_network_info()['ip']
            },
            debug=self._debug
        )
        logger.debug('Response _save_computer: {}'.format(response))

        self._computer_id = response.get('id')
        return self._computer_id

    def get_server_info(self):
        response = self._url_request.run(
            url=self.api_endpoint(self.URLS['get_server_info']),
            safe=False,
            exit_on_error=False,
            debug=self._debug
        )
        logger.debug('Response get_server_info: {}'.format(response))

        if isinstance(response, dict):
            self._server_info = response
    
    def get_computer_id(self):
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
        logger.debug('Response get_computer_id: {}'.format(response))

        if isinstance(response, dict) and 'error' in response:
            if response['error']['code'] == requests.codes.not_found:
                response = self._save_computer()
            else:
                self.operation_failed(response['error']['info'])
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
        logger.debug('Response end_of_transmission: {}'.format(response))

    def _show_running_options(self):
        conf_file = ''
        if os.path.isfile(settings.CONF_FILE):
            conf_file = settings.CONF_FILE

        print('')
        print(_('Running options: %s') % conf_file)
        print('\t%s: %s' % (_('Project'), self.migas_project))
        print('\t%s: %s' % (_('Server'), self.migas_server))
        print('\t%s: %s' % (
            _('migasfree server version'), self._server_info.get('version', _('None')))
        )
        print('\t%s: %s' % (
            _('Auto update packages'), self.migas_auto_update_packages
        ))
        print('\t%s: %s' % (_('Manage devices'), self.migas_manage_devices))
        print('\t%s: %s' % (_('Proxy'), self.migas_proxy))
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
        print('\t%s: %s' % (
            _('Package Proxy Cache'),
            self.migas_package_proxy_cache
        ))
        print('\t%s: %s' % (_('Debug'), self._debug))
        print('\t%s: %s' % (_('Computer name'), self.migas_computer_name))
        print('\t%s: %s' % (_('PMS'), self.pms))
        print('')

    def _write_error(self, msg, append=False):
        if append:
            _mode = 'a'
        else:
            _mode = 'wb'

        if not self._error_file_descriptor:
            self._error_file_descriptor = open(self.ERROR_FILE, _mode)

        self._error_file_descriptor.write('%s\n' % ('-' * 20))
        self._error_file_descriptor.write(
            '%s\n' % time.strftime("%Y-%m-%d %H:%M:%S")
        )
        self._error_file_descriptor.write('%s\n\n' % str(msg))

    def _usage_examples(self):
        raise NotImplementedError

    @staticmethod
    def _search_pms():
        pms_list = {
            'apt-get': 'Apt',
            'yum': 'Yum',
            'zypper': 'Zypper',
        }

        for item in pms_list:
            cmd = 'which {}'.format(item)
            ret, _, _ = utils.execute(cmd, interactive=False)
            if ret == 0:
                return pms_list[item]

        return None  # if not found

    def _pms_selection(self):
        pms_info = self._search_pms()
        logger.debug('PMS info: {}'.format(pms_info))
        if not pms_info:
            msg = _('Any PMS was not found. Cannot continue.')
            self.operation_failed(msg)
            logger.critical(msg)
            sys.exit(errno.EINPROGRESS)

        self.pms = Pms.factory(pms_info)()

    @staticmethod
    def operation_ok(info=''):
        if info:
            msg = str(info)
        else:
            msg = str(' ' + _('Ok')).rjust(38, '*')

        printcolor.ok(msg)

    @staticmethod
    def operation_failed(info=''):
        printcolor.fail(str(' ' + _('Failed')).rjust(38, '*'))
        if info:
            printcolor.fail(info)

    def run(self, args=None):
        raise NotImplementedError
