# Copyright (c) 2021-2025 Jose Antonio Chavarría <jachavar@gmail.com>
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

# import ctypes
# import getpass
import win32net

__author__ = 'Jose Antonio Chavarría'
__license__ = 'GPLv3'


def getpwuid(uid):
    return False  # TODO


def getpwnam(name):
    try:
        _info = win32net.NetUserGetInfo(None, name, 11)  # TODO using ctypes
        _name = _info['name']
        _fullname = _info['full_name']
    except Exception:
        _name = 'NoName'
        _fullname = 'NoFullName'

    _home = os.environ.get('USERPROFILE', '')
    _shell = os.environ.get('COMSPEC', '')

    return [
        _name,
        'x',
        '',  # uid does not exist in Windows
        '',  # gid does not exist in Windows
        _fullname,
        _home,
        _shell,
    ]


def getpwall():
    return []  # TODO
