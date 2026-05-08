# Copyright (c) 2024-2026 Jose Antonio Chavarría <jachavar@gmail.com>
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
import os

from ..utils import ALL_OK, execute, write_file_if_changed
from .pms import Pms, invalidate_installed_cache

_ = gettext.gettext

__author__ = 'Jose Antonio Chavarría'
__license__ = 'GPLv3'

logger = logging.getLogger('migasfree_client')


@Pms.register('Wpt')
class Wpt(Pms):
    """
    PMS for Windows Package Tool (Microsoft Windows)
    """

    def __init__(self):
        super().__init__()

        self._name = 'wpt'  # Package Management System name
        self._pms = 'wpt'  # Package Management System command
        program_data = os.getenv('PROGRAMDATA', 'C:\\ProgramData')
        self._repo = os.path.join(program_data, self._name, 'sources.list')  # Repositories file
        self._mimetype = [
            'application/gzip',
            'application/x-gzip',
        ]

    @invalidate_installed_cache
    def install(self, package):
        """
        bool install(string package)
        """

        cmd = [self._pms, 'install', package.strip()]
        logger.debug(' '.join(cmd))

        return execute(cmd)[0] == ALL_OK

    @invalidate_installed_cache
    def remove(self, package):
        """
        bool remove(string package)
        """

        cmd = [self._pms, 'remove', package.strip()]
        logger.debug(' '.join(cmd))

        return execute(cmd)[0] == ALL_OK

    def search(self, pattern):
        """
        bool search(string pattern)
        """

        cmd = [self._pms, 'search', pattern.strip()]
        logger.debug(' '.join(cmd))

        return execute(cmd)[0] == ALL_OK

    @invalidate_installed_cache
    def update_silent(self):
        """
        (bool, string) update_silent(void)
        """

        cmd = [self._pms, 'upgrade']
        logger.debug(' '.join(cmd))

        _ret, _, _error = execute(cmd, interactive=False, verbose=True)

        return _ret == ALL_OK, _error

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

        cmd = [self._pms, '--assume-yes', action, *package_set]
        logger.debug(' '.join(cmd))

        _ret, _, _error = execute(cmd, interactive=False, verbose=True)

        return _ret == ALL_OK, _error

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

    def is_installed(self, package):
        """
        bool is_installed(string package)
        """

        return package.strip() in self._get_installed_packages()

    def _get_installed_packages(self):
        """
        set _get_installed_packages(void)
        """

        if self._installed_cache is None:
            self._installed_cache = {pkg.split('_')[0] for pkg in self.query_all()}

        return self._installed_cache

    @invalidate_installed_cache
    def clean_all(self):
        """
        bool clean_all(void)
        """

        cmd = [self._pms, 'clean']
        logger.debug(' '.join(cmd))

        return execute(cmd)[0] == ALL_OK

    def query_all(self):
        """
        ordered list query_all(void)
        list format: name_version_architecture.extension
        """

        cmd = [self._pms, '--quiet', 'list', '--all', '--summary']
        logger.debug(' '.join(cmd))

        _ret, packages, _ = execute(cmd, interactive=False)
        if _ret != ALL_OK or not packages:
            return []

        return [f'{item.strip()}.tar.gz' for item in packages.splitlines()]

    def create_repos(self, protocol, server, repositories):
        """
        bool create_repos(string protocol, string server, list repositories)
        """

        content = ''.join(
            f'{repo.get("source_template").format(protocol=protocol, server=server)}' for repo in repositories
        )
        if not content:
            return True

        return write_file_if_changed(self._repo, content)

    @invalidate_installed_cache
    def import_server_key(self, file_key):
        """
        bool import_server_key(string file_key)
        Imports the server's GPG public key for package verification.
        """

        cmd = [self._pms, 'import-key', file_key]
        logger.debug(' '.join(cmd))

        ret, output, error = execute(cmd, interactive=False)
        if ret != ALL_OK:
            err_msg = f'{output.strip()} {error.strip()}'.strip()
            logger.error('Failed to import server key: %s', err_msg or 'Unknown error')

        return ret == ALL_OK

    def get_system_architecture(self):
        """
        string get_system_architecture(void)
        """

        return 'x64'

    def available_packages(self):
        """
        list available_packages(void)
        """

        cmd = [self._pms, '--quiet', 'search', '--summary']
        logger.debug(' '.join(cmd))

        _ret, _output, _error = execute(cmd, interactive=False)

        return sorted(_output.strip().splitlines()) if _ret == ALL_OK else []
