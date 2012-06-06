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

__author__  = 'Jose Antonio Chavarría'
__file__    = 'setup.py'
__date__    = '2012-06-06'
__license__ = 'GPLv3'

# http://guide.python-distribute.org/
# python setup.py --help-commands
# python setup.py build
# python setup.py sdist
# python setup.py bdist --format=rpm

# http://zetcode.com/articles/packageinpython/
# TODO https://wiki.ubuntu.com/PackagingGuide/Python
# TODO https://help.ubuntu.com/community/PythonRecipes/DebianPackage
# TODO https://github.com/astraw/stdeb

import sys

if not hasattr(sys, 'version_info') or sys.version_info < (2, 6, 0, 'final'):
    raise SystemExit('migasfree-client requires Python 2.6 or later.')

import os
README = open(os.path.join(os.path.dirname(__file__), 'README')).read()

import migasfree_client
VERSION = migasfree_client.__version__

import platform
_dist = platform.linux_distribution()
_requires = [
    'python (>=2.6)',
    'lshw', #'lshw (>=B.02.15)', # invalid version number
]
if _dist[0] == 'Fedora':
    _requires.append('pycurl (>=7.19)') # python-pycurl
    _requires.append('notify-python')
elif _dist[0] == 'openSUSE':
    _requires.append('curl (>=7.19)') # python-curl
    _requires.append('python-notify')
elif _dist[0] == 'Ubuntu':
    _requires.append('pycurl (>=7.19)')
    _requires.append('python-notify')

import glob
import subprocess

from distutils.core import setup
from distutils.command.build import build
from distutils.command.install_data import install_data
from distutils.log import warn, info, error, fatal
from distutils.dep_util import newer

PO_DIR = 'po'
MO_DIR = os.path.join('build', 'mo')

class BuildData(build):
    def run(self):
        build.run(self)

        for po in glob.glob(os.path.join(PO_DIR, '*.po')):
            lang = os.path.basename(po[:-3])
            mo = os.path.join(MO_DIR, lang, 'migasfree-client.mo')

            directory = os.path.dirname(mo)
            if not os.path.exists(directory):
                info('creating %s' % directory)
                os.makedirs(directory)

            if newer(po, mo):
                info('compiling %s -> %s' % (po, mo))
                try:
                    rc = subprocess.call(['msgfmt', '-o', mo, po])
                    if rc != 0:
                        raise Warning, "msgfmt returned %d" % rc
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

        for mo in glob.glob(os.path.join(MO_DIR, '*', 'migasfree-client.mo')):
            lang = os.path.basename(os.path.dirname(mo))
            dest = os.path.join('share', 'locale', lang, 'LC_MESSAGES')
            data_files.append((dest, [mo]))

        return data_files

setup(
    name         = 'migasfree-client',
    version      = VERSION,
    description  = 'migasfree-client rewritten in Python',
    long_description = README,
    license      = 'GPLv3',
    author       = 'Jose Antonio Chavarría',
    author_email = 'jachavar@gmail.com',
    url          = 'http://www.migasfree.org/',
    platforms    = ['Linux'],
    packages     = ['migasfree_client', 'migasfree_client.backends'],
    package_dir  = {
        'migasfree_client': 'migasfree_client',
        'migasfree_client.backends': 'migasfree_client/backends'
    },
    cmdclass     = {
        'build': BuildData,
        'install_data': InstallData,
    },
    data_files   = [
        ('/etc', ['conf/migasfree.conf']),
        ('/usr/share/icons/hicolor/scalable/actions', ['icons/scalable/migasfree-ok.svg']),
        ('/usr/share/icons/hicolor/scalable/apps', ['icons/scalable/migasfree.svg']),
        ('/usr/share/applications', ['launcher/migasfree-client.desktop']),
        ('/usr/share/doc/migasfree-client', [
            'AUTHORS',
            'INSTALL',
            'LICENSE',
            'MANIFEST.in',
            'README',
            'TODO',
            'migasfree-client.doap'
        ]),
    ],
    scripts = [
        'bin/migasfree',
        'bin/migasfree-upload',
    ],
    # http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers  = [
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
    requires = _requires,
)
