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

from rich import box
from rich.columns import Columns
from rich.panel import Panel
from rich.table import Table

from .command import MigasFreeCommand, require_computer_id, require_sign_keys
from .utils import ALL_OK

__author__ = 'Jose Antonio Chavarría <jachavar@gmail.com>'
__license__ = 'GPLv3'
__all__ = ['MigasFreeDevices']

_ = gettext.gettext
logger = logging.getLogger('migasfree_client')


class MigasFreeDevices(MigasFreeCommand):
    @require_sign_keys
    @require_computer_id
    def get_assigned_devices(self):
        logger.debug('Getting assigned devices')
        response = self._api_call('get_devices', data={'id': self._computer_id}, exit_on_error=True)
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

    @require_sign_keys
    @require_computer_id
    def assign_logical(self, logical_id, assigned=True):
        logger.debug('Assigning or unassigning logical device: id=%s, assigned=%s', logical_id, assigned)
        data = {'cid': self._computer_id, 'id': int(logical_id), 'assigned': assigned}
        response = self._api_call('assign_logical', data=data)
        return self._handle_response(response, success_msg=False)

    @require_sign_keys
    @require_computer_id
    def set_default_logical(self, logical_id):
        logger.debug('Setting default logical device: logical_id=%s', logical_id)
        data = {'cid': self._computer_id, 'logical_id': int(logical_id) if logical_id and logical_id != '0' else None}
        response = self._api_call('set_default_logical', data=data)
        return self._handle_response(response, success_msg=False)

    def run(self, args=None):
        super().run(args)
        if args is None:
            return

        if getattr(args, 'available', False):
            results = self.get_available_devices()
        elif getattr(args, 'logical', False):
            device_id = getattr(args, 'device_id', None)
            results = self.get_logical_devices(device_id=device_id)
        elif getattr(args, 'capabilities', None):
            capability_id = getattr(args, 'capabilities', None)
            results = self.get_capabilities(capability_id=capability_id)
        elif isinstance(getattr(args, 'assign', None), (str, int)):
            results = self.assign_logical(args.assign, assigned=True)
        elif isinstance(getattr(args, 'unassign', None), (str, int)):
            results = self.assign_logical(args.unassign, assigned=False)
        elif isinstance(getattr(args, 'set_default', None), (str, int)):
            results = self.set_default_logical(args.set_default)
        else:
            results = self.get_assigned_devices()

        if getattr(args, 'json', False):
            self.console.print(json.dumps(results, ensure_ascii=False), soft_wrap=True)
        elif isinstance(getattr(args, 'assign', None), (str, int)):
            self.console.print(_('Logical device assigned successfully.'))
        elif isinstance(getattr(args, 'unassign', None), (str, int)):
            self.console.print(_('Logical device unassigned successfully.'))
        elif isinstance(getattr(args, 'set_default', None), (str, int)):
            self.console.print(_('Default logical device updated successfully.'))
        elif not results:
            self.console.print(_('No results found.'))
        else:
            if getattr(args, 'available', False):
                self._print_available_physical_devices(results)
            elif getattr(args, 'logical', False):
                self._print_logical_devices(results)
            elif getattr(args, 'capabilities', None):
                self._print_capabilities(results)
            else:
                self._print_assigned_devices(results)

        sys.exit(ALL_OK)

    def _print_available_physical_devices(self, results):
        table = Table(box=box.SIMPLE, show_edge=False, title=_('Available Physical Devices'))
        table.add_column('ID', style='cyan', justify='right')
        table.add_column(_('Name'), style='green')
        table.add_column(_('Model'), style='magenta')
        table.add_column(_('Connection'), style='blue')
        table.add_column(_('Location'), style='yellow')

        for item in results:
            device_id = str(item.get('id', ''))
            name = item.get('name') or _('Unknown')

            model_col = ''
            if isinstance(item.get('model'), dict):
                model_name = item['model'].get('name', '')
                manufacturer = item['model'].get('manufacturer', {}).get('name', '')
                model_col = f'{manufacturer} {model_name}'.strip()
            elif item.get('manufacturer'):
                model_col = f'{item.get("manufacturer", "")} {item.get("model", "")}'.strip()

            connection = ''
            if isinstance(item.get('connection'), dict):
                connection = item['connection'].get('name', '')

            location = item.get('location', '')
            if not location and isinstance(item.get('data'), dict):
                location = item['data'].get('LOCATION', '')

            table.add_row(device_id, name, model_col, connection, location)

        self.console.print()
        self.console.print(table)

    def _print_logical_devices(self, results):
        # Build physical devices map to get locations
        phys_locations = {}
        try:
            available = self.get_available_devices()
            for dev in available:
                if dev.get('id'):
                    phys_locations[dev['id']] = dev.get('location') or ''
        except Exception:
            pass

        devices_dict = {}
        for item in results:
            dev_info = item.get('device') or {}
            dev_id = dev_info.get('id')
            if not dev_id:
                continue

            if dev_id not in devices_dict:
                devices_dict[dev_id] = {
                    'name': dev_info.get('name') or _('Unknown'),
                    'location': phys_locations.get(dev_id) or '',
                    '__str__': item.get('__str__') or '',
                    'logical_devices': [],
                }

            logical_name = (
                item.get('alternative_capability_name') or item.get('capability', {}).get('name') or _('Unknown')
            )
            devices_dict[dev_id]['logical_devices'].append(
                {
                    'id': item.get('id', ''),
                    'name': logical_name,
                }
            )

        cards = []
        for dev_id, dev_data in sorted(devices_dict.items()):
            logical_lines = []
            for log_dev in sorted(dev_data['logical_devices'], key=lambda x: x['name']):
                logical_lines.append(
                    f'  [cyan]•[/cyan] [dim]({log_dev["id"]})[/dim] [magenta]{log_dev["name"]}[/magenta]'
                )

            logical_content = '\n'.join(logical_lines)
            str_val = dev_data.get('__str__')
            str_line = f'\n[dim]{str_val}[/dim]' if str_val else ''
            loc = dev_data['location']
            loc_str = f'\n[dim]📍 {loc}[/dim]' if loc else ''

            card_content = f'[bold green]{dev_data["name"]}[/bold green]{str_line}{loc_str}\n\n{logical_content}'

            cards.append(
                Panel(
                    card_content,
                    title=f'[bold cyan]Device ID: {dev_id}[/bold cyan]',
                    title_align='left',
                    border_style='blue',
                    width=50,
                )
            )

        self.console.print()
        self.console.print(Columns(cards, equal=True, expand=False))

    def _print_capabilities(self, results):
        table = Table(box=box.SIMPLE, show_edge=False, title=_('Capabilities'))
        table.add_column('ID', style='cyan', justify='right')
        table.add_column(_('Name'), style='green')

        for item in results:
            table.add_row(str(item.get('id', '')), item.get('name', _('Unknown')))

        self.console.print()
        self.console.print(table)

    def _print_assigned_devices(self, results):
        assigned_list = []
        default_id = 0
        if isinstance(results, dict):
            assigned_list = results.get('logical') or []
            default_id = results.get('default') or 0
        elif isinstance(results, list):
            assigned_list = results

        devices_dict = {}
        for outer_item in assigned_list:
            if not isinstance(outer_item, dict):
                continue
            inner_keys = list(outer_item.keys())
            if not inner_keys:
                continue
            inner_item = outer_item[inner_keys[0]]
            if not isinstance(inner_item, dict):
                continue

            phys_name = inner_item.get('name') or _('Unknown')
            location = ''
            conn_data = inner_item.get('connection') or {}
            if isinstance(conn_data, dict):
                location = conn_data.get('LOCATION') or ''

            if phys_name not in devices_dict:
                devices_dict[phys_name] = {
                    'name': phys_name,
                    'location': location,
                    '__str__': inner_item.get('__str__') or '',
                    'logical_devices': [],
                }

            logical_name = inner_item.get('capability') or _('Unknown')
            devices_dict[phys_name]['logical_devices'].append(
                {
                    'id': inner_item.get('id', ''),
                    'name': logical_name,
                    'is_default': inner_item.get('id') == default_id,
                }
            )

        if not devices_dict:
            self.console.print(_('No results found.'))
            return

        cards = []
        for phys_name, dev_data in sorted(devices_dict.items()):
            logical_lines = []
            for log_dev in sorted(dev_data['logical_devices'], key=lambda x: x['name']):
                bullet = '[green]✔ DEFAULT[/green]' if log_dev['is_default'] else '[cyan]•[/cyan]'
                logical_lines.append(f'  {bullet} [dim]({log_dev["id"]})[/dim] [magenta]{log_dev["name"]}[/magenta]')

            logical_content = '\n'.join(logical_lines)
            str_val = dev_data.get('__str__')
            str_line = f'\n[dim]{str_val}[/dim]' if str_val else ''
            loc = dev_data['location']
            loc_str = f'\n[dim]📍 {loc}[/dim]' if loc else ''

            card_content = f'[bold green]{phys_name}[/bold green]{str_line}{loc_str}\n\n{logical_content}'

            cards.append(
                Panel(
                    card_content,
                    title='[bold cyan]Assigned[/bold cyan]',
                    title_align='left',
                    border_style='green' if any(x['is_default'] for x in dev_data['logical_devices']) else 'blue',
                    width=50,
                )
            )

        self.console.print()
        self.console.print(Columns(cards, equal=True, expand=False))
