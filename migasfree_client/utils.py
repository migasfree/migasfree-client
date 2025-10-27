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
import sys
import subprocess
import time
import difflib
import pwd
import platform
import errno
import re
import fcntl
import select
import uuid
import signal
import hashlib

if sys.version_info[0] <= 2:
    import commands
else:
    import subprocess as commands

try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser

from . import network, settings

import gettext

_ = gettext.gettext

__author__ = 'Jose Antonio Chavarría'
__license__ = 'GPLv3'

# TODO http://docs.python.org/library/unittest.html


def slugify(s):
    """
    https://blog.dolphm.com/slugify-a-string-in-python/
    Simplifies ugly strings into something URL-friendly.
    """

    s = s.lower()

    for c in [' ', '-', '.', '/']:
        s = s.replace(c, '_')

    s = re.sub(r'\W', '', s)
    s = s.replace('_', ' ')
    s = re.sub(r'\s+', ' ', s)
    s = s.strip()
    s = s.replace(' ', '-')

    return s


def get_config(ini_file, section):
    """
    int/dict get_config(string ini_file, string section)
    """

    if not os.path.isfile(ini_file):
        return errno.ENOENT  # FILE_NOT_FOUND

    try:
        config = ConfigParser.RawConfigParser()
        config.read(ini_file)

        return dict(config.items(section))
    except:
        return errno.ENOMSG  # INVALID_DATA


def remove_commented_lines(text):
    ret = []

    lines = text.split('\n')
    for line in lines:
        if not re.match(r'^([^#]*)#(.*)$', line):
            ret.append(line)

    return '\n'.join(ret)


def execute(cmd, verbose=False, interactive=True):
    """
    (int, string, string) execute(
        string cmd,
        bool verbose=False,
        bool interactive=True
    )
    """

    _output_buffer = ''

    if verbose:
        print(cmd)

    if interactive:
        _process = subprocess.Popen(cmd, shell=True, executable='/bin/bash')
    else:
        _process = subprocess.Popen(
            cmd, shell=True, executable='/bin/bash', stderr=subprocess.PIPE, stdout=subprocess.PIPE
        )

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
                    if isinstance(chunk, bytes) and not isinstance(chunk, str):
                        chunk = str(chunk, encoding='utf8')
                    if chunk and chunk != '\n':
                        print(chunk)
                    _output_buffer = '%s%s' % (_output_buffer, chunk)

    _output, _error = _process.communicate()

    if not interactive and _output_buffer:
        _output = _output_buffer

    if isinstance(_output, bytes) and not isinstance(_output, str):
        _output = str(_output, encoding='utf8')
    if isinstance(_error, bytes) and not isinstance(_error, str):
        _error = str(_error, encoding='utf8')

    return _process.returncode, _output, _error


