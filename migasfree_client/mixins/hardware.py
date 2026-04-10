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

import errno
import gettext
import json
import logging
import os
import sys

from migasfree_client import utils
from migasfree_client.command import require_computer_id

_ = gettext.gettext
logger = logging.getLogger('migasfree_client')


class HardwareCollectorMixin:
    """
    Mixin for collecting and uploading hardware inventory (using lshw).
    Assumes it is mixed into a class that has:
    - _computer_id
    - console
    - _url_request
    - api_endpoint()
    - URLS
    - _debug
    - operation_failed()
    - operation_ok()
    - _show_message()
    - _report_error()
    """

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
