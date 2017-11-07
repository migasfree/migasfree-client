#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Copyright (c) 2013-2017 Jose Antonio Chavarría <jachavar@gmail.com>
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
import logging
import errno
import getpass
import platform

from . import (
    settings,
    utils,
    url_request,
    printcolor,
    curl
)

from .backends import Pms

import gettext
_ = gettext.gettext

__author__ = 'Jose Antonio Chavarría'
__license__ = 'GPLv3'
__all__ = 'MigasFreeCommand'

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

    release = utils.get_mfc_release()

    CMD = 'migasfree-command'  # /usr/bin/migasfree-command
    LOCK_FILE = os.path.join(settings.TMP_PATH, '{0}.pid'.format(CMD))
    ERROR_FILE = os.path.join(settings.TMP_PATH, '{0}.err'.format(CMD))

    PUBLIC_KEY = 'server.pub'
    PRIVATE_KEY = ''
    REPOS_KEY = 'repositories.pub'

    ICON = 'apps/migasfree.svg'
    ICON_COMPLETED = 'actions/migasfree-ok.svg'

    _url_request = None

    _debug = False

    pms = None

    auto_register_user = ''
    auto_register_password = ''
    auto_register_command = 'register_computer'
    get_key_repositories_command = 'get_key_repositories'

    def __init__(self):
        _log_level = logging.INFO

        _config_client = utils.get_config(settings.CONF_FILE, 'client')
        if not isinstance(_config_client, dict):
            _config_client = {}

        self.migas_project = os.environ.get(
            'MIGASFREE_CLIENT_PROJECT',
            os.environ.get(
                'MIGASFREE_CLIENT_VERSION',  # backwards compatibility
                utils.get_mfc_project()
            )
        )

        self.PRIVATE_KEY = '{0}.pri'.format(self.migas_project)

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
            )
        )
        if self._debug:
            _log_level = logging.DEBUG

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
            'MIGASFREE_PACKAGER_PROJECT',
            os.environ.get(
                'MIGASFREE_PACKAGER_VERSION',  # backwards compatibility
                _config_packager.get(
                    'project',
                    _config_packager.get(
                        'version',  # backwards compatibility
                        None
                    )
                )
            )
        )
        self.packager_store = os.environ.get(
            'MIGASFREE_PACKAGER_STORE', _config_packager.get('store', None)
        )

        # http://www.lightbird.net/py-by-example/logging.html
        logging.basicConfig(
            format='%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s',
            level=_log_level,
            filename=settings.LOG_FILE
        )
        logging.info('*' * 20)
        logging.info('%s in execution', self.CMD)
        logging.info('Config file: %s', settings.CONF_FILE)
        logging.debug('Config client: %s', _config_client)
        logging.debug('Config packager: %s', _config_packager)

        self._pms_selection()
        self._init_url_request()

    def _init_url_request(self):
        _url_base = '{0}/api/'.format(self.migas_server)
        if self.migas_ssl_cert:
            _url_base = '{0}://{1}'.format('https', _url_base)
        else:
            _url_base = '{0}://{1}'.format('http', _url_base)
        self._url_request = url_request.UrlRequest(
            debug=self._debug,
            url_base=_url_base,
            proxy=self.migas_proxy,
            info_keys={
                'path': os.path.join(settings.KEYS_PATH, self.migas_server),
                'private': self.PRIVATE_KEY,
                'public': self.PUBLIC_KEY
            },
            cert=self.migas_ssl_cert
        )

    def _check_user_is_root(self):
        return utils.get_user_info(os.environ.get('USER'))['gid'] == 0

    def _user_is_not_root(self):
        if not self._check_user_is_root():
            self.operation_failed(
                _('User has insufficient privileges to execute this command')
            )
            sys.exit(errno.EACCES)

    def _check_sign_keys(self):
        _private_key = os.path.join(
            settings.KEYS_PATH, self.migas_server, self.PRIVATE_KEY
        )
        _public_key = os.path.join(
            settings.KEYS_PATH, self.migas_server, self.PUBLIC_KEY
        )
        _repos_key = os.path.join(
            settings.KEYS_PATH, self.migas_server, self.REPOS_KEY
        )
        if os.path.isfile(_private_key) and \
                os.path.isfile(_public_key) and \
                os.path.isfile(_repos_key):
            return True  # all OK

        logging.warning('Security keys are not present!!!')
        return self._auto_register()

    def _auto_register(self):
        # try to get keys
        print(_('Autoregistering computer...'))

        return self._save_sign_keys(
            self.auto_register_user,
            self.auto_register_password
        )

    def _save_sign_keys(self, user, password):
        # API keys
        _response = self._url_request.run(
            self.auto_register_command,
            data={
                'username': user,
                'password': password,
                'project': self.migas_project,
                'version': self.migas_project,  # backwards compatibility
                'platform': platform.system(),
                'pms': str(self.pms),
            },
            sign=False,
            exit_on_error=(user != self.auto_register_user)
        )
        logging.debug('Response _save_sign_keys: %s', _response)

        if not os.path.isdir(os.path.abspath(settings.KEYS_PATH)):
            try:
                os.makedirs(os.path.abspath(settings.KEYS_PATH))
            except OSError:
                _msg = _('Error creating %s directory') % settings.KEYS_PATH
                self.operation_failed(_msg)
                logging.error(_msg)
                return False

        if 'errmfs' in _response:
            _msg = _response['errmfs']['info']
            self.operation_failed(_msg)
            logging.error(_msg)

            if _response['errmfs']['code'] == errno.ECONNREFUSED:
                sys.exit(errno.ECONNREFUSED)

            return False

        for _file, _content in list(_response.items()):
            if _file == "migasfree-server.pub":
                _file = self.PUBLIC_KEY
            if _file == "migasfree-client.pri":
                _file = self.PRIVATE_KEY
            if _file == "migasfree-packager.pri":
                _file = self.PRIVATE_KEY

            _path_file = os.path.join(
                settings.KEYS_PATH, self.migas_server, _file
            )
            logging.debug('Trying writing file: %s', _path_file)
            _ret = utils.write_file(_path_file, str(_content))
            if _ret:
                print(_('Key %s created!') % _path_file)
            else:
                _msg = _('Error writing key file!!!')
                self.operation_failed(_msg)
                logging.error(_msg)
                return False

        # Repositories key
        return self._save_repos_key()

    def _save_repos_key(self):
        _curl = curl.Curl(
            '{0}/{1}'.format(
                self.migas_server,
                self.get_key_repositories_command
            ),
            proxy=self.migas_proxy,
            cert=self.migas_ssl_cert,
        )
        _curl.run()

        _response = str(_curl.body)

        logging.debug('Response _save_repos_key: %s', _response)

        _path = os.path.abspath(
            os.path.join(settings.KEYS_PATH, self.migas_server)
        )
        if not os.path.isdir(_path):
            try:
                os.makedirs(_path)
            except OSError:
                _msg = _('Error creating %s directory') % _path
                self.operation_failed(_msg)
                logging.error(_msg)
                return False

        _path_file = os.path.join(_path, self.REPOS_KEY)
        logging.debug('Trying writing file: %s', _path_file)
        _ret = utils.write_file(_path_file, _response)
        if _ret:
            if self.pms.import_server_key(_path_file):
                print(_('Key %s created!') % _path_file)
            else:
                print(_('ERROR: not import key: %s!') % _path_file)
        else:
            _msg = _('Error writing key file!!!')
            self.operation_failed(_msg)
            logging.error(_msg)
            return False

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
                logging.info('Empty user in register computer option')
                sys.exit(errno.EAGAIN)

            _pass = getpass.getpass('%s: ' % _('Password'))

            self._save_sign_keys(_user, _pass)
            self.operation_ok(_('Computer registered at server'))

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
            _cmd = 'which {0}'.format(_item)
            _ret, _, _ = utils.execute(_cmd, interactive=False)
            if _ret == 0:
                return _pms_list[_item]

        return None  # if not found

    def _pms_selection(self):
        _pms_info = self._search_pms()
        logging.debug('PMS info: %s', _pms_info)
        if not _pms_info:
            logging.critical('Any PMS was not found. Cannot continue.')
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
