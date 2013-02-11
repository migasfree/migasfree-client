#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Copyright (c) 2011-2013 Jose Antonio Chavarría
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

__author__ = 'Jose Antonio Chavarría'
__file__ = 'utils.py'
__date__ = '2013-01-26'

import subprocess
import os
import sys
import ConfigParser
import commands
import time
import difflib
import pwd
import platform
import errno
import re
import fcntl
import select

import gettext
_ = gettext.gettext

# TODO http://docs.python.org/library/unittest.html


def get_config(ini_file, section):
    '''
    int/dict get_config(string ini_file, string section)
    '''

    if not os.path.isfile(ini_file):
        return errno.ENOENT  # FILE_NOT_FOUND

    try:
        config = ConfigParser.RawConfigParser()
        config.read(ini_file)

        return dict(config.items(section))
    except:
        return errno.ENOMSG  # INVALID_DATA


def execute(cmd, verbose=False, interactive=True):
    '''
    (int, string, string) execute(string cmd, bool verbose = False, bool interactive = True)
    '''

    if verbose:
        print(cmd)

    if interactive:
        _process = subprocess.Popen(
            cmd,
            shell=True,
            executable='/bin/bash'
        )
    else:
        _process = subprocess.Popen(
            cmd,
            shell=True,
            executable='/bin/bash',
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE
        )

        _output_buffer = ''
        if verbose:
            fcntl.fcntl(
                _process.stdout.fileno(),
                fcntl.F_SETFL,
                fcntl.fcntl(_process.stdout.fileno(), fcntl.F_GETFL) | os.O_NONBLOCK,
            )

            while _process.poll() is None:
                readx = select.select([_process.stdout.fileno()], [], [])[0]
                if readx:
                    chunk = _process.stdout.read()
                    if chunk and chunk != '\n':
                        print(chunk)
                    _output_buffer = '%s%s' % (_output_buffer, chunk)

        '''
        # simple progress indicator
        # does not work with some commands (lshw, getting repositories...)
        if progress:
            while True:
                _output = _process.stdout.readline()
                sys.stdout.write('.')
                sys.stdout.flush()

                if not _output:
                    break
        '''

        '''
        while True:
            _out = _process.stdout.read(1)
            if _out == '' and _process.poll() != None:
                break
            if _out != '':
                sys.stdout.write(_out)
                sys.stdout.flush()
        '''

    _output, _error = _process.communicate()

    if not interactive and _output_buffer:
        _output = _output_buffer

    return (_process.returncode, _output, _error)


def get_hostname():
    '''
    string get_hostname(void)
    Returns only hostname (without domain)
    '''

    return platform.node().split('.')[0]


def get_graphic_pid():
    '''
    list get_graphic_pid(void)
    Detects Gnome, KDE, Xfce, Xfce4, LXDE
    '''

    _graphic_environments = [
        'gnome-session',    # Gnome
        'ksmserver',        # KDE
        'xfce-mcs-manage',  # Xfce
        'xfce4-session',    # Xfce4
        'lxsession'         # LXDE
    ]
    for _process in _graphic_environments:
        _pid = commands.getoutput('pidof %s' % _process)
        if _pid != '':
            # sometimes the command pidof return multiples pids, then we use the last pid
            _pid_list = _pid.split(' ')

            return [_pid_list.pop(), _process]

    return [None, None]


def get_graphic_user(pid):
    '''
    string get_graphic_user(int pid)
    '''

    _user = commands.getoutput('ps hp %s -o %s' % (str(pid), '"%U"'))
    if _user.isdigit():
        # ps command not always show username (show uid if len(username) > 8)
        return get_user_info(_user)['name']

    return _user


def grep(string, list_strings):
    '''
    http://casa.colorado.edu/~ginsbura/pygrep.htm
    py grep command
    sample command: grep("^x",dir())
    syntax: grep(regexp_string, list_of_strings_to_search)
    '''

    expr = re.compile(string)
    return [elem for elem in list_strings if expr.match(elem)]


