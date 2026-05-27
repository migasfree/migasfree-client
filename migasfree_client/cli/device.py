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

from ..command import MigasFreeCommand, require_computer_id, require_sign_keys
from ..utils import ALL_OK

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
        devices_dict = {}
        for item in results:
            device_id = item.get('id')
            if not device_id:
                continue

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

            ip = ''
            if isinstance(item.get('data'), dict):
                ip = item['data'].get('IP') or ''

            custom_name = ''
            if isinstance(item.get('data'), dict):
                custom_name = item['data'].get('NAME') or ''
                if custom_name in ('undefined', ''):
                    custom_name = ''

            devices_dict[device_id] = {
                'id': device_id,
                'name': item.get('name') or _('Unknown'),
                'model_col': model_col,
                'custom_name': custom_name,
                'location': location,
                'connection_name': connection,
                'ip': ip,
                'logical_devices': [],
            }

        self._print_device_cards(devices_dict)

    def _print_logical_devices(self, results):
        # Build physical devices map to get locations, IPs, connections, models, and custom names
        phys_locations = {}
        phys_ips = {}
        phys_connections = {}
        phys_models = {}
        phys_names = {}
        try:
            available = self.get_available_devices()
            for dev in available:
                dev_id = dev.get('id')
                if dev_id:
                    loc = dev.get('location') or ''
                    if not loc and isinstance(dev.get('data'), dict):
                        loc = dev['data'].get('LOCATION') or ''
                    phys_locations[dev_id] = loc

                    ip_val = ''
                    if isinstance(dev.get('data'), dict):
                        ip_val = dev['data'].get('IP') or ''
                    phys_ips[dev_id] = ip_val

                    name_val = ''
                    if isinstance(dev.get('data'), dict):
                        name_val = dev['data'].get('NAME') or ''
                        if name_val in ('undefined', ''):
                            name_val = ''
                    phys_names[dev_id] = name_val

                    conn_name = ''
                    if isinstance(dev.get('connection'), dict):
                        conn_name = dev['connection'].get('name') or ''
                    phys_connections[dev_id] = conn_name

                    model_col = ''
                    if isinstance(dev.get('model'), dict):
                        model_name = dev['model'].get('name', '')
                        manufacturer = dev['model'].get('manufacturer', {}).get('name', '')
                        model_col = f'{manufacturer} {model_name}'.strip()
                    elif dev.get('manufacturer'):
                        model_col = f'{dev.get("manufacturer", "")} {dev.get("model", "")}'.strip()
                    phys_models[dev_id] = model_col
        except Exception:
            pass

        devices_dict = {}
        for item in results:
            dev_info = item.get('device') or {}
            dev_id = dev_info.get('id')
            if not dev_id:
                continue

            model_col = phys_models.get(dev_id) or ''
            custom_name = phys_names.get(dev_id) or ''
            if not custom_name and not model_col:
                str_val = item.get('__str__') or ''
                parts = str_val.split('__')
                if len(parts) == 3:
                    custom_name = parts[0]
                elif len(parts) >= 4:
                    model_col = f'{parts[0]} {parts[1]}'.strip()

            if dev_id not in devices_dict:
                devices_dict[dev_id] = {
                    'id': dev_id,
                    'name': dev_info.get('name') or _('Unknown'),
                    'model_col': model_col,
                    'custom_name': custom_name,
                    'location': phys_locations.get(dev_id) or '',
                    'connection_name': phys_connections.get(dev_id) or '',
                    'ip': phys_ips.get(dev_id) or '',
                    'logical_devices': [],
                }

            logical_name = (
                item.get('alternative_capability_name') or item.get('capability', {}).get('name') or _('Unknown')
            )
            devices_dict[dev_id]['logical_devices'].append(
                {
                    'id': item.get('id', ''),
                    'name': logical_name,
                    'is_default': False,
                }
            )

        self._print_device_cards(devices_dict)

    def _print_device_cards(self, devices_dict):
        if not devices_dict:
            self.console.print(_('No results found.'))
            return

        cards = []
        for _key, dev_data in sorted(devices_dict.items()):
            logical_lines = []
            for log_dev in sorted(dev_data['logical_devices'], key=lambda x: x['name']):
                bullet = '[green]✔ DEFAULT[/green]' if log_dev.get('is_default') else '[cyan]•[/cyan]'
                logical_lines.append(f'  {bullet} [dim]({log_dev["id"]})[/dim] [magenta]{log_dev["name"]}[/magenta]')

            logical_content = '\n'.join(logical_lines)

            # Header is device id (or name if no id)
            title_name = str(dev_data.get('id') or '')
            if title_name:
                title = f'[bold cyan]Device ID: {title_name}[/bold cyan]'
            else:
                title = f'[bold cyan]{dev_data.get("name")}[/bold cyan]'

            # name (model.manufacturer.name model.name)
            phys_name = dev_data.get('name') or _('Unknown')
            model_col = dev_data.get('model_col') or ''
            name_model_line = f'{phys_name} ({model_col})' if model_col else phys_name

            # NAME (si existe) o model.manufacturer.name model.name
            custom_name = dev_data.get('custom_name')
            main_bold_val = custom_name or model_col or dev_data.get('name') or _('Unknown')
            main_bold_str = f'\n[bold green]{main_bold_val}[/bold green]'

            # LOCATION (si existe)
            loc = dev_data.get('location')
            loc_str = f'\n[dim]📍 {loc}[/dim]' if loc else ''

            # connection.name (IP si corresponde)
            conn_name = dev_data.get('connection_name')
            ip = dev_data.get('ip')
            conn_str = ''
            if conn_name and ip:
                conn_str = f'{conn_name} ({ip})'
            elif conn_name:
                conn_str = conn_name
            elif ip:
                conn_str = ip
            conn_line = f'\n[dim]🔌 {conn_str}[/dim]' if conn_str else ''

            if logical_content:
                card_content = f'{name_model_line}{main_bold_str}{loc_str}{conn_line}\n\n{logical_content}'
            else:
                card_content = f'{name_model_line}{main_bold_str}{loc_str}{conn_line}'

            cards.append(
                Panel(
                    card_content,
                    title=title,
                    title_align='left',
                    border_style='green' if any(x.get('is_default') for x in dev_data['logical_devices']) else 'blue',
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
            ip = ''
            custom_name = ''
            conn_data = inner_item.get('connection') or {}
            if isinstance(conn_data, dict):
                location = conn_data.get('LOCATION') or ''
                ip = conn_data.get('IP') or ''
                custom_name = conn_data.get('NAME') or ''
                if custom_name in ('undefined', ''):
                    custom_name = ''

            conn_name = inner_keys[0]
            model_col = f'{inner_item.get("manufacturer", "")} {inner_item.get("model", "")}'.strip()

            if phys_name not in devices_dict:
                devices_dict[phys_name] = {
                    'id': inner_item.get('id'),
                    'name': phys_name,
                    'model_col': model_col,
                    'custom_name': custom_name,
                    'location': location,
                    'connection_name': conn_name,
                    'ip': ip,
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

        self._print_device_cards(devices_dict)
