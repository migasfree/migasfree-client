#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Copyright (c) 2011-2015 Jose Antonio Chavarría
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
__all__ = ('MigasFreeClient', 'main')

import os

import sys
import errno
import argparse
import json
import time
import tempfile
import platform

# http://stackoverflow.com/questions/1112343/how-do-i-capture-sigint-in-python
import signal

import gettext
_ = gettext.gettext

import logging
logger = logging.getLogger(__name__)

# sys.path.append(os.path.dirname(__file__))  # DEBUG

from datetime import datetime

from . import (
    settings,
    utils,
    printcolor,
    network,
)

from .command import (
    MigasFreeCommand,
    __version__,
)
from .devices import Printer


class MigasFreeClient(MigasFreeCommand):
    APP_NAME = 'Migasfree'
    CMD = 'migasfree'  # /usr/bin/migasfree

    _graphic_user = None
    _notify = None

    _error_file_descriptor = None

    def __init__(self):
        self._user_is_not_root()

        signal.signal(signal.SIGINT, self._exit_gracefully)
        signal.signal(signal.SIGQUIT, self._exit_gracefully)
        signal.signal(signal.SIGTERM, self._exit_gracefully)

        MigasFreeCommand.__init__(self)
        self._init_environment()

    def _init_environment(self):
        _graphic_pid, _graphic_process = utils.get_graphic_pid()
        logger.debug('Graphic pid: %s', _graphic_pid)
        logger.debug('Graphic process: %s', _graphic_process)

        if not _graphic_pid:
            self._graphic_user = os.environ.get('USER')
            print(_('No detected graphic process'))
        else:
            self._graphic_user = utils.get_graphic_user(_graphic_pid)
            _user_display = utils.get_user_display_graphic(_graphic_pid)
            logger.debug('Graphic display: %s', _user_display)

            try:
                import pygtk
                pygtk.require('2.0')
                import pynotify

                pynotify.init(self.APP_NAME)
                self._notify = pynotify.Notification(self.APP_NAME)
            except ImportError:
                pass  # graphical notifications no available

        logger.debug('Graphic user: %s', self._graphic_user)

    def _exit_gracefully(self, signal_number, frame):
        self._show_message(_('Killing %s before time!!!') % self.CMD)
        logger.critical('Exiting %s, signal: %s', self.CMD, signal_number)
        sys.exit(errno.EINPROGRESS)

    def _show_running_options(self):
        MigasFreeCommand._show_running_options(self)

        print('\t%s: %s' % (_('Graphic user'), self._graphic_user))
        print('')

    def _usage_examples(self):
        print('\n' + _('Examples:'))

        print('  ' + _('Register computer at server:'))
        print('\t%s -r' % self.CMD)
        print('\t%s --register\n' % self.CMD)

        print('  ' + _('Synchronize computer with server:'))
        print('\t%s -y' % self.CMD)
        print('\t%s --sync\n' % self.CMD)

        print('  ' + _('Search package:'))
        print('\t%s -s bluefish' % self.CMD)
        print('\t%s --search=bluefish\n' % self.CMD)

        print('  ' + _('Install package:'))
        print('\t%s -i bluefish' % self.CMD)
        print('\t%s --install bluefish\n' % self.CMD)

        print('  ' + _('Purge package:'))
        print('\t%s -p bluefish' % self.CMD)
        print('\t%s --purge bluefish\n' % self.CMD)

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

    def _show_message(self, msg, icon=None):
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

    def _eval_code(self, lang, code):
        # clean code...
        code = code.replace('\r', '').strip()
        logger.debug('Language code: %s', lang)
        logger.debug('Code: %s', code)

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
        logger.debug('Executed command: %s', _cmd)
        logger.debug('Output: %s', _output)
        if _ret != 0:
            logger.error('Error: %s', _error)

        try:
            os.remove(_filename)
        except IOError:
            pass

        return _output

    def _eval_attributes(self, properties):
        response = {
            'id': self._computer_id,
            'uuid': utils.get_hardware_uuid(),
            'name': self.migas_computer_name,
            'ip_address': network.get_network_info()['ip'],
            'sync_user': self._graphic_user,
            'sync_fullname': utils.get_user_info(
                self._graphic_user
            )['fullname'],
            'sync_attributes': {}
        }

        # properties converted in attributes
        self._show_message(_('Evaluating attributes...'))
        for _item in properties:
            response['sync_attributes'][_item['prefix']] = \
                self._eval_code(_item['language'], _item['code'])
            _info = '%s: %s' % (
                _item['prefix'],
                response['sync_attributes'][_item['prefix']]
            )
            if response['sync_attributes'][_item['prefix']].strip() != '':
                self.operation_ok(_info)
            else:
                self.operation_failed(_info)
                self._write_error(
                    'Error: property %s without value\n' % _item['prefix']
                )

        return response

    def _eval_faults(self, fault_definitions):
        _response = {
            'id': self._computer_id,
            'faults': {}
        }

        # evaluate faults
        self._show_message(_('Executing faults...'))
        for _item in fault_definitions:
            _result = self._eval_code(_item['language'], _item['code'])
            _info = '%s: %s' % (_item['name'], _result)
            if _result:
                # only send faults with output!!!
                _response['faults'][_item['name']] = _result
                self.operation_failed(_info)
            else:
                self.operation_ok(_info)

        return _response

    def get_properties(self):
        if not self._computer_id:
            self.get_computer_id()

        self._show_message(_('Getting properties...'))
        response = self._url_request.run(
            url=self._url_base + 'safe/computers/properties/',
            data={
                'id': self._computer_id
            },
            debug=self._debug
        )
        logger.debug('Response get_properties_id: %s', response)

        if 'error' in response:
            self.operation_failed(response['error']['info'])
            sys.exit(errno.ENODATA)

        self.operation_ok()

        return response

    def get_fault_definitions(self):
        if not self._computer_id:
            self.get_computer_id()

        self._show_message(_('Getting fault definitions...'))
        response = self._url_request.run(
            url=self._url_base + 'safe/computers/faults/definitions/',
            data={
                'id': self._computer_id
            },
            debug=self._debug
        )
        logger.debug('Response get_fault_definitions: %s', response)

        if 'error' in response:
            self.operation_failed(response['error']['info'])
            sys.exit(errno.ENODATA)

        self.operation_ok()

        return response

    def get_repositories(self):
        if not self._computer_id:
            self.get_computer_id()

        self._show_message(_('Getting repositories...'))
        response = self._url_request.run(
            url=self._url_base + 'safe/computers/repositories/',
            data={
                'id': self._computer_id
            },
            exit_on_error=False,
            debug=self._debug
        )
        logger.debug('Response get_repositories: %s', response)

        if 'error' in response:
            self.operation_failed(response['error']['info'])
            #sys.exit(errno.ENODATA)
            return None

        self.operation_ok()

        return response

    def get_mandatory_packages(self):
        if not self._computer_id:
            self.get_computer_id()

        self._show_message(_('Getting mandatory packages...'))
        response = self._url_request.run(
            url=self._url_base + 'safe/computers/packages/mandatory/',
            data={
                'id': self._computer_id
            },
            exit_on_error=False,
            debug=self._debug
        )
        logger.debug('Response get_mandatory_packages: %s', response)

        if 'error' in response:
            self.operation_failed(response['error']['info'])
            #sys.exit(errno.ENODATA)
            return None

        self.operation_ok()

        return response

    def _software_history(self, software):
        history = ''

        # if have been installed packages manually
        # information is uploaded to server
        if os.path.isfile(settings.SOFTWARE_FILE) \
        and os.stat(settings.SOFTWARE_FILE).st_size:
            diff_software = utils.compare_lists(
                open(
                    settings.SOFTWARE_FILE,
                    'U'
                ).read().splitlines(),  # not readlines!!!
                software
            )

            if diff_software:
                file_mtime = time.strftime(
                    '%Y-%m-%d %H:%M:%S',
                    time.localtime(os.path.getmtime(settings.SOFTWARE_FILE))
                )
                now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                history = '# [%s, %s]\n%s' % (
                    file_mtime,
                    now,
                    '\n'.join(diff_software)
                )
                logger.debug('Software diff: %s', history)

        return history

    def _upload_old_errors(self):
        '''
        if there are old errors, upload them to server
        '''
        if os.path.isfile(self.ERROR_FILE) \
        and os.stat(self.ERROR_FILE).st_size:
            self._show_message(_('Uploading old errors...'))
            response = self._url_request.run(
                url=self._url_base + 'safe/computers/errors/',
                #data=open(self.ERROR_FILE, 'rb').read()
                data={
                    'id': self._computer_id,
                    'description': utils.read_file(self.ERROR_FILE)
                },
                debug=self._debug
            )
            logger.debug('Response _upload_old_errors: %s', response)
            self.operation_ok()
            os.remove(self.ERROR_FILE)

        self._error_file_descriptor = open(self.ERROR_FILE, 'wb')

    def _create_repositories(self):
        repos = self.get_repositories()
        if not repos:
            return

        self._show_message(_('Creating repositories...'))

        _server = self.migas_server
        if self.migas_package_proxy_cache:
            _server = '%s/%s' % (self.migas_package_proxy_cache, _server)

        _ret = self.pms.create_repos(
            _server,
            utils.slugify(unicode(self.migas_project)),
            repos
        )

        if _ret:
            self.operation_ok()
        else:
            _msg = _('Error creating repositories: %s') % repos
            self.operation_failed(_msg)
            logger.error(_msg)
            self._write_error(_msg)

    def _clean_pms_cache(self):
        '''
        clean cache of Package Management System
        '''
        self._show_message(_('Getting repositories metadata...'))
        _ret = self.pms.clean_all()

        if _ret:
            self.operation_ok()
        else:
            _msg = _('Error getting repositories metadata')
            self.operation_failed(_msg)
            logger.error(_msg)
            self._write_error(_msg)

    def _uninstall_packages(self, packages):
        self._show_message(_('Uninstalling packages...'))
        _ret, _error = self.pms.remove_silent(packages)
        if _ret:
            self.operation_ok()
        else:
            _msg = _('Error uninstalling packages: %s') % _error
            self.operation_failed(_msg)
            logger.error(_msg)
            self._write_error(_msg)

    def _install_mandatory_packages(self, packages):
        self._show_message(_('Installing mandatory packages...'))
        _ret, _error = self.pms.install_silent(packages)
        if _ret:
            self.operation_ok()
        else:
            _msg = _('Error installing packages: %s') % _error
            self.operation_failed(_msg)
            logger.error(_msg)
            self._write_error(_msg)

    def _update_packages(self):
        self._show_message(_('Updating packages...'))
        _ret, _error = self.pms.update_silent()
        if _ret:
            self.operation_ok()
        else:
            _msg = _('Error updating packages: %s') % _error
            self.operation_failed(_msg)
            logger.error(_msg)
            self._write_error(_msg)

    def _update_hardware_inventory(self):
        self._show_message(_('Capturing hardware information...'))
        _cmd = 'lshw -json'
        _ret, _output, _error = utils.execute(_cmd, interactive=False)
        if _ret == 0:
            self.operation_ok()
        else:
            _msg = _('lshw command failed: %s') % _error
            self.operation_failed(_msg)
            logger.error(_msg)
            self._write_error(_msg)

        _hardware = json.loads(_output)
        logger.debug('Hardware inventory: %s', _hardware)

        self._show_message(_('Sending hardware information...'))
        _ret = self._url_request.run(
            url=self._url_base + 'upload_computer_hardware',
            data=_hardware,
            exit_on_error=False,
            debug=self._debug
        )
        if _ret['errmfs']['code'] == server_errors.ALL_OK:
            self.operation_ok()
        else:
            self.operation_failed()
            _msg = _ret['errmfs']['info']
            logger.error(_msg)
            self._write_error(_msg)

    def _upload_execution_errors(self):
        self._error_file_descriptor.close()
        self._error_file_descriptor = None

        if os.stat(self.ERROR_FILE).st_size:
            self._show_message(_('Sending errors to server...'))
            self._url_request.run(
                url=self._url_base + 'safe/computers/errors/',
                data={
                    'id': self._computer_id,
                    'description': utils.read_file(self.ERROR_FILE)
                },
                debug=self._debug
            )
            self.operation_ok()

            if not self._debug:
                os.remove(self.ERROR_FILE)

    def upload_attributes(self):
        response = self.get_properties()

        attributes = self._eval_attributes(response)
        logger.debug('Attributes to send: %s', attributes)

        self._show_message(_('Uploading attributes...'))
        response = self._url_request.run(
            url=self._url_base + 'safe/computers/attributes/',
            data=attributes,
            debug=self._debug
        )
        self.operation_ok()
        logger.debug('Response upload_attributes: %s', response)

        return response

    def upload_faults(self):
        response = self.get_fault_definitions()
        if len(response) > 0:
            data = self._eval_faults(response)
            logger.debug('Faults to send: %s', data)

            self._show_message(_('Uploading faults...'))
            response = self._url_request.run(
                url=self._url_base + 'safe/computers/faults/',
                data=data,
                debug=self._debug
            )
            self.operation_ok()
            logger.debug('Response upload_faults: %s', response)

        return response

    def _mandatory_pkgs(self):
        response = self.get_mandatory_packages()
        if not response:
            return

        if 'remove' in response:
            self._uninstall_packages(response['remove'])
        if 'install' in response:
            self._install_mandatory_packages(response['install'])

    def _upload_software(self, before, history):
        if not self._computer_id:
            self.get_computer_id()

        after = self.pms.query_all()
        utils.write_file(settings.SOFTWARE_FILE, '\n'.join(after))

        diff_software = utils.compare_lists(before, after)
        if diff_software:
            data = time.strftime('# %Y-%m-%d %H:%M:%S\n', time.localtime()) \
                + '\n'.join(diff_software)
            logger.debug('Software diff: %s', data)
            history = data + history  # reverse chronological
            print(_('Software diff: %s') % history)

        self._show_message(_('Uploading software...'))
        response = self._url_request.run(
            url=self._url_base + 'safe/computers/software/',
            data={
                'id': self._computer_id,
                'inventory': after,
                'history': history
            },
            debug=self._debug
        )
        logger.debug('Response _upload_software: %s', response)

        if 'error' in response:
            self.operation_failed(response['error']['info'])
            sys.exit(errno.ENODATA)

        self.operation_ok()

        return response

    def end_synchronization(self, start_date, consumer=''):
        if not consumer:
            consumer = self.CMD

        self._show_message(_('Ending synchronization...'))
        response = self._url_request.run(
            url=self._url_base + 'safe/synchronization/',
            data={
                'id': self._computer_id,
                'start_date': start_date,
                'consumer': '%s %s' % (consumer, __version__)
            },
            debug=self._debug
        )
        self.operation_ok()
        logger.debug('Response upload_accurate_connection: %s', response)

        return response


    def synchronize(self):
        start_date = datetime.now().isoformat()

        self._check_sign_keys()

        self._show_message(_('Connecting to migasfree server...'))

        self._upload_old_errors()
        self.upload_attributes()
        self.upload_faults()

        software_before = self.pms.query_all()
        logger.debug('Actual software: %s', software_before)

        software_history = self._software_history(software_before)

        self._create_repositories()
        self._clean_pms_cache()
        self._mandatory_pkgs()
        if self.migas_auto_update_packages is True:
            self._update_packages()

        self._upload_software(software_before, software_history)

        """
        # TODO
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
                url=self._url_base + 'upload_devices_changes',
                data={'installed': _installed, 'removed': _removed},
                debug=self._debug
            )
        """

        self._upload_execution_errors()
        self.end_synchronization(start_date)
        self._show_message(_('Operations completed'), self.ICON_COMPLETED)

    def _search(self, pattern):
        return self.pms.search(pattern)

    def _install_package(self, pkg):
        software_before = self.pms.query_all()
        software_history = self._software_history(software_before)

        self._show_message(_('Installing package: %s') % pkg)
        _ret = self.pms.install(pkg)

        self._upload_software(software_before, software_history)

        return _ret

    def _remove_package(self, pkg):
        software_before = self.pms.query_all()
        software_history = self._software_history(software_before)

        self._show_message(_('Removing package: %s') % pkg)
        _ret = self.pms.remove(pkg)

        self._upload_software(software_before, software_history)

        return _ret

    def _install_printer(self, device):
        if device['packages']:
            self._install_mandatory_packages(device['packages'])

        self._show_message(_('Installing device: %s') % device['model'])
        _installed, _output = Printer.install(device)
        if _installed:
            _ret = _output
            self.operation_ok()
            logger.debug('Device installed: %s', device['model'])
        else:
            _ret = 0
            _msg = _('Error installing device: %s') % _output
            self.operation_failed(_msg)
            logger.error(_msg)
            self._write_error(_msg)

        self._show_message()

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

        self._show_message(_('Removing device: %s') % _printer_name)

        _removed, _output = Printer.remove(_printer_name)
        if _removed:
            _ret = device_id
            self.operation_ok()
            logger.debug('Device removed: %s', _printer_name)
        else:
            _ret = 0
            _msg = _('Error removing device: %s') % _output
            self.operation_failed(_msg)
            logger.error(_msg)
            self._write_error(_msg)

        self._show_message()

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

    def _parse_args(self):
        program = 'migasfree client'
        print(_('%(program)s version: %(version)s') % {
            'program': program,
            'version': __version__
        })

        parser = argparse.ArgumentParser(
            prog=self.CMD,
            description=program
        )

        parser.add_argument(
            '-d', '--debug',
            action='store_true',
            help=_('Enable debug mode')
        )

        register_group = parser.add_argument_group('register')
        register_group.add_argument(
            '-r', '--register',
            action='store_true',
            help=_('Register computer at server')
        )

        sync_group = parser.add_argument_group('sync')
        sync_group.add_argument(
            '-y', '--sync',
            action='store_true',
            help=_('Synchronize computer with server')
        )

        sync_group.add_argument(
            '-f', '--force-upgrade',
            action='store_true',
            help=_('Force package upgrades')
        )

        search_group = parser.add_argument_group('search')
        search_group.add_argument(
            '-s', '--search',
            action='store',
            metavar='STRING',
            help=_('Search package in repositories')
        )

        install_group = parser.add_argument_group('install')
        install_group.add_argument(
            '-i', '--install',
            action='store',
            metavar='PACKAGE',
            help=_('Install package')
        )

        purge_group = parser.add_argument_group('purge')
        install_group.add_argument(
            '-p', '--purge',
            action='store',
            metavar='PACKAGE',
            help=_('Purge package')
        )

        args = parser.parse_args()

        # check restrictions
        if args.register and \
        (args.install or args.purge or args.sync or args.search):
            self._usage_examples()
            parser.error(_('Register option is exclusive!!!'))
        if args.sync and \
        (args.install or args.purge or args.search):
            self._usage_examples()
            parser.error(_('Sync option is exclusive!!!'))
        if args.search and (args.install or args.purge):
            self._usage_examples()
            parser.error(_('Search option is exclusive!!!'))
        if args.install and args.purge:
            parser.print_help()
            self._usage_examples()
            parser.error(_('Install and purge are exclusive!!!'))

        return args

    def run(self):
        args = self._parse_args()

        if args.force_upgrade:
            self.migas_auto_update_packages = True

        if args.debug:
            self._debug = True
            logger.setLevel(logging.DEBUG)

        self._show_running_options()

        # actions dispatcher
        if args.sync:
            utils.check_lock_file(self.CMD, self.LOCK_FILE)
            self.synchronize()
            utils.remove_file(self.LOCK_FILE)
        elif args.register:
            self._register_computer()
        elif args.search:
            self._search(args.search)
        elif args.install:
            utils.check_lock_file(self.CMD, self.LOCK_FILE)
            self._install_package(args.install)
            utils.remove_file(self.LOCK_FILE)
        elif args.purge:
            utils.check_lock_file(self.CMD, self.LOCK_FILE)
            self._remove_package(args.purge)
            utils.remove_file(self.LOCK_FILE)
        else:
            self._usage_examples()

        sys.exit(os.EX_OK)


def main():
    mfc = MigasFreeClient()
    mfc.run()

if __name__ == "__main__":
    main()
