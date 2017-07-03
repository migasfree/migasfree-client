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

import os
import logging

from .pms import Pms
from migasfree_client.utils import execute

__author__ = 'Jose Antonio Chavarría'
__license__ = 'GPLv3'


@Pms.register('Yum')
class Yum(Pms):
    """
    PMS for yum based systems (Fedora, Red Hat, CentOS, ...)
    """

    def __init__(self):
        Pms.__init__(self)

        self._name = 'yum'          # Package Management System name
        self._pm = '/bin/rpm'       # Package Manager command
        self._pms = '/usr/bin/yum'  # Package Management System command

        # Repositories file
        if os.path.isdir('/etc/yum.repos.d'):
            self._repo = '/etc/yum.repos.d/migasfree.repo'
        else:
            self._repo = '/etc/yum/repos.d/migasfree.repo'

    def install(self, package):
        """
        bool install(string package)
        """

        self._cmd = '{} install {}'.format(self._pms, package.strip())
        logging.debug(self._cmd)

        return execute(self._cmd)[0] == 0

    def remove(self, package):
        """
        bool remove(string package)
        """

        self._cmd = '{} remove {}'.format(self._pms, package.strip())
        logging.debug(self._cmd)

        return execute(self._cmd)[0] == 0

    def search(self, pattern):
        """
        bool search(string pattern)
        """

        self._cmd = '{} search {}'.format(self._pms, pattern.strip())
        logging.debug(self._cmd)

        return execute(self._cmd)[0] == 0

    def update_silent(self):
        """
        (bool, string) update_silent(void)
        """

        self._cmd = '{} --assumeyes update'.format(self._pms)
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

        self._cmd = '{} --assumeyes install {}'.format(
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

        self._cmd = '{} --assumeyes remove {}'.format(
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

        self._cmd = '{} -q {}'.format(self._pm, package.strip())
        logging.debug(self._cmd)

        return execute(self._cmd, interactive=False)[0] == 0

    def clean_all(self):
        """
        bool clean_all(void)
        """

        self._cmd = '{} clean all'.format(self._pms)
        logging.debug(self._cmd)
        if execute(self._cmd)[0] == 0:
            self._cmd = '{} --assumeyes check-update'.format(self._pms)
            logging.debug(self._cmd)
            return execute(self._cmd)[0] == 0

        return False

    def query_all(self):
        """
        ordered list query_all(void)
        """

        self._cmd = '{} -qa'.format(self._pm)
        logging.debug(self._cmd)
        _ret, _output, _ = execute(self._cmd, interactive=False)
        if _ret != 0:
            return []

        return sorted(_output.split('\n'))

    def create_repos(self, template, server, project, repositories):
        """
        bool create_repos(string template, string server, string project, list repositories)
        """

        repo_template = \
"""[{repo}]
name={repo}
baseurl={url}/{repo}
gpgcheck=0
enabled=1
http_caching=none
metadata_expire=1
""".format(url=template.format(server, project), repo='{repo}')

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

        self._cmd = 'rpm --import {} > /dev/null'.format(file_key)
        logging.debug(self._cmd)
        return execute(self._cmd)[0] == 0