def get_user_display_graphic(pid, timeout=10, interval=1):
    '''
    string get_user_display_graphic(string pid, int timeout = 10, int interval = 1)
    '''

    _display = []
    while not _display and timeout > 0:
        # a data line ends in 0 byte, not newline
        _display = grep(
            'DISPLAY',
            open("/proc/%s/environ" % pid).read().split('\0')
        )
        if _display:
            _display = _display[0].split('=').pop()
            return _display

        time.sleep(interval)
        timeout -= interval

    if not _display:
        _display = ':0.0'

    return _display


def compare_lists(a, b):
    '''
    list compare_lists(list a, list b)
    returns ordered diff list
    '''

    _result = list(difflib.unified_diff(a, b, n=0))
    # clean lines... (only package lines are important)
    # http://docs.python.org/tutorial/controlflow.html#for-statements
    for _line in _result[:]:
        if _line.startswith('+++') or _line.startswith('---') \
        or _line.startswith('@@'):
            _result.remove(_line)

    return sorted(_result)


def compare_files(a, b):
    '''
    list compare_files(a, b)
    returns ordered diff list
    '''

    if not os.path.isfile(a) or not os.path.isfile(b):
        return None

    # U - open for input as a text file with universal newline interpretation
    # http://www.python.org/dev/peps/pep-0278/
    _list_a = open(a, 'U').readlines()
    _list_b = open(b, 'U').readlines()

    return compare_lists(_list_a, _list_b)


def get_user_info(user):
    '''
    bool/list get_user_info(string user)
    '''

    try:
        _info = pwd.getpwnam(user)
    except KeyError:
        try:
            _info = pwd.getpwuid(int(user))
        except:
            return False

    return {
        'name': _info[0],
        'pwd': _info[1],  # if 'x', encrypted
        'uid': _info[2],
        'gid': _info[3],
        'fullname': _info[4],
        'home': _info[5],
        'shell': _info[6]
    }


def write_file(filename, content):
    '''
    bool write_file(string filename, string content)
    '''

    _file = None
    try:
        _file = open(filename, 'wb')
        _file.write(content)
        _file.flush()
        os.fsync(_file.fileno())
        _file.close()

        return True
    except IOError:
        return False
    finally:
        if _file is not None:
            _file.close()


def remove_file(archive):
    if os.path.isfile(archive):
        os.remove(archive)


# based in http://code.activestate.com/recipes/577058/
def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is one of "yes" or "no".
    """
    valid = {
        _("yes"): "yes", _("y"): "yes",
        _("no"): "no", _("n"): "no"
    }
    if default is None:
        prompt = ' %s ' % _("[y/n]")
    elif default == "yes":
        prompt = ' %s ' % _("[Y/n]")
    elif default == "no":
        prompt = ' %s ' % _("[y/N]")
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while 1:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return default
        elif choice in valid.keys():
            return valid[choice]
        else:
            print(_("Please respond with 'yes' or 'no' (or 'y' or 'n')."))


def check_lock_file(cmd, lock_file):
    if os.path.isfile(lock_file):
        _file = None
        try:
            _file = open(lock_file, 'r')
            _pid = _file.read()
        except IOError:
            pass
        finally:
            if _file is not None:
                _file.close()

        if not _pid:
            _pid = -1
        else:
            _pid = int(_pid)

        try:
            if os.getsid(_pid):
                print(_('Another instance of %(cmd)s is running: %(pid)d') % {
                    'cmd': cmd,
                    'pid': int(_pid)
                })
                sys.exit(errno.EPERM)
        except OSError:
            pass
    else:
        write_file(lock_file, str(os.getpid()))


def get_current_user():
    '''
    string get_current_user(void)
    returns a string in format 'name~fullname'
    '''

    _graphic_pid, _graphic_process = get_graphic_pid()
    if not _graphic_pid:
        _graphic_user = os.environ['USER']
    else:
        _graphic_user = get_graphic_user(_graphic_pid)

    _info = get_user_info(_graphic_user)
    if not _info:
        _fullname = ''
    else:
        _fullname = _info['fullname']

    return '%s~%s' % (_graphic_user, _fullname)


def get_mfc_version():
    from . import settings

    _config = get_config(settings.CONF_FILE, 'client')
    if type(_config) is dict and 'version' in _config:
        return _config.get('version')

    return '-'.join(platform.linux_distribution()[0:2])  # if not set
