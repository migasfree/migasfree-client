# -*- coding: UTF-8 -*-

# Copyright (c) 2011-2017 Jose Antonio Chavarría <jachavar@gmail.com>
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
from migasfree_client.utils import execute

__author__ = 'Jose Antonio Chavarría'
__license__ = 'GPLv3'


@Pms.register('Apt')
class Apt(Pms):
    """
    PMS for apt based systems (Debian, Ubuntu, Mint, ...)
    """

    def __init__(self):
        Pms.__init__(self)

        self._name = 'apt-get'      # Package Management System name
        self._pm = '/usr/bin/dpkg'  # Package Manager command
        self._pms = 'DEBIAN_FRONTEND=noninteractive /usr/bin/apt-get'  # Package Management System command
        self._repo = '/etc/apt/sources.list.d/migasfree.list'  # Repositories file

        self._pms_search = '/usr/bin/apt-cache'
        self._pms_query = '/usr/bin/dpkg-query'

        self._silent_options = '-o APT::Get::Purge=true -o Dpkg::Options::=--force-confdef' \
            ' -o Dpkg::Options::=--force-confold -o Debug::pkgProblemResolver=1 ' \
            '--assume-yes --force-yes --allow-unauthenticated --auto-remove'

    def install(self, package):
        """
        bool install(string package)
        """

        self._cmd = '{0} install -o APT::Get::Purge=true {1}'.format(
            self._pms,
            package.strip()
        )
        logging.debug(self._cmd)

        return execute(self._cmd)[0] == 0

    def remove(self, package):
        """
        bool remove(string package)
        """

        self._cmd = '{0} purge {1}'.format(self._pms, package.strip())
        logging.debug(self._cmd)

        return execute(self._cmd)[0] == 0

    def search(self, pattern):
        """
        bool search(string pattern)
        """

        self._cmd = '{0} search {1}'.format(self._pms_search, pattern.strip())
        logging.debug(self._cmd)

        return execute(self._cmd)[0] == 0

    def update_silent(self):
        """
        (bool, string) update_silent(void)
        """

        self._cmd = '{0} {1} dist-upgrade'.format(
            self._pms,
            self._silent_options
        )
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

        self._cmd = '{0} {1} install {2}'.format(
            self._pms,
            self._silent_options,
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

        self._cmd = '{0} {1} purge {2}'.format(
            self._pms,
            self._silent_options,
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

        self._cmd = '{0} --status {1} | grep "Status: install ok installed"'.format(
            self._pm,
            package.strip()
        )
        logging.debug(self._cmd)

        return execute(self._cmd, interactive=False)[0] == 0

    def clean_all(self):
        """
        bool clean_all(void)
        """

        self._cmd = '{0} clean'.format(self._pms)
        logging.debug(self._cmd)
        if execute(self._cmd)[0] == 0:
            self._cmd = '{0} -o Acquire::Languages=none --assume-yes update'.format(self._pms)
            logging.debug(self._cmd)
            return execute(self._cmd)[0] == 0

        return False

    def query_all(self):
        """
        ordered list query_all(void)
        """

        _, _packages, _ = execute(
            '{0} --list'.format(self._pm),
            interactive=False
        )
        if not _packages:
            return []

        _packages = _packages.strip().splitlines()
        _result = list()
        for _line in _packages:
            if _line.startswith('ii'):
                _tmp = re.split(' +', _line)
                _result.append('{0}-{1}'.format(_tmp[1], _tmp[2]))

        return _result

    def create_repos(self, template, server, project, repositories):
        """
        bool create_repos(string template, string server, string project, list repositories)
        """

        repo_template = 'deb {0} {repo} PKGS\n'.format(
            template.format(server=server, project=project),
            repo='{repo}'
        )

        _file = None
        try:
            _file = open(self._repo, 'wb')
            for _repo in repositories:
                _file.write(repo_template.format(repo=_repo['name']))

            return True
        except IOError:
            return False
        finally:
            if _file is not None:
                _file.close()

    def import_server_key(self, file_key):
        """
        bool import_server_key(string file_key)
        """

        self._cmd = 'apt-key add {0} >/dev/null'.format(file_key)
        logging.debug(self._cmd)
        return execute(self._cmd)[0] == 0

    def available_packages(self):
        """
        list available_packages(void)
        """

        self._cmd = '{0} pkgnames'.format(self._pms_search)
        logging.debug(self._cmd)
        _ret, _output, _error = execute(self._cmd, interactive=False)
        if _ret == 0:
            return sorted(_output.strip().splitlines())

        return []
