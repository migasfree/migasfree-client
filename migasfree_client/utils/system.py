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

import os
import platform
import sys

try:
    import pwd
except ImportError:
    from .. import winpwd as pwd


def is_windows():
    return sys.platform == 'win32'


def is_linux():
    return sys.platform == 'linux'


def get_hostname():
    """
    string get_hostname(void)
    Returns only hostname (without domain)
    """
    return platform.node().split('.')[0]


def get_user_info(user):
    """
    bool/list get_user_info(string user)
    """
    try:
        _info = pwd.getpwnam(user)
    except (KeyError, TypeError):
        try:
            _info = pwd.getpwuid(int(user))
        except KeyError:
            return False

    return {
        'name': _info[0],
        'pwd': _info[1],  # if 'x', encrypted
        'uid': _info[2],
        'gid': _info[3],
        # http://en.wikipedia.org/wiki/Gecos_field
        'fullname': _info[4].split(',', 1)[0],
        'home': _info[5],
        'shell': _info[6],
    }


def is_root_user():
    if is_windows():
        import ctypes

        return ctypes.windll.shell32.IsUserAnAdmin() != 0

    user_info = get_user_info(os.getuid())
    if not isinstance(user_info, dict):
        return False

    return user_info.get('gid') == 0


def slugify(s):
    """
    https://blog.dolphm.com/slugify-a-string-in-python/
    Simplifies ugly strings into something URL-friendly.
    """
    import re

    s = s.lower()

    for c in [' ', '-', '.', '/']:
        s = s.replace(c, '_')

    s = re.sub(r'\W', '', s)
    s = s.replace('_', ' ')
    s = re.sub(r'\s+', ' ', s)
    s = s.strip()
    s = s.replace(' ', '-')

    return s


def get_distro_project():
    if is_windows():
        return slugify(f'{platform.system()}-{platform.version()}')

    import distro

    return slugify(f'{distro.name()}-{distro.version()}')


def get_distro_name():
    if is_windows():
        return slugify(platform.system())

    import distro

    return slugify(distro.name().strip().split()[0])
