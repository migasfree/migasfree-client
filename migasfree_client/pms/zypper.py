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

import logging

from .pms import Pms
from ..utils import execute, write_file


@Pms.register('Zypper')
class Zypper(Pms):
    '''
    PMS for zypper based systems (openSUSE, SLED, SLES, ...)
    '''

    def __init__(self):
        Pms.__init__(self)

        self._name = 'zypper'          # Package Management System name
        self._pm = '/bin/rpm'          # Package Manager command
        self._pms = '/usr/bin/zypper'  # Package Management System command
        self._repo = '/etc/zypp/repos.d/migasfree.repo'  # Repositories file
        self._mimetype = [
            'application/x-rpm',
            'application/x-redhat-package-manager'
        ]

    def install(self, package):
        '''
        bool install(string package)
        '''

        self._cmd = '%s install --no-force-resolution %s' % (
            self._pms,
            package.strip()
        )
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

        self._cmd = '%s search %s' % (self._pms, pattern.strip())
        logging.debug(self._cmd)

        return (execute(self._cmd)[0] == 0)

    def update_silent(self):
        '''
        (bool, string) update_silent(void)
        '''

        self._cmd = '%s --non-interactive update --no-force-resolution "*"' % self._pms
        logging.debug(self._cmd)
        _ret, _output, _error = execute(
            self._cmd,
            interactive=False,
            verbose=True
        )
        if _ret != 0:
            return (False, '%s\n%s\n%s' % (str(_ret), _output, _error))

        self._cmd = '%s lu -a' % self._pms
        logging.debug(self._cmd)
        _ret, _output, _error = execute(
            self._cmd,
            interactive=False,
            verbose=True
        )

        return (_ret == 0, '%s\n%s\n%s' % (str(_ret), _output, _error))

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

        self._cmd = '%s --non-interactive install --no-force-resolution %s' \
            % (self._pms, ' '.join(package_set))
        logging.debug(self._cmd)
        _ret, _output, _error = execute(
            self._cmd,
            interactive=False,
            verbose=True
        )

        return (_ret == 0, '%s\n%s\n%s' % (str(_ret), _output, _error))

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

        self._cmd = '%s --non-interactive remove %s' \
            % (self._pms, ' '.join(package_set))
        logging.debug(self._cmd)
        _ret, _output, _error = execute(
            self._cmd,
            interactive=False,
            verbose=True
        )

        return (_ret == 0, '%s\n%s\n%s' % (str(_ret), _output, _error))

    def is_installed(self, package):
        '''
        bool is_installed(string package)
        '''

        self._cmd = '%s -q %s' % (self._pm, package.strip())
        logging.debug(self._cmd)

        return (execute(self._cmd, interactive=False)[0] == 0)

    def clean_all(self):
        '''
        bool clean_all(void)
        '''

        self._cmd = '%s clean --all' % self._pms
        logging.debug(self._cmd)
        if execute(self._cmd)[0] == 0:
            self._cmd = '%s --non-interactive refresh' % self._pms
            logging.debug(self._cmd)
            return (execute(self._cmd)[0] == 0)

        return False

    def query_all(self):
        '''
        ordered list query_all(void)
        list format: name_version_architecture.extension
        '''

        self._cmd = '%s --queryformat "%%{NAME}_%%{VERSION}-%%{RELEASE}_%%{ARCH}.rpm\n" -qa' % self._pm
        logging.debug(self._cmd)
        _ret, _output, _error = execute(self._cmd, interactive=False)
        if _ret != 0:
            return []

        return sorted(_output.split('\n'))

    def create_repos(self, server, project, repositories):
        '''
        bool create_repos(string server, string project, list repositories)
        '''

        template = \
"""[%(repo)s]
name=%(repo)s
baseurl=http://%(server)s/pub/%(project)s/repos/%(repo)s
gpgcheck=0
enabled=1
http_caching=none
metadata_expire=1
""" % {'server': server, 'project': project, 'repo': '%(repo)s'}

        content = ''
        for repo in repositories:
            content += template % {'repo': repo}

        return write_file(self._repo, content)

    def import_server_key(self, file_key):
        '''
        bool import_server_key(string file_key)
        '''

        self._cmd = '%s --import %s > /dev/null' % (self._pm, file_key)
        logging.debug(self._cmd)

        return (execute(self._cmd)[0] == 0)

    def get_system_architecture(self):
        '''
        string get_system_architecture(void)
        '''

        self._cmd = '%s -q --qf "%{arch}" -f /etc/lsb-release' % self._pm
        logging.debug(self._cmd)

        _ret, _arch, _error = execute(self._cmd, interactive=False)

        return _arch.strip() if _ret == 0 else ''
