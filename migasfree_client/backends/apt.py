# -*- coding: UTF-8 -*-

# Copyright (c) 2011-2025 Jose Antonio Chavarría <jachavar@gmail.com>
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
import shutil
import re
import logging
import tempfile

from migasfree_client.utils import execute, write_file, which
from .pms import Pms

__author__ = 'Jose Antonio Chavarría'
__license__ = 'GPLv3'


@Pms.register('Apt')
class Apt(Pms):
    """
    PMS for apt based systems (Debian, Ubuntu, Mint, ...)
    """

    def __init__(self):
        Pms.__init__(self)

        self._name = 'apt-get'  # Package Management System name
        self._pm = '/usr/bin/dpkg'  # Package Manager command
        self._pms = 'DEBIAN_FRONTEND=noninteractive /usr/bin/apt-get'  # Package Management System command
        self._repo_dir = '/etc/apt/sources.list.d'  # Repositories path
        self._keyring_dir = '/etc/apt/trusted.gpg.d'

        self._pms_search = '/usr/bin/apt-cache'
        self._pms_query = '/usr/bin/dpkg-query'

        self._silent_options = (
            '-o APT::Get::Purge=true -o Dpkg::Options::=--force-confdef'
            ' -o Dpkg::Options::=--force-confold -o Debug::pkgProblemResolver=1'
            ' --assume-yes --allow-downgrades --allow-change-held-packages'
            ' --allow-unauthenticated --auto-remove'
        )

    def install(self, package):
        """
        bool install(string package)
        """

        self._cmd = '{0} install -o APT::Get::Purge=true {1}'.format(self._pms, package.strip())
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

        self._cmd = '{0} {1} dist-upgrade'.format(self._pms, self._silent_options)
        logging.debug(self._cmd)
        _ret, _output, _error = execute(self._cmd, interactive=False, verbose=True)

        return _ret == 0, _output + _error

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

        self._cmd = '{0} {1} install {2}'.format(self._pms, self._silent_options, ' '.join(package_set))
        logging.debug(self._cmd)
        _ret, _output, _error = execute(self._cmd, interactive=False, verbose=True)

        return _ret == 0, _output + _error

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

        self._cmd = '{0} {1} purge {2}'.format(self._pms, self._silent_options, ' '.join(package_set))
        logging.debug(self._cmd)
        _ret, _output, _error = execute(self._cmd, interactive=False, verbose=True)

        return _ret == 0, _output + _error

    def is_installed(self, package):
        """
        bool is_installed(string package)
        """

        self._cmd = '{0} --status {1} | grep "Status: install ok installed"'.format(self._pm, package.strip())
        logging.debug(self._cmd)

        return execute(self._cmd, interactive=False)[0] == 0

    def clean_all(self):
        """
        bool clean_all(void)
        """

        self._cmd = '{0} clean'.format(self._pms)
        logging.debug(self._cmd)
        if execute(self._cmd)[0] == 0:
            execute('rm --recursive --force /var/lib/apt/lists')
            self._cmd = '{0} -o Acquire::Languages=none --assume-yes update'.format(self._pms)
            logging.debug(self._cmd)
            return execute(self._cmd)[0] == 0

        return False

    def query_all(self):
        """
        ordered list query_all(void)
        list format: name_version_architecture.extension
        """

        _, _packages, _ = execute('{0} --list'.format(self._pm), interactive=False)
        if not _packages:
            return []

        _packages = _packages.strip().splitlines()
        _result = []
        for _line in _packages:
            if _line.startswith('ii'):
                _tmp = re.split(' +', _line)
                _result.append('{0}_{1}_{2}.deb'.format(_tmp[1], _tmp[2], _tmp[3]))

        return _result

    def _adapt_sources(self, sources_content, server):
        """
        Adds 'Signed-By: <key>' in each block of sources content if not exists (deb822)
        """

        signed_by_line = 'Signed-By: {0}'.format(os.path.join(self._keyring_dir, '{0}.gpg'.format(server)))

        blocks = sources_content.split('\n\n')  # each block separated by empty line
        new_blocks = []

        for block in blocks:
            lines = block.splitlines()
            for i, line in enumerate(lines):
                line_lower = line.lower()
                if line_lower.startswith('signed-by:'):
                    value = line[10:].strip()
                    if not value:
                        lines[i] = signed_by_line

            # if signed-by not exists, add to the end
            if all(not line.lower().startswith('signed-by:') for line in lines):
                lines.append(signed_by_line)

            new_blocks.append('\n'.join(lines))

        return '\n\n'.join(new_blocks)

    def _convert_list_to_sources(self, list_content, server):
        """
        Converts formated content .list to .sources format using 'apt modernize-sources'

        Returns .sources content as string, or None if it fails
        """

        # Create temp file .list at _repo_dir
        fd, list_path = tempfile.mkstemp(prefix='tmp_repo_', suffix='.list', dir=self._repo_dir)
        os.close(fd)

        try:
            if not write_file(list_path, list_content):
                logging.error('Error writing temp file %s', list_path)
                return ''

            cmd = 'yes | /usr/bin/apt modernize-sources {0}'.format(list_path)
            logging.debug(cmd)
            ret, _, err = execute(cmd, interactive=False)
            if ret != 0:
                logging.error('apt modernize-sources failed: %s', str(err))
                return ''

            sources_path = list_path[:-5] + '.sources'
            if not os.path.isfile(sources_path):
                logging.error('Generated .sources file not found: %s', sources_path)
                return ''

            with open(sources_path) as f:
                sources_content = f.read()

            return self._adapt_sources(sources_content, server)

        finally:  # Cleaning temp files
            if os.path.isfile(list_path):
                os.remove(list_path)

            sources_path = list_path[:-5] + '.sources'
            if os.path.isfile(sources_path):
                os.remove(sources_path)

            backup_path = list_path + '.bak'
            if os.path.isfile(backup_path):
                os.remove(backup_path)

    def _get_pms_version(self):
        """
        Detects APT version (if fails, default to 2.x for compatibility)
        """

        cmd = "{0} --version | head -n1 | awk '{{print $2}}'".format(self._pms)
        ret, out, _ = execute(cmd, interactive=False)
        apt_version = out.strip() if ret == 0 else '2.0'
        logging.debug('Detected APT version: %s', apt_version)

        # extracts the first three number groups
        match = re.match(r'(\d+)\.(\d+)(?:\.(\d+))?', apt_version)
        if not match:
            return (2, 0)  # for compatibility

        return tuple(int(x) for x in match.groups() if x is not None)

    def create_repos(self, protocol, server, project, repositories, template=''):
        """
        bool create_repos(string protocol, string server, string project, list repositories, string template='')
        """

        base_url = template.format(server=server, project=project, protocol=protocol)
        content = ''
        for repo in repositories:
            if 'source_template' in repo:
                content += repo['source_template'].format(server=server, project=project, protocol=protocol)
            else:
                content += 'deb {url} {repo} PKGS\n'.format(url=base_url, repo=repo['name'])

        if not content:
            return True

        # Choose format by APT version
        self._repo = os.path.join(self._repo_dir, 'migasfree.list')
        try:
            apt_version = self._get_pms_version()
            if apt_version[0] >= 3:
                content = self._convert_list_to_sources(content, server)
                self._repo = os.path.join(self._repo_dir, 'migasfree.sources')
        except Exception:
            pass

        logging.debug('Creating repos: %s', self._repo)

        return write_file(self._repo, content)

    def import_server_key(self, file_key):
        """
        bool import_server_key(string file_key)
        """

        apt_version = self._get_pms_version()
        if apt_version and apt_version >= (2, 1):
            # try with gpg --dearmor
            try:
                if not os.path.exists(self._keyring_dir):
                    os.makedirs(self._keyring_dir)

                key_dest = os.path.join(self._keyring_dir, '{0}.gpg'.format(os.path.basename(file_key)))

                self._cmd = 'gpg --dearmor < {0} > {1}'.format(file_key, key_dest)
                logging.debug(self._cmd)

                ret, _, err = execute(self._cmd, interactive=False)
                if ret == 0:
                    logging.debug('Imported key with gpg --dearmor at %s', key_dest)
                    return True

                logging.warning('Error gpg --dearmor: %s', err)
                return False

            except Exception as e:
                logging.error('Error in import_server_key with gpg: %s', str(e))
                return False

        elif which('apt-key'):
            self._cmd = 'APT_KEY_DONT_WARN_ON_DANGEROUS_USAGE=1 apt-key add {0} >/dev/null'.format(file_key)
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
