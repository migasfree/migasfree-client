# -*- coding: UTF-8 -*-

# Copyright (c) 2011-2021 Jose Antonio Chavarría <jachavar@gmail.com>
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

__author__ = 'Jose Antonio Chavarría'
__license__ = 'GPLv3'


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

        cmd = '{} install -o APT::Get::Purge=true {}'.format(
            self._pms,
            package.strip()
        )
        logging.debug(cmd)

        return execute(cmd)[0] == 0

    def remove(self, package):
        """
        bool remove(string package)
        """

        cmd = '{} purge {}'.format(self._pms, package.strip())
        logging.debug(cmd)

        return execute(cmd)[0] == 0

    def search(self, pattern):
        """
        bool search(string pattern)
        """

        cmd = '{} search {}'.format(self._pms_search, pattern.strip())
        logging.debug(cmd)

        return execute(cmd)[0] == 0

    def update_silent(self):
        """
        (bool, string) update_silent(void)
        """

        cmd = '{} {} dist-upgrade'.format(
            self._pms,
            self._silent_options
        )
        logging.debug(cmd)

        _ret, _, _error = execute(cmd, interactive=False, verbose=True)

        return _ret == 0, _error

    def install_silent(self, package_set):
        """
        (bool, string) install_silent(list package_set)
        """

        if not isinstance(package_set, list):
            return False, 'package_set is not a list: %s' % package_set

        for pkg in package_set[:]:
            if self.is_installed(pkg):
                package_set.remove(pkg)

        if not package_set:
            return True, None

        cmd = '{} {} install {}'.format(
            self._pms,
            self._silent_options,
            ' '.join(package_set)
        )
        logging.debug(cmd)

        _ret, _, _error = execute(cmd, interactive=False, verbose=True)

        return _ret == 0, _error

    def remove_silent(self, package_set):
        """
        (bool, string) remove_silent(list package_set)
        """

        if not isinstance(package_set, list):
            return False, 'package_set is not a list: %s' % package_set

        for pkg in package_set[:]:
            if not self.is_installed(pkg):
                package_set.remove(pkg)

        if not package_set:
            return True, None

        cmd = '{} {} purge {}'.format(
            self._pms,
            self._silent_options,
            ' '.join(package_set)
        )
        logging.debug(cmd)

        _ret, _, _error = execute(cmd, interactive=False, verbose=True)

        return _ret == 0, _error

    def is_installed(self, package):
        """
        bool is_installed(string package)
        """

        cmd = '{} --status {} | grep "Status: install ok installed"'.format(
            self._pm,
            package.strip()
        )
        logging.debug(cmd)

        return execute(cmd, interactive=False)[0] == 0

    def clean_all(self):
        """
        bool clean_all(void)
        """

        cmd = '{} clean'.format(self._pms)
        logging.debug(cmd)

        if execute(cmd)[0] == 0:
            execute('rm --recursive --force /var/lib/apt/lists')
            cmd = '{} -o Acquire::Languages=none --assume-yes update'.format(self._pms)
            logging.debug(cmd)

            return execute(cmd)[0] == 0

        return False

    def query_all(self):
        """
        ordered list query_all(void)
        list format: name_version_architecture.extension
        """

        _, _packages, _ = execute(
            '{} --list'.format(self._pm),
            interactive=False
        )
        if not _packages:
            return []

        _packages = _packages.strip().splitlines()
        _result = list()
        for _line in _packages:
            if _line.startswith('ii'):
                _tmp = re.split(' +', _line)
                _result.append('{}_{}_{}.deb'.format(_tmp[1], _tmp[2], _tmp[3]))

        return _result

    def create_repos(self, protocol, server, repositories):
        """
        bool create_repos(string protocol, string server, list repositories)
        """

        content = ''
        for repo in repositories:
            content += repo.get('source_template').format(protocol=protocol, server=server)

        return write_file(self._repo, content)

    def import_server_key(self, file_key):
        """
        bool import_server_key(string file_key)
        """

        cmd = 'APT_KEY_DONT_WARN_ON_DANGEROUS_USAGE=1 apt-key add {} > /dev/null'.format(file_key)
        logging.debug(cmd)

        return execute(cmd)[0] == 0

    def get_system_architecture(self):
        """
        string get_system_architecture(void)
        """

        cmd = 'echo "$(%(pm)s --print-architecture) $(%(pm)s --print-foreign-architectures)"' % {'pm': self._pm}
        logging.debug(cmd)

        _ret, _arch, _ = execute(cmd, interactive=False)

        return _arch.strip() if _ret == 0 else ''

    def available_packages(self):
        """
        list available_packages(void)
        """

        cmd = '{} pkgnames'.format(self._pms_search)
        logging.debug(cmd)

        _ret, _output, _error = execute(cmd, interactive=False)

        return sorted(_output.strip().splitlines()) if _ret == 0 else []
