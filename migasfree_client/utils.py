# -*- coding: UTF-8 -*-

# Copyright (c) 2011-2024 Jose Antonio Chavarría <jachavar@gmail.com>
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
import platform
import json
import errno
import re
import select
import uuid
import signal
import gettext
import configparser
import hashlib
import magic

try:
    import pwd
except ImportError:
    from . import winpwd as pwd

from . import settings

__author__ = 'Jose Antonio Chavarría'
__license__ = 'GPLv3'

_ = gettext.gettext

# TODO http://docs.python.org/library/unittest.html

ALL_OK = 0 if sys.platform == 'win32' else os.EX_OK


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


def is_windows():
    return sys.platform == 'win32'


def is_linux():
    return sys.platform == 'linux'


def sanitize_path(value):
    if is_windows():
        return value.replace('\\', '_').replace('/', '_').replace(
            ':', '_'
        ).replace('?', '_').replace('"', '_').replace(
            '|', '_'
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
        if is_windows():
            _process = subprocess.Popen(
                cmd,
                shell=True,
            )
        else:
            _process = subprocess.Popen(
                cmd,
                shell=True,
                executable='/bin/bash'
            )
    else:
        if is_windows():
            _process = subprocess.Popen(
                cmd,
                shell=True,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE
            )
        else:
            _process = subprocess.Popen(
                cmd,
                shell=True,
                executable='/bin/bash',
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE
            )

        if verbose:
            if not is_windows():
                import fcntl

                fcntl.fcntl(
                    _process.stdout.fileno(),
                    fcntl.F_SETFL,
                    fcntl.fcntl(
                        _process.stdout.fileno(),
                        fcntl.F_GETFL
                    ) | os.O_NONBLOCK,
                )

            while _process.poll() is None:
                readx = select.select([_process.stdout.fileno()], [], [])[0]
                if readx:
                    chunk = _process.stdout.read()
                    if isinstance(chunk, bytes) and not isinstance(chunk, str):
                        chunk = str(chunk, encoding='utf8')
                    if chunk and chunk != '\n':
                        print(chunk)
                    _output_buffer = f'{_output_buffer}{chunk}'

    _output, _error = _process.communicate()

    if not interactive and _output_buffer:
        _output = _output_buffer

    if isinstance(_output, bytes) and not isinstance(_output, str):
        try:
            _output = str(_output, encoding='utf8')
        except UnicodeDecodeError:
            _output = str(_output)
    if isinstance(_error, bytes) and not isinstance(_error, str):
        try:
            _error = str(_error, encoding='utf8')
        except UnicodeDecodeError:
            _error = str(_error)

    return _process.returncode, _output, _error


def timeout_execute(cmd, timeout=60):
    # based in http://amix.dk/blog/post/19408

    if is_linux():
        _process = subprocess.Popen(
            cmd,
            shell=True,
            executable='/bin/bash',
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    else:
        _process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

    if timeout > 0:
        _seconds_elapsed = 0
        _interval = 0.2
        while _process.poll() is None:
            time.sleep(_interval)
            _seconds_elapsed += _interval

            if _seconds_elapsed > timeout:
                if is_linux():
                    os.kill(_process.pid, signal.SIGKILL)
                    os.waitpid(-1, os.WNOHANG)
                else:
                    import psutil
                    psutil.Process(_process.pid).kill()

                return 1, '', _('"%s" command expired timeout') % cmd

    _output, _error = _process.communicate()

    if isinstance(_output, bytes) and not isinstance(_output, str):
        try:
            _output = str(_output, encoding='utf8')
        except UnicodeDecodeError:
            _output = str(_output)
    if isinstance(_error, bytes) and not isinstance(_error, str):
        try:
            _error = str(_error, encoding='utf8')
        except UnicodeDecodeError:
            _error = str(_error)

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
    Detects Gnome, KDE, Xfce, Xfce4, LXDE, LXQt, Unity
    """

    _graphic_environments = [
        'gnome-session-binary',  # Gnome & Unity
        'gnome-session',         # Gnome
        'ksmserver',             # KDE
        'xfce-mcs-manage',       # Xfce
        'xfce4-session',         # Xfce4
        'lxsession',             # LXDE
        'lxqt-session',          # LXQt
        'mate-session',          # MATE
    ]
    for _process in _graphic_environments:
        _pid = subprocess.getoutput(f'pidof -s {_process}')
        if _pid:
            return [_pid, _process]

    return [None, None]


def get_graphic_user(pid=0):
    """
    string get_graphic_user(int pid=0)
    """

    if is_windows():
        import getpass

        return getpass.getuser()

    if not pid:
        pid = get_graphic_pid()[0]
        if not pid:
            return ''

    _user = subprocess.getoutput(f'ps hp {pid} -o euser')
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

    if is_windows():
        return ''

    _display = []
    while not _display and timeout > 0:
        # a data line ends in 0 byte, not newline
        _display = grep(
            'DISPLAY',
            open(f'/proc/{pid}/environ', encoding='utf_8').read().split('\0')
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
    """
    list compare_lists(list a, list b)
    returns ordered diff list
    """

    _result = list(difflib.unified_diff(a, b, n=0))
    # clean lines... (only package lines are important)
    # http://docs.python.org/tutorial/controlflow.html#for-statements
    for _line in _result[:]:
        if _line.startswith('+++') or _line.startswith('---') \
                or _line.startswith('@@'):
            _result.remove(_line)

    return sorted(_result)


def compare_files(a, b):
    """
    list compare_files(a, b)
    returns ordered diff list
    """

    if not os.path.isfile(a) or not os.path.isfile(b):
        return None

    # U - open for input as a text file with universal newline interpretation
    # http://www.python.org/dev/peps/pep-0278/
    with open(a, encoding='utf_8') as f:
        _list_a = f.readlines()
    with open(b, encoding='utf_8') as f:
        _list_b = f.readlines()

    return compare_lists(_list_a, _list_b)


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
        'shell': _info[6]
    }


def read_file(filename, mode='rb'):
    with open(filename, mode) as _file:
        ret = _file.read()

    return ret


def write_file(filename, content):
    """
    bool write_file(string filename, string content)
    """

    _dir = os.path.dirname(filename)
    if not os.path.exists(_dir):
        try:
            os.makedirs(_dir, 0o0777)
        except OSError:
            return False

    try:
        with open(filename, 'wb') as _file:
            try:
                _file.write(content.encode('utf-8'))
            except AttributeError:
                _file.write(content)

            _file.flush()
            os.fsync(_file.fileno())

        return True
    except IOError:
        return False


def remove_file(archive):
    if os.path.isfile(archive):
        os.remove(archive)


def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is one of "yes" or "no".

    Based in http://code.activestate.com/recipes/577058/
    """
    valid = {
        _("yes"): "yes", _("y"): "yes",
        _("no"): "no", _("n"): "no"
    }
    if default is None:
        prompt = ' {} '.format(_("[y/n]"))
    elif default == "yes":
        prompt = ' {} '.format(_("[Y/n]"))
    elif default == "no":
        prompt = ' {} '.format(_("[y/N]"))
    else:
        raise ValueError(f"invalid default answer: '{default}'")

    while 1:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return default

        if choice in valid.keys():
            return valid[choice]

        print(_("Please respond with 'yes' or 'no' (or 'y' or 'n')."))


def process_is_active(pid):
    if is_linux():
        return os.getsid(pid)

    import psutil

    for proc in psutil.process_iter():
        if proc.pid == pid:
            return True

    return False


def check_lock_file(cmd, lock_file):
    if os.path.isfile(lock_file):
        _file = None
        _pid = None
        try:
            _file = open(lock_file, encoding='utf_8')
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
            if process_is_active(_pid):
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

    return f'{_graphic_user}~{_fullname}'


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


def get_mfc_project():
    _config = get_config(settings.CONF_FILE, 'client')
    if isinstance(_config, dict) and 'project' in _config:
        return _config.get('project')

    return get_distro_project()  # if not set


def get_mfc_computer_name():
    _config = get_config(settings.CONF_FILE, 'client')
    if isinstance(_config, dict) and 'computer_name' in _config:
        return _config.get('computer_name')

    return get_hostname()  # if not set


def get_smbios_version():
    _cmd = 'LC_ALL=C sudo dmidecode -t 0 | grep SMBIOS | grep present'
    if is_windows():
        _cmd = 'dmidecode -t bios | findstr /i SMBIOS | findstr /i present'

    _ret, _smbios, _ = execute(_cmd, interactive=False)
    if _ret != 0 or _smbios == '' or _smbios is None:
        return 0, 0

    _smbios = _smbios.split()[1]  # expected: "SMBIOS x.x present."
    return tuple(int(x) for x in _smbios.split('.'))


def get_uuid_from_mac():
    from . import network

    return f'00000000-0000-0000-0000-{network.get_first_mac()}'


def get_hardware_uuid():
    _uuid_format = '%s%s%s%s-%s%s-%s%s-%s-%s'

    _cmd = 'sudo dmidecode --string system-uuid'
    if is_windows():
        _cmd = 'dmidecode --string system-uuid'

    _ret, _uuid, _ = execute(_cmd, interactive=False)
    _uuid = remove_commented_lines(_uuid)
    _uuid = _uuid.strip()
    if _ret != 0 or _uuid == '' or _uuid is None:
        return get_uuid_from_mac()

    try:
        _byte_array = uuid.UUID(_uuid).hex
    except ValueError:
        return get_uuid_from_mac()

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
            _byte_array[20:32]
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
            _byte_array[20:32]
        )

    _ms_uuid = _ms_uuid.upper()

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


def execute_as_user(args):
    # http://stackoverflow.com/questions/1770209/run-child-processes-as-different-user-from-a-long-running-process
    user_name, _ = get_current_user().split('~')
    user_info = get_user_info(user_name)

    env = os.environ.copy()
    env['HOME'] = user_info.get('home')
    env['LOGNAME'] = user_info.get('name')
    env['PWD'] = user_info.get('home')
    env['USER'] = user_info.get('name')

    if is_linux():
        process = subprocess.Popen(
            args,
            preexec_fn=demote(user_info.get('uid'), user_info.get('gid')),
            cwd=user_info.get('home'),
            env=env
        )
    else:
        process = subprocess.Popen(args, cwd=user_info.get('home'), env=env)

    process.wait()


def demote(user_uid, user_gid):
    def result():
        os.setgid(user_gid)
        os.setuid(user_uid)

    return result


def build_magic():
    # http://www.zak.co.il/tddpirate/2013/03/03/the-python-module-for-file-type-identification-called-magic-is-not-standardized/
    try:
        my_magic = magic.open(magic.MAGIC_MIME_TYPE)
        my_magic.load()
    except AttributeError:
        my_magic = magic.Magic(mime=True)
        my_magic.file = my_magic.from_file

    return my_magic


def md5sum(archive):
    if not archive:
        return ''

    with open(archive, encoding='utf_8') as handle:
        _md5 = handle.read().encode()

    return hashlib.md5(_md5).hexdigest()


def escape_quotes(text):
    return text.replace('"', '\\\"')


def get_trait(prefix, key=None, state='after'):
    if state not in ['before', 'after']:
        return None

    data = json.loads(read_file(settings.TRAITS_FILE))
    data = data[state]

    if prefix:
        ret = list(filter(lambda item: item['prefix'] == prefix, data))
        if key:
            ret = [item.get(key) for item in ret]
        if len(ret) == 1:
            return ret[0]
        else:
            return ret
    else:
        return None


def trait_value_exists(prefix, value, state='after'):
    result = get_trait(prefix, 'value', state)

    if isinstance(result, list):
        return value in result

    return result == value
