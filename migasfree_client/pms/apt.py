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
import re
import logging
import tempfile

from .pms import Pms
from ..utils import execute, write_file, sanitize_path

__author__ = 'Jose Antonio Chavarría'
__license__ = 'GPLv3'

logger = logging.getLogger('migasfree_client')


@Pms.register('Apt')
class Apt(Pms):
    """
    PMS for apt based systems (Debian, Ubuntu, Mint, Zorin, ...)
    """

    def __init__(self):
        super().__init__()

        self._name = 'apt'  # Package Management System name
        self._pm = '/usr/bin/dpkg'  # Package Manager command
        self._pms = 'DEBIAN_FRONTEND=noninteractive /usr/bin/apt-get'  # Package Management System command
        self._repo_dir = '/etc/apt/sources.list.d'  # Repositories path
        self._keyring_dir = '/etc/apt/trusted.gpg.d'

        self._mimetype = [
            'application/x-debian-package',
            'application/vnd.debian.binary-package',
        ]

        self._pms_search = '/usr/bin/apt-cache'
        self._pms_query = '/usr/bin/dpkg-query'

        self._silent_options = (
            '-o APT::Get::Purge=true '
            '-o Dpkg::Options::=--force-confdef '
            '-o Dpkg::Options::=--force-confold '
            '-o Debug::pkgProblemResolver=1 '
            '--assume-yes --allow-downgrades '
            '--allow-change-held-packages '
            '--allow-unauthenticated --auto-remove'
        )

    def install(self, package):
        """
        bool install(string package)
        """

        cmd = f'{self._pms} install -o APT::Get::Purge=true {package.strip()}'
        logger.debug(cmd)

        return execute(cmd)[0] == 0

    def remove(self, package):
        """
        bool remove(string package)
        """

        cmd = f'{self._pms} purge {package.strip()}'
        logger.debug(cmd)

        return execute(cmd)[0] == 0

    def search(self, pattern):
        """
        bool search(string pattern)
        """

        cmd = f'{self._pms_search} search {pattern.strip()}'
        logger.debug(cmd)

        return execute(cmd)[0] == 0

    def update_silent(self):
        """
        (bool, string) update_silent(void)
        """

        cmd = f'{self._pms} {self._silent_options} dist-upgrade'
        logger.debug(cmd)

        ret, output, error = execute(cmd, interactive=False, verbose=True)

        return ret == 0, f'{output}{error}'

    def install_silent(self, package_set):
        """
        (bool, string) install_silent(list package_set)
        """

        if not isinstance(package_set, list):
            return False, f'package_set is not a list: {package_set}'

        package_set = [pkg for pkg in package_set if not self.is_installed(pkg)]
        if not package_set:
            return True, None

        cmd = f'{self._pms} {self._silent_options} install {" ".join(package_set)}'
        logger.debug(cmd)

        ret, output, error = execute(cmd, interactive=False, verbose=True)

        return ret == 0, f'{output}{error}'

    def remove_silent(self, package_set):
        """
        (bool, string) remove_silent(list package_set)
        """

        if not isinstance(package_set, list):
            return False, f'package_set is not a list: {package_set}'

        package_set = [pkg for pkg in package_set if self.is_installed(pkg)]
        if not package_set:
            return True, None

        cmd = f'{self._pms} {self._silent_options} purge {" ".join(package_set)}'
        logger.debug(cmd)

        ret, output, error = execute(cmd, interactive=False, verbose=True)

        return ret == 0, f'{output}{error}'

    def is_installed(self, package):
        """
        bool is_installed(string package)
        """

        cmd = f'{self._pm} --status {package.strip()} | grep "Status: install ok installed"'
        logger.debug(cmd)

        return execute(cmd, interactive=False)[0] == 0

    def clean_all(self):
        """
        bool clean_all(void)
        """

        cmd = f'{self._pms} clean'
        logger.debug(cmd)

        if execute(cmd)[0] == 0:
            execute('rm --recursive --force /var/lib/apt/lists')
            cmd = f'{self._pms} -o Acquire::Languages=none --assume-yes update'
            logger.debug(cmd)

            return execute(cmd)[0] == 0

        return False

    def query_all(self):
        """
        ordered list query_all(void)
        list format: name_version_architecture.extension
        """

        cmd = f'{self._pm} --list'
        logger.debug(cmd)

        packages = execute(cmd, interactive=False)[1].strip().splitlines()
        if not packages:
            return []

        pattern = re.compile(r'^ii\s+(\S+)\s+(\S+)\s+(\S+)')
        result = [
            f'{match.group(1)}_{match.group(2)}_{match.group(3)}.deb'
            for match in (pattern.match(line) for line in packages)
            if match
        ]

        return result

    def _adapt_sources(self, sources_content, server):
        """
        Adds 'Signed-By: <key>' in each block of sources content if not exists (deb822)
        """

        key_path = os.path.join(self._keyring_dir, f'{sanitize_path(server)}.gpg')
        signed_by_line = f'Signed-By: {key_path}'

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

            cmd = f'yes | /usr/bin/apt modernize-sources {list_path}'
            logging.debug(cmd)
            ret, _, err = execute(cmd, interactive=False)
            if ret != 0:
                logging.error('apt modernize-sources failed: %s', str(err))
                return ''

            sources_path = list_path[:-5] + '.sources'
            if not os.path.isfile(sources_path):
                logging.error('Generated .sources file not found: %s', sources_path)
                return ''

            with open(sources_path, encoding='utf-8') as f:
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

        cmd = f"{self._pms} --version | head -n1 | awk '{{print $2}}'"
        ret, out, _ = execute(cmd, interactive=False)
        apt_version = out.strip() if ret == 0 else '2.0'
        logging.debug('Detected APT version: %s', apt_version)

        return tuple(int(x) for x in apt_version.split('.'))

    def create_repos(self, protocol, server, repositories):
        """
        bool create_repos(string protocol, string server, list repositories)
        """

        content = ''.join(
            f'{repo.get("source_template").format(protocol=protocol, server=server)}' for repo in repositories
        )

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

        name = os.path.basename(file_key)
        key_target = os.path.join(self._keyring_dir, f'{name}.gpg')
        cmd = f'gpg --output {key_target} --dearmor --yes {file_key} > /dev/null'
        logger.debug(cmd)

        return execute(cmd, interactive=False)[0] == 0

    def get_system_architecture(self):
        """
        string get_system_architecture(void)
        """

        cmd = f'echo "$({self._pm} --print-architecture) $({self._pm} --print-foreign-architectures)"'
        logger.debug(cmd)

        ret, arch, _ = execute(cmd, interactive=False)

        return arch.strip() if ret == 0 else ''

    def available_packages(self):
        """
        list available_packages(void)
        """

        cmd = f'{self._pms_search} pkgnames'
        logger.debug(cmd)

        ret, output, _ = execute(cmd, interactive=False)

        return sorted(output.strip().splitlines()) if ret == 0 else []
