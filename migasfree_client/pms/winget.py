# -*- coding: UTF-8 -*-

# Copyright (c) 2021 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2021 Alberto Gacías <alberto@migasfree.org>
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

from ..utils import execute

from .pms import Pms

__author__ = ['Jose Antonio Chavarría', 'Alberto Gacías']
__license__ = 'GPLv3'


@Pms.register('Winget')
class Winget(Pms):
    """
    PMS for winget (Microsoft Windows)
    """

    def __init__(self):
        super().__init__()

        self._name = 'winget'  # Package Management System name
        self._pms = 'winget'  # Package Management System command
        self._mimetype = ['application/yaml']

    def install(self, package):
        """
        bool install(string package)
        """

        cmd = '{} install --scope=machine --silent {}'.format(self._pms, package.strip())
        logging.debug(cmd)

        return execute(cmd, interactive=True)[0] == 0

    def remove(self, package):
        """
        bool remove(string package)
        """

        cmd = '{} uninstall --silent {}'.format(self._pms, package.strip())
        logging.debug(cmd)

        return execute(cmd, interactive=True)[0] == 0

    def search(self, pattern):
        """
        bool search(string pattern)
        """

        cmd = '{} search {}'.format(self._pms, pattern.strip())
        logging.debug(cmd)

        return execute(cmd, interactive=True)[0] == 0

    def update_silent(self):
        """
        (bool, string) update_silent(void)
        """

        cmd = '{} upgrade --all --silent'.format(self._pms)
        logging.debug(cmd)

        _ret, _, _error = execute(cmd, verbose=True)

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

        for pkg in package_set[:]:
            cmd = '{} install --scope=machine --silent {}'.format(self._pms, pkg)
            logging.debug(cmd)

            _ret, _, _error = execute(cmd, verbose=True)

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

        for pkg in package_set[:]:
            cmd = '{} uninstall --silent {}'.format(self._pms, pkg)
            logging.debug(cmd)

            _ret, _, _error = execute(cmd, verbose=True)

        return _ret == 0, _error

    def is_installed(self, package):
        """
        bool is_installed(string package)
        """

        cmd = '{} list {}'.format(self._pms, package)
        logging.debug(cmd)

        return execute(cmd, interactive=True)[0] == 0

    def clean_all(self):
        """
        bool clean_all(void)
        """

        return True  # (Not implemented in winget)

    def query_all(self):
        """
        ordered list query_all(void)
        list format: name_version_architecture.extension
        """

        _, _packages, _ = execute(
            '{} list'.format(self._pms),
            interactive=False
        )

        _result = list()
        for _line in _packages.splitlines()[4:]:  # Remove header -> 2 lines
            _result.append(
                '{}_{}_{}.yaml'.format(
                    _line[49:100].strip().split('_')[0],
                    _line[100:].strip(),
                    'x64'
                )
            )

        return _result

    def create_repos(self, protocol, server, repositories):
        """
        bool create_repos(string protocol, string server, list repositories)
        """

        cmd = [
            '{} source reset --force'.format(self._pms),
            '{} source remove winget'.format(self._pms)
        ]

        for repo in repositories:
            cmd.append('{pms} source add -n {repo}'.format(
                pms=self._pms,
                repo=repo.get('source_template').format(protocol=protocol, server=server)
            ))

        _, _packages, _ = execute(' && '.join(cmd))

        return True  # FIXME

    def import_server_key(self, file_key):
        """
        bool import_server_key(string file_key)
        """

        return True  # (implemented in source.msix file)

    def get_system_architecture(self):
        """
        string get_system_architecture(void)
        """

        return 'x64'

    def available_packages(self):
        """
        list available_packages(void)
        """

        cmd = '{} search'.format(self._pms)
        logging.debug(cmd)

        _ret, _output, _error = execute(cmd)

        return sorted(_output.strip().splitlines()) if _ret == 0 else []
