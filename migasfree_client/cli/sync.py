# Copyright (c) 2011-2026 Jose Antonio Chavarría <jachavar@gmail.com>
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

import copy
import errno
import gettext
import json
import logging
import os
import signal
import sys
from collections import defaultdict
from datetime import datetime

from .. import (
    availability,
    settings,
    utils,
)
from ..command import MigasFreeCommand, lock_file_context, require_computer_id, require_sign_keys
from ..mixins.evaluator import CodeEvaluatorMixin
from ..mixins.hardware import HardwareCollectorMixin
from ..mixins.software import SoftwareManagerMixin

__author__ = 'Jose Antonio Chavarría <jachavar@gmail.com>'
__license__ = 'GPLv3'
__all__ = ['MigasFreeSync']

_ = gettext.gettext
logger = logging.getLogger('migasfree_client')


class MigasFreeSync(CodeEvaluatorMixin, HardwareCollectorMixin, SoftwareManagerMixin, MigasFreeCommand):
    APP_NAME = 'Migasfree'

    _graphic_user = None

    _error_file_descriptor = None

    _pms_status_ok = True  # indicates the status of transactions with PMS

    def __init__(self):
        signal.signal(signal.SIGINT, self._exit_gracefully)
        signal.signal(signal.SIGTERM, self._exit_gracefully)
        if utils.is_linux():
            signal.signal(signal.SIGQUIT, self._exit_gracefully)

        super().__init__()
        self._init_environment()

    def _init_environment(self):
        graphic_pid, graphic_process = utils.get_graphic_pid()
        logger.debug('Graphic pid: %s', graphic_pid)
        logger.debug('Graphic process: %s', graphic_process)

        if not graphic_pid:
            self._graphic_user = os.environ.get('USER')
            logger.warning('No detected graphic process')
        else:
            self._graphic_user = utils.get_graphic_user(graphic_pid)
            user_display = utils.get_user_display_graphic(graphic_pid)
            logger.debug('Graphic display: %s', user_display)

        logger.debug('Graphic user: %s', self._graphic_user)

    def _exit_gracefully(self, signal_number, frame):
        self._show_message(_('Killing %s before time') % self.CMD)
        logger.critical('Exiting %s, signal: %s', self.CMD, signal_number)
        sys.exit(errno.EINPROGRESS)

    def _show_running_options(self):
        super()._show_running_options()
        self.console.print('\t{}: {}'.format(_('Graphic user'), self._graphic_user))
        self.console.print()

    def _usage_examples(self):
        self.console.print('\n' + _('Examples:'))

        self.console.print('  ' + _('Register computer at server:'))
        self.console.print(f'\t{self.CMD} register\n')

        self.console.print('  ' + _('Synchronize computer with server:'))
        self.console.print(f'\t{self.CMD} sync\n')

        self.console.print('  ' + _('Search package:'))
        self.console.print(f'\t{self.CMD} search bluefish\n')

        self.console.print('  ' + _('Install package:'))
        self.console.print(f'\t{self.CMD} install bluefish\n')

        self.console.print('  ' + _('Purge package:'))
        self.console.print(f'\t{self.CMD} purge bluefish\n')

        self.console.print('  ' + _('Get computer traits at server:'))
        self.console.print(f'\t{self.CMD} traits\n')
        self.console.print(f'\t{self.CMD} traits SET\n')
        self.console.print(f'\t{self.CMD} traits CID id\n')

    def get_repos_key(self):
        self._show_message(_('Getting repositories key...'))

        response = self._url_request.run(
            url=self.api_endpoint(self.URLS['get_repositories_keys']),
            safe=False,
            exit_on_error=False,
            debug=self._debug,
        )
        logger.debug('Response get_repos_key: %s', response)

        path = settings.TMP_PATH
        if not self._check_path(path):
            return False

        path_file = os.path.join(path, utils.sanitize_path(self.migas_server))
        logger.debug('Trying writing file: %s', path_file)

        ret = utils.write_file(path_file, response)
        if not ret:
            msg = _('Error writing key file')
            self.operation_failed(msg)
            logger.error(msg)

            return False

        if self.pms.import_server_key(path_file):
            self.operation_ok()
        else:
            _msg = _('ERROR: not import repositories key: %s!') % path_file
            self.operation_failed(_msg)
            logging.error(_msg)
            return False

        return True

    @require_computer_id
    def get_properties(self):
        response = self._api_call('get_properties', {'id': self._computer_id}, message=_('Getting properties...'))
        return self._handle_response(response)

    @require_computer_id
    def get_fault_definitions(self):
        response = self._api_call(
            'get_fault_definitions',
            {'id': self._computer_id},
            exit_on_error=False,
            message=_('Getting fault definitions...'),
        )
        return self._handle_response_with_default(response, default='')

    @require_computer_id
    def get_repositories(self):
        if not self.get_repos_key():
            sys.exit(errno.EPERM)

        response = self._api_call(
            'get_repositories',
            {'id': self._computer_id},
            exit_on_error=False,
            message=_('Getting repositories...'),
        )
        return self._handle_response_with_default(response, default=[])

    @require_computer_id
    def get_mandatory_packages(self):
        response = self._api_call(
            'get_mandatory_packages',
            {'id': self._computer_id},
            exit_on_error=False,
            message=_('Getting mandatory packages...'),
        )
        return self._handle_response_with_default(response, default=None)

    @require_computer_id
    def get_devices(self):
        """Get assigned devices. Returns {'logical': [...], 'default': int}."""
        response = self._api_call(
            'get_devices',
            {'id': self._computer_id},
            exit_on_error=False,
            message=_('Getting devices...'),
        )
        return self._handle_response_with_default(response, default=None)

    @require_computer_id
    def get_traits(self):
        if not self._quiet:
            self._show_message(_('Getting traits...'))

        response = self._api_call('get_traits', {'id': self._computer_id})

        if 'error' in response:
            self.operation_failed(response['error']['info'])
            sys.exit(errno.ENODATA)

        if not self._quiet:
            self.operation_ok()

        return response

    def upload_old_errors(self):
        """
        if there are old errors, upload them to server
        """
        if os.path.isfile(self.ERROR_FILE) and os.stat(self.ERROR_FILE).st_size:
            if not self._computer_id:
                self.get_computer_id()

            self.show_stage(_('Uploading old errors...'), stage='connection')
            with self.console.status(''):
                response = self._url_request.run(
                    url=self.api_endpoint(self.URLS['upload_errors']),
                    data={'id': self._computer_id, 'description': utils.read_file(self.ERROR_FILE, 'r')},
                    debug=self._debug,
                )
                logger.debug('Response upload_old_errors: %s', response)

            self.operation_ok()
            os.remove(self.ERROR_FILE)

        self._url_request._check_tmp_path()
        self._error_file_descriptor = open(self.ERROR_FILE, 'wb')  # noqa: SIM115

    def upload_execution_errors(self):
        self._error_file_descriptor.close()
        self._error_file_descriptor = None

        if os.stat(self.ERROR_FILE).st_size:
            self.show_stage(_('Sending errors to server...'), stage='connection')
            with self.console.status(''):
                self._url_request.run(
                    url=self.api_endpoint(self.URLS['upload_errors']),
                    data={'id': self._computer_id, 'description': utils.read_file(self.ERROR_FILE, 'r')},
                    debug=self._debug,
                )
            self.operation_ok()

            if not self._debug:
                os.remove(self.ERROR_FILE)

    def upload_attributes(self):
        response = self.get_properties()

        attributes = self._eval_attributes(response)
        logger.debug('Attributes to send: %s', attributes)

        self.show_stage(_('Uploading attributes...'), stage='attributes')
        with self.console.status(''):
            response = self._url_request.run(
                url=self.api_endpoint(self.URLS['upload_attributes']), data=attributes, debug=self._debug
            )

        self.operation_ok()
        logger.debug('Response upload_attributes: %s', response)

        return response

    def upload_faults(self):
        response = self.get_fault_definitions()
        if response:
            data = self._eval_faults(response)
            logger.debug('Faults to send: %s', data)

            self.show_stage(_('Uploading faults...'), stage='faults')
            with self.console.status(''):
                response = self._url_request.run(
                    url=self.api_endpoint(self.URLS['upload_faults']), data=data, debug=self._debug
                )

            self.operation_ok()
            logger.debug('Response upload_faults: %s', response)

        return response

    def end_synchronization(self, start_date, consumer=''):
        if not consumer:
            consumer = self.CMD

        self.show_stage(_('Ending synchronization...'), stage='finish')
        with self.console.status(''):
            response = self._url_request.run(
                url=self.api_endpoint(self.URLS['upload_sync']),
                data={
                    'id': self._computer_id,
                    'start_date': start_date,
                    'consumer': f'{consumer} {utils.get_mfc_release()}',
                    'pms_status_ok': self._pms_status_ok,
                },
                debug=self._debug,
            )

        self.operation_ok()
        logger.debug('Response upload_sync: %s', response)

        return response

    @require_sign_keys
    def cmd_synchronize(self):
        start_date = datetime.now().isoformat()
        self.show_stage(_('Connecting to migasfree server...'), stage='connection')

        available, _retry_after = availability.check_availability(
            self._url_request, self.api_endpoint(self.URLS['upload_sync_availability']), self._computer_id
        )
        if not available:
            msg = _('Server is saturated. Synchronization will be queued and performed via migasfree-agent service.')
            self._show_message(msg)
            logger.warning(msg)
            sys.exit(errno.EAGAIN)

        self.upload_old_errors()
        self._execute_path(settings.PRE_SYNC_PATH)
        self.upload_attributes()
        self.upload_faults()

        if self.pms:
            software_before = self.pms.query_all()
            logger.debug('Actual software: %s', software_before)

            software_history = self.software_history(software_before)

            self.create_repositories()
            self.clean_pms_cache()
            self.mandatory_pkgs()
            if self.migas_auto_update_packages is True:
                self._update_packages()

            self.upload_software(software_before, software_history)

        if self.migas_upload_hardware and self.hardware_capture_is_required():
            self.update_hardware_inventory()

        self.sync_logical_devices()

        self._traits()

        self._events()

        self._execute_path(settings.POST_SYNC_PATH)
        self.upload_execution_errors()
        self.end_synchronization(start_date)
        self.end_of_transmission()
        self.show_stage(_('Completed operations'), stage='finish')

    def cmd_attributes(self):
        self.show_stage(_('Connecting to migasfree server...'), stage='connection')
        self.upload_old_errors()
        self.upload_attributes()
        self.upload_execution_errors()
        self.end_of_transmission()
        self.show_stage(_('Completed operations'), stage='finish')

    def cmd_faults(self):
        self.show_stage(_('Connecting to migasfree server...'), stage='connection')
        self.upload_old_errors()
        self.upload_faults()
        self.upload_execution_errors()
        self.end_of_transmission()
        self.show_stage(_('Completed operations'), stage='finish')

    def cmd_devices(self):
        self.show_stage(_('Connecting to migasfree server...'), stage='connection')
        self.upload_old_errors()
        self.sync_logical_devices()
        self.upload_execution_errors()
        self.end_of_transmission()
        self.show_stage(_('Completed operations'), stage='finish')

    def cmd_hardware(self):
        self.show_stage(_('Connecting to migasfree server...'), stage='connection')
        self.upload_old_errors()
        self.update_hardware_inventory()
        self.upload_execution_errors()
        self.end_of_transmission()
        self.show_stage(_('Completed operations'), stage='finish')

    def cmd_software(self):
        if self.pms:
            self.show_stage(_('Connecting to migasfree server...'), stage='connection')
            self.upload_old_errors()

            software_before = self.pms.query_all()
            logger.debug('Actual software: %s', software_before)

            software_history = self.software_history(software_before)
            self.upload_software(software_before, software_history)

            self.upload_execution_errors()
            self.end_of_transmission()
            self.show_stage(_('Completed operations'), stage='finish')

    def _traits(self, show=True):
        traits = self.get_traits()
        if show:
            if getattr(self, '_json', False):
                import sys

                sys.stdout.write(json.dumps({'type': 'traits', 'data': traits}) + '\n')
                sys.stdout.flush()
            else:
                self.console.print(json.dumps(traits, indent=settings.JSON_INDENT, ensure_ascii=False), soft_wrap=True)

        content = {}
        if os.path.isfile(settings.TRAITS_FILE):
            content = json.loads(utils.read_file(settings.TRAITS_FILE))

        before = content.get('after', [])

        content = {'before': before, 'after': traits}

        utils.write_file(settings.TRAITS_FILE, json.dumps(content, indent=settings.JSON_INDENT))

        return traits

    def _run_events(self, diff):
        self.show_stage(_('Running events...'), stage='software')

        sentinel = True
        for key, _value in diff:
            event = os.path.join(settings.EVENTS_SYNC_PATH, key)
            if os.path.exists(event):
                for filename in os.listdir(event):
                    _file = os.path.join(event, filename)
                    ret, _output, error = utils.execute([_file], interactive=False)
                    if ret != 0:
                        sentinel = False
                        msg = _('Error running event %s: %s') % (_file, error)
                        self.operation_failed(msg)
                        logging.error(msg)
                        self._write_error(msg)

        if sentinel:
            self.operation_ok()

    def _events(self):
        def to_prefix_dict(traits_list):
            ret = defaultdict(list)

            for item in traits_list:
                ret[item['prefix']].append(item['value'])

            return dict(ret)

        def to_env(content, prefix):
            ret = ''
            for key in content:
                if len(content[key]) == 1:
                    value = utils.escape_quotes(content[key][0])
                    ret += f'{prefix}{key}="{value}"\n'
                else:
                    value = ' '.join([f'"{utils.escape_quotes(item)}"' for item in content[key]])
                    ret += f'{prefix}{key}=({value})\n'

            return ret

        # read traits
        content = json.loads(utils.read_file(settings.TRAITS_FILE))
        before = content.get('before', [])
        after = content.get('after', [])

        before_prefix_value = to_prefix_dict(before)
        after_prefix_value = to_prefix_dict(after)

        # create events environment
        if not os.path.isdir(settings.EVENTS_SYNC_PATH):
            os.makedirs(settings.EVENTS_SYNC_PATH)

        utils.write_file(
            settings.EVENTS_JSON_FILE,
            json.dumps(
                {
                    'before': before_prefix_value,
                    'after': after_prefix_value,
                },
                indent=settings.JSON_INDENT,
            ),
        )

        utils.write_file(
            settings.EVENTS_ENV_FILE,
            f'{to_env(before_prefix_value, "BEFORE_TRAIT_")}{to_env(after_prefix_value, "TRAIT_")}',
        )

        # calculate diff
        diff = [
            (key, {'before': before_prefix_value.get(key), 'after': after_prefix_value.get(key)})
            for key in before_prefix_value
            if key not in after_prefix_value or before_prefix_value[key] != after_prefix_value[key]
        ]
        if not diff:
            return

        self._run_events(diff)

    def cmd_install_package(self, pkg):
        self._check_pms()

        software_before = self.pms.query_all()
        software_history = self.software_history(software_before)

        self._show_message(_('Installing package: %s') % pkg)
        ret = self.pms.install(pkg)

        self.upload_software(software_before, software_history)
        self.end_of_transmission()

        return ret

    def cmd_remove_package(self, pkg):
        self._check_pms()

        software_before = self.pms.query_all()
        software_history = self.software_history(software_before)

        self._show_message(_('Removing package: %s') % pkg)
        ret = self.pms.remove(pkg)

        self.upload_software(software_before, software_history)
        self.end_of_transmission()

        return ret

    def _is_migasfree_printer(self, printer_info):
        """Check if printer info follows migasfree format (5 parts separated by __)."""
        return len(printer_info.split('__')) == 5

    def _get_printer_logical_id(self, printer_info):
        """Extract logical_id from migasfree printer info format."""
        return int(printer_info.split('__')[4])

    def _install_device_packages(self, devices):
        """Install required packages for devices. Returns False if installation fails."""
        for device in devices['logical']:
            if (
                'PRINTER' in device
                and 'packages' in device['PRINTER']
                and device['PRINTER']['packages']
                and not self.install_mandatory_packages(device['PRINTER']['packages'])
            ):
                return False
        return True

    def _init_devices_class(self):
        """Initialize device class and validate connection. Returns False on error."""
        self._devices_class_selection()
        if not self.devices_class:
            _msg = _('A class was not detected to manage the devices')
            logging.error(_msg)
            self._write_error(_msg)
            return False

        try:
            self.devices_class.get_connection()
        except RuntimeError:
            self.show_stage(_('Synchronizing logical devices...'), stage='hardware')
            _msg = _('Printer service is not running')
            self.operation_failed(_msg)
            logging.error(_msg)
            self._write_error(_msg)
            return False
        except NameError:
            self.show_stage(_('Synchronizing logical devices...'), stage='hardware')
            _msg = _('Printer service is required. If not, configure Manage_Devices parameter to False.')
            self.operation_failed(_msg)
            logging.error(_msg)
            self._write_error(_msg)
            return False

        return True

    def _build_logical_devices_map(self, devices):
        """Build dictionary of logical devices keyed by id."""
        logical_devices = {}
        for device in devices['logical']:
            if 'PRINTER' in device:
                dev = self.devices_class.load_device(device['PRINTER'])
                logical_devices[int(dev.logical_id)] = copy.deepcopy(dev)
        return logical_devices

    def _sync_existing_printers(self, printers, logical_devices):
        """Sync existing printers: relate to logical devices or remove orphans."""
        for printer in printers:
            printer_info = printers[printer]['printer-info']
            if not self._is_migasfree_printer(printer_info):
                continue

            key = self._get_printer_logical_id(printer_info)
            if key in logical_devices:
                logical_devices[key].printer_name = printer
                logical_devices[key].printer_data = printers[printer]
            else:
                self._remove_orphan_printer(printer)

    def _remove_orphan_printer(self, printer):
        """Remove a printer that is no longer in logical devices."""
        try:
            self._show_message(_('Removing device: %s') % printer)
            self.devices_class.delete(printer)
            self.operation_ok()
            logging.debug('Device removed: %s', printer)
        except RuntimeError:
            self._report_error(_('Error removing device: %s') % printer)

    def _install_changed_devices(self, logical_devices):
        """Install devices that have changed configuration."""
        for _key, value in logical_devices.items():
            if value.driver is None:
                self._report_missing_driver_error(value)
                continue

            if value.is_changed():
                self._install_device(value)

    def _report_missing_driver_error(self, device):
        """Report error for device with missing driver."""
        _msg = _(
            'Error: no driver defined for device %s. '
            'Please, configure capability %s, in the model %s %s, and project %s'
        ) % (
            device.name,
            device.info.split('__')[2],  # capability
            device.info.split('__')[0],  # manufacturer
            device.info.split('__')[1],  # model
            self.migas_project,
        )
        self._report_error(_msg)

    def _install_device(self, device):
        """Install a single device."""
        self._show_message(_('Installing device: %s') % device.name)
        if device.install():
            self.operation_ok()
            logging.debug('Device installed: %s', device.name)
        else:
            self._report_error(_('Error installing device: %s') % device.name)

    def _set_default_printer(self, devices, logical_devices):
        """Set system default printer if specified. Returns False on error."""
        if devices['default'] == 0 or devices['default'] not in logical_devices:
            return True

        device = logical_devices[devices['default']]
        _printer_name = device.name or device.printer_name

        if self.devices_class.get_printer_id(self.devices_class.get_default()) == devices['default']:
            return True  # Already set as default

        try:
            self._show_message(_('Setting default device: %s') % _printer_name)
            self.devices_class.set_default(_printer_name)
            self.operation_ok()
        except RuntimeError:
            self._report_error(_('Error setting default device: %s') % _printer_name)
            return False

        return True

    def sync_logical_devices(self):
        """Synchronize logical devices from server with local printers."""
        devices = self.get_devices()
        if not devices:
            return False

        if not self.migas_manage_devices:
            _msg = _('Assigned device(s) but client does not manage devices')
            logging.error(_msg)
            self._write_error(_msg)
            return False

        if not self._install_device_packages(devices):
            return False

        if not self._init_devices_class():
            return False

        logical_devices = self._build_logical_devices_map(devices)

        try:
            printers = self.devices_class.get_printers()
        except RuntimeError:
            self.show_stage(_('Synchronizing logical devices...'), stage='hardware')
            self._report_error(_('Error getting printers information'))
            return False

        self._sync_existing_printers(printers, logical_devices)
        self._install_changed_devices(logical_devices)

        return self._set_default_printer(devices, logical_devices)

    def _handle_sync_command(self, args):
        self._check_user_is_root()
        if args.force_upgrade:
            self.migas_auto_update_packages = True

        if args.devices:
            with lock_file_context(self.CMD, self.LOCK_FILE):
                self.cmd_devices()
        elif args.software:
            with lock_file_context(self.CMD, self.LOCK_FILE):
                self.cmd_software()
        elif args.hardware:
            self.cmd_hardware()
        elif args.attributes:
            self.cmd_attributes()
        elif args.faults:
            self.cmd_faults()
        else:
            with lock_file_context(self.CMD, self.LOCK_FILE):
                self.cmd_synchronize()

        if not self._pms_status_ok:
            sys.exit(errno.EPROTO)

    def _handle_install_command(self, args):
        self._check_user_is_root()
        with lock_file_context(self.CMD, self.LOCK_FILE):
            self.cmd_install_package(' '.join(args.pkg_install))

    def _handle_purge_command(self, args):
        self._check_user_is_root()
        with lock_file_context(self.CMD, self.LOCK_FILE):
            self.cmd_remove_package(' '.join(args.pkg_purge))

    def run(self, args=None):
        super().run(args)

        if not self._quiet:
            self._show_running_options()

        if not args or not hasattr(args, 'cmd'):
            self._usage_examples()
            sys.exit(utils.ALL_OK)

        command_handlers = {
            'sync': self._handle_sync_command,
            'install': self._handle_install_command,
            'purge': self._handle_purge_command,
        }

        handler = command_handlers.get(args.cmd)
        if handler:
            handler(args)

        sys.exit(utils.ALL_OK)
