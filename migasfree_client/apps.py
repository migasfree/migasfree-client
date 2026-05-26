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
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table

from .command import MigasFreeCommand, require_computer_id, require_sign_keys
from .utils import ALL_OK

__author__ = 'Jose Antonio Chavarría <jachavar@gmail.com>'
__license__ = 'GPLv3'
__all__ = ['MigasFreeApps', 'MigasFreeCategories']

_ = gettext.gettext
logger = logging.getLogger('migasfree_client')


class MigasFreeCategories(MigasFreeCommand):
    @require_sign_keys
    def get_categories(self):
        logger.debug('Getting categories')
        response = self._api_call('get_categories', exit_on_error=True)
        return self._handle_response(response, success_msg=False)

    def run(self, args=None):
        super().run(args)

        categories = self.get_categories()

        if getattr(args, 'json', False):
            self.console.print(json.dumps(categories, ensure_ascii=False), soft_wrap=True)
        elif not categories:
            self.console.print(_('No results found.'))
        else:
            table = Table(box=box.SIMPLE, show_edge=False, title=_('Categories'))
            table.add_column('ID', style='cyan', justify='right')
            table.add_column(_('Name'), style='green')

            for cat in categories:
                table.add_row(str(cat.get('id', '')), cat.get('name', ''))

            self.console.print()
            self.console.print(table)

        sys.exit(ALL_OK)


class MigasFreeApps(MigasFreeCommand):
    @require_sign_keys
    @require_computer_id
    def get_available_apps(self, category_id=None):
        logger.debug('Getting available apps')
        data = {'cid': self._computer_id}
        if category_id:
            data['category'] = category_id

        response = self._api_call('get_available_apps', data=data)
        return self._handle_response(response, success_msg=False)

    def run(self, args=None):
        super().run(args)

        category_id = getattr(args, 'category', None)

        apps = self.get_available_apps(category_id=category_id)

        if getattr(args, 'json', False):
            self.console.print(json.dumps(apps, ensure_ascii=False), soft_wrap=True)
        elif not apps:
            self.console.print(_('No results found.'))
        else:
            cards = []
            for app in apps:
                app_id = str(app.get('id', ''))
                name = app.get('name', '')

                cat = app.get('category') or {}
                category_name = cat.get('name', '') if isinstance(cat, dict) else str(cat)

                lvl = app.get('level') or {}
                level_name = lvl.get('name', '') if isinstance(lvl, dict) else str(lvl)

                desc = app.get('description', '')
                score_val = app.get('score') or 1

                # Extract related packages for the current project only
                pkgs_list = []
                for pbp in app.get('packages_by_project', []):
                    proj_name = pbp.get('project', {}).get('name', '')
                    if proj_name and proj_name != self.migas_project:
                        continue
                    pkgs_to_install = pbp.get('packages_to_install', [])
                    if isinstance(pkgs_to_install, list):
                        pkgs_list.extend(pkgs_to_install)
                    elif isinstance(pkgs_to_install, str):
                        pkgs_list.append(pkgs_to_install)

                # Format card elements resembling the desktop play look
                category_name_escaped = escape(category_name)
                name_escaped = escape(name)
                level_name_escaped = escape(level_name)
                desc_escaped = escape(desc)

                category_str = f'[dim]{category_name_escaped}[/dim]\n' if category_name_escaped else ''
                name_str = f'[bold]{name_escaped}[/bold]'
                stars = '[yellow]★[/yellow]' * score_val + '[dim]☆[/dim]' * (5 - score_val)
                stars_str = f'\n{stars}  [dim]({level_name_escaped})[/dim]' if level_name_escaped else f'\n{stars}'
                desc_str = f'\n\n{desc_escaped}' if desc_escaped else ''

                pkgs_str = ''
                if pkgs_list:
                    pkgs_escaped = [escape(pkg) for pkg in sorted(pkgs_list)]
                    pkgs_formatted = ', '.join(f'[cyan]{pkg}[/cyan]' for pkg in pkgs_escaped)
                    pkgs_str = f'\n\n[dim]📦 {pkgs_formatted}[/dim]'

                card_content = f'{category_str}{name_str}{stars_str}{desc_str}{pkgs_str}'

                cards.append(
                    Panel(
                        card_content,
                        title=f'[bold cyan]App ID: {app_id}[/bold cyan]',
                        title_align='left',
                        border_style='blue',
                        width=50,
                    )
                )

            self.console.print()
            self.console.print(Columns(cards, equal=True, expand=False))

        sys.exit(ALL_OK)
