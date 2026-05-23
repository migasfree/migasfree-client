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
import logging
import sys

from rich.table import Table

from .command import MigasFreeCommand, require_computer_id, require_sign_keys
from .utils import ALL_OK

__author__ = 'Jose Antonio Chavarría <jachavar@gmail.com>'
__license__ = 'GPLv3'
__all__ = ['MigasFreeAttributes']

_ = gettext.gettext
logger = logging.getLogger('migasfree_client')


class MigasFreeAttributes(MigasFreeCommand):
    def __init__(self):
        super().__init__()

    @require_computer_id
    def get_assigned_attributes(self):
        import os

        if not os.path.isfile(os.path.join(self._get_keys_path(), self.PRIVATE_KEY)):
            return {}

        logger.debug('Getting assigned attributes')
        response = self._api_call('get_assigned_attributes', data={'id': self._computer_id}, exit_on_error=False)

        if isinstance(response, dict) and 'error' in response:
            self.operation_failed(
                '{} ({})'.format(response['error']['info'], _('Review keys or register computer again'))
            )
            import errno

            sys.exit(errno.ENODATA)

        return response

    @require_computer_id
    def get_cid_attribute(self):
        import os

        if not os.path.isfile(os.path.join(self._get_keys_path(), self.PRIVATE_KEY)):
            return {}

        logger.debug('Getting CID attribute')
        response = self._api_call('get_cid_attribute', data={'id': self._computer_id}, exit_on_error=False)

        if isinstance(response, dict) and 'error' in response:
            self.operation_failed(
                '{} ({})'.format(response['error']['info'], _('Review keys or register computer again'))
            )
            import errno

            sys.exit(errno.ENODATA)

        return response

    @require_sign_keys
    def _show_attributes(self, cid_only=False, output_json=False):
        info = self.get_cid_attribute() if cid_only else self.get_assigned_attributes()

        if output_json:
            import json

            self.console.print(json.dumps(info), soft_wrap=True)
            return

        table = Table(show_header=True, header_style='bold')

        if not self._quiet:
            table.add_column('ID')
            table.add_column('VALUE')
            if 'results' in info and isinstance(info['results'], list):
                for attr in info['results']:
                    table.add_row(str(attr.get('id', '')), str(attr.get('value', '')))
            self.console.print(table)
        else:
            if 'results' in info and isinstance(info['results'], list):
                for attr in info['results']:
                    self.console.print(f'{attr.get("id", "")}\t{attr.get("value", "")}')

    def run(self, args=None):
        super().run(args)

        if not self._quiet:
            self._show_running_options()
            self.console.print()

        output_json = getattr(args, 'json', False)
        cid_only = getattr(args, 'cid', False)

        self._show_attributes(cid_only=cid_only, output_json=output_json)
        self.end_of_transmission()

        sys.exit(ALL_OK)
