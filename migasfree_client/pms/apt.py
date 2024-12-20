# -*- coding: UTF-8 -*-

# Copyright (c) 2011-2024 Jose Antonio Chavarría <jachavar@gmail.com>
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

import re
import logging

from .pms import Pms
from ..utils import execute, write_file
from ..settings import KEYS_PATH

__author__ = 'Jose Antonio Chavarría'
__license__ = 'GPLv3'

logger = logging.getLogger('migasfree_client')


@Pms.register('Apt')
class Apt(Pms):
    """
    PMS for apt based systems (Debian, Ubuntu, Mint, ...)
    """

    def __init__(self):
        super().__init__()

        self._name = 'apt'          # Package Management System name
        self._pm = '/usr/bin/dpkg'  # Package Manager command
        self._pms = 'DEBIAN_FRONTEND=noninteractive /usr/bin/apt-get'  # Package Management System command
        self._repo = '/etc/apt/sources.list.d/migasfree.list'  # Repositories file
        self._mimetype = [
            'application/x-debian-package',
            'application/vnd.debian.binary-package',
        ]

        self._pms_search = '/usr/bin/apt-cache'
        self._pms_query = '/usr/bin/dpkg-query'

        self._silent_options = '-o APT::Get::Purge=true ' \
                               '-o Dpkg::Options::=--force-confdef ' \
                               '-o Dpkg::Options::=--force-confold ' \
                               '-o Debug::pkgProblemResolver=1 ' \
                               '--assume-yes --force-yes ' \
                               '--allow-unauthenticated --auto-remove'

    def install(self, package):
        """
        bool install(string package)
        """

        cmd = f'{self._pms} install -o APT::Get::Purge=true {package.strip()}'
        logger.debug(cmd)

        return execute(cmd)[0] == 0

    def remove(self, package):
        """
        bool remove(string package)
        """

        cmd = f'{self._pms} purge {package.strip()}'
        logger.debug(cmd)

        return execute(cmd)[0] == 0

    def search(self, pattern):
        """
        bool search(string pattern)
        """

        cmd = f'{self._pms_search} search {pattern.strip()}'
        logger.debug(cmd)

        return execute(cmd)[0] == 0

    def update_silent(self):
        """
        (bool, string) update_silent(void)
        """

        cmd = f'{self._pms} {self._silent_options} dist-upgrade'
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

        cmd = f'{self._pms} {self._silent_options} install {" ".join(package_set)}'
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

        cmd = f'{self._pms} {self._silent_options} purge {" ".join(package_set)}'
        logger.debug(cmd)

        _ret, _, _error = execute(cmd, interactive=False, verbose=True)

        return _ret == 0, _error

    def is_installed(self, package):
        """
        bool is_installed(string package)
        """

        cmd = f'{self._pm} --status {package.strip()} | grep "Status: install ok installed"'
        logger.debug(cmd)

        return execute(cmd, interactive=False)[0] == 0

    def clean_all(self):
        """
        bool clean_all(void)
        """

        cmd = f'{self._pms} clean'
        logger.debug(cmd)

        if execute(cmd)[0] == 0:
            execute('rm --recursive --force /var/lib/apt/lists')
            cmd = f'{self._pms} -o Acquire::Languages=none --assume-yes update'
            logger.debug(cmd)

            return execute(cmd)[0] == 0

        return False

    def query_all(self):
        """
        ordered list query_all(void)
        list format: name_version_architecture.extension
        """

        cmd = f'{self._pm} --list'
        logger.debug(cmd)

        packages = execute(cmd, interactive=False)[1].strip().splitlines()
        if not packages:
            return []

        pattern = re.compile(r'^ii\s+(\S+)\s+(\S+)\s+(\S+)')
        result = [f'{match.group(1)}_{match.group(2)}_{match.group(3)}.deb' for match in (
            pattern.match(line) for line in packages
        ) if match]

        return result

    def create_repos(self, protocol, server, repositories):
        """
        bool create_repos(string protocol, string server, list repositories)
        """

        content = ''.join(
            f"{repo.get('source_template').format(protocol=protocol, server=server)}" for repo in repositories
        )

        return write_file(self._repo, content)

    def import_server_key(self, file_key):
        """
        bool import_server_key(string file_key)
        """

        name = file_key.rsplit('.', 1)[0].replace(KEYS_PATH, '').split('/')[1]
        cmd = f'gpg --output /etc/apt/trusted.gpg.d/{name}.gpg --dearmor --yes {file_key} > /dev/null'
        logger.debug(cmd)

        return execute(cmd)[0] == 0

    def get_system_architecture(self):
        """
        string get_system_architecture(void)
        """

        cmd = f'echo "$({self._pm} --print-architecture) $({self._pm} --print-foreign-architectures)"'
        logger.debug(cmd)

        _ret, _arch, _ = execute(cmd, interactive=False)

        return _arch.strip() if _ret == 0 else ''

    def available_packages(self):
        """
        list available_packages(void)
        """

        cmd = f'{self._pms_search} pkgnames'
        logger.debug(cmd)

        _ret, _output, _error = execute(cmd, interactive=False)

        return sorted(_output.strip().splitlines()) if _ret == 0 else []
