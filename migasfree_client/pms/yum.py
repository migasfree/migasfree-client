# -*- coding: UTF-8 -*-

# Copyright (c) 2011-2019 Jose Antonio Chavarría <jachavar@gmail.com>
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
from ..utils import execute, write_file

__author__ = 'Jose Antonio Chavarría'
__license__ = 'GPLv3'


@Pms.register('Yum')
class Yum(Pms):
    """
    PMS for yum based systems (Fedora, Red Hat, CentOS, ...)
    """

    def __init__(self):
        super().__init__()

        self._name = 'yum'  # Package Management System name
        self._pm = '/bin/rpm'  # Package Manager command
        self._pms = '/usr/bin/yum'  # Package Management System command

        # Repositories file
        if os.path.isdir('/etc/yum.repos.d'):
            self._repo = '/etc/yum.repos.d/migasfree.repo'
        else:
            self._repo = '/etc/yum/repos.d/migasfree.repo'

        self._mimetype = [
            'application/x-rpm',
            'application/x-redhat-package-manager'
        ]

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
            ret, _, _ = execute(self._cmd)
            return ret == 0 or ret == 100

        return False

    def query_all(self):
        """
        ordered list query_all(void)
        list format: name_version_architecture.extension
        """

        self._cmd = '%s --queryformat "%%{NAME}_%%{VERSION}-%%{RELEASE}_%%{ARCH}.rpm\n" -qa' % self._pm
        logging.debug(self._cmd)
        _ret, _output, _ = execute(self._cmd, interactive=False)
        if _ret != 0:
            return []

        return sorted(_output.strip().splitlines())

    def create_repos(self, protocol, server, repositories):
        """
        bool create_repos(string protocol, string server, list repositories)
        """

        content = ''
        for repo in repositories:
            content += repo.get('source_template').format(protocol=protocol, server=server)

        return write_file(self._repo, content)

    def import_server_key(self, file_key):
        """
        bool import_server_key(string file_key)
        """

        self._cmd = '{} --import {} > /dev/null'.format(self._pm, file_key)
        logging.debug(self._cmd)

        return execute(self._cmd)[0] == 0

    def get_system_architecture(self):
        """
        string get_system_architecture(void)
        """

        self._cmd = 'echo $(%s -q --qf "%%{arch}" -f /etc/$(sed -n "s/^distroverpkg=//p" /etc/yum.conf))' % self._pm
        logging.debug(self._cmd)

        _ret, _arch, _ = execute(self._cmd, interactive=False)

        return _arch.strip() if _ret == 0 else ''

    def available_packages(self):
        """
        list available_packages(void)
        """

        self._cmd = "{} --quiet list available | awk -F. '{{print $1}}' | grep -v '^ ' | sed '1d'".format(
            self._pms
        )
        logging.debug(self._cmd)
        _ret, _output, _error = execute(self._cmd, interactive=False)
        if _ret == 0:
            return sorted(_output.strip().splitlines())

        return []
