# Copyright (c) 2026 Jose Antonio Chavarría <jachavar@gmail.com>
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
import gettext
import logging
import os
import socket
import tempfile

from .. import network, utils
from .renderer import show_stage

_ = gettext.gettext
logger = logging.getLogger('migasfree_client')


class CodeEvaluatorMixin:
    """
    Mixin for executing server-provided code (traits, faults).
    Assumes it is mixed into a class that has:
    - _computer_id
    - migas_computer_name
    - _graphic_user
    - console
    - operation_ok()
    - operation_failed()
    - _write_error()
    - _show_message()
    """

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

        if lang not in allowed_languages:
            return 0, '', ''

        if lang == 'python':
            if utils.is_windows():
                import sys

                if getattr(sys, 'frozen', False):
                    cmd = [sys.executable, 'eval', filename]
                else:
                    cmd = [sys.executable, filename]
            else:
                cmd = ['python3', filename]
        elif lang == 'cmd' and utils.is_windows():
            cmd = ['cmd', '/c', filename]
        elif lang == 'powershell' and utils.is_windows():
            cmd = ['powershell', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', filename]
        else:
            cmd = [lang, filename]

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
        show_stage(self, _('Evaluating attributes...'), stage='attributes')
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

        show_stage(self, _('Executing faults...'), stage='faults')
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
