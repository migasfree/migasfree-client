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

__author__ = 'Jose Antonio Chavarría <jachavar@gmail.com>'
__license__ = 'GPLv3'

# https://pythonhosted.org/setuptools
# python setup.py --help-commands
# python setup.py bdist_egg
# python setup.py bdist_wheel
# python setup.py build
# python setup.py sdist
# python setup.py bdist --format=rpm
# python setup.py bdist_rpm
# python setup.py --command-packages=stdeb.command bdist_deb (python-stdeb)

# http://zetcode.com/articles/packageinpython/
# TODO https://wiki.ubuntu.com/PackagingGuide/Python
# TODO https://help.ubuntu.com/community/PythonRecipes/DebianPackage

import os
import sys
import glob
import subprocess
import logging
import re

# set DISTUTILS_DEBUG as environment variable to get debug info

from setuptools import setup, find_packages

try:
    from setuptools.command.build_py import build_py as build
    from setuptools.command.install_data import install_data
except ImportError:
    from distutils.command.build import build
    from distutils.command.install_data import install_data

try:
    from distutils.dep_util import newer
except ImportError:

    def newer(source, target):
        try:
            return os.path.getmtime(source) > os.path.getmtime(target)
        except OSError:
            return True  # if target not exist, source is newer


PATH = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(PATH, 'README.md'), encoding='utf-8') as f:
    README = f.read()


with open(os.path.join(PATH, 'migasfree_client', '__init__.py'), encoding='utf-8') as f:
    VERSION = re.search(r"__version__ = '(.*)'", f.read()).group(1)

REQUIRES = filter(
    lambda s: len(s) > 0, open(os.path.join(PATH, 'requirements.txt'), encoding='utf-8').read().split('\n')
)

APP_NAME = 'migasfree_client'
DOMAIN = 'migasfree'
PO_DIR = 'po'
MO_DIR = os.path.join('build', 'mo')


class BuildData(build):
    def run(self):
        build.run(self)

        for po in glob.glob(os.path.join(PO_DIR, '*.po')):
            lang = os.path.basename(po[:-3])
            mo = os.path.join(MO_DIR, lang, f'{DOMAIN}.mo')

            directory = os.path.dirname(mo)
            if not os.path.exists(directory):
                logging.info('creating %s', directory)
                os.makedirs(directory)

            if newer(po, mo):
                logging.info('compiling %s -> %s', po, mo)
                try:
                    rc = subprocess.call(['msgfmt', '-o', mo, po])
                    if rc != 0:
                        raise Warning(f'msgfmt returned {rc}')
                except OSError as e:
                    logging.error(
                        'Building gettext files failed.  Try setup.py \
                        --without-gettext [build|install]'
                    )
                    logging.error('Error: %s', {str(e)})
                    sys.exit(1)


class InstallData(install_data):
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
    name=APP_NAME,
    version=VERSION,
    description='Synchronizes a computer from a migasfree server',
    long_description=README,
    license='GPLv3',
    keywords=['migasfree', 'systems management', 'devops'],
    author='Jose Antonio Chavarría',
    author_email='jachavar@gmail.com',
    maintainer='Jose Antonio Chavarría',
    maintainer_email='jachavar@gmail.com',
    url='http://www.migasfree.org/',
    platforms=['Linux', 'Windows 10'],
    install_requires=REQUIRES,
    python_requires='>=3.6.0',
    packages=find_packages(),
    entry_points={'console_scripts': ['migasfree = migasfree_client.__main__:main']},
    cmdclass={
        'build': BuildData,
        'install_data': InstallData,
    },
    data_files=[
        (
            'share/icons/hicolor/scalable/apps',
            ['icons/scalable/migasfree.svg', 'icons/scalable/migasfree-server-network.svg'],
        ),
        (
            'share/doc/migasfree-client',
            [
                'AUTHORS',
                'INSTALL',
                'LICENSE',
                'MANIFEST.in',
                'README.md',
                'migasfree-client.doap',
                'conf/migasfree.conf',
            ],
        ),
    ],
    # http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Microsoft :: Windows :: Windows 10',
        'Programming Language :: Python',
        'Topic :: System :: Software Distribution',
    ],
)
