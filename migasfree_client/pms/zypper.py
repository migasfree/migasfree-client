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

import logging

from .pms import Pms
from ..settings import KEYS_PATH
from ..utils import execute, write_file

__author__ = 'Jose Antonio Chavarría'
__license__ = 'GPLv3'


@Pms.register('Zypper')
class Zypper(Pms):
    """
    PMS for zypper based systems (openSUSE, SLED, SLES, ...)
    """

    def __init__(self):
        super().__init__()

        self._name = 'zypper'  # Package Management System name
        self._pm = '/bin/rpm'  # Package Manager command
        self._pms = '/usr/bin/zypper'  # Package Management System command
        self._repo = '/etc/zypp/repos.d/migasfree.repo'  # Repositories file
        self._mimetype = [
            'application/x-rpm',
            'application/x-redhat-package-manager'
        ]

    def install(self, package):
        """
        bool install(string package)
        """

        cmd = '{} install --no-force-resolution {}'.format(
            self._pms,
            package.strip()
        )
        logging.debug(cmd)

        return execute(cmd)[0] == 0

    def remove(self, package):
        """
        bool remove(string package)
        """

        cmd = '{} remove {}'.format(self._pms, package.strip())
        logging.debug(cmd)

        return execute(cmd)[0] == 0

    def search(self, pattern):
        """
        bool search(string pattern)
        """

        cmd = '{} search {}'.format(self._pms, pattern.strip())
        logging.debug(cmd)

        return execute(cmd)[0] == 0

    def update_silent(self):
        """
        (bool, string) update_silent(void)
        """

        cmd = '{} --non-interactive update --no-force-resolution'.format(self._pms)
        logging.debug(cmd)

        _ret, _output, _error = execute(cmd, interactive=False, verbose=True)
        if _ret != 0:
            return False, '{}\n{}\n{}'.format(_ret, _output, _error)

        cmd = '{} lu -a'.format(self._pms)
        logging.debug(cmd)

        _ret, _output, _error = execute(cmd, interactive=False, verbose=True)

        return _ret == 0, '{}\n{}\n{}'.format(_ret, _output, _error)

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

        cmd = '{} --non-interactive install --no-force-resolution {}'.format(
            self._pms,
            ' '.join(package_set)
        )
        logging.debug(cmd)

        _ret, _output, _error = execute(cmd, interactive=False, verbose=True)

        return _ret == 0, '{}\n{}\n{}'.format(_ret, _output, _error)

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

        cmd = '{} --non-interactive remove {}'.format(
            self._pms,
            ' '.join(package_set)
        )
        logging.debug(cmd)

        _ret, _output, _error = execute(cmd, interactive=False, verbose=True)

        return _ret == 0, '{}\n{}\n{}'.format(_ret, _output, _error)

    def is_installed(self, package):
        """
        bool is_installed(string package)
        """

        cmd = '{} -q {}'.format(self._pm, package.strip())
        logging.debug(cmd)

        return execute(cmd, interactive=False)[0] == 0

    def clean_all(self):
        """
        bool clean_all(void)
        """

        cmd = '{} clean --all'.format(self._pms)
        logging.debug(cmd)
        if execute(cmd)[0] == 0:
            cmd = '{} --non-interactive refresh'.format(self._pms)
            logging.debug(cmd)

            return execute(cmd)[0] == 0

        return False

    def query_all(self):
        """
        ordered list query_all(void)
        list format: name_version_architecture.extension
        """

        cmd = '%s --queryformat "%%{NAME}_%%{VERSION}-%%{RELEASE}_%%{ARCH}.rpm\n" -qa' % self._pm
        logging.debug(cmd)

        _ret, _output, _ = execute(cmd, interactive=False)

        return sorted(_output.strip().splitlines()) if _ret == 0 else []

    def create_repos(self, protocol, server, repositories):
        """
        bool create_repos(string protocol, string server, list repositories)
        """

        content = ''
        for repo in repositories:
            content += repo.get('source_template').format(
                protocol=protocol,
                server=server,
                keys_path=KEYS_PATH
            )

        return write_file(self._repo, content)

    def import_server_key(self, file_key):
        """
        bool import_server_key(string file_key)
        """

        cmd = '{} --import {} > /dev/null'.format(self._pm, file_key)
        logging.debug(cmd)

        return execute(cmd)[0] == 0

    def get_system_architecture(self):
        """
        string get_system_architecture(void)
        """

        cmd = '%s -q --qf "%%{arch}" -f /etc/lsb-release' % self._pm
        logging.debug(cmd)

        _ret, _arch, _ = execute(cmd, interactive=False)

        return _arch.strip() if _ret == 0 else ''

    def available_packages(self):
        """
        list available_packages(void)
        """

        cmd = "{} pa | awk -F'|' '{{print $3}}'".format(self._pms)
        logging.debug(cmd)

        _ret, _output, _error = execute(cmd, interactive=False)

        return sorted(_output.strip().splitlines()) if _ret == 0 else []
