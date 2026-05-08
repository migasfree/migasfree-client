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

import configparser
import difflib
import errno
import os
import re

from .system import is_windows


def sanitize_path(value):
    """
    Sanitize a path to prevent directory traversal and remove invalid characters.
    """
    # Remove directory traversal sequences
    value = value.replace('..', '')

    # Normalize slashes to current OS
    value = os.path.normpath(value)

    # Remove leading separators to prevent absolute paths
    while value.startswith(os.sep):
        value = value[1:]

    if is_windows():
        return (
            value.replace('\\', '_')
            .replace('/', '_')
            .replace(':', '_')
            .replace('?', '_')
            .replace('"', '_')
            .replace('|', '_')
        )

    return value


def get_config(ini_file, section):
    """
    int/dict get_config(string ini_file, string section)
    """
    if not os.path.isfile(ini_file):
        return errno.ENOENT  # FILE_NOT_FOUND

    try:
        config = configparser.RawConfigParser()
        config.read(ini_file)

        return dict(config.items(section))
    except configparser.Error:
        return errno.ENOMSG  # INVALID_DATA


def remove_commented_lines(text):
    lines = text.split('\n')
    result = [line for line in lines if not re.match(r'^([^#]*)#(.*)$', line)]

    return '\n'.join(result)


def _bytes_to_str(data):
    """Convert bytes to string with UTF-8 encoding, fallback to str() on error."""
    if data is None:
        return ''
    if isinstance(data, bytes) and not isinstance(data, str):
        try:
            return str(data, encoding='utf8')
        except UnicodeDecodeError:
            return str(data)
    return data


def grep(string, list_strings):
    """
    http://casa.colorado.edu/~ginsbura/pygrep.htm
    py grep command
    sample command: grep("^x", dir())
    syntax: grep(regexp_string, list_of_strings_to_search)
    """
    expr = re.compile(string)
    return [elem for elem in list_strings if expr.match(elem)]


def compare_lists(a, b):
    """
    list compare_lists(list a, list b)
    returns ordered diff list
    """
    _result = [line for line in difflib.unified_diff(a, b, n=0) if not line.startswith(('+++', '---', '@@'))]

    return sorted(_result)


def cast_to_bool(value, default=False):
    if str(value).lower() in ['false', 'off', 'no', 'n', '0']:
        return False

    if str(value).lower() in ['true', 'on', 'yes', 'y', '1']:
        return True

    return default


def escape_quotes(text):
    return text.replace('"', '\\"')
