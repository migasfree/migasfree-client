#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Copyright (c) 2011-2018 Jose Antonio Chavarría <jachavar@gmail.com>
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

CONF_FILE = os.environ.get('MIGASFREE_CONF', '/etc/migasfree.conf')

LOG_FILE = '/var/tmp/migasfree.log'
SOFTWARE_FILE = '/var/tmp/installed_software.txt'

KEYS_PATH = '/var/migasfree-client/keys'
DEVICES_PATH = '/var/migasfree-client/devices'
TMP_PATH = '/tmp/migasfree-client'
LOCALE_PATH = '/usr/share/locale'
ICON_PATH = '/usr/share/icons/hicolor/scalable'
DOC_PATH = '/usr/share/doc/migasfree-client'
APP_DATA_PATH = '/usr/share/migasfree-client'
PRE_SYNC_PATH = os.path.join(APP_DATA_PATH, 'pre-sync.d')
POST_SYNC_PATH = os.path.join(APP_DATA_PATH, 'post-sync.d')
