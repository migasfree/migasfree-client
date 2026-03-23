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

import contextlib
import copy
import errno
import gettext
import json
import logging
import os
import signal
import socket
import sys
import tempfile
from collections import defaultdict
from datetime import datetime

from . import (
    availability,
    network,
    settings,
    utils,
)
from .command import MigasFreeCommand, lock_file_context, require_computer_id, require_sign_keys

__author__ = 'Jose Antonio Chavarría <jachavar@gmail.com>'
__license__ = 'GPLv3'
__all__ = ['MigasFreeSync']

_ = gettext.gettext
logger = logging.getLogger('migasfree_client')


class MigasFreeSync(MigasFreeCommand):
    APP_NAME = 'Migasfree'

    _graphic_user = None

    _error_file_descriptor = None

    _pms_status_ok = True  # indicates the status of transactions with PMS

    def __init__(self):
        self._check_user_is_root()

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
        self._show_message(_('Killing %s before time!!!') % self.CMD)
        logger.critical('Exiting %s, signal: %s', self.CMD, signal_number)
        sys.exit(errno.EINPROGRESS)

    def _show_running_options(self):
        super()._show_running_options()

        print('\t{}: {}'.format(_('Graphic user'), self._graphic_user))
        print()

    def _usage_examples(self):
        print('\n' + _('Examples:'))

        print('  ' + _('Register computer at server:'))
        print(f'\t{self.CMD} register\n')

        print('  ' + _('Synchronize computer with server:'))
        print(f'\t{self.CMD} sync\n')

        print('  ' + _('Search package:'))
        print(f'\t{self.CMD} search bluefish\n')

        print('  ' + _('Install package:'))
        print(f'\t{self.CMD} install bluefish\n')

        print('  ' + _('Purge package:'))
        print(f'\t{self.CMD} purge bluefish\n')

        print('  ' + _('Get computer traits at server:'))
        print(f'\t{self.CMD} traits\n')
        print(f'\t{self.CMD} traits SET\n')
        print(f'\t{self.CMD} traits CID id\n')

    def _eval_code(self, name, lang, code):
        code = code.replace('\r', '').strip()  # clean code
        logger.debug('Name: %s', name)
        logger.debug('Language code: %s', lang)
        logger.debug('Code: %s', code)

        filename = tempfile.mkstemp()[1]
        utils.write_file(filename, code)

        allowed_languages = ['python', 'perl', 'php', 'ruby']
        if utils.is_linux():
            allowed_languages.append('bash')
        if utils.is_windows():
            allowed_languages.extend(['cmd', 'powershell'])

        if lang in allowed_languages:
            if lang == 'python' and utils.is_linux():
                lang = 'python3'
            cmd = [lang, filename]
        else:
            cmd = [':']  # gracefully degradation

        ret, output, error = utils.timeout_execute(cmd)
        logger.debug('Executed command: %s', cmd)
        logger.debug('Output: %s', output)
        if ret != 0:
            logger.error('Error: %s', error)
            msg = _('Name: "%s"\n') % name
            msg += _('Code "%s" with error: %s') % (code, error)
            self._write_error(msg)

        with contextlib.suppress(IOError):
            os.remove(filename)

        return ret, output, error

    def _eval_attributes(self, properties):
        response = {
            'id': self._computer_id,
            'uuid': utils.get_hardware_uuid(),
            'name': self.migas_computer_name,
            'fqdn': socket.getfqdn(),
            'ip_address': network.get_network_info()['ip'],
            'sync_user': self._graphic_user,
            'sync_fullname': utils.get_user_info(self._graphic_user)['fullname'],
            'sync_attributes': {},
        }

        # properties converted in attributes
        self._show_message(_('Evaluating attributes...'))
        with self.console.status(''):
            for item in properties:
                ret, response['sync_attributes'][item['prefix']], error = self._eval_code(
                    item['prefix'], item['language'], item['code']
                )
                info = f'{item["prefix"]}: {response["sync_attributes"][item["prefix"]]}'
                if ret == 0 and response['sync_attributes'][item['prefix']].strip() != '':
                    self.operation_ok(info)
                else:
                    if error:
                        info = f'{item["prefix"]}: {error}'
                        self.operation_failed(info)
                        self._write_error(_('Error: property %s without value') % item['prefix'])

        return response

    def _eval_faults(self, fault_definitions):
        response = {'id': self._computer_id, 'faults': {}}

        self._show_message(_('Executing faults...'))
        with self.console.status(''):
            for item in fault_definitions:
                ret, result, error = self._eval_code(item['name'], item['language'], item['code'])
                info = f'{item["name"]}: {result}'
                if ret == 0:
                    if result:
                        # only send faults with output!!!
                        response['faults'][item['name']] = result
                        self.operation_failed(info)
                    else:
                        self.operation_ok(info)
                else:
                    self.operation_failed(f'{item["name"]}: {error}')

        return response

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
            msg = _('Error writing key file!!!')
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

    @staticmethod
    def software_history(software):
        history = {}

        # if have been managed packages manually
        # information is uploaded to server
        if os.path.isfile(settings.SOFTWARE_FILE) and os.stat(settings.SOFTWARE_FILE).st_size:
            diff_software = utils.compare_lists(
                open(settings.SOFTWARE_FILE, encoding='utf_8').read().splitlines(),  # not readlines!!!  # noqa: SIM115
                software,
            )

            if diff_software:
                history = {
                    'installed': [x for x in diff_software if x.startswith('+')],
                    'uninstalled': [x for x in diff_software if x.startswith('-')],
                }
                logger.debug('Software diff: %s', history)

        return history

    def upload_old_errors(self):
        """
        if there are old errors, upload them to server
        """
        if os.path.isfile(self.ERROR_FILE) and os.stat(self.ERROR_FILE).st_size:
            if not self._computer_id:
                self.get_computer_id()

            self._show_message(_('Uploading old errors...'))
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

    def create_repositories(self):
        self._check_pms()

        repos = self.get_repositories()

        self._show_message(_('Creating repositories...'))

        server = self.migas_server
        if self.migas_package_proxy_cache:
            server = f'{self.migas_package_proxy_cache}/{server}'

        ret = self.pms.create_repos(self.migas_protocol, server, repos)

        if ret:
            self.operation_ok()
        else:
            self._pms_status_ok = False
            self._report_error(_('Error creating repositories: %s') % repos)

    def clean_pms_cache(self):
        """
        clean cache of Package Management System
        """
        self._check_pms()

        self._show_message(_('Getting repositories metadata...'))
        ret = self.pms.clean_all()

        if ret:
            self.operation_ok()
        else:
            self._report_error(_('Error getting repositories metadata'))

    def uninstall_packages(self, packages):
        self._check_pms()

        self._show_message(_('Uninstalling packages...'))
        ret, error = self.pms.remove_silent(packages)

        if ret:
            self.operation_ok()
        else:
            self._pms_status_ok = False
            self._report_error(_('Error uninstalling packages: %s') % error)

    def install_mandatory_packages(self, packages):
        self._check_pms()

        self._show_message(_('Installing mandatory packages...'))
        ret, error = self.pms.install_silent(packages)

        if ret:
            self.operation_ok()
        else:
            self._pms_status_ok = False
            self._report_error(_('Error installing packages: %s') % error)

        return ret

    def _update_packages(self):
        self._check_pms()

        self._show_message(_('Updating packages...'))
        ret, error = self.pms.update_silent()

        if ret:
            self.operation_ok()
        else:
            self._pms_status_ok = False
            self._report_error(_('Error updating packages: %s') % error)

        return ret

    @require_computer_id
    def hardware_capture_is_required(self):
        with self.console.status(''):
            response = self._url_request.run(
                url=self.api_endpoint(self.URLS['get_hardware_required']),
                data={'id': self._computer_id},
                exit_on_error=False,
                debug=self._debug,
            )
            logger.debug('Response hardware_capture_is_required: %s', response)

        if isinstance(response, dict) and 'error' in response:
            self.operation_failed(response['error']['info'])
            sys.exit(errno.ENODATA)

        return response.get('capture', False)

    @require_computer_id
    def update_hardware_inventory(self):
        hardware = {}

        self._show_message(_('Capturing hardware information...'))
        env = os.environ.copy()
        if not utils.is_windows():
            env['LC_ALL'] = 'C'
        cmd = ['lshw', '-json']
        if utils.is_windows():
            cmd = ['lshw', '--json']
            env = None
        with self.console.status(''):
            ret, output, error = utils.execute(cmd, interactive=False, env=env)

        if ret == 0:
            self.operation_ok()
        else:
            self._report_error(_('lshw command failed: %s') % error)
            return

        try:
            hardware = json.loads(output)
        except ValueError as e:
            self._show_message(_('Parsing hardware information...'))
            self._report_error(f'{_("Hardware information")}: {e!s}')
            return

        logger.debug('Hardware inventory: %s', hardware)

        self._show_message(_('Sending hardware information...'))
        response = self._url_request.run(
            url=self.api_endpoint(self.URLS['upload_hardware']),
            data={'id': self._computer_id, 'hardware': hardware},
            exit_on_error=False,
            debug=self._debug,
        )
        logger.debug('Response upload_hardware: %s', response)

        if 'error' in response:
            self._report_error(response['error']['info'])
            return

        self.operation_ok()

    def upload_execution_errors(self):
        self._error_file_descriptor.close()
        self._error_file_descriptor = None

        if os.stat(self.ERROR_FILE).st_size:
            self._show_message(_('Sending errors to server...'))
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

        self._show_message(_('Uploading attributes...'))
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

            self._show_message(_('Uploading faults...'))
            with self.console.status(''):
                response = self._url_request.run(
                    url=self.api_endpoint(self.URLS['upload_faults']), data=data, debug=self._debug
                )

            self.operation_ok()
            logger.debug('Response upload_faults: %s', response)

        return response

    def mandatory_pkgs(self):
        response = self.get_mandatory_packages()
        if not response:
            return

        if 'remove' in response:
            self.uninstall_packages(response['remove'])
        if 'install' in response:
            self.install_mandatory_packages(response['install'])

    @require_computer_id
    def upload_software(self, before, history):
        self._check_pms()

        after = self.pms.query_all()
        utils.write_file(settings.SOFTWARE_FILE, '\n'.join(after))

        diff_software = utils.compare_lists(before, after)
        if diff_software:
            data = {
                'installed': [x for x in diff_software if x.startswith('+')],
                'uninstalled': [x for x in diff_software if x.startswith('-')],
            }
            logger.debug('Software diff: %s', data)

            if data['installed']:
                if 'installed' in history:
                    history['installed'].extend(data['installed'])
                else:
                    history['installed'] = data['installed']
            if data['uninstalled']:
                if 'uninstalled' in history:
                    history['uninstalled'].extend(data['uninstalled'])
                else:
                    history['uninstalled'] = data['uninstalled']

            self._show_message(_('Software diff'))
            self.console.print(history)

        self._show_message(_('Uploading software...'))
        response = self._api_call(
            'upload_software',
            {'id': self._computer_id, 'inventory': after, 'history': history},
        )
        return self._handle_response(response)

    def end_synchronization(self, start_date, consumer=''):
        if not consumer:
            consumer = self.CMD

        self._show_message(_('Ending synchronization...'))
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
        self._show_message(_('Connecting to migasfree server...'))

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
        self._show_message(_('Completed operations'))

    def cmd_attributes(self):
        self._show_message(_('Connecting to migasfree server...'))
        self.upload_old_errors()
        self.upload_attributes()
        self.upload_execution_errors()
        self.end_of_transmission()
        self._show_message(_('Completed operations'))

    def cmd_faults(self):
        self._show_message(_('Connecting to migasfree server...'))
        self.upload_old_errors()
        self.upload_faults()
        self.upload_execution_errors()
        self.end_of_transmission()
        self._show_message(_('Completed operations'))

    def cmd_devices(self):
        self._show_message(_('Connecting to migasfree server...'))
        self.upload_old_errors()
        self.sync_logical_devices()
        self.upload_execution_errors()
        self.end_of_transmission()
        self._show_message(_('Completed operations'))

    def cmd_hardware(self):
        self._show_message(_('Connecting to migasfree server...'))
        self.upload_old_errors()
        self.update_hardware_inventory()
        self.upload_execution_errors()
        self.end_of_transmission()
        self._show_message(_('Completed operations'))

    def cmd_software(self):
        if self.pms:
            self._show_message(_('Connecting to migasfree server...'))
            self.upload_old_errors()

            software_before = self.pms.query_all()
            logger.debug('Actual software: %s', software_before)

            software_history = self.software_history(software_before)
            self.upload_software(software_before, software_history)

            self.upload_execution_errors()
            self.end_of_transmission()
            self._show_message(_('Completed operations'))

    def _traits(self, show=True):
        traits = self.get_traits()
        if show:
            print(json.dumps(traits, indent=settings.JSON_INDENT, ensure_ascii=False))

        content = {}
        if os.path.isfile(settings.TRAITS_FILE):
            content = json.loads(utils.read_file(settings.TRAITS_FILE))

        before = content.get('after', [])

        content = {'before': before, 'after': traits}

        utils.write_file(settings.TRAITS_FILE, json.dumps(content, indent=settings.JSON_INDENT))

        return traits

    @require_sign_keys
    def cmd_traits(self, prefix, key):
        traits = self._traits(show=False)
        self.end_of_transmission()

        if prefix:
            ret = filter(lambda item: item['prefix'] == prefix, traits)
            if key:
                ret = [item.get(key) for item in ret]

            traits = list(ret)

        print(json.dumps(traits, indent=settings.JSON_INDENT, ensure_ascii=False))

    def _run_events(self, diff):
        self._show_message(_('Running events...'))

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

    def cmd_search(self, pattern):
        self._check_pms()

        return self.pms.search(pattern)

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
            self._show_message(_('Synchronizing logical devices...'))
            _msg = _('Printer service is not running!!!')
            self.operation_failed(_msg)
            logging.error(_msg)
            self._write_error(_msg)
            return False
        except NameError:
            self._show_message(_('Synchronizing logical devices...'))
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
            self._show_message(_('Synchronizing logical devices...'))
            self._report_error(_('Error getting printers information'))
            return False

        self._sync_existing_printers(printers, logical_devices)
        self._install_changed_devices(logical_devices)

        return self._set_default_printer(devices, logical_devices)

    def _handle_sync_command(self, args):
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

    def _handle_register_command(self, args):
        self.cmd_register_computer(args.user)

    def _handle_search_command(self, args):
        self.cmd_search(' '.join(args.pattern))

    def _handle_install_command(self, args):
        with lock_file_context(self.CMD, self.LOCK_FILE):
            self.cmd_install_package(' '.join(args.pkg_install))

    def _handle_purge_command(self, args):
        with lock_file_context(self.CMD, self.LOCK_FILE):
            self.cmd_remove_package(' '.join(args.pkg_purge))

    def _handle_traits_command(self, args):
        self.cmd_traits(args.prefix, args.traits_key)

    def run(self, args=None):
        super().run(args)

        if not self._quiet:
            self._show_running_options()

        if not args or not hasattr(args, 'cmd'):
            self._usage_examples()
            sys.exit(utils.ALL_OK)

        command_handlers = {
            'sync': self._handle_sync_command,
            'register': self._handle_register_command,
            'search': self._handle_search_command,
            'install': self._handle_install_command,
            'purge': self._handle_purge_command,
            'traits': self._handle_traits_command,
        }

        handler = command_handlers.get(args.cmd)
        if handler:
            handler(args)

        sys.exit(utils.ALL_OK)
