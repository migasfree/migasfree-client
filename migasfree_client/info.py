# Copyright (c) 2018-2025 Jose Antonio Chavarría <jachavar@gmail.com>
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
import logging
import sys

from rich.table import Table

from .command import MigasFreeCommand, require_computer_id, require_sign_keys
from .utils import ALL_OK

__author__ = 'Jose Antonio Chavarría <jachavar@gmail.com>'
__license__ = 'GPLv3'
__all__ = ['MigasFreeInfo']

_ = gettext.gettext
logger = logging.getLogger('migasfree_client')


class MigasFreeInfo(MigasFreeCommand):
    def __init__(self):
        self._check_user_is_root()
        super().__init__()

    @require_computer_id
    def get_label(self):
        logger.debug('Getting label')
        with self.console.status(''):
            response = self._url_request.run(
                url=self.api_endpoint(self.URLS['get_label']),
                data={'id': self._computer_id},
                debug=self._debug,
            )

        logger.debug('Response get_label: %s', response)
        if self._debug:
            self.console.log(f'Response: {response}')

        if 'error' in response:
            self.operation_failed(response['error']['info'])
            sys.exit(errno.ENODATA)

        return response

    @require_sign_keys
    def _show_info(self, key=None):
        info = self.get_label()
        table = Table(show_header=True, header_style='bold')

        if not key:
            if not self._quiet:
                table.add_column('ID')
                table.add_column('NAME')
                table.add_column('SEARCH')
                table.add_column('UUID')
                table.add_row(str(self._computer_id), info['name'], info['search'], info['uuid'])
                self.console.print(table)
            else:
                print(f'{self._computer_id}\t{info["name"]}\t{info["search"]}\t{info["uuid"]}')
        elif key == 'id':
            if not self._quiet:
                table.add_column('ID')
                table.add_row(str(self._computer_id))
                self.console.print(table)
            else:
                print(self._computer_id)
        else:
            if not self._quiet:
                table.add_column(key.upper())
                table.add_row(info[key])
                self.console.print(table)
            else:
                print(info[key])

    def run(self, args=None):
        super().run(args)

        if not self._quiet:
            self._show_running_options()
            print()

        self._show_info(key=args.key)
        self.end_of_transmission()

        sys.exit(ALL_OK)
