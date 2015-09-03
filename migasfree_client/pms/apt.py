#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Copyright (c) 2011-2015 Jose Antonio Chavarría
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
__license__ = 'GPLv3'

import re
import logging

from .pms import Pms
from ..utils import execute, write_file


@Pms.register('Apt')
class Apt(Pms):
    '''
    PMS for apt based systems (Debian, Ubuntu, Mint, ...)
    '''

    def __init__(self):
        Pms.__init__(self)

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

        self._silent_options = '-o APT::Get::Purge=true -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confold -o Debug::pkgProblemResolver=1 --assume-yes --force-yes --allow-unauthenticated --auto-remove'

    def install(self, package):
        '''
        bool install(string package)
        '''

        self._cmd = '%s install -o APT::Get::Purge=true %s' % (
            self._pms,
            package.strip()
        )
        logging.debug(self._cmd)

        return (execute(self._cmd)[0] == 0)

    def remove(self, package):
        '''
        bool remove(string package)
        '''

        self._cmd = '%s purge %s' % (self._pms, package.strip())
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

        self._cmd = '%s %s dist-upgrade' % (
            self._pms,
            self._silent_options
        )
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

        self._cmd = '%s %s install %s' % (
            self._pms,
            self._silent_options,
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

        self._cmd = '%s %s purge %s' % (
            self._pms,
            self._silent_options,
            ' '.join(package_set)
        )
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
            self._cmd = '%s -o Acquire::Languages=none --assume-yes update' % self._pms
            logging.debug(self._cmd)
            return (execute(self._cmd)[0] == 0)

        return False

    def query_all(self):
        '''
        ordered list query_all(void)
        list format: name_version_architecture.extension
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
                _result.append('%s_%s_%s.deb' % (_tmp[1], _tmp[2], _tmp[3]))

        return _result

    def create_repos(self, server, project, repositories):
        '''
        bool create_repos(string server, string project, list repositories)
        '''

        template = \
"""deb http://%(server)s/pub/%(project)s/repos %(repo)s PKGS
""" % {'server': server, 'project': project, 'repo': '%(repo)s'}

        content = ''
        for repo in repositories:
            content += template % {'repo': repo}

        return write_file(self._repo, content)

    def import_server_key(self, file_key):
        '''
        bool import_server_key(string file_key)
        '''

        self._cmd = 'apt-key add %s > /dev/null' % file_key
        logging.debug(self._cmd)

        return (execute(self._cmd)[0] == 0)

    def get_system_architecture(self):
        '''
        string get_system_architecture(void)
        '''

        self._cmd = 'echo "$(%s --print-architecture) $(%s --print-foreign-architectures)"' % self._pm
        logging.debug(self._cmd)

        _ret, _arch, _error = execute(self._cmd, interactive=False)

        return _arch.strip() if _ret == 0 else ''
