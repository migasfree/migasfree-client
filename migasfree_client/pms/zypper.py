# Copyright (c) 2011-2026 Jose Antonio Chavarría <jachavar@gmail.com>
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

import logging

from ..utils import ALL_OK, execute
from .pms import Pms, invalidate_installed_cache
from .yum import Yum

__author__ = 'Jose Antonio Chavarría'
__license__ = 'GPLv3'

logger = logging.getLogger('migasfree_client')


@Pms.register('Zypper')
class Zypper(Yum):
    """
    PMS for zypper based systems (openSUSE, SLED, SLES, ...)
    """

    def __init__(self):
        super().__init__()

        self._name = 'zypper'  # Package Management System name
        self._pms = '/usr/bin/zypper'  # Package Management System command
        self._repo = '/etc/zypp/repos.d/migasfree.repo'  # Repositories file

    @invalidate_installed_cache
    def install(self, package):
        """
        bool install(string package)
        """

        cmd = [self._pms, 'install', '--no-force-resolution', package.strip()]
        logger.debug(' '.join(cmd))

        return execute(cmd)[0] == ALL_OK
    @invalidate_installed_cache
    def update_silent(self):
        """
        (bool, string) update_silent(void)
        """

        cmd = [self._pms, '--non-interactive', 'update', '--no-force-resolution']
        logger.debug(' '.join(cmd))

        _ret, _output, _error = execute(cmd, interactive=False, verbose=True)
        if _ret != ALL_OK:
            return False, f'{_ret}\n{_output}\n{_error}'

        cmd = [self._pms, 'lu', '-a']
        logger.debug(' '.join(cmd))

        _ret, _output, _error = execute(cmd, interactive=False, verbose=True)

        return _ret == ALL_OK, f'{_ret}\n{_output}\n{_error}'

    @invalidate_installed_cache
    def _execute_silent(self, action, package_set):
        """
        (bool, string) _execute_silent(string action, list package_set)
        Common logic for install_silent and remove_silent
        """

        if not isinstance(package_set, list):
            return False, f'package_set is not a list: {package_set}'

        installed = self._get_installed_packages()

        if action == 'install':
            package_set = [pkg.strip() for pkg in package_set if pkg.strip() not in installed]
        elif action == 'remove':
            package_set = [pkg.strip() for pkg in package_set if pkg.strip() in installed]

        if not package_set:
            return True, None

        cmd = [self._pms, '--non-interactive', action]
        if action == 'install':
            cmd.append('--no-force-resolution')
        cmd.extend(package_set)

        logger.debug(' '.join(cmd))

        _ret, _output, _error = execute(cmd, interactive=False, verbose=True)

        return _ret == ALL_OK, f'{_ret}\n{_output}\n{_error}'

    def install_silent(self, package_set):
        """
        (bool, string) install_silent(list package_set)
        """

        return self._execute_silent('install', package_set)

    def remove_silent(self, package_set):
        """
        (bool, string) remove_silent(list package_set)
        """

        return self._execute_silent('remove', package_set)

    @invalidate_installed_cache
    def clean_all(self):
        """
        bool clean_all(void)
        """

        cmd = [self._pms, 'clean', '--all']
        logger.debug(' '.join(cmd))

        if execute(cmd)[0] == ALL_OK:
            cmd = [self._pms, '--non-interactive', 'refresh']
            logger.debug(' '.join(cmd))

            return execute(cmd)[0] == ALL_OK

        return False

    def get_system_architecture(self):
        """
        string get_system_architecture(void)
        """

        cmd = [self._pm, '-q', '--qf', '%{arch}', '-f', '/etc/lsb-release']
        logger.debug(' '.join(cmd))

        _ret, _arch, _ = execute(cmd, interactive=False)

        return _arch.strip() if _ret == ALL_OK else ''

    def available_packages(self):
        """
        list available_packages(void)
        """

        cmd = [self._pms, 'pa']
        logger.debug(' '.join(cmd))

        _ret, _output, _error = execute(cmd, interactive=False)
        if _ret != ALL_OK:
            return []

        # Parse output: " [i+] | repository | package_name | version | architecture"
        # We only need the package name
        result = []
        for line in _output.strip().splitlines():
            line = line.strip()
            # Skip headers or empty lines
            if not line or '|' not in line or line.startswith('S |'):
                continue

            parts = line.split('|')
            if len(parts) >= 3:
                # Column 2 is package name
                pkg_name = parts[2].strip()
                result.append(pkg_name)

        return sorted(set(result))
