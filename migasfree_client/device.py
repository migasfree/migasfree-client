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

import gettext
import json
import logging
import sys

from .command import MigasFreeCommand, lock_file_context, require_computer_id, require_sign_keys
from .utils import ALL_OK

__author__ = 'Jose Antonio Chavarría <jachavar@gmail.com>'
__license__ = 'GPLv3'
__all__ = ['MigasFreeDevices']

_ = gettext.gettext
logger = logging.getLogger('migasfree_client')


class MigasFreeDevices(MigasFreeCommand):
    def __init__(self):
        super().__init__()

    @require_sign_keys
    @require_computer_id
    def get_assigned_devices(self):
        logger.debug('Getting assigned devices')
        response = self._api_call('get_devices', exit_on_error=True)
        return self._handle_response(response, success_msg=False)

    @require_sign_keys
    @require_computer_id
    def get_available_devices(self):
        logger.debug('Getting available physical devices')
        data = {'cid': self._computer_id}

        response = self._api_call('get_available_devices', data=data)

        return self._handle_response(response, success_msg=False)

    @require_sign_keys
    @require_computer_id
    def get_logical_devices(self, device_id=None):
        logger.debug('Getting logical devices')
        data = {'cid': self._computer_id}
        if device_id:
            data['did'] = device_id

        response = self._api_call('get_logical_devices', data=data)

        return self._handle_response(response, success_msg=False)

    @require_sign_keys
    def get_capabilities(self, capability_id=None):
        logger.debug('Getting capabilities')
        data = {}
        if capability_id:
            data['id'] = capability_id

        response = self._api_call('get_capabilities', data=data)

        return self._handle_response(response, success_msg=False)

    def run(self, args=None):
        super().run(args)

        with lock_file_context(self.CMD, self.LOCK_FILE):
            if getattr(args, 'available', False):
                results = self.get_available_devices()
            elif getattr(args, 'logical', False):
                device_id = getattr(args, 'device_id', None)
                results = self.get_logical_devices(device_id=device_id)
            elif getattr(args, 'capabilities', None):
                capability_id = getattr(args, 'capabilities', None)
                results = self.get_capabilities(capability_id=capability_id)
            else:
                results = self.get_assigned_devices()

        if getattr(args, 'json', False):
            self.console.print(json.dumps(results, ensure_ascii=False), soft_wrap=True)
        else:
            self.console.print()
            self.console.print(_('Devices:'))
            for item in results:
                name = item.get('name') or item.get('capability', {}).get('name') or _('Unknown')
                self.console.print(f'  {item.get("id", "")}: {name}')

        sys.exit(ALL_OK)
