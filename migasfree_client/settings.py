# -*- coding: UTF-8 -*-

# Copyright (c) 2011-2021 Jose Antonio Chavarría <jachavar@gmail.com>
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

__author__ = 'Jose Antonio Chavarría'
__license__ = 'GPLv3'

if os.environ.get('WINDIR'):
    windir_path = os.environ.get('WINDIR')
    program_data_path = os.environ.get('PROGRAMDATA')

    APP_DATA_PATH = '{}\\migasfree-client'.format(program_data_path)
    DOC_PATH = '{}\\doc'.format(APP_DATA_PATH)
    KEYS_PATH = '{}\\keys'.format(APP_DATA_PATH)
    DEVICES_PATH = '{}\\devices'.format(APP_DATA_PATH)
    TMP_PATH = '{}\\temp'.format(windir_path)
    ICON_PATH = '{}\\icons'.format(APP_DATA_PATH)
    LOCALE_PATH = '{}\\locale'.format(APP_DATA_PATH)

    CONF_FILE = os.environ.get('MIGASFREE_CONF', '{}\\migasfree.conf'.format(APP_DATA_PATH))

    LOG_FILE = '{}\\logs\\migasfree.log'.format(TMP_PATH)
    SOFTWARE_FILE = '{}\\installed_software.txt'.format(APP_DATA_PATH)
else:
    APP_DATA_PATH = '/usr/share/migasfree-client'
    DOC_PATH = '/usr/share/doc/migasfree-client'
    KEYS_PATH = '/var/migasfree-client/keys'
    DEVICES_PATH = '/var/migasfree-client/devices'
    TMP_PATH = '/tmp/migasfree-client'
    ICON_PATH = '/usr/share/icons/hicolor/scalable'
    LOCALE_PATH = '/usr/share/locale'

    CONF_FILE = os.environ.get('MIGASFREE_CONF', '/etc/migasfree.conf')

    LOG_FILE = '/var/tmp/migasfree.log'
    SOFTWARE_FILE = '/var/tmp/installed_software.txt'

PRE_SYNC_PATH = os.path.join(APP_DATA_PATH, 'pre-sync.d')
POST_SYNC_PATH = os.path.join(APP_DATA_PATH, 'post-sync.d')

CERT_FILE = os.path.join(TMP_PATH, 'cert.pem')
