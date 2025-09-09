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

__author__ = 'Jose Antonio Chavarría'
__license__ = 'GPLv3'

if os.environ.get('WINDIR'):
    import sysconfig

    windir_path = os.environ.get('WINDIR')
    program_data_path = os.environ.get('PROGRAMDATA')
    data_path = os.path.join(sysconfig.get_paths()['data'], 'share')

    APP_DATA_PATH = os.path.join(program_data_path, 'migasfree-client')
    DOC_PATH = os.path.join(data_path, 'doc')
    KEYS_PATH = os.path.join(APP_DATA_PATH, 'keys')
    DEVICES_PATH = os.path.join(APP_DATA_PATH, 'devices')
    TMP_PATH = os.path.join(windir_path, 'temp')
    ICON_PATH = os.path.join(data_path, 'icons', 'hicolor', 'scalable')
    LOCALE_PATH = os.path.join(data_path, 'locale')

    CONF_FILE = os.environ.get('MIGASFREE_CONF', os.path.join(APP_DATA_PATH, 'migasfree.conf'))

    LOG_FILE = os.path.join(TMP_PATH, 'migasfree.log')
    SOFTWARE_FILE = os.path.join(APP_DATA_PATH, 'installed_software.txt')
    TRAITS_FILE = os.path.join(APP_DATA_PATH, 'computer_traits.json')
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
    TRAITS_FILE = '/var/tmp/computer_traits.json'

PRE_SYNC_PATH = os.path.join(APP_DATA_PATH, 'pre-sync.d')
POST_SYNC_PATH = os.path.join(APP_DATA_PATH, 'post-sync.d')
EVENTS_SYNC_PATH = os.path.join(APP_DATA_PATH, 'events.d')
EVENTS_ENV_FILE = os.path.join(EVENTS_SYNC_PATH, '.env')
EVENTS_JSON_FILE = os.path.join(EVENTS_SYNC_PATH, '.json')

CERT_FILE = os.path.join(TMP_PATH, 'cert.pem')

JSON_INDENT = 4
