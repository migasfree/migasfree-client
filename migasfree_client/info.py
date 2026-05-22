# Copyright (c) 2018-2026 Jose Antonio Chavarría <jachavar@gmail.com>
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
        super().__init__()

    @require_computer_id
    def get_info(self):
        logger.debug('Getting info')
        response = self._api_call('get_info', {'id': self._computer_id})
        return self._handle_response(response, success_msg=False)

    @require_sign_keys
    def _show_info(self, key=None, output_json=False):
        info = self.get_info()

        if output_json:
            import json

            if not key:
                out = info.copy()
                out['id'] = self._computer_id
                self.console.print(json.dumps(out))
            elif key == 'id':
                self.console.print(json.dumps({'id': self._computer_id}))
            else:
                self.console.print(json.dumps({key: info[key]}))
            return

        table = Table(show_header=True, header_style='bold')

        if not key:
            if not self._quiet:
                table.add_column('KEY')
                table.add_column('VALUE')
                table.add_row('id', str(self._computer_id))
                for k in sorted(info.keys()):
                    val = str(info[k]) if info[k] is not None else ''
                    table.add_row(k, val)
                self.console.print(table)
            else:
                fields = [str(self._computer_id)]
                for k in sorted(info.keys()):
                    val = str(info[k]) if info[k] is not None else ''
                    fields.append(val)
                self.console.print('\t'.join(fields))
        elif key == 'id':
            if not self._quiet:
                table.add_column('ID')
                table.add_row(str(self._computer_id))
                self.console.print(table)
            else:
                self.console.print(str(self._computer_id))
        else:
            val = str(info[key]) if info[key] is not None else ''
            if not self._quiet:
                table.add_column(key.upper())
                table.add_row(val)
                self.console.print(table)
            else:
                self.console.print(val)

    def run(self, args=None):
        super().run(args)

        if not self._quiet:
            self._show_running_options()
            self.console.print()

        key = getattr(args, 'key', None)
        output_json = getattr(args, 'json', False)

        self._show_info(key=key, output_json=output_json)
        self.end_of_transmission()

        sys.exit(ALL_OK)
