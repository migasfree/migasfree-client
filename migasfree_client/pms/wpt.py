# -*- coding: UTF-8 -*-

# Copyright (c) 2024-2025 Jose Antonio Chavarría <jachavar@gmail.com>
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

import os
import gettext
import logging

from .pms import Pms
from ..utils import execute, write_file

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
        self._repo = os.path.join(os.getenv('PROGRAMDATA'), self._name, 'sources.list')  # Repositories file
        self._mimetype = [
            'application/gzip',
            'application/x-gzip',
        ]

    def install(self, package):
        """
        bool install(string package)
        """

        cmd = f'{self._pms} install {package.strip()}'
        logger.debug(cmd)

        return execute(cmd)[0] == 0

    def remove(self, package):
        """
        bool remove(string package)
        """

        cmd = f'{self._pms} remove {package.strip()}'
        logger.debug(cmd)

        return execute(cmd)[0] == 0

    def search(self, pattern):
        """
        bool search(string pattern)
        """

        cmd = f'{self._pms} search "{pattern.strip()}"'
        logger.debug(cmd)

        return execute(cmd)[0] == 0

    def update_silent(self):
        """
        (bool, string) update_silent(void)
        """

        cmd = f'{self._pms} upgrade'
        logger.debug(cmd)

        _ret, _, _error = execute(cmd, interactive=False, verbose=True)

        return _ret == 0, _error

    def install_silent(self, package_set):
        """
        (bool, string) install_silent(list package_set)
        """

        if not isinstance(package_set, list):
            return False, f'package_set is not a list: {package_set}'

        package_set = [pkg for pkg in package_set if not self.is_installed(pkg)]
        if not package_set:
            return True, None

        cmd = f'{self._pms} --assume-yes install {" ".join(package_set)}'
        logger.debug(cmd)

        _ret, _, _error = execute(cmd, interactive=False, verbose=True)

        return _ret == 0, _error

    def remove_silent(self, package_set):
        """
        (bool, string) remove_silent(list package_set)
        """

        if not isinstance(package_set, list):
            return False, f'package_set is not a list: {package_set}'

        package_set = [pkg for pkg in package_set if self.is_installed(pkg)]
        if not package_set:
            return True, None

        cmd = f'{self._pms} --assume-yes remove {" ".join(package_set)}'
        logger.debug(cmd)

        _ret, _, _error = execute(cmd, interactive=False, verbose=True)

        return _ret == 0, _error

    def is_installed(self, package):
        """
        bool is_installed(string package)
        """

        cmd = f'{self._pms} status --is-installed {package.strip()}'
        logger.debug(cmd)

        return execute(cmd, interactive=False)[0] == 0

    def clean_all(self):
        """
        bool clean_all(void)
        """

        cmd = f'{self._pms} clean'
        logger.debug(cmd)

        return execute(cmd)[0] == 0

    def query_all(self):
        """
        ordered list query_all(void)
        list format: name_version_architecture.extension
        """

        cmd = f'{self._pms} --quiet list --all --summary'
        logger.debug(cmd)

        _, packages, _ = execute(cmd, interactive=False)
        if not packages:
            return []

        return [f'{item.strip()}.tar.gz' for item in packages]

    def create_repos(self, protocol, server, repositories):
        """
        bool create_repos(string protocol, string server, list repositories)
        """

        content = ''.join(
            f'{repo.get("source_template").format(protocol=protocol, server=server)}' for repo in repositories
        )

        return write_file(self._repo, content)

    def import_server_key(self, file_key):
        """
        bool import_server_key(string file_key)
        """

        return True  # TODO

    def get_system_architecture(self):
        """
        string get_system_architecture(void)
        """

        return 'x64'

    def available_packages(self):
        """
        list available_packages(void)
        """

        cmd = f'{self._pms} --quiet search --summary'
        logger.debug(cmd)

        _ret, _output, _error = execute(cmd, interactive=False)

        return sorted(_output.strip().splitlines()) if _ret == 0 else []
