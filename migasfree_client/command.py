#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Copyright (c) 2013 Jose Antonio Chavarría
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
__all__ = ('MigasFreeCommand', 'operation_ok', 'operation_failed')

import os

# package imports
"""
from . import (
    settings,
    utils,
    url_request
)
"""
import settings
import utils
import url_request
import printcolor

version_file = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    'VERSION'
)
if not os.path.exists(version_file):
    version_file = os.path.join(settings.DOC_PATH, 'VERSION')

__version__ = open(version_file).read().splitlines()[0]

import sys
import logging
import errno
import getpass
import platform

import gettext
_ = gettext.gettext

from backends import Pms


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

    _url_request = None

    _debug = False

    pms = None

    def __init__(self):
        _config_client = utils.get_config(settings.CONF_FILE, 'client')

        self.migas_version = utils.get_mfc_version()
        self.migas_computer_name = utils.get_mfc_computer_name()
        if type(_config_client) is dict:
            self.migas_server = _config_client.get('server', 'migasfree.org')
            self.migas_proxy = _config_client.get('proxy', None)
            self.migas_ssl_cert = _config_client.get('ssl_cert', None)
            self.migas_package_proxy_cache = _config_client.get(
                'package_proxy_cache',
                None
            )

            self.migas_gui_verbose = True  # by default
            if 'gui_verbose' in _config_client:
                if _config_client['gui_verbose'] == 'False' \
                or _config_client['gui_verbose'] == '0' \
                or _config_client['gui_verbose'] == 'Off':
                    self.migas_gui_verbose = False

            if 'debug' in _config_client:
                if _config_client['debug'] == 'True' \
                or _config_client['debug'] == '1' \
                or _config_client['debug'] == 'On':
                    self._debug = True
                    _log_level = logging.DEBUG

        _config_packager = utils.get_config(settings.CONF_FILE, 'packager')
        if type(_config_packager) is dict:
            self.packager_user = _config_packager.get('user', None)
            self.packager_pwd = _config_packager.get('password', None)
            self.packager_version = _config_packager.get('version', None)
            self.packager_store = _config_packager.get('store', None)

        # http://www.lightbird.net/py-by-example/logging.html
        _log_level = logging.INFO
        logging.basicConfig(
            format='%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s',
            level=_log_level,
            filename=settings.LOG_FILE
        )
        logging.info('*' * 20)
        logging.info('%s in execution', self.CMD)
        logging.debug('Config client: %s', _config_client)
        logging.debug('Config packager: %s', _config_packager)

        # init UrlRequest
        _url_base = '%s/api/' % str(self.migas_server)
        if self.migas_ssl_cert:
            _url_base = '%s://%s' % ('https', _url_base)
        else:
            _url_base = '%s://%s' % ('http', _url_base)
        self._url_request = url_request.UrlRequest(
            debug=self._debug,
            url_base=_url_base,
            proxy=self.migas_proxy,
            info_keys={
                'path': settings.KEYS_PATH,
                'private': self.PRIVATE_KEY,
                'public': self.PUBLIC_KEY
            },
            cert=self.migas_ssl_cert
        )

        self._pms_selection()

    def _check_sign_keys(self):
        _private_key = os.path.join(settings.KEYS_PATH, self.PRIVATE_KEY)
        _public_key = os.path.join(settings.KEYS_PATH, self.PUBLIC_KEY)
        if os.path.isfile(_private_key) and os.path.isfile(_public_key):
            return  # all OK

        logging.warning('Security keys are not present!!!')
        self._auto_register()

    def _auto_register(self):
        # try to get keys
        _data = {
            'username': '',
            'password': '',
            'version': self.migas_version,
            'platform': platform.system(),  # new for server 3.0
            'pms': str(self.pms),  # new for server 3.0
        }
        print(_('Autoregistering computer...'))

        return self._save_sign_keys(_data)

    def _save_sign_keys(self, data):
        if not os.path.isdir(os.path.abspath(settings.KEYS_PATH)):
            try:
                os.makedirs(os.path.abspath(settings.KEYS_PATH))
            except:
                _msg = _('Error creating %s directory') % settings.KEYS_PATH
                self.operation_failed(_msg)
                logging.error(_msg)
                sys.exit(errno.ENOTDIR)

        _response = self._url_request.run(
            'register_computer',
            data=data,
            sign=False
        )
        logging.debug('Response _save_sign_keys: %s', _response)

        if 'errmfs' in _response:
            _msg = _response['errmfs']['info']
            self.operation_failed(_msg)
            logging.error(_msg)
            sys.exit(errno.ENOENT)

        for _file, _content in list(_response.items()):
            _path_file = os.path.join(settings.KEYS_PATH, _file)
            logging.debug('Trying writing file: %s', _path_file)
            _ret = utils.write_file(_path_file, str(_content))
            if _ret:
                print(_('Key %s created!') % _path_file)
            else:
                _msg = _('Error writing key file!!!')
                self.operation_failed(_msg)
                logging.error(_msg)
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

        _user = raw_input('%s: ' % _('User to register computer at server'))
        if not _user:
            self.operation_failed(_('Empty user. Exiting %s.') % self.CMD)
            logging.info('Empty user in register computer option')
            sys.exit(errno.EAGAIN)

        _pass = getpass.getpass('%s: ' % _('Password'))

        _data = {
            'username': _user,
            'password': _pass,
            'version': self.migas_version,
            'platform': platform.system(),  # new for server 3.0
            'pms': str(self.pms),  # new for server 3.0
        }
        self._save_sign_keys(_data)
        self.operation_ok(_('Computer registered at server'))

    def _show_running_options(self):
        print('')
        print(_('Running options:'))
        print('\t%s: %s' % (_('Version'), self.migas_version))
        print('\t%s: %s' % (_('Server'), self.migas_server))
        print('\t%s: %s' % (_('Proxy'), self.migas_proxy))
        print('\t%s: %s' % (_('SSL certificate'), self.migas_ssl_cert))
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
            'zypper': 'Zypper',
            'yum': 'Yum',
            'apt-get': 'Apt'
        }

        for _item in _pms_list:
            _cmd = 'which %s' % _item
            _ret, _output, _error = utils.execute(_cmd, interactive=False)
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
