#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Copyright (c) 2011-2012 Jose Antonio Chavarría
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
__file__   = 'zypper.py'
__date__   = '2012-06-06'

import logging

from pms import Pms
from migasfree_client.utils import execute

class Zypper(Pms):
    '''
    PMS for zypper based systems (openSUSE, SLED, SLES, ...)
    '''

    def __init__(self):
        Pms.__init__(self)

        self._name = 'zypper'          # Package Management System name
        self._pm   = '/bin/rpm'        # Package Manager command
        self._pms  = '/usr/bin/zypper' # Package Management System command
        self._repo = '/etc/zypp/repos.d/migasfree.repo' # Repositories file

    def install(self, package):
        '''
        bool install(string package)
        '''

        self._cmd = '%s install --no-force-resolution %s' % (self._pms, package.strip())
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
        _ret, _output, _error = execute(self._cmd, interactive = False)
        if _ret != 0:
            return (False, '%s\n%s' % (_output, _error))

        #self._cmd = '%s --quiet lu -a' % self._pms
        self._cmd = '%s lu -a' % self._pms
        logging.debug(self._cmd)
        _ret, _output, _error = execute(
            self._cmd,
            interactive = False,
            verbose = True
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

        self._cmd = '%s --non-interactive install --no-force-resolution %s' \
            % (self._pms, ' '.join(package_set))
        logging.debug(self._cmd)
        _ret, _output, _error = execute(
            self._cmd,
            interactive = False,
            verbose = True
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

        self._cmd = '%s --non-interactive remove %s' \
            % (self._pms, ' '.join(package_set))
        logging.debug(self._cmd)
        _ret, _output, _error = execute(
            self._cmd,
            interactive = False,
            verbose = True
        )

        return (_ret == 0, _error)

    def is_installed(self, package):
        '''
        bool is_installed(string package)
        '''

        self._cmd = '%s -q %s' % (self._pm, package.strip())
        logging.debug(self._cmd)

        return (execute(self._cmd, interactive = False)[0] == 0)

    def clean_all(self):
        '''
        bool clean_all(void)
        '''

        self._cmd = '%s clean --all' % self._pms
        logging.debug(self._cmd)
        if execute(self._cmd)[0] == 0:
            #self._cmd = '%s refresh --force-resolution' % self._pms
            self._cmd = '%s --non-interactive refresh' % self._pms
            logging.debug(self._cmd)
            return (execute(self._cmd)[0] == 0)

        return False

    def query_all(self):
        '''
        ordered list query_all(void)
        '''

        self._cmd = '%s -qa' % self._pm
        logging.debug(self._cmd)
        _ret, _output, _error = execute(self._cmd, interactive = False)
        if _ret != 0:
            return []

        return sorted(_output.split('\n'))

    def create_repos(self, server, version, repositories):
        '''
        bool create_repos(string server, string version, list repositories)
        '''

        _template = \
"""[%(repo)s]
name=%(repo)s
baseurl=http://%(server)s/repo/%(version)s/REPOSITORIES/%(repo)s
gpgcheck=0
enabled=1
http_caching=none
metadata_expire=1
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