def timeout_execute(cmd, timeout=60):
    # based in http://amix.dk/blog/post/19408

    _process = subprocess.Popen(cmd, shell=True, executable='/bin/bash', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if timeout > 0:
        _seconds_elapsed = 0
        _interval = 0.2
        while _process.poll() is None:
            time.sleep(_interval)
            _seconds_elapsed += _interval

            if _seconds_elapsed > timeout:
                os.kill(_process.pid, signal.SIGKILL)
                os.waitpid(-1, os.WNOHANG)
                return 1, '', _('"%s" command expired timeout') % cmd

    _output, _error = _process.communicate()

    if isinstance(_output, bytes) and not isinstance(_output, str):
        _output = str(_output, encoding='utf8')
    if isinstance(_error, bytes) and not isinstance(_error, str):
        _error = str(_error, encoding='utf8')

    return _process.returncode, _output, _error


def get_hostname():
    """
    string get_hostname(void)
    Returns only hostname (without domain)
    """

    return platform.node().split('.')[0]


def get_graphic_pid():
    """
    list get_graphic_pid(void)
    Detects desktop environment and returns [PID, environment_name] if found
    """

    _graphic_environments = [
        'gnome-session-binary',  # Gnome & Unity
        'gnome-session',  # Gnome
        'ksmserver',  # KDE
        'xfce-mcs-manage',  # Xfce
        'xfce4-session',  # Xfce4
        'lxsession',  # LXDE
        'lxqt-session',  # LXQt
        'mate-session',  # MATE
        'cinnamon-session',  # Cinnamon
        'cinnamon-session-binary',  # Cinnamon
        'cosmic-session',  # Cosmic (Pop OS!)
        'enlightenment',  # Enlightenment
        'pantheon',  # Pantheon (elementary OS)
        'deepin',  # Deepin
        'budgie-desktop',  # Budgie (Linux Mint)
        'sway',  # Sway (Wayland)
        'i3',  # i3 (Tiling WM)
        'openbox',  # Openbox
        'awesome',  # Awesome WM
        'fluxbox',  # Fluxbox
        'herbstluftwm',  # Herbstluftwm
        'lumina',  # Lumina (LightDM)
        'xmonad',  # XMonad
        'dwm',  # DWM
        'stumpwm',  # StumpWM
        'windowmaker',  # WindowMaker
        'jwm',  # JWM
    ]

    for _process in _graphic_environments:
        _pid = commands.getoutput('pidof -s {0}'.format(_process))
        if _pid:
            return [_pid, _process]

    return [None, None]


def get_graphic_user(pid=0):
    """
    string get_graphic_user(int pid=0)
    """

    if not pid:
        pid = get_graphic_pid()[0]
        if not pid:
            return ''

    _user = commands.getoutput('ps hp {0} -o euser'.format(pid))
    if _user.isdigit():
        # ps command not always show username (show uid if len(username) > 8)
        _user_info = get_user_info(_user)
        if _user_info is False:  # p.e. chroot environment
            return 'root'

        return _user_info['name']

    return _user.strip()


def grep(string, list_strings):
    """
    http://casa.colorado.edu/~ginsbura/pygrep.htm
    py grep command
    sample command: grep("^x", dir())
    syntax: grep(regexp_string, list_of_strings_to_search)
    """

    expr = re.compile(string)
    return [elem for elem in list_strings if expr.match(elem)]


def get_user_display_graphic(pid, timeout=10, interval=1):
    """
    string get_user_display_graphic(
        string pid,
        int timeout=10,
        int interval=1
    )
    """

    _display = []
    while not _display and timeout > 0:
        # a data line ends in 0 byte, not newline
        _display = grep('DISPLAY', open('/proc/{0}/environ'.format(pid)).read().split('\0'))
        if _display:
            _display = _display[0].split('=').pop()
            return _display

        time.sleep(interval)
        timeout -= interval

    if not _display:
        _display = ':0.0'

    return _display


def compare_lists(a, b):
    """
    list compare_lists(list a, list b)
    returns ordered diff list
    """

    _result = list(difflib.unified_diff(a, b, n=0))
    # clean lines... (only package lines are important)
    # http://docs.python.org/tutorial/controlflow.html#for-statements
    for _line in _result[:]:
        if _line.startswith('+++') or _line.startswith('---') or _line.startswith('@@'):
            _result.remove(_line)

    return sorted(_result)


def compare_files(a, b):
    """
    list compare_files(a, b)
    returns ordered diff list
    """

    if not os.path.isfile(a) or not os.path.isfile(b):
        return None

    _list_a = open(a).readlines()
    _list_b = open(b).readlines()

    return compare_lists(_list_a, _list_b)


def get_user_info(user):
    """
    bool/list get_user_info(string user)
    """

    try:
        _info = pwd.getpwnam(user)
    except KeyError:
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


def write_file(filename, content):
    """
    bool write_file(string filename, string content)
    """

    _dir = os.path.dirname(filename)
    if not os.path.exists(_dir):
        try:
            os.makedirs(_dir, 0o777)
        except OSError:
            return False

    _file = None
    try:
        _file = open(filename, 'wb')
        if sys.version_info[0] < 3:
            _file.write(content)
        else:
            try:
                _file.write(bytes(content))
            except TypeError:
                _file.write(bytes(content, encoding='utf8'))
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


def query_yes_no(question, default='yes'):
    """
    based in http://code.activestate.com/recipes/577058/

    Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is one of "yes" or "no".
    """
    valid = {_('yes'): 'yes', _('y'): 'yes', _('no'): 'no', _('n'): 'no'}
    if default is None:
        prompt = ' %s ' % _('[y/n]')
    elif default == 'yes':
        prompt = ' %s ' % _('[Y/n]')
    elif default == 'no':
        prompt = ' %s ' % _('[y/N]')
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while 1:
        sys.stdout.write(question + prompt)
        if sys.version_info[0] < 3:
            choice = raw_input().lower()
        else:
            choice = input().lower()
        if default is not None and choice == '':
            return default
        if choice in valid.keys():
            return valid[choice]

        print(_("Please respond with 'yes' or 'no' (or 'y' or 'n')."))


def check_lock_file(cmd, lock_file):
    _pid = 0

    if os.path.isfile(lock_file):
        _file = None
        try:
            _file = open(lock_file)
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
                print(_('Another instance of %(cmd)s is running: %(pid)d') % {'cmd': cmd, 'pid': int(_pid)})
                sys.exit(errno.EPERM)
        except OSError:
            pass
    else:
        write_file(lock_file, str(os.getpid()))


def get_current_user():
    """
    string get_current_user(void)
    returns a string in format 'name~fullname'
    """

    _graphic_pid, _ = get_graphic_pid()
    if not _graphic_pid:
        _graphic_user = os.environ.get('USER')
    else:
        _graphic_user = get_graphic_user(_graphic_pid)

    _info = get_user_info(_graphic_user)
    if not _info:
        _fullname = ''
    else:
        _fullname = _info['fullname']

    return '{0}~{1}'.format(_graphic_user, _fullname)


def get_distro_project():
    try:
        import distro

        project = '{0}-{1}'.format(distro.name(), distro.version())
    except ImportError:
        project = '-'.join(platform.linux_distribution()[0:2])

    return slugify(project)


def get_distro_name():
    try:
        import distro

        name = distro.name()
    except ImportError:
        name = platform.linux_distribution()[0]

    return slugify(name.strip().split()[0])


def get_distro_major_version():
    try:
        import distro

        major_version = distro.version()
    except ImportError:
        major_version = platform.linux_distribution()[1]

    return major_version.strip().split('.')[0]


def get_mfc_project():
    _config = get_config(settings.CONF_FILE, 'client')

    if isinstance(_config, dict) and 'project' in _config:
        return _config.get('project')

    # backwards compatibility
    if isinstance(_config, dict) and 'version' in _config:
        return _config.get('version')

    # if not set
    return get_distro_project()


def get_mfc_version():
    # backwards compatibility method
    return get_mfc_project()


def get_mfc_computer_name():
    _config = get_config(settings.CONF_FILE, 'client')
    if isinstance(_config, dict) and 'computer_name' in _config:
        return _config.get('computer_name')

    return get_hostname()  # if not set


def get_smbios_version():
    # issue #33
    _ret, _smbios, _ = execute('LC_ALL=C sudo dmidecode -t 0 | grep SMBIOS | grep present', interactive=False)
    if _ret != 0 or _smbios == '' or _smbios is None:
        return 0, 0

    _smbios = _smbios.split()[1]  # expected: "SMBIOS x.x present."
    return tuple(int(x) for x in _smbios.split('.'))


def get_uuid_from_mac():
    return '00000000-0000-0000-0000-{0}'.format(network.get_first_mac())


def get_hardware_uuid():
    _uuid_format = '%s%s%s%s-%s%s-%s%s-%s-%s'

    # issue #16, issue #28
    _ret, _uuid, _ = execute('sudo dmidecode --string system-uuid', interactive=False)
    _uuid = remove_commented_lines(_uuid)  # issue #75
    _uuid = _uuid.replace('\n', '')
    if _ret != 0 or _uuid == '' or _uuid is None:
        return get_uuid_from_mac()

    try:
        _byte_array = uuid.UUID(_uuid).hex
    except ValueError:
        return get_uuid_from_mac()

    # issue #33
    if get_smbios_version() >= (2, 6):
        _ms_uuid = _uuid_format % (
            _byte_array[0:2],
            _byte_array[2:4],
            _byte_array[4:6],
            _byte_array[6:8],
            _byte_array[8:10],
            _byte_array[10:12],
            _byte_array[12:14],
            _byte_array[14:16],
            _byte_array[16:20],
            _byte_array[20:32],
        )
    else:
        # http://stackoverflow.com/questions/10850075/guid-uuid-compatibility-issue-between-net-and-linux
        _ms_uuid = _uuid_format % (
            _byte_array[6:8],
            _byte_array[4:6],
            _byte_array[2:4],
            _byte_array[0:2],
            _byte_array[10:12],
            _byte_array[8:10],
            _byte_array[14:16],
            _byte_array[12:14],
            _byte_array[16:20],
            _byte_array[20:32],
        )

    _ms_uuid = _ms_uuid.upper()

    # exceptions (issue #4)
    if _ms_uuid == '03000200-0400-0500-0006-000700080009':  # ASRock
        _ms_uuid = get_uuid_from_mac()

    return _ms_uuid


def cast_to_bool(value, default=False):
    if str(value).lower() in ['false', 'off', 'no', 'n', '0']:
        return False

    if str(value).lower() in ['true', 'on', 'yes', 'y', '1']:
        return True

    return default


def is_xsession():
    return os.environ.get('DISPLAY') is not None


def is_zenity():
    _ret, _, _ = execute('which zenity', interactive=False)
    return _ret == 0


def get_mfc_release():
    from . import __version__

    return __version__


def md5sum(archive):
    if not archive:
        return ''

    with open(archive) as handle:
        _md5 = handle.read()
        if sys.version_info[0] > 2:
            _md5 = _md5.encode()

    return hashlib.md5(_md5).hexdigest()


def which(cmd):
    paths = os.environ.get('PATH', '').split(os.pathsep)
    for path in paths:
        full_path = os.path.join(path, cmd)
        if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
            return full_path

    return None
