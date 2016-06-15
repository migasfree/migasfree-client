#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Copyright (c) 2011-2016 Jose Antonio Chavarría <jachavar@gmail.com>
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
# python setup.py build
# python setup.py sdist
# python setup.py bdist --format=rpm
# python setup.py --command-packages=stdeb.command bdist_deb (python-stdeb)

# http://zetcode.com/articles/packageinpython/
# TODO https://wiki.ubuntu.com/PackagingGuide/Python
# TODO https://help.ubuntu.com/community/PythonRecipes/DebianPackage

import sys

if not hasattr(sys, 'version_info') or sys.version_info < (2, 7, 0, 'final'):
    raise SystemExit('migasfree-client requires Python 2.7 or later.')

import os
PATH = os.path.dirname(os.path.abspath(__file__))
README = open(os.path.join(PATH, 'README.md')).read()
VERSION = open(os.path.join(PATH, 'VERSION')).read().strip()

REQUIRES = filter(lambda s: len(s) > 0,
    open(os.path.join(PATH, 'requirements.txt')).read().split('\n'))

import glob
import subprocess

from setuptools import setup, find_packages
from distutils.command.build import build
from distutils.command.install_data import install_data
from distutils.log import info, error
from distutils.dep_util import newer

APP_NAME = 'migasfree-client'
PO_DIR = 'po'
MO_DIR = os.path.join('build', 'mo')


class BuildData(build):
    def run(self):
        build.run(self)

        for po in glob.glob(os.path.join(PO_DIR, '*.po')):
            lang = os.path.basename(po[:-3])
            mo = os.path.join(MO_DIR, lang, '%s.mo' % APP_NAME)

            directory = os.path.dirname(mo)
            if not os.path.exists(directory):
                info('creating %s' % directory)
                os.makedirs(directory)

            if newer(po, mo):
                info('compiling %s -> %s' % (po, mo))
                try:
                    rc = subprocess.call(['msgfmt', '-o', mo, po])
                    if rc != 0:
                        raise Warning("msgfmt returned %d" % rc)
                except Exception, e:
                    error("Building gettext files failed.  Try setup.py \
                        --without-gettext [build|install]")
                    error("Error: %s" % str(e))
                    sys.exit(1)


class InstallData(install_data):
    def run(self):
        self.data_files.extend(self._find_mo_files())
        install_data.run(self)

    def _find_mo_files(self):
        data_files = []

        for mo in glob.glob(os.path.join(MO_DIR, '*', '%s.mo' % APP_NAME)):
            lang = os.path.basename(os.path.dirname(mo))
            dest = os.path.join('share', 'locale', lang, 'LC_MESSAGES')
            data_files.append((dest, [mo]))

        return data_files

setup(
    name=APP_NAME,
    version=VERSION,
    description='Synchronizes a computer from a migasfree server',
    long_description=README,
    license='GPLv3',
    keywords='migasfree systems management devops',
    author='Jose Antonio Chavarría',
    author_email='jachavar@gmail.com',
    url='http://www.migasfree.org/',
    platforms=['Linux'],
    install_requires=REQUIRES,
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'migasfree = migasfree_client.__main__:main'
        ]
    },
    cmdclass={
        'build': BuildData,
        'install_data': InstallData,
    },
    data_files=[
        (
            'share/icons/hicolor/scalable/actions',
            ['icons/scalable/migasfree-ok.svg']
        ),
        (
            'share/icons/hicolor/scalable/apps',
            ['icons/scalable/migasfree.svg']
        ),
        ('share/doc/migasfree-client', [
            'AUTHORS',
            'INSTALL',
            'LICENSE',
            'MANIFEST.in',
            'README.md',
            'VERSION',
            'migasfree-client.doap',
            'conf/migasfree.conf'
        ]),
    ],
    # http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: X11 Applications :: Gnome',
        'Environment :: X11 Applications :: KDE',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Topic :: System :: Software Distribution',
    ],
)
