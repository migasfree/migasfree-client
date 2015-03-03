#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Copyright (c) 2013-2015 Jose Antonio Chavarría
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
#
# Author: Jose Antonio Chavarría <jachavar@gmail.com>

__author__ = 'Jose Antonio Chavarría'
__license__ = 'GPLv3'
__all__ = ('MigasFreeCommand')

import os

from . import (
    settings,
    utils,
    network,
    url_request,
    printcolor,
)

version_file = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    'VERSION'
)
if not os.path.exists(version_file):
    version_file = os.path.join(settings.DOC_PATH, 'VERSION')

__version__ = open(version_file).read().splitlines()[0]

import sys
import errno
import getpass
import platform

import gettext
_ = gettext.gettext

import logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s',
    level=logging.INFO,
    filename=settings.LOG_FILE
)
logger = logging.getLogger(__name__)

from .pms import Pms

# implicit print flush
buf_arg = 0
if sys.version_info[0] == 3:
    os.environ['PYTHONUNBUFFERED'] = '1'
    buf_arg = 1

sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buf_arg)
sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', buf_arg)


class MigasFreeCommand(object):
    '''
    Interface class
    '''

    CMD = 'migasfree-command'  # /usr/bin/migasfree-command
    LOCK_FILE = os.path.join(settings.TMP_PATH, '%s.pid' % CMD)
    ERROR_FILE = os.path.join(settings.TMP_PATH, '%s.err' % CMD)

    PUBLIC_KEY = 'migasfree-server.pub'
    PRIVATE_KEY = 'migasfree-client.pri'

    ICON = 'apps/migasfree.svg'
    ICON_COMPLETED = 'actions/migasfree-ok.svg'

    _url_base = None
    _url_request = None

    _debug = False

    pms = None

    auto_register_user = ''
    auto_register_password = ''
    auto_register_end_point = 'public/keys/project/'

    _computer_id = None

    def __init__(self):
        _config_client = utils.get_config(settings.CONF_FILE, 'client')
        if type(_config_client) is not dict:
            _config_client = {}

        self.migas_project = os.environ.get(
            'MIGASFREE_CLIENT_PROJECT', utils.get_mfc_project()
        )
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

        self.migas_proxy = os.environ.get(
            'MIGASFREE_CLIENT_PROXY', _config_client.get('proxy', None)
        )
        self.migas_ssl_cert = os.environ.get(
            'MIGASFREE_CLIENT_SSL_CERT', _config_client.get('ssl_cert', None)
        )
        self.migas_package_proxy_cache = os.environ.get(
            'MIGASFREE_CLIENT_PACKAGE_PROXY_CACHE',
            _config_client.get('package_proxy_cache', None)
        )

        self.migas_gui_verbose = utils.cast_to_bool(
            os.environ.get(
                'MIGASFREE_CLIENT_GUI_VERBOSE',
                _config_client.get('gui_verbose', True)
            ),
            default=True
        )

        self._debug = utils.cast_to_bool(
            os.environ.get(
                'MIGASFREE_CLIENT_DEBUG',
                _config_client.get('debug', False)
            ),
            default=False
        )
        if self._debug:
            logger.setLevel(logging.DEBUG)

        _config_packager = utils.get_config(settings.CONF_FILE, 'packager')
        if type(_config_packager) is not dict:
            _config_packager = {}

        self.packager_user = os.environ.get(
            'MIGASFREE_PACKAGER_USER', _config_packager.get('user', None)
        )
        self.packager_pwd = os.environ.get(
            'MIGASFREE_PACKAGER_PASSWORD',
            _config_packager.get('password', None)
        )
        self.packager_version = os.environ.get(
            'MIGASFREE_PACKAGER_VERSION', _config_packager.get('version', None)
        )
        self.packager_store = os.environ.get(
            'MIGASFREE_PACKAGER_STORE', _config_packager.get('store', None)
        )

        # http://www.lightbird.net/py-by-example/logging.html
        logger.info('*' * 20)
        logger.info('%s in execution', self.CMD)
        logger.info('Config file: %s', settings.CONF_FILE)
        logger.debug('Config client: %s', _config_client)
        logger.debug('Config packager: %s', _config_packager)

        self._init_url_base()

        # init UrlRequest
        self._url_request = url_request.UrlRequest(
            debug=self._debug,
            proxy=self.migas_proxy,
            project=self.migas_project,
            keys={
                'private': self.PRIVATE_KEY,
                'public': self.PUBLIC_KEY
            },
            cert=self.migas_ssl_cert
        )

        self._pms_selection()

    def _init_url_base(self):
        self._url_base = '%s/api/v1/' % str(self.migas_server)
        if self.migas_ssl_cert:
            self._url_base = '%s://%s' % ('https', self._url_base)
        else:
            self._url_base = '%s://%s' % ('http', self._url_base)

    def _check_user_is_root(self):
        return utils.get_user_info(os.environ.get('USER'))['gid'] == 0

    def _user_is_not_root(self):
        if not self._check_user_is_root():
            self.operation_failed(
                _('User has insufficient privileges to execute this command')
            )
            sys.exit(errno.EACCES)

    def _check_sign_keys(self):
        _private_key = os.path.join(settings.KEYS_PATH, self.PRIVATE_KEY)
        _public_key = os.path.join(settings.KEYS_PATH, self.PUBLIC_KEY)
        if os.path.isfile(_private_key) and os.path.isfile(_public_key):
            if not self._computer_id:
                self.get_computer_id()

            return True  # all OK

        logger.warning('Security keys are not present!!!')
        return self._auto_register()

    def _check_keys_path(self):
        if not os.path.isdir(os.path.abspath(settings.KEYS_PATH)):
            try:
                os.makedirs(os.path.abspath(settings.KEYS_PATH))
            except:
                _msg = _('Error creating %s directory') % settings.KEYS_PATH
                self.operation_failed(_msg)
                logger.error(_msg)
                sys.exit(errno.ENOTDIR)

    def _auto_register(self):
        print(_('Autoregistering computer...'))

        if self._save_sign_keys(
            self.auto_register_user, self.auto_register_password
        ):
            return self._save_computer()

    def _save_sign_keys(self, user, password):
        response = self._url_request.run(
            url=self._url_base + self.auto_register_end_point,
            data={
                'username': user,
                'password': password,
                'project': self.migas_project,
                'platform': platform.system(),
                'pms': str(self.pms),
            },
            safe=False,
            debug=self._debug
        )
        logger.debug('Response _save_sign_keys: %s', response)

        self._check_keys_path()
        if self.PRIVATE_KEY not in response or self.PUBLIC_KEY not in response:
            msg = _('An error has occurred while autoregistering computer. '
            'Unable to continue.')
            self.operation_failed(msg)
            logger.error(msg)
            sys.exit(errno.ENOENT)

        for _file, _content in list(response.items()):
            _path_file = os.path.join(settings.KEYS_PATH, _file)
            logger.debug('Trying writing file: %s', _path_file)
            _ret = utils.write_file(_path_file, str(_content))
            if _ret:
                print(_('Key %s created!') % _path_file)
            else:
                msg = _('Error writing key file!!!')
                self.operation_failed(msg)
                logger.error(msg)
                sys.exit(errno.ENOENT)

        return True

    def _register_computer(self):
        _continue = utils.query_yes_no(
            _('Have you check config options in this machine (%s)?')
            % settings.CONF_FILE
        )
        if _continue == 'no':
            _msg = _('Check %s file and register again') % settings.CONF_FILE
            self.operation_failed(_msg)
            sys.exit(errno.EAGAIN)

        if not self._auto_register():
            _user = raw_input('%s: ' % _('User to register computer at server'))
            if not _user:
                self.operation_failed(_('Empty user. Exiting %s.') % self.CMD)
                logger.info('Empty user in register computer option')
                sys.exit(errno.EAGAIN)

            _pass = getpass.getpass('%s: ' % _('Password'))

            self._save_sign_keys(_user, _pass)
            self.operation_ok(_('Computer registered at server'))

    def _save_computer(self):
        response = self._url_request.run(
            url=self._url_base + 'safe/computers/',
            data={
                'uuid': utils.get_hardware_uuid(),
                'name': self.migas_computer_name,
                'ip_address': network.get_network_info()['ip']
            },
            debug=self._debug
        )
        logger.debug('Response _save_computer: %s', response)

        self._computer_id = response.get('id')
        return True

    def get_computer_id(self):
        if self._computer_id:
            return self._computer_id

        response = self._url_request.run(
            url=self._url_base + 'safe/computers/id/',
            data={
                'uuid': utils.get_hardware_uuid(),
                'name': self.migas_computer_name
            },
            debug=self._debug
        )
        logger.debug('Response get_computer_id: %s', response)

        self._computer_id = response
        return self._computer_id

    def _show_running_options(self):
        print('')
        print(_('Running options: %s') % settings.CONF_FILE)
        print('\t%s: %s' % (_('Project'), self.migas_project))
        print('\t%s: %s' % (_('Server'), self.migas_server))
        print('\t%s: %s' % (_('Auto update packages'), self.migas_auto_update_packages))
        print('\t%s: %s' % (_('Proxy'), self.migas_proxy))
        print('\t%s: %s' % (_('SSL certificate'), self.migas_ssl_cert))
        if self.migas_ssl_cert is not None and \
        not os.path.exists(self.migas_ssl_cert):
            print('\t\t%s: %s' % (_('Warning'), _('Certificate does not exist and authentication is not guaranteed')))
        print('\t%s: %s' % (
            _('Package Proxy Cache'),
            self.migas_package_proxy_cache
        ))
        print('\t%s: %s' % (_('Debug'), self._debug))
        print('\t%s: %s' % (_('Computer name'), self.migas_computer_name))
        print('\t%s: %s' % (_('GUI verbose'), self.migas_gui_verbose))
        print('\t%s: %s' % (_('PMS'), self.pms))
        print('')

    def _usage_examples(self):
        raise NotImplementedError

    def _search_pms(self):
        _pms_list = {
            'apt-get': 'Apt',
            'yum': 'Yum',
            'zypper': 'Zypper',
        }

        for _item in _pms_list:
            _cmd = 'which %s' % _item
            _ret, _output, _error = utils.execute(_cmd, interactive=False)
            if _ret == 0:
                return _pms_list[_item]

        return None  # if not found

    def _pms_selection(self):
        _pms_info = self._search_pms()
        logger.debug('PMS info: %s', _pms_info)
        if not _pms_info:
            logger.critical('Any PMS was not found. Cannot continue.')
            sys.exit(errno.EINPROGRESS)

        self.pms = Pms.factory(_pms_info)()

    def operation_ok(self, info=''):
        _msg = str(' ' + _('Ok')).rjust(38, '*')
        if info:
            _msg = str(info)

        printcolor.ok(_msg)

    def operation_failed(self, info=''):
        printcolor.fail(str(' ' + _('Failed')).rjust(38, '*'))
        if info:
            printcolor.fail(info)

    def run(self):
        raise NotImplementedError
