# -*- coding: UTF-8 -*-

# Copyright (c) 2021 Jose Antonio Chavarría <jachavar@gmail.com>
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
from ..utils import execute, write_file, read_file

import gettext
_ = gettext.gettext

__author__ = 'Jose Antonio Chavarría'
__license__ = 'GPLv3'


@Pms.register('Pacman')
class Pacman(Pms):
    """
    PMS for pacman based systems (Arch, Manjaro, KaOS, ...)
    """

    def __init__(self):
        super().__init__()

        self._name = 'pacman'  # Package Management System name
        self._pms = 'LC_ALL=C /usr/bin/pacman'  # Package Management System command
        self._repo = '/etc/pacman.d/migasfree.list'  # Repositories file
        self._config = '/etc/pacman.conf'
        self._mimetype = [
            'application/x-alpm-package',
            'application/x-zstd-compressed-alpm-package',
            'application/x-gtar',
        ]

        self._pms_cache = '/usr/bin/paccache'
        self._pms_key = '/usr/bin/pacman-key'

    def install(self, package):
        """
        bool install(string package)
        """

        self._cmd = '{} --upgrade {}'.format(
            self._pms,
            package.strip()
        )
        logging.debug(self._cmd)

        return execute(self._cmd)[0] == 0

    def remove(self, package):
        """
        bool remove(string package)
        """

        self._cmd = '{} --remove --recursive {}'.format(
            self._pms,
            package.strip()
        )
        logging.debug(self._cmd)

        return execute(self._cmd)[0] == 0

    def search(self, pattern):
        """
        bool search(string pattern)
        """

        self._cmd = '{} --sync --search {}'.format(
            self._pms,
            pattern.strip()
        )
        logging.debug(self._cmd)

        return execute(self._cmd)[0] == 0

    def update_silent(self):
        """
        (bool, string) update_silent(void)
        """

        self._cmd = '{} --sync --refresh -uu --noconfirm'.format(self._pms)
        logging.debug(self._cmd)
        _ret, _, _error = execute(
            self._cmd,
            interactive=False,
            verbose=True
        )

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

        self._cmd = '{} --upgrade --noconfirm {}'.format(
            self._pms,
            ' '.join(package_set)
        )
        logging.debug(self._cmd)
        _ret, _, _error = execute(
            self._cmd,
            interactive=False,
            verbose=True
        )

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

        self._cmd = '{} --remove --recursive --noconfirm {}'.format(
            self._pms,
            ' '.join(package_set)
        )
        logging.debug(self._cmd)
        _ret, _, _error = execute(
            self._cmd,
            interactive=False,
            verbose=True
        )

        return _ret == 0, _error

    def is_installed(self, package):
        """
        bool is_installed(string package)
        """

        self._cmd = '{} --query {}'.format(
            self._pms,
            package.strip()
        )
        logging.debug(self._cmd)

        return execute(self._cmd, interactive=False)[0] == 0

    def clean_all(self):
        """
        bool clean_all(void)
        """

        self._cmd = '{} --remove'.format(self._pms_cache)
        logging.debug(self._cmd)

        return execute(self._cmd)[0] == 0

    def query_all(self):
        """
        ordered list query_all(void)
        list format: name_version_architecture.extension
        """

        _, _packages, _ = execute(
            '{} --query --info'.format(self._pms),
            interactive=False
        )
        if not _packages:
            return []

        _packages = _packages.strip().split('\n\n')
        _result = list()
        for _info in _packages:
            _pkg_info = {}
            _info = _info.splitlines()
            for _item in _info:
                if _item.startswith(('Name', 'Version', 'Architecture')):
                    key, value = _item.strip().split(':', 1)
                    _pkg_info[key.strip()] = value.strip()

            _result.append('{}_{}_{}.pkg.tar.zst'.format(  # FIXME extension
                _pkg_info['Name'],
                _pkg_info['Version'],
                _pkg_info['Architecture']
            ))

        return _result

    def _include_config(self):
        # add Include = /etc/pacman.d/migasfree.list in /etc/pacman.conf
        # if not included yet before NOTE pacman-key
        line = 'Include = {}'.format(self._repo)
        config = read_file(self._config).decode()
        if line in config:
            return  # nothing to do

        config = config.splitlines()
        substring = 'NOTE: You must run `pacman-key --init` before first using pacman'
        index = [i for i, s in enumerate(config) if substring in s]
        if index[0]:
            config.insert(index[0], line)
            write_file(self._config, '\n'.join(config))
        else:
            print(_('Add manually "%s" to file %s inside "options" section as last option') % (line, self._config))

    def create_repos(self, protocol, server, repositories):
        """
        bool create_repos(string protocol, string server, list repositories)
        """

        self._include_config()

        content = ''
        for repo in repositories:
            content += repo.get('source_template').format(protocol=protocol, server=server)

        return write_file(self._repo, content)

    def import_server_key(self, file_key):
        """
        bool import_server_key(string file_key)
        TODO test
        """

        self._cmd = '{} --populate {} > /dev/null'.format(
            self._pms_key,
            file_key
        )
        logging.debug(self._cmd)

        return execute(self._cmd)[0] == 0

    def get_system_architecture(self):
        """
        string get_system_architecture(void)
        """

        self._cmd = 'uname -m'
        logging.debug(self._cmd)

        _ret, _arch, _ = execute(self._cmd, interactive=False)

        return _arch.strip() if _ret == 0 else ''

    def available_packages(self):
        """
        list available_packages(void)
        """

        self._cmd = '{} --sync --search --quiet'.format(self._pms)
        logging.debug(self._cmd)
        _ret, _output, _error = execute(self._cmd, interactive=False)
        if _ret == 0:
            return sorted(_output.strip().splitlines())

        return []
