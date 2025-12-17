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

import configparser
import difflib
import errno
import gettext
import hashlib
import json
import os
import platform
import re
import select
import signal
import subprocess
import sys
import time
import uuid

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
            _process = subprocess.Popen(cmd, shell=True, executable='/bin/bash')
    else:
        if is_windows():
            _process = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        else:
            _process = subprocess.Popen(
                cmd, shell=True, executable='/bin/bash', stderr=subprocess.PIPE, stdout=subprocess.PIPE
            )

        if verbose:
            if not is_windows():
                import fcntl

                fcntl.fcntl(
                    _process.stdout.fileno(),
                    fcntl.F_SETFL,
                    fcntl.fcntl(_process.stdout.fileno(), fcntl.F_GETFL) | os.O_NONBLOCK,
                )

            while _process.poll() is None:
                try:
                    readx = select.select([_process.stdout.fileno()], [], [])[0]
                except OSError:
                    readx = None

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
            cmd, shell=True, executable='/bin/bash', stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
    else:
        _process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

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
        'cinnamon-session-binary',  # Cinnamon
        'cinnamon-session',  # Cinnamon
        'cosmic-session',  # Cosmic (Pop OS!)
        'cutefish-session',  # Cutefish OS
        'lingmo-session',  # Lingmo OS
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

    oldest_match = None
    oldest_starttime = float('inf')
    for pid in os.listdir('/proc'):
        if not pid.isdigit():
            continue

        try:
            # Read full command line (better than comm which is truncated to 15 chars)
            with open(f'/proc/{pid}/cmdline', 'r') as f:
                cmdline = f.read()
            
            # Get executable name from cmdline
            exe_name = os.path.basename(cmdline.split('\x00')[0])
            # Check if matches any graphic environment
            matching_env = None
            for env in _graphic_environments:
                if env == exe_name or exe_name.startswith(env):
                    matching_env = env
                    break
            
            if not matching_env:
                continue

            # Get process start time to find oldest
            with open(f'/proc/{pid}/stat', 'r') as f:
                stat = f.read().split()
                starttime = int(stat[21])

            if starttime < oldest_starttime:
                oldest_starttime = starttime
                oldest_match = (pid, matching_env)
        except (OSError, IOError, IndexError, ValueError):
            continue

    return list(oldest_match) if oldest_match else [None, None]


def get_graphic_user(pid=0):
    """
    string get_graphic_user(int pid=0)
    """

    if is_windows():
        import win32ts

        _user = win32ts.WTSQuerySessionInformation(None, -1, win32ts.WTSUserName)
        if not _user:
            import psutil

            for p in psutil.process_iter():
                if p.name() == 'explorer.exe':
                    _user = p.username().rsplit('\\', 1)[1]
                    break

        return _user.strip()

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


def get_user_display_graphic(pid):
    """
    string get_user_display_graphic(string pid)
    Returns DISPLAY environment variable from process or default ':0.0'
    """
    if is_windows():
        return ''

    try:
        with open(f'/proc/{pid}/environ', encoding='utf-8') as f:
            environ = f.read().split('\0')
        
        for item in environ:
            if item.startswith('DISPLAY='):
                return item.split('=', 1)[1]
    except (OSError, IOError):
        pass

    return ':0.0'  # Default display


def compare_lists(a, b):
    """
    list compare_lists(list a, list b)
    returns ordered diff list
    """

    # clean lines... (only package lines are important)
    _result = [line for line in difflib.unified_diff(a, b, n=0) if not line.startswith(('+++', '---', '@@'))]

    return sorted(_result)


def compare_files(a, b):
    """
    list compare_files(a, b)
    returns ordered diff list
    """

    if not os.path.isfile(a) or not os.path.isfile(b):
        return None

    with open(a, encoding='utf-8') as f:
        _list_a = f.readlines()
    with open(b, encoding='utf-8') as f:
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
    except OSError:
        return False


def remove_file(archive):
    if os.path.isfile(archive):
        os.remove(archive)


def query_yes_no(question, default='yes'):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is one of "yes" or "no".

    Based in http://code.activestate.com/recipes/577058/
    """
    valid = {_('yes'): 'yes', _('y'): 'yes', _('no'): 'no', _('n'): 'no'}
    if default is None:
        prompt = ' {} '.format(_('[y/n]'))
    elif default == 'yes':
        prompt = ' {} '.format(_('[Y/n]'))
    elif default == 'no':
        prompt = ' {} '.format(_('[y/N]'))
    else:
        raise ValueError(f"invalid default answer: '{default}'")

    while 1:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return default

        if choice in valid:
            return valid[choice]

        print(_("Please respond with 'yes' or 'no' (or 'y' or 'n')."))


def process_is_active(pid):
    if is_linux():
        return os.getsid(pid)

    import psutil

    return any(proc.pid == pid for proc in psutil.process_iter())


def check_lock_file(cmd, lock_file):
    _pid = None
    if os.path.isfile(lock_file):
        try:
            with open(lock_file, encoding='utf-8') as _file:
                _pid = _file.read().strip()
        except OSError:
            _pid = -1
        else:
            if not _pid:
                _pid = -1
            else:
                try:
                    _pid = int(_pid)
                except ValueError:
                    _pid = -1

        try:
            if process_is_active(_pid):
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
    _graphic_user = os.environ.get('USER') if not _graphic_pid else get_graphic_user(_graphic_pid)

    _info = get_user_info(_graphic_user)
    _fullname = '' if not _info else _info['fullname']

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
            args, preexec_fn=demote(user_info.get('uid'), user_info.get('gid')), cwd=user_info.get('home'), env=env
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

    with open(archive, encoding='utf-8') as handle:
        _md5 = handle.read().encode()

    return hashlib.md5(_md5).hexdigest()


def escape_quotes(text):
    return text.replace('"', '\\"')


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

        return ret

    return None


def trait_value_exists(prefix, value, state='after'):
    result = get_trait(prefix, 'value', state)

    if isinstance(result, list):
        return value in result

    return result == value
