# -*- coding: UTF-8 -*-

# Copyright (c) 2011-2025 Jose Antonio Chavarría <jachavar@gmail.com>
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
from .yum import Yum
from ..utils import execute

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

    def install(self, package):
        """
        bool install(string package)
        """

        cmd = f'{self._pms} install --no-force-resolution {package.strip()}'
        logger.debug(cmd)

        return execute(cmd)[0] == 0

    def update_silent(self):
        """
        (bool, string) update_silent(void)
        """

        cmd = f'{self._pms} --non-interactive update --no-force-resolution'
        logger.debug(cmd)

        _ret, _output, _error = execute(cmd, interactive=False, verbose=True)
        if _ret != 0:
            return False, f'{_ret}\n{_output}\n{_error}'

        cmd = f'{self._pms} lu -a'
        logger.debug(cmd)

        _ret, _output, _error = execute(cmd, interactive=False, verbose=True)

        return _ret == 0, f'{_ret}\n{_output}\n{_error}'

    def install_silent(self, package_set):
        """
        (bool, string) install_silent(list package_set)
        """

        if not isinstance(package_set, list):
            return False, f'package_set is not a list: {package_set}'

        package_set = [pkg for pkg in package_set if not self.is_installed(pkg)]
        if not package_set:
            return True, None

        cmd = f'{self._pms} --non-interactive install --no-force-resolution {" ".join(package_set)}'
        logger.debug(cmd)

        _ret, _output, _error = execute(cmd, interactive=False, verbose=True)

        return _ret == 0, f'{_ret}\n{_output}\n{_error}'

    def remove_silent(self, package_set):
        """
        (bool, string) remove_silent(list package_set)
        """

        if not isinstance(package_set, list):
            return False, f'package_set is not a list: {package_set}'

        package_set = [pkg for pkg in package_set if self.is_installed(pkg)]
        if not package_set:
            return True, None

        cmd = f'{self._pms} --non-interactive remove {" ".join(package_set)}'
        logger.debug(cmd)

        _ret, _output, _error = execute(cmd, interactive=False, verbose=True)

        return _ret == 0, f'{_ret}\n{_output}\n{_error}'

    def clean_all(self):
        """
        bool clean_all(void)
        """

        cmd = f'{self._pms} clean --all'
        logger.debug(cmd)

        if execute(cmd)[0] == 0:
            cmd = f'{self._pms} --non-interactive refresh'
            logger.debug(cmd)

            return execute(cmd)[0] == 0

        return False

    def get_system_architecture(self):
        """
        string get_system_architecture(void)
        """

        cmd = f'{self._pm} -q --qf "%{{arch}}" -f /etc/lsb-release'
        logger.debug(cmd)

        _ret, _arch, _ = execute(cmd, interactive=False)

        return _arch.strip() if _ret == 0 else ''

    def available_packages(self):
        """
        list available_packages(void)
        """

        cmd = f"{self._pms} pa | awk -F'|' '{{print $3}}'"
        logger.debug(cmd)

        _ret, _output, _error = execute(cmd, interactive=False)

        return sorted(_output.strip().splitlines()) if _ret == 0 else []
