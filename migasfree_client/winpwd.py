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

"""
Windows implementation of pwd module functions.

This module provides equivalent functionality to the Unix pwd module
for Windows systems, using the win32net API.

The returned structure mimics pwd.struct_passwd:
    [0] pw_name:   Login name
    [1] pw_passwd: Optional encrypted password (always 'x')
    [2] pw_uid:    Numerical user ID (SID string on Windows)
    [3] pw_gid:    Numerical group ID (empty on Windows)
    [4] pw_gecos:  User name or comment (full name)
    [5] pw_dir:    User home directory
    [6] pw_shell:  User command interpreter
"""

import os

import win32api
import win32net
import win32security

__author__ = 'Jose Antonio Chavarría'
__license__ = 'GPLv3'


class struct_passwd:  # noqa: N801
    """
    Structure similar to pwd.struct_passwd for Windows compatibility.
    """

    def __init__(self, pw_name, pw_passwd, pw_uid, pw_gid, pw_gecos, pw_dir, pw_shell):
        self.pw_name = pw_name
        self.pw_passwd = pw_passwd
        self.pw_uid = pw_uid
        self.pw_gid = pw_gid
        self.pw_gecos = pw_gecos
        self.pw_dir = pw_dir
        self.pw_shell = pw_shell

    def __iter__(self):
        return iter(
            [
                self.pw_name,
                self.pw_passwd,
                self.pw_uid,
                self.pw_gid,
                self.pw_gecos,
                self.pw_dir,
                self.pw_shell,
            ]
        )

    def __getitem__(self, index):
        return list(self)[index]

    def __repr__(self):
        return (
            f"struct_passwd(pw_name='{self.pw_name}', pw_passwd='{self.pw_passwd}', "
            f"pw_uid='{self.pw_uid}', pw_gid='{self.pw_gid}', pw_gecos='{self.pw_gecos}', "
            f"pw_dir='{self.pw_dir}', pw_shell='{self.pw_shell}')"
        )


def _get_user_sid(username):
    """
    Get the SID string for a given username.

    Args:
        username: The username to look up.

    Returns:
        The SID string or empty string if not found.
    """
    try:
        sid, _, _ = win32security.LookupAccountName(None, username)
        return win32security.ConvertSidToStringSid(sid)
    except Exception:
        return ''


def _get_username_from_sid(sid_string):
    """
    Get the username from a SID string.

    Args:
        sid_string: The SID string to look up.

    Returns:
        The username or None if not found.
    """
    try:
        sid = win32security.ConvertStringSidToSid(sid_string)
        name, _, _ = win32security.LookupAccountSid(None, sid)
        return name
    except Exception:
        return None


def _get_user_home(username):
    """
    Get the home directory for a user.

    Args:
        username: The username to look up.

    Returns:
        The home directory path.
    """
    # For current user, use environment variable
    current_user = os.environ.get('USERNAME', '')
    if username.lower() == current_user.lower():
        return os.environ.get('USERPROFILE', '')

    # For other users, construct the path
    users_dir = os.path.dirname(os.environ.get('USERPROFILE', 'C:\\Users'))
    return os.path.join(users_dir, username)


def getpwuid(uid):
    """
    Return the password database entry for the given numeric user ID.

    On Windows, the UID is treated as a SID string.

    Args:
        uid: User ID (SID string on Windows).

    Returns:
        struct_passwd: Password database entry.

    Raises:
        KeyError: If the user is not found.
    """
    if isinstance(uid, int):
        # On Windows, we can't look up users by numeric ID
        # Try to get the current user instead
        try:
            username = win32api.GetUserName()
            return getpwnam(username)
        except Exception as e:
            raise KeyError(f'getpwuid(): uid not found: {uid}') from e

    # Treat uid as SID string
    username = _get_username_from_sid(str(uid))
    if username is None:
        raise KeyError(f'getpwuid(): uid not found: {uid}')

    return getpwnam(username)


def getpwnam(name):
    """
    Return the password database entry for the given user name.

    Args:
        name: Username to look up.

    Returns:
        struct_passwd: Password database entry.

    Raises:
        KeyError: If the user is not found.
    """
    try:
        info = win32net.NetUserGetInfo(None, name, 11)
        pw_name = info.get('name', name)
        pw_gecos = info.get('full_name', '')
        pw_uid = _get_user_sid(pw_name)
    except win32net.error:
        # User might exist but not accessible via NetUserGetInfo
        # (e.g., domain users, system accounts)
        pw_name = name
        pw_gecos = name
        pw_uid = _get_user_sid(name)
        if not pw_uid:
            raise KeyError(f'getpwnam(): name not found: {name}')  # noqa: B904

    pw_dir = _get_user_home(pw_name)
    pw_shell = os.environ.get('COMSPEC', 'C:\\Windows\\System32\\cmd.exe')

    return struct_passwd(
        pw_name=pw_name,
        pw_passwd='x',
        pw_uid=pw_uid,
        pw_gid='',
        pw_gecos=pw_gecos,
        pw_dir=pw_dir,
        pw_shell=pw_shell,
    )


def getpwall():
    """
    Return a list of all available password database entries.

    Returns:
        list: List of struct_passwd objects for all local users.
    """
    users = []
    resume_handle = 0

    try:
        while True:
            user_list, _total, resume_handle = win32net.NetUserEnum(
                None,  # Server name (None = local)
                0,  # Level (0 = basic info)
                0,  # Filter (0 = all users)
                resume_handle,  # Resume handle
            )

            for user_info in user_list:
                try:
                    username = user_info['name']
                    users.append(getpwnam(username))
                except (KeyError, Exception):
                    # Skip users that can't be fully resolved
                    pass

            if resume_handle == 0:
                break
    except win32net.error:
        # If NetUserEnum fails, return at least the current user
        try:
            current_user = win32api.GetUserName()
            users.append(getpwnam(current_user))
        except Exception:
            pass

    return users
