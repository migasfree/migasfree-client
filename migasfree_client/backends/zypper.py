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

import logging

from .pms import Pms
from migasfree_client.utils import execute

__author__ = 'Jose Antonio Chavarría'
__license__ = 'GPLv3'


@Pms.register('Zypper')
class Zypper(Pms):
    """
    PMS for zypper based systems (openSUSE, SLED, SLES, ...)
    """

    def __init__(self):
        Pms.__init__(self)

        self._name = 'zypper'          # Package Management System name
        self._pm = '/bin/rpm'          # Package Manager command
        self._pms = '/usr/bin/zypper'  # Package Management System command
        self._repo = '/etc/zypp/repos.d/migasfree.repo'  # Repositories file

    def install(self, package):
        """
        bool install(string package)
        """

        self._cmd = '{0} install --no-force-resolution {1}'.format(
            self._pms,
            package.strip()
        )
        logging.debug(self._cmd)

        return execute(self._cmd)[0] == 0

    def remove(self, package):
        """
        bool remove(string package)
        """

        self._cmd = '{0} remove {1}'.format(self._pms, package.strip())
        logging.debug(self._cmd)

        return execute(self._cmd)[0] == 0

    def search(self, pattern):
        """
        bool search(string pattern)
        """

        self._cmd = '{0} search {1}'.format(self._pms, pattern.strip())
        logging.debug(self._cmd)

        return execute(self._cmd)[0] == 0

    def update_silent(self):
        """
        (bool, string) update_silent(void)
        """

        self._cmd = '{0} --non-interactive update --no-force-resolution "*"'.format(self._pms)
        logging.debug(self._cmd)
        _ret, _output, _error = execute(
            self._cmd,
            interactive=False,
            verbose=True
        )
        if _ret != 0:
            return False, '{0}\n{1}\n{2}'.format(_ret, _output, _error)

        self._cmd = '{0} lu -a'.format(self._pms)
        logging.debug(self._cmd)
        _ret, _output, _error = execute(
            self._cmd,
            interactive=False,
            verbose=True
        )

        return _ret == 0, '{0}\n{1}\n{2}'.format(_ret, _output, _error)

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

        self._cmd = '{0} --non-interactive install --no-force-resolution {1}'.format(
            self._pms,
            ' '.join(package_set)
        )
        logging.debug(self._cmd)
        _ret, _output, _error = execute(
            self._cmd,
            interactive=False,
            verbose=True
        )

        return _ret == 0, '{0}\n{1}\n{2}'.format(_ret, _output, _error)

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

        self._cmd = '{0} --non-interactive remove {1}'.format(
            self._pms,
            ' '.join(package_set)
        )
        logging.debug(self._cmd)
        _ret, _output, _error = execute(
            self._cmd,
            interactive=False,
            verbose=True
        )

        return _ret == 0, '{0}\n{1}\n{2}'.format(_ret, _output, _error)

    def is_installed(self, package):
        """
        bool is_installed(string package)
        """

        self._cmd = '{0} -q {1}'.format(self._pm, package.strip())
        logging.debug(self._cmd)

        return execute(self._cmd, interactive=False)[0] == 0

    def clean_all(self):
        """
        bool clean_all(void)
        """

        self._cmd = '{0} clean --all'.format(self._pms)
        logging.debug(self._cmd)
        if execute(self._cmd)[0] == 0:
            self._cmd = '{0} --non-interactive refresh'.format(self._pms)
            logging.debug(self._cmd)
            return execute(self._cmd)[0] == 0

        return False

    def query_all(self):
        """
        ordered list query_all(void)
        """

        self._cmd = '{0} -qa'.format(self._pm)
        logging.debug(self._cmd)
        _ret, _output, _ = execute(self._cmd, interactive=False)
        if _ret != 0:
            return []

        return sorted(_output.strip().splitlines())

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
""".format(url=template.format(server=server, project=project), repo='{repo}')

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

        self._cmd = '{0} --import {1} > /dev/null'.format(self._pm, file_key)
        logging.debug(self._cmd)
        return execute(self._cmd)[0] == 0

    def available_packages(self):
        """
        list available_packages(void)
        """

        self._cmd = "{0} pa | awk -F'|' '{{print $3}}'".format(self._pms)
        logging.debug(self._cmd)
        _ret, _output, _error = execute(self._cmd, interactive=False)
        if _ret == 0:
            return sorted(_output.strip().splitlines())

        return []
