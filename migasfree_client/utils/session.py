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

import gettext
import os
import subprocess
import sys

from rich import print as rprint

from .process import demote, execute
from .system import get_user_info, is_linux, is_windows

_ = gettext.gettext


def get_graphic_pid():
    """
    list get_graphic_pid(void)
    Detects desktop environment and returns [PID, environment_name] if found
    """
    if is_windows():
        import psutil

        for proc in psutil.process_iter():
            try:
                if proc.name().lower() == 'explorer.exe':
                    return [proc.pid, proc.name()]
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return [None, None]

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
            with open(f'/proc/{pid}/cmdline') as f:
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
            with open(f'/proc/{pid}/stat') as f:
                stat = f.read().split()
                starttime = int(stat[21])

            if starttime < oldest_starttime:
                oldest_starttime = starttime
                oldest_match = (pid, matching_env)
        except (OSError, IndexError, ValueError):
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

    try:
        _proc = subprocess.run(
            ['ps', 'hp', str(pid), '-o', 'euser'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,  # noqa: UP021
            check=False,
        )
        _user = _proc.stdout.strip()
    except OSError:
        _user = ''
    if _user.isdigit():
        # ps command not always show username (show uid if len(username) > 8)
        _user_info = get_user_info(_user)
        if _user_info is False:  # p.e. chroot environment
            return 'root'

        return _user_info['name']

    return _user.strip()


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
    except OSError:
        pass

    return ':0.0'  # Default display


def is_xsession():
    return os.environ.get('DISPLAY') is not None


def is_zenity():
    _ret, _, _ = execute(['which', 'zenity'], interactive=False)

    return _ret == 0


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

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return default

        if choice in valid:
            return valid[choice]

        rprint(_("Please respond with 'yes' or 'no' (or 'y' or 'n')."))
