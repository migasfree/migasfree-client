# -*- coding: utf-8 -*-

# jhbuild - a build script for GNOME 1.x and 2.x
# Copyright (C) 2001-2004 James Henstridge
#
#       trayicon.py: simple wrapper for zenity based tray icons
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

import os
import sys
import subprocess


class TrayIcon:
    def __init__(self, env=None):
        self._run_zenity(env)

    def _run_zenity(self, env):
        # run zenity with stdout and stderr directed to /dev/null
        def preexec():
            null = open('/dev/null', 'w')
            try:
                os.dup2(null.fileno(), sys.stdout.fileno())
                os.dup2(null.fileno(), sys.stderr.fileno())
            finally:
                null.close()
            os.setsid()

        try:
            self.proc = subprocess.Popen(
                ['zenity', '--notification', '--listen'],
                close_fds=True,
                preexec_fn=preexec,
                stdin=subprocess.PIPE,
                env=env  # jact 2011-04-20
            )
        except (OSError, IOError):
            self.proc = None

    def close(self):
        status = None
        if self.proc:
            self.proc.stdin.close()
            status = self.proc.wait()
            self.proc = None
        return status

    def _send_cmd(self, cmd):
        if not self.proc:
            return

        if isinstance(cmd, unicode):
            cmd = cmd.encode('utf-8')
        try:
            self.proc.stdin.write(cmd)
            self.proc.stdin.flush()
        except (IOError, OSError):
            self.close()

    def set_icon(self, icon):
        self._send_cmd('icon: %s\n' % icon)

    def set_tooltip(self, tooltip):
        self._send_cmd('tooltip: %s\n' % tooltip)
        # self._send_cmd('message: %s\n' % tooltip)  # jact 2011-04-17

    def set_visible(self, visible):
        if visible:
            visible = 'true'
        else:
            visible = 'false'
        self._send_cmd('visible: %s\n' % visible)
