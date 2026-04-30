# Copyright (c) 2011-2026 Jose Antonio Chavarría <jachavar@gmail.com>
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
import os
import re
import tempfile

from ..utils import ALL_OK, execute, sanitize_path, write_file, write_file_if_changed
from .pms import Pms, invalidate_installed_cache

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
        self._pms = ['env', 'DEBIAN_FRONTEND=noninteractive', '/usr/bin/apt-get']  # Package Management System command
        self._repo_dir = '/etc/apt/sources.list.d'  # Repositories path
        self._keyring_dir = '/etc/apt/trusted.gpg.d'

        self._repo_list = 'migasfree.list'
        self._repo_sources = 'migasfree.sources'

        self._mimetype = [
            'application/x-debian-package',
            'application/vnd.debian.binary-package',
        ]

        self._pms_search = '/usr/bin/apt-cache'
        self._pms_query = '/usr/bin/dpkg-query'

        self._silent_options = [
            '-o',
            'APT::Get::Purge=true',
            '-o',
            'Dpkg::Options::=--force-confdef',
            '-o',
            'Dpkg::Options::=--force-confold',
            '-o',
            'Debug::pkgProblemResolver=1',
            '--assume-yes',
            '--allow-downgrades',
            '--allow-change-held-packages',
            '--allow-unauthenticated',
            '--auto-remove',
        ]

    @invalidate_installed_cache
    def install(self, package):
        """
        bool install(string package)
        """

        cmd = [*self._pms, 'install', '-o', 'APT::Get::Purge=true', package.strip()]
        logger.debug(' '.join(cmd))

        return execute(cmd)[0] == ALL_OK

    @invalidate_installed_cache
    def remove(self, package):
        """
        bool remove(string package)
        """

        cmd = [*self._pms, 'purge', package.strip()]
        logger.debug(' '.join(cmd))

        return execute(cmd)[0] == ALL_OK

    def search(self, pattern):
        """
        bool search(string pattern)
        """

        cmd = [self._pms_search, 'search', pattern.strip()]
        logger.debug(' '.join(cmd))

        return execute(cmd)[0] == ALL_OK

    @invalidate_installed_cache
    def update_silent(self):
        """
        (bool, string) update_silent(void)
        """

        cmd = [*self._pms, *self._silent_options, 'dist-upgrade']
        logger.debug(' '.join(cmd))

        ret, output, error = execute(cmd, interactive=False, verbose=True)

        return ret == ALL_OK, f'{output}{error}'

    @invalidate_installed_cache
    def _execute_silent(self, action, package_set):
        """
        (bool, string) _execute_silent(string action, list package_set)
        Common logic for install_silent and remove_silent
        """

        if not isinstance(package_set, list):
            return False, f'package_set is not a list: {package_set}'

        # Performance Optimization: Get all installed packages once to avoid N+1 processes
        installed = self._get_installed_packages()

        if action == 'install':
            package_set = [pkg.strip() for pkg in package_set if pkg.strip() not in installed]
        elif action == 'purge':
            package_set = [pkg.strip() for pkg in package_set if pkg.strip() in installed]

        if not package_set:
            return True, None

        cmd = [*self._pms, *self._silent_options, action, *package_set]
        logger.debug(' '.join(cmd))

        ret, output, error = execute(cmd, interactive=False, verbose=True)

        return ret == ALL_OK, f'{output}{error}'

    def _get_installed_packages(self):
        """
        set _get_installed_packages(void)
        """

        if self._installed_cache is None:
            self._installed_cache = {pkg.split('_')[0] for pkg in self.query_all()}

        return self._installed_cache

    def install_silent(self, package_set):
        """
        (bool, string) install_silent(list package_set)
        """

        return self._execute_silent('install', package_set)

    def remove_silent(self, package_set):
        """
        (bool, string) remove_silent(list package_set)
        """

        return self._execute_silent('purge', package_set)

    def is_installed(self, package):
        """
        bool is_installed(string package)
        """

        return package.strip() in self._get_installed_packages()

    @invalidate_installed_cache
    def clean_all(self):
        """
        bool clean_all(void)
        """

        cmd = [*self._pms, 'clean']
        logger.debug(' '.join(cmd))

        if execute(cmd)[0] == ALL_OK:
            cmd = ['rm', '--recursive', '--force', '/var/lib/apt/lists']
            logger.debug(' '.join(cmd))
            execute(cmd)

            cmd = [*self._pms, '-o', 'Acquire::Languages=none', '--assume-yes', 'update']
            logger.debug(' '.join(cmd))

            return execute(cmd)[0] == ALL_OK

        return False

    def query_all(self):
        """
        ordered list query_all(void)
        list format: name_version_architecture.extension
        """

        cmd = [self._pm, '--list']
        logger.debug(' '.join(cmd))

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
        Converts formatted content .list to .sources format using 'apt modernize-sources'

        Returns .sources content as string, or None if it fails
        """

        # Security Hardening: Use TemporaryDirectory for safer cleanup
        with tempfile.TemporaryDirectory() as tmp_dir:
            list_path = os.path.join(tmp_dir, self._repo_list)

            if not write_file(list_path, list_content):
                logging.error('Error writing temp file %s', list_path)
                return ''

            # apt modernize-sources converts <file>.list to <file>.sources
            # and creates a .list.bak
            # We must override Dir::Etc configuration to point to our temp dir,
            # otherwise it ignores the argument and looks at system sources.
            # IMPORTANT: Do NOT use /dev/null as SourceList — apt may try to
            # back it up or modify it, corrupting /dev/null when running as root.
            empty_source_list = os.path.join(tmp_dir, 'empty.list')
            write_file(empty_source_list, '')
            cmd = [
                '/usr/bin/apt',
                '-o', f'Dir::Etc::SourceList={empty_source_list}',
                '-o', f'Dir::Etc::SourceParts={tmp_dir}',
                'modernize-sources',
                '--assume-yes',
            ]
            logging.debug(' '.join(cmd))
            ret, _, err = execute(cmd, interactive=False)
            if ret != ALL_OK:
                logging.error('apt modernize-sources failed: %s', str(err))
                return ''

            sources_path = os.path.join(tmp_dir, self._repo_sources)
            if not os.path.isfile(sources_path):
                logging.error('Generated .sources file not found: %s', sources_path)
                return ''

            with open(sources_path, encoding='utf-8') as f:
                sources_content = f.read()

            return self._adapt_sources(sources_content, server)

    def _get_pms_version(self):
        """
        Detects APT version (if fails, default to 2.x for compatibility)
        """

        # Shell Reduction: Use Python regex instead of awk/pipes
        cmd = [self._pms[2], '--version']
        ret, output, _ = execute(cmd, interactive=False)

        if ret != ALL_OK or not output:
            return (2, 0)

        # Expected format: "apt 2.9.21 (amd64)"
        match = re.search(r'apt\s+(\d+)\.(\d+)(?:\.(\d+))?', output)
        if not match:
            return (2, 0)

        logging.debug('Detected APT version: %s', match.group(0))

        return tuple(int(x) for x in match.groups() if x is not None)

    def create_repos(self, protocol, server, repositories):
        """
        bool create_repos(string protocol, string server, list repositories)
        """

        content = ''.join(
            f'{repo.get("source_template").format(protocol=protocol, server=server)}' for repo in repositories
        )
        if not content:
            return True

        # Choose format by APT version
        list_path = os.path.join(self._repo_dir, self._repo_list)
        sources_path = os.path.join(self._repo_dir, self._repo_sources)
        self._repo = list_path

        try:
            apt_version = self._get_pms_version()
            if apt_version[0] >= 3:
                sources_content = self._convert_list_to_sources(content, server)
                if sources_content:
                    content = sources_content
                    self._repo = sources_path
                else:
                    logging.warning('Failed to convert repos to .sources format, falling back to .list')

            # Clean up the format not in use to avoid duplicates
            other_repo = sources_path if self._repo == list_path else list_path
            if os.path.isfile(other_repo):
                os.remove(other_repo)

        except (AttributeError, ValueError, IndexError) as e:
            logging.debug('Error detecting APT version or converting sources: %s', str(e))

        logging.debug('Creating repos: %s', self._repo)

        return write_file_if_changed(self._repo, content)

    def import_server_key(self, file_key):
        """
        bool import_server_key(string file_key)
        """

        name = os.path.basename(file_key)
        key_target = os.path.join(self._keyring_dir, f'{name}.gpg')
        cmd = ['gpg', '--output', key_target, '--dearmor', '--yes', file_key]
        logger.debug(' '.join(cmd))

        return execute(cmd, interactive=False)[0] == ALL_OK

    def get_system_architecture(self):
        """
        string get_system_architecture(void)
        """

        # Shell Reduction: Avoid subshell-based echo
        cmd = [self._pm, '--print-architecture']
        logger.debug(' '.join(cmd))
        ret, arch, _ = execute(cmd, interactive=False)

        cmd = [self._pm, '--print-foreign-architectures']
        logger.debug(' '.join(cmd))
        _, foreign_arch, _ = execute(cmd, interactive=False)

        if ret != ALL_OK:
            return ''

        result = f'{arch.strip()} {foreign_arch.strip()}'.strip()
        logger.debug('System architecture: %s', result)

        return result

    def available_packages(self):
        """
        list available_packages(void)
        """

        cmd = [self._pms_search, 'pkgnames']
        logger.debug(' '.join(cmd))

        ret, output, _ = execute(cmd, interactive=False)

        return sorted(output.strip().splitlines()) if ret == ALL_OK else []
