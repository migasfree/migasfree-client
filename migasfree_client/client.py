#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Copyright (c) 2011-2016 Jose Antonio Chavarría <jachavar@gmail.com>
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

__author__ = 'Jose Antonio Chavarría'
__license__ = 'GPLv3'
__all__ = ('MigasFreeClient', 'main')

import os

import sys
import errno
import logging
import optparse
import json
import time
import tempfile
import platform

# http://stackoverflow.com/questions/1112343/how-do-i-capture-sigint-in-python
import signal

import gettext
_ = gettext.gettext

# sys.path.append(os.path.dirname(__file__))  # DEBUG

from . import (
    settings,
    utils,
    server_errors,
    printcolor,
    network,
)

from .command import MigasFreeCommand
from .devices import Printer


class MigasFreeClient(MigasFreeCommand):
    APP_NAME = 'Migasfree'
    CMD = 'migasfree'  # /usr/bin/migasfree

    _graphic_user = None
    _notify = None

    _error_file_descriptor = None

    _pms_status_ok = True  # indicates the status of transactions with PMS

    def __init__(self):
        self._user_is_not_root()

        signal.signal(signal.SIGINT, self._exit_gracefully)
        signal.signal(signal.SIGQUIT, self._exit_gracefully)
        signal.signal(signal.SIGTERM, self._exit_gracefully)

        MigasFreeCommand.__init__(self)
        self._init_environment()

    def _init_environment(self):
        _graphic_pid, _graphic_process = utils.get_graphic_pid()
        logging.debug('Graphic pid: %s', _graphic_pid)
        logging.debug('Graphic process: %s', _graphic_process)

        if not _graphic_pid:
            self._graphic_user = os.environ.get('USER')
            print(_('No detected graphic process'))
        else:
            self._graphic_user = utils.get_graphic_user(_graphic_pid)
            _user_display = utils.get_user_display_graphic(_graphic_pid)
            logging.debug('Graphic display: %s', _user_display)

            try:
                import pygtk
                pygtk.require('2.0')
                import pynotify

                pynotify.init(self.APP_NAME)
                self._notify = pynotify.Notification(self.APP_NAME)
            except ImportError:
                pass  # graphical notifications no available

        logging.debug('Graphic user: %s', self._graphic_user)

    def _exit_gracefully(self, signal_number, frame):
        self._send_message(_('Killing %s before time!!!') % self.CMD)
        logging.critical('Exiting %s, signal: %s', self.CMD, signal_number)
        sys.exit(errno.EINPROGRESS)

    def _show_running_options(self):
        MigasFreeCommand._show_running_options(self)

        print('\t%s: %s' % (_('Graphic user'), self._graphic_user))
        print('')

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

            if self.migas_gui_verbose:
                if not icon:
                    icon = os.path.join(settings.ICON_PATH, self.ICON)

                if self._notify:
                    icon = 'file://%s' % os.path.join(settings.ICON_PATH, icon)

                    try:
                        self._notify.update(self.APP_NAME, msg, icon)
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
            logging.warning('Computer not found.')
            return self._auto_register()

        if _ret['errmfs']['code'] != server_errors.ALL_OK:
            _msg = 'Error: %s\nInfo: %s' % (
                server_errors.error_info(_ret['errmfs']['code']),
                _ret['errmfs']['info']
            )
            self.operation_failed(_msg)
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

        _ret, _output, _error = utils.timeout_execute(_cmd)
        logging.debug('Executed command: %s', _cmd)
        logging.debug('Output: %s', _output)
        if _ret != 0:
            logging.error('Error: %s', _error)

        try:
            os.remove(_filename)
        except IOError:
            pass

        return _output

    def _eval_attributes(self, properties):
        _response = {
            'computer': {
                'hostname': self.migas_computer_name,
                'ip': network.get_network_info()['ip'],
                'version': self.migas_version,
                'platform': platform.system(),
                'pms': str(self.pms),
                'user': self._graphic_user,
                'user_fullname': utils.get_user_info(
                    self._graphic_user
                )['fullname']
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
                self.operation_ok(_info)
            else:
                self.operation_failed(_info)
                self._write_error(
                    'Error: property %s without value\n' % _item['name']
                )

        return _response

    def _eval_faults(self, faultsdef):
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
                self.operation_failed(_info)
            else:
                self.operation_ok(_info)

        return _response

    def _get_attributes(self):
        '''
        get properties and returns attributes to send
        '''
        self._send_message(_('Getting properties...'))
        _request = self._url_request.run('get_properties')
        logging.debug('Update request: %s', _request)

        if not _request:
            self.operation_failed(_('No data requested from server'))
            sys.exit(errno.ENODATA)

        self.operation_ok()

        _attributes = self._eval_attributes(_request['properties'])
        logging.debug('Attributes to send: %s', _attributes)

        return _attributes

    def _software_inventory(self):
        # actual software
        _software_before = self.pms.query_all()
        logging.debug('Actual software: %s', _software_before)

        # if have been installed packages manually
        # information is uploaded to server
        if os.path.isfile(settings.SOFTWARE_FILE) \
        and os.stat(settings.SOFTWARE_FILE).st_size:
            _diff_software = utils.compare_lists(
                open(
                    settings.SOFTWARE_FILE,
                    'U'
                ).read().splitlines(),  # not readlines!!!
                _software_before
            )

            if _diff_software:
                self._send_message(_('Uploading manual software...'))
                _file_mtime = time.strftime(
                    '%Y-%m-%d %H:%M:%S',
                    time.localtime(os.path.getmtime(settings.SOFTWARE_FILE))
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
                self.operation_ok()

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
            self.operation_ok()
            os.remove(self.ERROR_FILE)

        self._error_file_descriptor = open(self.ERROR_FILE, 'wb')

    def _create_repositories(self, repos):
        self._send_message(_('Creating repositories...'))

        _server = self.migas_server
        if self.migas_package_proxy_cache:
            _server = '%s/%s' % (self.migas_package_proxy_cache, _server)

        _ret = self.pms.create_repos(
            _server,
            self.migas_version,
            repos
        )

        if _ret:
            self.operation_ok()
        else:
            self._pms_status_ok = False
            _msg = _('Error creating repositories: %s') % repos
            self.operation_failed(_msg)
            logging.error(_msg)
            self._write_error(_msg)

    def _clean_pms_cache(self):
        '''
        clean cache of Package Management System
        '''
        self._send_message(_('Getting repositories metadata...'))
        _ret = self.pms.clean_all()

        if _ret:
            self.operation_ok()
        else:
            _msg = _('Error getting repositories metadata')
            self.operation_failed(_msg)
            logging.error(_msg)
            self._write_error(_msg)

    def _uninstall_packages(self, packages):
        self._send_message(_('Uninstalling packages...'))
        _ret, _error = self.pms.remove_silent(packages)
        if _ret:
            self.operation_ok()
        else:
            self._pms_status_ok = False
            _msg = _('Error uninstalling packages: %s') % _error
            self.operation_failed(_msg)
            logging.error(_msg)
            self._write_error(_msg)

    def _install_mandatory_packages(self, packages):
        self._send_message(_('Installing mandatory packages...'))
        _ret, _error = self.pms.install_silent(packages)
        if _ret:
            self.operation_ok()
        else:
            self._pms_status_ok = False
            _msg = _('Error installing packages: %s') % _error
            self.operation_failed(_msg)
            logging.error(_msg)
            self._write_error(_msg)

        return _ret

    def _update_packages(self):
        self._send_message(_('Updating packages...'))
        _ret, _error = self.pms.update_silent()
        if _ret:
            self.operation_ok()
        else:
            self._pms_status_ok = False
            _msg = _('Error updating packages: %s') % _error
            self.operation_failed(_msg)
            logging.error(_msg)
            self._write_error(_msg)

        return _ret

    def _update_hardware_inventory(self):
        self._send_message(_('Capturing hardware information...'))
        _cmd = 'LC_ALL=C lshw -json'
        _ret, _output, _error = utils.execute(_cmd, interactive=False)
        if _ret == 0:
            self.operation_ok()
        else:
            _msg = _('lshw command failed: %s') % _error
            self.operation_failed(_msg)
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
            self.operation_ok()
        else:
            self.operation_failed()
            _msg = _ret['errmfs']['info']
            logging.error(_msg)
            self._write_error(_msg)

    def _upload_execution_errors(self):
        self._error_file_descriptor.close()
        self._error_file_descriptor = None

        if os.stat(self.ERROR_FILE).st_size:
            self._send_message(_('Sending errors to server...'))
            self._url_request.run(
                'upload_computer_errors',
                data=open(self.ERROR_FILE, 'rb').read()
            )
            self.operation_ok()

            if not self._debug:
                os.remove(self.ERROR_FILE)

    def _update_system(self):
        if not self._check_sign_keys():
            sys.exit(errno.EPERM)

        if self._send_message(_('Connecting to migasfree server...')):
            self.operation_ok()
        else:
            sys.exit(errno.EBADRQC)

        self._upload_old_errors()

        _response = self._get_attributes()

        self._send_message(_('Uploading attributes...'))
        _request = self._url_request.run(
            'upload_computer_info',
            data=_response
        )
        self.operation_ok()
        logging.debug('Server response: %s', _request)

        if len(_request['faultsdef']) > 0:
            _response = self._eval_faults(_request['faultsdef'])
            logging.debug('Faults to send: %s', _response)

            self._send_message(_('Uploading faults...'))
            _request_faults = self._url_request.run(
                'upload_computer_faults',
                data=_response
            )
            self.operation_ok()
            logging.debug('Server response: %s', _request_faults)

        _software_before = self._software_inventory()

        self._create_repositories(_request['repositories'])

        self._clean_pms_cache()

        self._uninstall_packages(_request['packages']['remove'])
        self._install_mandatory_packages(_request['packages']['install'])
        if self.migas_auto_update_packages is True:
            self._update_packages()

        # upload computer software history
        _software_after = self.pms.query_all()
        utils.write_file(settings.SOFTWARE_FILE, '\n'.join(_software_after))
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
            self.operation_ok()

        self._send_message(_('Uploading software inventory...'))
        if _request['base']:
            logging.info('This computer is software reference')
            self._url_request.run(
                'upload_computer_software_base',
                data='\n'.join(_software_after)
            )
            self.operation_ok()

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
        self.operation_ok()

        if _request.get('hardware_capture') is True:
            self._update_hardware_inventory()

        # remove and install devices (new in server 4.2) (issue #31)
        if 'devices' in _request:
            _installed = []
            _removed = []
            if 'remove' in _request['devices'] \
            and len(_request['devices']['remove']):
                _removed = self._remove_devices(_request['devices']['remove'])

            if 'install' in _request['devices'] \
            and len(_request['devices']['install']):
                _installed = self._install_devices(_request['devices']['install'])

            self._url_request.run(
                'upload_devices_changes',
                data={'installed': _installed, 'removed': _removed}
            )

        self._upload_execution_errors()

        self._send_message(_('Operations completed'), self.ICON_COMPLETED)

        # clean computer messages in server
        self._send_message()

    def _search(self, pattern):
        return self.pms.search(pattern)

    def _install_package(self, pkg):
        self._check_sign_keys()

        self._send_message(_('Installing package: %s') % pkg)
        _ret = self.pms.install(pkg)
        self._send_message()

        return _ret

    def _remove_package(self, pkg):
        self._check_sign_keys()

        self._send_message(_('Removing package: %s') % pkg)
        _ret = self.pms.remove(pkg)
        self._send_message()

        return _ret

    def _install_printer(self, device):
        if 'packages' in device and device['packages']:
            if not self._install_mandatory_packages(device['packages']):
                return False

        self._remove_printer(device['id'])

        self._send_message(_('Installing device: %s') % device['model'])
        _installed, _output = Printer.install(device)
        if _installed:
            _ret = _output
            self.operation_ok()
            logging.debug('Device installed: %s', device['model'])
        else:
            _ret = False
            _msg = _('Error installing device: %s') % _output
            self.operation_failed(_msg)
            logging.error(_msg)
            self._write_error(_msg)

        self._send_message()

        return _ret

    def _install_devices(self, devices):
        self._check_sign_keys()

        _installed_ids = []
        for device in devices:
            if 'PRINTER' in device:
                _id = self._install_printer(device['PRINTER'])
                if _id:
                    _installed_ids.append(_id)

        return _installed_ids

    def _remove_printer(self, device_id):
        # expected pattern: PRINTER.name__PRINTER.model__PRINTER.id (issue #31)
        _printer_name = Printer.search('__%d$' % device_id)
        if _printer_name == '':
            return device_id  # not installed, removed for server

        self._send_message(_('Removing device: %s') % _printer_name)

        _removed, _output = Printer.remove(_printer_name)
        if _removed:
            _ret = device_id
            self.operation_ok()
            logging.debug('Device removed: %s', _printer_name)
        else:
            _ret = 0
            _msg = _('Error removing device: %s') % _output
            self.operation_failed(_msg)
            logging.error(_msg)
            self._write_error(_msg)

        self._send_message()

        return _ret

    def _remove_devices(self, devices):
        self._check_sign_keys()

        _removed_ids = []
        for device in devices:
            if 'PRINTER' in device:
                _id = self._remove_printer(device['PRINTER'])
                if _id:
                    _removed_ids.append(_id)

        return _removed_ids

    def run(self):
        _program = 'migasfree client'
        parser = optparse.OptionParser(
            description=_program,
            prog=self.CMD,
            version=self.release,
            usage='%prog options'
        )

        print(_('%(program)s version: %(version)s') % {
            'program': _program,
            'version': self.release
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
            help=_('Install package')
        )
        parser.add_option(
            "--remove", "-r",
            action="store_true",
            help=_('Remove package')
        )
        parser.add_option("--package", "-p", action="store",
            help=_('Package to install or remove'))

        parser.add_option("--force-upgrade", "-a", action="store_true",
            help=_('Force package upgrades'))

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
        if options.install and not options.package:
            self._usage_examples()
            parser.error(_('Install needs a package!!!'))
        if options.remove and not options.package:
            self._usage_examples()
            parser.error(_('Remove needs a package!!!'))

        if options.force_upgrade:
            self.migas_auto_update_packages = True

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
        elif options.remove and options.package:
            self._remove_package(options.package)
        else:
            parser.print_help()
            self._usage_examples()

        utils.remove_file(self.LOCK_FILE)

        if not self._pms_status_ok:
            sys.exit(errno.EPROTO)

        sys.exit(os.EX_OK)


def main():
    mfc = MigasFreeClient()
    mfc.run()

if __name__ == "__main__":
    main()
