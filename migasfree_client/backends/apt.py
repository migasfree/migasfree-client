#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Copyright (c) 2011-2013 Jose Antonio Chavarría
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
#
# Author: Jose Antonio Chavarría <jachavar@gmail.com>

__author__ = 'Jose Antonio Chavarría'
__file__ = 'apt.py'
__date__ = '2013-01-26'

import re
import logging

from .pms import Pms
from migasfree_client.utils import execute


@Pms.register('Apt')
class Apt(Pms):
    '''
    PMS for apt based systems (Debian, Ubuntu, Mint, ...)
    '''

    def __init__(self):
        Pms.__init__(self)

        self._name = 'apt-get'      # Package Management System name
        self._pm = '/usr/bin/dpkg'  # Package Manager command
        self._pms = 'DEBIAN_FRONTEND=noninteractive /usr/bin/apt-get'  # Package Management System command
        self._repo = '/etc/apt/sources.list.d/migasfree.list'  # Repositories file

        self._pms_search = '/usr/bin/apt-cache'
        self._pms_query = '/usr/bin/dpkg-query'

    def install(self, package):
        '''
        bool install(string package)
        '''

        self._cmd = '%s install %s' % (self._pms, package.strip())
        logging.debug(self._cmd)

        return (execute(self._cmd)[0] == 0)

    def remove(self, package):
        '''
        bool remove(string package)
        '''

        self._cmd = '%s remove %s' % (self._pms, package.strip())
        logging.debug(self._cmd)

        return (execute(self._cmd)[0] == 0)

    def search(self, pattern):
        '''
        bool search(string pattern)
        '''

        self._cmd = '%s search %s' % (self._pms_search, pattern.strip())
        logging.debug(self._cmd)

        return (execute(self._cmd)[0] == 0)

    def update_silent(self):
        '''
        (bool, string) update_silent(void)
        '''

        self._cmd = '%s --assume-yes --force-yes --allow-unauthenticated dist-upgrade' % self._pms
        logging.debug(self._cmd)
        _ret, _output, _error = execute(
            self._cmd,
            interactive=False,
            verbose=True
        )

        return (_ret == 0, _error)

    def install_silent(self, package_set):
        '''
        (bool, string) install_silent(list package_set)
        '''

        if not type(package_set) is list:
            return (False, 'package_set is not a list: %s' % package_set)

        for pkg in package_set[:]:
            if self.is_installed(pkg):
                package_set.remove(pkg)

        if not package_set:
            return (True, None)

        self._cmd = '%s --assume-yes --force-yes --allow-unauthenticated install %s' % (
            self._pms,
            ' '.join(package_set)
        )
        logging.debug(self._cmd)
        _ret, _output, _error = execute(
            self._cmd,
            interactive=False,
            verbose=True
        )

        return (_ret == 0, _error)

    def remove_silent(self, package_set):
        '''
        (bool, string) remove_silent(list package_set)
        '''

        if not type(package_set) is list:
            return (False, 'package_set is not a list: %s' % package_set)

        for pkg in package_set[:]:
            if not self.is_installed(pkg):
                package_set.remove(pkg)

        if not package_set:
            return (True, None)

        self._cmd = '%s --assume-yes remove %s' \
            % (self._pms, ' '.join(package_set))
        logging.debug(self._cmd)
        _ret, _output, _error = execute(
            self._cmd,
            interactive=False,
            verbose=True
        )

        return (_ret == 0, _error)

    def is_installed(self, package):
        '''
        bool is_installed(string package)
        '''

        self._cmd = '%s --status %s | grep "Status: install ok installed"' % (
            self._pm,
            package.strip()
        )
        logging.debug(self._cmd)

        return (execute(self._cmd, interactive=False)[0] == 0)

    def clean_all(self):
        '''
        bool clean_all(void)
        '''

        self._cmd = '%s clean' % self._pms
        logging.debug(self._cmd)
        if execute(self._cmd)[0] == 0:
            self._cmd = '%s --assume-yes update' % self._pms
            logging.debug(self._cmd)
            return (execute(self._cmd)[0] == 0)

        return False

    def query_all(self):
        '''
        ordered list query_all(void)
        '''

        _ret, _packages, _error = execute(
            '%s --list' % self._pm,
            interactive=False
        )
        if not _packages:
            return []

        _packages = _packages.splitlines()
        _result = list()
        for _line in _packages:
            if _line.startswith('ii'):
                _tmp = re.split(' +', _line)
                _result.append('%s-%s' % (_tmp[1], _tmp[2]))

        return _result

    def create_repos(self, server, version, repositories):
        '''
        bool create_repos(string server, string version, list repositories)
        '''

        _template = \
"""deb http://%(server)s/repo/%(version)s/REPOSITORIES %(repo)s PKGS
""" % {'server': server, 'version': version, 'repo': '%(repo)s'}

        _file = None
        try:
            _file = open(self._repo, 'wb')
            for _repo in repositories:
                _file.write(_template % {'repo': _repo['name']})

            return True
        except IOError:
            return False
        finally:
            if _file is not None:
                _file.close()
