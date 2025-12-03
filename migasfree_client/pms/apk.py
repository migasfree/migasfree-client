# Copyright (c) 2025 Jose Antonio Chavarría <jachavar@gmail.com>
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

from ..utils import execute
from .pms import Pms

_ = gettext.gettext

__author__ = 'Jose Antonio Chavarría'
__license__ = 'GPLv3'

logger = logging.getLogger('migasfree_client')


@Pms.register('Apk')
class Apk(Pms):
    """
    PMS for APK based systems (Alpine Linux)
    """

    def __init__(self):
        super().__init__()

        self._name = 'apk'
        self._pms = '/sbin/apk'
        self._repo = '/etc/apk/repositories'
        self._mimetype = ['application/vnd.alpine.apk']

    def install(self, package):
        """
        bool install(string package)
        """

        cmd = f'{self._pms} add {package.strip()}'
        logger.debug(cmd)

        return execute(cmd)[0] == 0

    def remove(self, package):
        """
        bool remove(string package)
        """

        cmd = f'{self._pms} del {package.strip()}'
        logger.debug(cmd)

        return execute(cmd)[0] == 0

    def search(self, pattern):
        """
        bool search(string pattern)
        """

        cmd = f'{self._pms} search {pattern.strip()}'
        logger.debug(cmd)

        return execute(cmd)[0] == 0

    def update_silent(self):
        """
        (bool, string) update_silent(void)
        """

        cmd = f'{self._pms} update'
        logger.debug(cmd)

        _ret, _, _error = execute(cmd, interactive=False, verbose=True)

        if _ret == 0:
            cmd = f'{self._pms} upgrade'
            logger.debug(cmd)
            _ret, _, _error_upgrade = execute(cmd, interactive=False, verbose=True)
            if _error_upgrade:
                _error = f'{_error}\n{_error_upgrade}' if _error else _error_upgrade

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

        cmd = f'{self._pms} add {" ".join(package_set)}'
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

        cmd = f'{self._pms} del {" ".join(package_set)}'
        logger.debug(cmd)

        _ret, _, _error = execute(cmd, interactive=False, verbose=True)

        return _ret == 0, _error

    def is_installed(self, package):
        """
        bool is_installed(string package)
        """

        cmd = f'{self._pms} info -e {package.strip()}'
        logger.debug(cmd)

        return execute(cmd, interactive=False)[0] == 0

    def clean_all(self):
        """
        bool clean_all(void)
        """

        cmd = f'{self._pms} cache clean'
        logger.debug(cmd)

        return execute(cmd)[0] == 0

    def query_all(self):
        """
        ordered list query_all(void)
        list format: name_version_architecture.extension
        """

        cmd = f'{self._pms} info -v'
        logger.debug(cmd)

        _, _packages, _ = execute(cmd, interactive=False)
        if not _packages:
            return []

        arch = self.get_system_architecture()

        _result = []
        for line in _packages.strip().splitlines():
            _result.append(f'{line}_{arch}.apk')

        return sorted(_result)

    def create_repos(self, protocol, server, repositories):
        """
        bool create_repos(string protocol, string server, list repositories)
        """

        current_content = ''
        if os.path.exists(self._repo):
            with open(self._repo, encoding='utf-8') as f:
                current_content = f.read()

        new_lines = []
        for repo in repositories:
            line = repo.get('source_template').format(protocol=protocol, server=server)
            if line.strip() not in current_content:
                new_lines.append(line)

        if new_lines:
            try:
                with open(self._repo, 'a', encoding='utf-8') as f:
                    f.write('\n' + '\n'.join(new_lines) + '\n')
            except OSError:
                return False

        return True

    def import_server_key(self, file_key):
        """
        bool import_server_key(string file_key)
        """

        cmd = f'cp {file_key} /etc/apk/keys/'
        logger.debug(cmd)

        return execute(cmd)[0] == 0

    def get_system_architecture(self):
        """
        string get_system_architecture(void)
        """

        cmd = f'{self._pms} --print-arch'
        logger.debug(cmd)

        _ret, _arch, _ = execute(cmd, interactive=False)

        return _arch.strip() if _ret == 0 else ''

    def available_packages(self):
        """
        list available_packages(void)
        """

        cmd = f'{self._pms} search -q'
        logger.debug(cmd)

        _ret, _output, _error = execute(cmd, interactive=False)

        return sorted(_output.strip().splitlines()) if _ret == 0 else []
