#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Copyright (c) 2011-2013 Jose Antonio Chavarría
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
__file__ = 'client.py'
__date__ = '2013-01-26'
__version__ = '3.0'
__license__ = 'GPLv3'
__all__ = ('MigasFreeClient', 'main')

import os
import sys
import errno
import logging
import optparse
import json
import time
import getpass
import tempfile
import platform

import gettext
_ = gettext.gettext

import pygtk
pygtk.require('2.0')
import pynotify

#sys.path.append(os.path.dirname(__file__))  # DEBUG

# http://stackoverflow.com/questions/1112343/how-do-i-capture-sigint-in-python
import signal

# package imports
"""
from . import (
    settings,
    utils,
    server_errors,
    printcolor,
    url_request,
    network
)
"""
import settings
import utils
import server_errors
import printcolor
import url_request
import network

from backends import Pms


def _operation_ok(info=''):
    _msg = str(' ' + _('Ok')).rjust(38, '*')
    if info:
        _msg = str(info)

    printcolor.ok(_msg)


def _operation_failed(info=''):
    printcolor.fail(str(' ' + _('Failed')).rjust(38, '*'))
    if info:
        printcolor.fail(info)


def _search_pms():
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


class MigasFreeClient(object):
    APP_NAME = 'Migasfree'
    CMD = 'migasfree'  # /usr/bin/migasfree
    LOCK_FILE = '/tmp/%s.pid' % CMD
    ERROR_FILE = '/tmp/%s.err' % CMD

    SOFTWARE_FILE = '/var/log/installed_software.txt'

    PUBLIC_KEY = 'migasfree-server.pub'
    PRIVATE_KEY = 'migasfree-client.pri'

    ICON_PATH = '/usr/share/icons/hicolor/scalable/apps'
    ICON = 'migasfree.svg'
    ICON_COMPLETED = 'migasfree-ok.svg'

    _graphic_user = None
    _notify = None

    pms = None

    _url_request = None

    _debug = False
    _error_file_descriptor = None

    def __init__(self):
        signal.signal(signal.SIGINT, self._exit_gracefully)
        signal.signal(signal.SIGQUIT, self._exit_gracefully)
        signal.signal(signal.SIGTERM, self._exit_gracefully)

        self._read_conf_file()

        self._init_environment()

        # init UrlRequest
        _url_base = '%s/migasfree/api/' % str(self.migas_server)
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

    def _read_conf_file(self):
        _config = utils.get_config(settings.CONF_FILE, 'client')
        _log_level = logging.INFO

        if type(_config) is dict:
            self.migas_server = _config.get('server', 'migasfree.org')
            self.migas_version = _config.get(
                'version',
                '-'.join(platform.linux_distribution()[0:1])
            )
            self.migas_computer_name = _config.get(
                'computer_name',
                utils.get_hostname()
            )
            self.migas_proxy = _config.get('proxy', None)
            self.migas_ssl_cert = _config.get('ssl_cert', None)
            if 'debug' in _config:
                if _config['debug'] == 'True' \
                or _config['debug'] == '1' \
                or _config['debug'] == 'On':
                    self._debug = True
                    _log_level = logging.DEBUG

        # http://www.lightbird.net/py-by-example/logging.html
        logging.basicConfig(
            format='%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s',
            level=_log_level,
            filename=settings.LOG_FILE
        )
        logging.info('*' * 20)
        logging.info('%s in execution', self.CMD)
        logging.debug('Config: %s', _config)

    def _init_environment(self):
        _graphic_pid, _graphic_process = utils.get_graphic_pid()
        logging.debug('Graphic pid: %s', _graphic_pid)
        logging.debug('Graphic process: %s', _graphic_process)

        if not _graphic_pid:
            self._graphic_user = os.environ['USER']
            print(_('No detected graphic process'))
        else:
            self._graphic_user = utils.get_graphic_user(_graphic_pid)
            _user_display = utils.get_user_display_graphic(_graphic_pid)
            logging.debug('Graphic display: %s', _user_display)
            pynotify.init(self.APP_NAME)
            self._notify = pynotify.Notification(self.APP_NAME)
        logging.debug('Graphic user: %s', self._graphic_user)

    def _pms_selection(self):
        _pms_info = _search_pms()
        logging.debug('PMS info: %s', _pms_info)
        if not _pms_info:
            logging.critical('Any PMS was not found. Cannot continue.')
            sys.exit(errno.EINPROGRESS)

        self.pms = Pms.factory(_pms_info)()

    def _show_running_options(self):
        print('')
        print(_('Running options:'))
        print('\t%s: %s' % (_('Version'), self.migas_version))
        print('\t%s: %s' % (_('Server'), self.migas_server))
        print('\t%s: %s' % (_('Proxy'), self.migas_proxy))
        print('\t%s: %s' % (_('SSL certificate'), self.migas_ssl_cert))
        print('\t%s: %s' % (_('Debug'), self._debug))
        print('\t%s: %s' % (_('Graphic user'), self._graphic_user))
        print('\t%s: %s' % (_('PMS'), self.pms))
        print('')

    def _exit_gracefully(self, signal_number, frame):
        self._send_message(_('Killing %s before time!!!') % self.CMD)
        logging.critical('Exiting %s, signal: %s', self.CMD, signal_number)
        sys.exit(errno.EINPROGRESS)

    def _usage_examples(self):
        print('\n' + _('Examples:'))

        print('  ' + _('Register computer at server:'))
        print('\t%s -g' % self.CMD)
        print('\t%s --register\n' % self.CMD)

        print('  ' + _('Update the system:'))
        print('\t%s -u' % self.CMD)
        print('\t%s --update\n' % self.CMD)

        print('  ' + _('Search package:'))
        print('\t%s -s bluefish' % self.CMD)
        print('\t%s --search=bluefish\n' % self.CMD)

        print('  ' + _('Install package:'))
        print('\t%s -ip bluefish' % self.CMD)
        print('\t%s --install --package=bluefish\n' % self.CMD)

        print('  ' + _('Remove package:'))
        print('\t%s -rp bluefish' % self.CMD)
        print('\t%s --remove --package=bluefish\n' % self.CMD)

        # TODO
        #print '  ' + _('Install device:')
        #print '\t%s -id 12307' % self.CMD
        #print '\t%s --install --device=12307\n' % self.CMD

        # TODO
        #print '  ' + _('Remove device:')
        #print '\t%s -rd 12307' % self.CMD
        #print '\t%s --remove --device=12307' % self.CMD

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

    def _send_message(self, msg='', icon=None):
        if msg:
            print('')
            printcolor.info(str(' ' + msg + ' ').center(76, '*'))

            if not icon:
                icon = os.path.join(self.ICON_PATH, self.ICON)

            if self._notify:
                icon = 'file://%s' % os.path.join(self.ICON_PATH, icon)

                try:
                    self._notify.update(self.APP_NAME, msg, icon)
                    self._notify.set_timeout(pynotify.EXPIRES_DEFAULT)
                    self._notify.show()
                except:
                    pass

        _ret = self._url_request.run(
            'upload_computer_message',
            data=msg,
            exit_on_error=False
        )
        logging.debug('Message response: %s', _ret)
        if self._debug:
            print(('Message response: %s' % _ret))

        if 'errmfs' in _ret \
        and _ret['errmfs']['code'] == server_errors.COMPUTER_NOT_FOUND:
            return self._auto_register()

        if _ret['errmfs']['code'] != server_errors.ALL_OK:
            _msg = 'Error: %s\nInfo: %s' % (
                server_errors.error_info(_ret['errmfs']['code']),
                _ret['errmfs']['info']
            )
            _operation_failed(_msg)
            self._write_error(_msg, append=True)

        return (_ret['errmfs']['code'] == server_errors.ALL_OK)

    def _eval_code(self, lang, code):
        # clean code...
        code = code.replace('\r', '').strip()
        logging.debug('Language code: %s', lang)
        logging.debug('Code: %s', code)

        _filename = tempfile.mkstemp()[1]
        with open(_filename, 'wb') as _code_file:
            _code_file.write(code)

        _allowed_languages = [
            'bash',
            'python',
            'perl',
            'php',
            'ruby'
        ]

        if lang in _allowed_languages:
            _cmd = '%s %s' % (lang, _filename)
        else:
            _cmd = ':'  # gracefully degradation

        _ret, _output, _error = utils.execute(_cmd, interactive=False)
        logging.debug('Executed command: %s', _cmd)
        logging.debug('Output: %s', _output)

        try:
            os.remove(_filename)
        except IOError:
            pass

        return _output

    def _eval_attributes(self, properties):
        # response struct
        _response = {
            'computer': {
                'hostname': self.migas_computer_name,
                'ip': network.get_network_info()['ip'],
                'version': self.migas_version,
                'platform': platform.system(),  # new for server 3.0
                'user': self._graphic_user,
                'user_fullname': utils.get_user_info(self._graphic_user)['fullname']
            },
            'attributes': {}
        }

        # properties converted in attributes
        self._send_message(_('Evaluating attributes...'))
        for _item in properties:
            _response['attributes'][_item['name']] = \
                self._eval_code(_item['language'], _item['code'])
            _info = '%s: %s' % (
                _item['name'],
                _response['attributes'][_item['name']]
            )
            if _response['attributes'][_item['name']].strip() != '':
                _operation_ok(_info)
            else:
                _operation_failed(_info)
                self._write_error('Error: property %s without value\n' % _item['name'])

        return _response

    def _eval_faults(self, faultsdef):
        # response struct
        _response = {
            'faults': {}
        }

        # evaluate faults
        self._send_message(_('Executing faults...'))
        for _item in faultsdef:
            _result = self._eval_code(_item['language'], _item['code'])
            _info = '%s: %s' % (_item['name'], _result)
            if _result:
                # only send faults with output!!!
                _response['faults'][_item['name']] = _result
                _operation_failed(_info)
            else:
                _operation_ok(_info)

        return _response

    def _get_attributes(self):
        '''
        get properties and returns attributes to send
        '''
        self._send_message(_('Getting properties...'))
        _request = self._url_request.run('get_properties')
        logging.debug('Update request: %s', _request)

        if not _request:
            _operation_failed(_('No data requested from server'))
            sys.exit(errno.ENODATA)

        _operation_ok()

        _attributes = self._eval_attributes(_request['properties'])
        logging.debug('Attributes to send: %s', _attributes)

        return _attributes

    def _software_inventory(self):
        # actual software
        _software_before = self.pms.query_all()
        logging.debug('Actual software: %s', _software_before)

        # if have been installed packages manually
        # information is uploaded to server
        if os.path.isfile(self.SOFTWARE_FILE) \
        and os.stat(self.SOFTWARE_FILE).st_size:
            _diff_software = utils.compare_lists(
                open(self.SOFTWARE_FILE, 'U').read().splitlines(),  # not readlines!!!
                _software_before
            )

            if _diff_software:
                self._send_message(_('Uploading manual software...'))
                _file_mtime = time.strftime(
                    '%Y-%m-%d %H:%M:%S',
                    time.localtime(os.path.getmtime(self.SOFTWARE_FILE))
                )
                _now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                _data = '# [%s, %s]\n%s' % (
                    _file_mtime,
                    _now,
                    '\n'.join(_diff_software)
                )
                logging.debug('Software diff: %s', _data)
                self._url_request.run(
                    'upload_computer_software_history',
                    data=_data
                )
                _operation_ok()

        return _software_before

    def _upload_old_errors(self):
        '''
        if there are old errors, upload them to server
        '''
        if os.path.isfile(self.ERROR_FILE) \
        and os.stat(self.ERROR_FILE).st_size:
            self._send_message(_('Uploading old errors...'))
            self._url_request.run(
                'upload_computer_errors',
                data=open(self.ERROR_FILE, 'rb').read()
            )
            _operation_ok()
            # delete old errors
            os.remove(self.ERROR_FILE)

        # create new error file and open to write
        self._error_file_descriptor = open(self.ERROR_FILE, 'wb')

    def _create_repositories(self, repos):
        self._send_message(_('Creating repositories...'))

        _ret = self.pms.create_repos(
            self.migas_server,
            self.migas_version,
            repos
        )

        if _ret:
            _operation_ok()
        else:
            _msg = _('Error creating repositories: %s') % repos
            _operation_failed(_msg)
            logging.error(_msg)
            self._write_error(_msg)

    def _clean_pms_cache(self):
        '''
        clean cache of Package Management System
        '''
        self._send_message(_('Getting repositories metadata...'))
        _ret = self.pms.clean_all()

        if _ret:
            _operation_ok()
        else:
            _msg = _('Error getting repositories metadata')
            _operation_failed(_msg)
            logging.error(_msg)
            self._write_error(_msg)

    def _uninstall_packages(self, packages):
        self._send_message(_('Uninstalling packages...'))
        _ret, _error = self.pms.remove_silent(packages)
        if _ret:
            _operation_ok()
        else:
            _msg = _('Error uninstalling packages: %s') % _error
            _operation_failed(_msg)
            logging.error(_msg)
            self._write_error(_msg)

    def _install_mandatory_packages(self, packages):
        self._send_message(_('Installing mandatory packages...'))
        _ret, _error = self.pms.install_silent(packages)
        if _ret:
            _operation_ok()
        else:
            _msg = _('Error installing packages: %s') % _error
            _operation_failed(_msg)
            logging.error(_msg)
            self._write_error(_msg)

    def _update_packages(self):
        self._send_message(_('Updating packages...'))
        _ret, _error = self.pms.update_silent()
        if _ret:
            _operation_ok()
        else:
            _msg = _('Error updating packages: %s') % _error
            _operation_failed(_msg)
            logging.error(_msg)
            self._write_error(_msg)

    def _update_hardware_inventory(self):
        self._send_message(_('Capturing hardware information...'))
        _cmd = 'lshw -json'
        _ret, _output, _error = utils.execute(_cmd, interactive=False)
        if _ret == 0:
            _operation_ok()
        else:
            _msg = _('lshw command failed: %s') % _error
            _operation_failed(_msg)
            logging.error(_msg)
            self._write_error(_msg)

        _hardware = json.loads(_output)
        logging.debug('Hardware inventory: %s', _hardware)

        self._send_message(_('Sending hardware information...'))
        _ret = self._url_request.run(
            'upload_computer_hardware',
            data=_hardware,
            exit_on_error=False
        )
        if _ret['errmfs']['code'] == server_errors.ALL_OK:
            _operation_ok()
        else:
            _operation_failed()
            _msg = _ret['errmfs']['info']
            logging.error(_msg)
            self._write_error(_msg)

    def _upload_execution_errors(self):
        self._error_file_descriptor.close()
        if os.stat(self.ERROR_FILE).st_size:
            self._send_message(_('Sending errors to server...'))
            self._url_request.run(
                'upload_computer_errors',
                data=open(self.ERROR_FILE, 'rb').read()
            )
            _operation_ok()

            # delete errors
            if not self._debug:
                os.remove(self.ERROR_FILE)

    def _update_system(self):
        self._check_sign_keys()

        if self._send_message(_('Connecting to migasfree server...')):
            _operation_ok()
        else:
            sys.exit(errno.EBADRQC)

        self._upload_old_errors()

        _response = self._get_attributes()

        # send response to server and evaluate new request
        self._send_message(_('Uploading attributes...'))
        _request = self._url_request.run(
            'upload_computer_info',
            data=_response
        )
        _operation_ok()
        logging.debug('Server response: %s', _request)

        if len(_request['faultsdef']) > 0:
            _response = self._eval_faults(_request['faultsdef'])
            logging.debug('Faults to send: %s', _response)

            # send faults to server
            self._send_message(_('Uploading faults...'))
            _request_faults = self._url_request.run(
                'upload_computer_faults',
                data=_response
            )
            _operation_ok()
            logging.debug('Server response: %s', _request_faults)

        _software_before = self._software_inventory()

        self._create_repositories(_request['repositories'])

        self._clean_pms_cache()

        # first remove packages
        self._uninstall_packages(_request['packages']['remove'])

        # then install new packages
        self._install_mandatory_packages(_request['packages']['install'])

        # finally update packages
        self._update_packages()

        # upload computer software history
        _software_after = self.pms.query_all()
        utils.write_file(self.SOFTWARE_FILE, '\n'.join(_software_after))
        _diff_software = utils.compare_lists(_software_before, _software_after)
        if _diff_software:
            self._send_message(_('Uploading software history...'))
            _data = time.strftime('# %Y-%m-%d %H:%M:%S\n', time.localtime()) \
                + '\n'.join(_diff_software)
            logging.debug('Software diff: %s', _data)
            print(_('Software diff: %s') % _data)
            self._url_request.run(
                'upload_computer_software_history',
                data=_data
            )
            _operation_ok()

        # upload the software inventory
        self._send_message(_('Uploading software inventory...'))
        if _request['base']:
            logging.info('This computer is software reference')
            self._url_request.run(
                'upload_computer_software_base',
                data='\n'.join(_software_after)
            )
            _operation_ok()

        _software_base = self._url_request.run('get_computer_software')
        _software_base = _software_base.split('\n')
        logging.debug('Software base: %s', _software_base)

        _diff_software = utils.compare_lists(_software_base, _software_after)
        _diff_software = '\n'.join(_diff_software)
        logging.debug('Software base diff: %s', _diff_software)
        self._url_request.run(
            'upload_computer_software_base_diff',
            data=_diff_software
        )
        _operation_ok()

        # update computer hardware inventory
        if _request.get('hardware_capture') is True:  # new in server 3.0
            self._update_hardware_inventory()

        # TODO remove and install devices

        # upload execution errors to server
        self._upload_execution_errors()

        self._send_message(_('Completed operations'), self.ICON_COMPLETED)
        time.sleep(3)  # to see update completed icon ;)

        # clean computer messages in server
        self._send_message()

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
            'platform': platform.system()  # new for server 3.0
        }
        print(_('Autoregistering computer...'))

        return self._save_sign_keys(_data)

    def _save_sign_keys(self, data):
        if not os.path.isdir(os.path.abspath(settings.KEYS_PATH)):
            try:
                os.makedirs(os.path.abspath(settings.KEYS_PATH))
            except:
                _msg = _('Error creating %s directory') % settings.KEYS_PATH
                _operation_failed(_msg)
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
            _operation_failed(_msg)
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
                _operation_failed(_msg)
                logging.error(_msg)
                sys.exit(errno.ENOENT)

        return True

    def _register_computer(self):
        _continue = utils.query_yes_no(
            _('Have you check config options in this machine (%s)?') % settings.CONF_FILE
        )
        if _continue == 'no':
            _operation_failed(_('Check %s file and register again') % settings.CONF_FILE)
            sys.exit(errno.EAGAIN)

        _user = raw_input('%s: ' % _('User to register computer at server'))
        if not _user:
            _operation_failed(_('Empty user. Exiting %s.') % self.CMD)
            logging.info('Empty user in register computer option')
            sys.exit(errno.EAGAIN)

        _pass = getpass.getpass('%s: ' % _('Password'))

        _data = {
            'username': _user,
            'password': _pass,
            'version': self.migas_version,
            'platform': platform.system()  # new for server 3.0
        }
        self._save_sign_keys(_data)
        _operation_ok(_('Computer registered at server'))

    def _search(self, pattern):
        return self.pms.search(pattern)

    def _install_package(self, pkg):
        self._send_message(_('Installing package: %s') % pkg)
        _ret = self.pms.install(pkg)
        self._send_message()
        return _ret

    def _remove_package(self, pkg):
        self._send_message(_('Removing package: %s') % pkg)
        _ret = self.pms.remove(pkg)
        self._send_message()
        return _ret

    # TODO
    def _install_device(self, dev):
        self._send_message(_('Installing device: %s') % dev)
        #download_file_and_run "device/?CMD=install&HOST=$HOSTNAME&NUMBER=pkg" "$_DIR_TMP/install_device"
        print('TODO')
        self._send_message()

    # TODO
    def _remove_device(self, dev):
        self._send_message(_('Removing device: %s') % dev)
        #download_file_and_run "device/?CMD=remove\HOST=$HOSTNAME\NUMBER=dev" "$_DIR_TMP/remove_device"
        print('TODO')
        self._send_message()

    def run(self):
        _program = 'migasfree client'
        parser = optparse.OptionParser(
            description=_program,
            prog=self.CMD,
            version=__version__,
            usage='%prog options'
        )

        print(_('%(program)s version: %(version)s') % {
            'program': _program,
            'version': __version__
        })

        parser.add_option("--register", "-g", action="store_true",
            help=_('Register computer at server'))
        parser.add_option("--update", "-u", action="store_true",
            help=_('Update system from repositories'))
        parser.add_option("--search", "-s", action="store",
            help=_('Search package in repositories'))
        parser.add_option(
            "--install", "-i",
            action="store_true",
            #help=_('Install package or device')
            help=_('Install package')
        )
        parser.add_option(
            "--remove", "-r",
            action="store_true",
            #help=_('Remove package or device')
            help=_('Remove package')
        )
        parser.add_option("--package", "-p", action="store",
            help=_('Package to install or remove'))
        #parser.add_option("--device", "-d", action = "store",
        #    help = _('Device to install or remove'))

        options, arguments = parser.parse_args()

        # check restrictions
        if options.register and \
        (options.install or options.remove or options.update or options.search):
            self._usage_examples()
            parser.error(_('Register option is exclusive!!!'))
        if options.update and \
        (options.install or options.remove or options.search):
            self._usage_examples()
            parser.error(_('Update option is exclusive!!!'))
        if options.search and (options.install or options.remove):
            self._usage_examples()
            parser.error(_('Search option is exclusive!!!'))
        if options.install and options.remove:
            parser.print_help()
            self._usage_examples()
            parser.error(_('Install and remove are exclusive!!!'))
        if options.install and not (options.package or options.device):
            self._usage_examples()
            #parser.error(_('Install needs package or device!!!'))
            parser.error(_('Install needs a package!!!'))
        if options.remove and not (options.package or options.device):
            self._usage_examples()
            #parser.error(_('Remove needs package or device!!!'))
            parser.error(_('Remove needs a package!!!'))

        utils.check_lock_file(self.CMD, self.LOCK_FILE)

        self._show_running_options()

        # actions dispatcher
        if options.update:
            self._update_system()
        elif options.register:
            self._register_computer()
        elif options.search:
            self._search(options.search)
        elif options.install and options.package:
            self._install_package(options.package)
        elif options.install and options.device:
            self._install_device(options.device)
        elif options.remove and options.package:
            self._remove_package(options.package)
        elif options.remove and options.device:
            self._remove_device(options.device)
        else:
            parser.print_help()
            self._usage_examples()

        utils.remove_file(self.LOCK_FILE)

        sys.exit(os.EX_OK)  # no error


def main():
    mfc = MigasFreeClient()
    mfc.run()

if __name__ == "__main__":
    main()
