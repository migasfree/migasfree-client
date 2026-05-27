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
import sys

from rich.table import Table

from ..command import MigasFreeCommand, set_debug_log_level
from ..utils import ALL_OK

__author__ = 'Jose Antonio Chavarría <jachavar@gmail.com>'
__license__ = 'GPLv3'
__all__ = ['MigasFreePackages']

_ = gettext.gettext


class MigasFreePackages(MigasFreeCommand):
    def __init__(self):
        super().__init__()
        self.pms_selection()

    def run(self, args=None):
        if hasattr(args, 'debug') and args.debug:
            self._debug = True
            set_debug_log_level()

        if hasattr(args, 'quiet') and args.quiet:
            self._quiet = True

        if not self.pms:
            msg = _('No Package Management System (PMS) found on this system.')
            if self._quiet:
                print(json.dumps({'error': msg}))
            else:
                self.console.print(msg, style='red')
            sys.exit(ALL_OK)

        if args.available:
            self._handle_available()
        elif args.installed:
            self._handle_installed()
        elif args.check:
            self._handle_check(args.check[0])

        sys.exit(ALL_OK)

    def _handle_available(self):
        packages = self.pms.available_packages()
        if self._quiet:
            print(json.dumps(packages))
        else:
            self.console.print()
            self.console.print(
                '┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n'
                '┃' + _('AVAILABLE PACKAGES IN REPOSITORIES').center(64) + '┃\n'
                '┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛',
                style='bold green',
            )
            for pkg in packages:
                self.console.print(f'  • {pkg}')
            self.console.print(_('Total Available Packages: {0}').format(len(packages)), style='bold')
            self.console.print()

    def _handle_installed(self):
        packages = self.pms.query_all()
        if self._quiet:
            print(json.dumps(packages))
        else:
            self.console.print()
            table = Table(show_header=True, header_style='bold magenta')
            table.add_column(_('Package Name'), style='bold')
            table.add_column(_('Version'))
            table.add_column(_('Architecture'))

            for pkg in packages:
                # Format: name_version_architecture.ext
                parts = pkg.rsplit('.', 1)[0].split('_')
                name = parts[0]
                version = parts[1] if len(parts) > 1 else ''
                arch = parts[2] if len(parts) > 2 else ''
                table.add_row(name, version, arch)

            self.console.print(table)
            self.console.print(_('Total Installed Packages: {0}').format(len(packages)), style='bold')
            self.console.print()

    def _handle_check(self, json_array_str):
        try:
            packages_to_check = json.loads(json_array_str)
        except Exception:
            msg = _('Invalid JSON array provided for packages check.')
            if self._quiet:
                print(json.dumps({'error': msg}))
            else:
                self.console.print(msg, style='red')
            sys.exit(ALL_OK)

        installed_packages = []
        for pkg in packages_to_check:
            if self.pms.is_installed(pkg):
                installed_packages.append(pkg)

        if self._quiet:
            print(json.dumps(installed_packages))
        else:
            self.console.print()
            self.console.print(_('Checking package installation status:'), style='bold')
            for pkg in packages_to_check:
                if pkg in installed_packages:
                    self.console.print(f'[✓] {pkg:<30} - [green]' + _('Installed') + '[/green]')
                else:
                    self.console.print(f'[✗] {pkg:<30} - [red]' + _('Not Installed') + '[/red]')
            self.console.print()
