#!/usr/bin/env python3
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

# Minimal setup.py for compatibility with stdeb.
# All configuration is in pyproject.toml.
# This file handles translation building and installation.

import glob
import os
import subprocess

from setuptools import setup
from setuptools.command.build_py import build_py

try:
    from setuptools.command.install_data import install_data
except ImportError:
    from distutils.command.install_data import install_data

DOMAIN = 'migasfree'
PO_DIR = 'po'
MO_DIR = os.path.join('build', 'mo')


def newer(source, target):
    """Check if source is newer than target."""
    try:
        return os.path.getmtime(source) > os.path.getmtime(target)
    except OSError:
        return True


class BuildData(build_py):
    """Build command that also compiles translations."""

    def run(self):
        # Compile translations
        for po in glob.glob(os.path.join(PO_DIR, '*.po')):
            lang = os.path.basename(po[:-3])
            mo = os.path.join(MO_DIR, lang, f'{DOMAIN}.mo')

            directory = os.path.dirname(mo)
            if not os.path.exists(directory):
                os.makedirs(directory)

            if newer(po, mo):
                try:
                    subprocess.call(['msgfmt', '-o', mo, po])
                except OSError as e:
                    print(f'Warning: msgfmt failed: {e}')

        # Run the standard build_py
        build_py.run(self)


class InstallData(install_data):
    """Install command that includes compiled translations."""

    def _find_mo_files(self):
        data_files = []
        for mo in glob.glob(os.path.join(MO_DIR, '*', f'{DOMAIN}.mo')):
            lang = os.path.basename(os.path.dirname(mo))
            dest = os.path.join('share', 'locale', lang, 'LC_MESSAGES')
            data_files.append((dest, [mo]))
        self.data_files.extend(data_files)

    def run(self):
        self._find_mo_files()
        install_data.run(self)


setup(
    cmdclass={
        'build_py': BuildData,
        'install_data': InstallData,
    },
)
