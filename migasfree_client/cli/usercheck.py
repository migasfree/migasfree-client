# Copyright (c) 2026 Jose Antonio Chavarría <jachavar@gmail.com>
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

import contextlib
import gettext
import json
import os
import platform
import subprocess
import sys
from typing import ClassVar

from ..command import MigasFreeCommand
from ..utils import ALL_OK

__author__ = 'Jose Antonio Chavarría <jachavar@gmail.com>'
__license__ = 'GPLv3'
__all__ = ['MigasFreeUserCheck']

_ = gettext.gettext


class MigasFreeUserCheck(MigasFreeCommand):
    def __init__(self):
        super().__init__()

    def run(self, args=None):
        super().run(args, init_command=False, show_config=False)

        username = args.user
        password = args.password

        authenticated = False
        is_privileged = False
        groups = []
        error_msg = None

        os_platform = platform.system()

        if os_platform == 'Windows':
            try:
                import ctypes

                import win32net
                import win32security

                domain = os.environ.get('USERDOMAIN', '')
                try:
                    win32security.LogonUser(
                        username,
                        domain,
                        password,
                        win32security.Logon32_LOGON_NETWORK,
                        win32security.Logon32_PROVIDER_DEFAULT,
                    )
                    authenticated = True
                except win32security.error as e:
                    authenticated = False
                    error_msg = str(e)

                if authenticated:
                    if ctypes.windll.shell32.IsUserAnAdmin() == 1:
                        is_privileged = True

                    # Try to retrieve local groups
                    try:
                        local_groups = win32net.NetUserGetLocalGroups(None, username)
                        groups.extend(local_groups)
                        global_groups = win32net.NetUserGetGroups(None, username)
                        groups.extend([g[0] for g in global_groups])
                    except Exception:
                        pass
            except Exception as e:
                authenticated = False
                is_privileged = False
                error_msg = str(e)

        elif os_platform == 'Linux':
            import ctypes
            import ctypes.util
            import grp
            import pwd

            # Get user groups
            try:
                user_pw = pwd.getpwnam(username)
                with contextlib.suppress(KeyError):
                    groups.append(grp.getgrgid(user_pw.pw_gid).gr_name)
                for g in grp.getgrall():
                    if username in g.gr_mem:
                        groups.append(g.gr_name)
            except KeyError:
                pass

            # 1. Helper to run PAM authentication using ctypes
            cleanup_refs = []

            def pam_auth(user_, pwd_):
                path = ctypes.util.find_library('pam')
                if not path:
                    return False
                try:
                    libpam = ctypes.CDLL(path)
                except OSError:
                    return False

                class PamHandle(ctypes.Structure):
                    pass

                class PamMessage(ctypes.Structure):
                    _fields_: ClassVar = [('msg_style', ctypes.c_int), ('msg', ctypes.c_char_p)]

                class PamResponse(ctypes.Structure):
                    _fields_: ClassVar = [('resp', ctypes.c_char_p), ('resp_retcode', ctypes.c_int)]

                class PamConv(ctypes.Structure):
                    _fields_: ClassVar = [
                        (
                            'conv',
                            ctypes.CFUNCTYPE(
                                ctypes.c_int,
                                ctypes.c_int,
                                ctypes.POINTER(ctypes.POINTER(PamMessage)),
                                ctypes.POINTER(ctypes.POINTER(PamResponse)),
                                ctypes.c_void_p,
                            ),
                        ),
                        ('appdata_ptr', ctypes.c_void_p),
                    ]

                def conversation(num_msg, msg, resp, appdata_ptr):
                    try:
                        response = (PamResponse * num_msg)()
                        for i in range(num_msg):
                            pm = msg[i].contents
                            style = pm.msg_style
                            response[i].resp_retcode = 0
                            response[i].resp = None
                            if style == 1:  # PAM_PROMPT_ECHO_OFF
                                pwd_bytes = pwd_.encode('utf-8') if isinstance(pwd_, str) else pwd_
                                cleanup_refs.append(pwd_bytes)
                                c_pwd = ctypes.c_char_p(pwd_bytes)
                                cleanup_refs.append(c_pwd)
                                response[i].resp = c_pwd
                        cleanup_refs.append(response)
                        resp[0] = response
                        return 0  # PAM_SUCCESS
                    except Exception:
                        return 19  # PAM_CONV_ERR

                conv_func_type = ctypes.CFUNCTYPE(
                    ctypes.c_int,
                    ctypes.c_int,
                    ctypes.POINTER(ctypes.POINTER(PamMessage)),
                    ctypes.POINTER(ctypes.POINTER(PamResponse)),
                    ctypes.c_void_p,
                )

                pam_start = libpam.pam_start
                pam_start.restype = ctypes.c_int
                pam_start.argtypes = [
                    ctypes.c_char_p,
                    ctypes.c_char_p,
                    ctypes.POINTER(PamConv),
                    ctypes.POINTER(ctypes.POINTER(PamHandle)),
                ]

                pam_authenticate = libpam.pam_authenticate
                pam_authenticate.restype = ctypes.c_int
                pam_authenticate.argtypes = [ctypes.POINTER(PamHandle), ctypes.c_int]

                pam_end = libpam.pam_end
                pam_end.restype = ctypes.c_int
                pam_end.argtypes = [ctypes.POINTER(PamHandle), ctypes.c_int]

                handle = ctypes.POINTER(PamHandle)()
                conv = PamConv(conv_func_type(conversation), 0)

                try:
                    u_enc = username.encode('utf-8')
                except Exception:
                    u_enc = str(username).encode('utf-8')

                retval = pam_start(b'sudo', u_enc, ctypes.byref(conv), ctypes.byref(handle))
                if retval == 0:
                    retval = pam_authenticate(handle, 0)
                    pam_end(handle, retval)
                return retval == 0

            # 2. Check Sudo privileges/groups
            def is_admin_group(user_):
                admin_groups = ['sudo', 'wheel', 'root']
                target_gids = []
                for gname in admin_groups:
                    with contextlib.suppress(KeyError):
                        target_gids.append(grp.getgrnam(gname).gr_gid)
                if not target_gids:
                    return False
                try:
                    user_pw = pwd.getpwnam(user_)
                    user_groups_ids = [user_pw.pw_gid]
                    for g in grp.getgrall():
                        if user_ in g.gr_mem:
                            user_groups_ids.append(g.gr_gid)
                    return bool(set(target_gids) & set(user_groups_ids))
                except KeyError:
                    return False

            def is_root(user_):
                try:
                    return pwd.getpwnam(user_).pw_uid == 0
                except KeyError:
                    pass
                return False

            def check_sudo_auth(user_, password_):
                try:
                    import getpass

                    cur_user = getpass.getuser()
                    cmd = []
                    if cur_user == 'root' and user_ != 'root':
                        cmd = ['su', user_, '-c', 'sudo -S -v -k']
                    elif user_ == cur_user or user_ == 'root' or cur_user == 'root':
                        cmd = ['sudo', '-S', '-v', '-k']
                    else:
                        return False

                    input_bytes = password_.encode('utf-8') + b'\n' if isinstance(password_, str) else password_ + b'\n'
                    p = subprocess.run(cmd, input=input_bytes, stdout=subprocess.PIPE, stderr=subprocess.PIPE)  # noqa: UP022
                    return p.returncode == 0
                except Exception:
                    return False

            # Run Auth check
            if check_sudo_auth(username, password):
                authenticated = True
                is_privileged = True
            else:
                authenticated = pam_auth(username, password)
                if authenticated and (is_admin_group(username) or is_root(username)):
                    is_privileged = True

        if self._quiet:
            response = {
                'authenticated': authenticated,
                'is_privileged': is_privileged,
                'username': username,
                'platform': os_platform.lower(),
                'groups': groups,
            }
            if error_msg:
                response['error'] = error_msg
            self.console.print(json.dumps(response), soft_wrap=True)
        else:
            self.console.print()
            self.console.print(
                _('USER AUTHENTICATION STATUS')
                + '\n'
                + '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━',
                style='bold cyan',
            )

            label_username = _('Username:')
            label_platform = _('Platform:')
            label_auth = _('Authenticated:')
            label_priv = _('Privileges:')
            label_groups = _('Groups:')
            label_error = _('Error Details:')

            # Find max length of labels for perfect alignment
            max_len = (
                max(len(label_username), len(label_platform), len(label_auth), len(label_priv), len(label_groups)) + 2
            )

            self.console.print(f'{label_username:<{max_len}} {username}')
            self.console.print(f'{label_platform:<{max_len}} {os_platform.lower()}')

            auth_status = (
                '[bold green]' + _('[YES] Success') + '[/bold green]'
                if authenticated
                else '[bold red]' + _('[NO] Failed') + '[/bold red]'
            )
            self.console.print(f'{label_auth:<{max_len}} {auth_status}')

            priv_status = (
                '[bold green]' + _('[YES] Administrative Access') + '[/bold green]'
                if is_privileged
                else '[bold yellow]' + _('[NO] Standard Access') + '[/bold yellow]'
            )
            self.console.print(f'{label_priv:<{max_len}} {priv_status}')

            self.console.print(f'{label_groups:<{max_len}} {", ".join(groups)}')
            if error_msg:
                self.console.print(f'{label_error:<{max_len}} {error_msg}', style='red')
            self.console.print()

        sys.exit(ALL_OK)
