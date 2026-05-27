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
import json
import logging
import os
import select
import signal
import subprocess
import sys
import time

from .. import settings
from .data import _bytes_to_str
from .system import is_linux, is_windows

_ = gettext.gettext
logger = logging.getLogger('migasfree_client')
ALL_OK = 0 if sys.platform == 'win32' else os.EX_OK


def _create_subprocess(cmd, capture_output=True, input_data=None, **kwargs):
    """Create a subprocess with platform-specific settings.

    Args:
        cmd: Command string or list to execute. Using a list forces shell=False for safety.
        capture_output: If True, capture stdout/stderr; if False, let them inherit

    Returns:
        subprocess.Popen instance
    """
    is_shell = isinstance(cmd, str)
    common_args: dict = {'shell': is_shell}

    if is_linux() and is_shell:
        common_args['executable'] = '/bin/bash'

    if capture_output:
        common_args['stdout'] = subprocess.PIPE
        common_args['stderr'] = subprocess.PIPE

    if input_data is not None:
        common_args['stdin'] = subprocess.PIPE

    if kwargs:
        common_args.update(kwargs)

    return subprocess.Popen(cmd, **common_args)


def _stream_output_nonblocking(process):
    """Stream process output in non-blocking mode (Linux only).

    Returns:
        Collected output as string
    """
    output_buffer = ''

    if is_windows():
        # Non-blocking streaming not supported on Windows in this manner
        while process.poll() is None:
            try:
                readx = select.select([process.stdout.fileno()], [], [])[0]
            except OSError:
                readx = None

            if readx:
                chunk = process.stdout.read()
                chunk = _bytes_to_str(chunk)
                if chunk and chunk != '\n':
                    if getattr(settings, 'JSON_OUTPUT', False):
                        for line in chunk.splitlines():
                            if line.strip():
                                sys.stdout.write(json.dumps({'type': 'log', 'stage': 'pms', 'message': line}) + '\n')
                        sys.stdout.flush()
                    else:
                        sys.stdout.write(chunk)
                        sys.stdout.flush()
                    logger.info(chunk)
                output_buffer = f'{output_buffer}{chunk}'
    else:
        import fcntl

        fcntl.fcntl(
            process.stdout.fileno(),
            fcntl.F_SETFL,
            fcntl.fcntl(process.stdout.fileno(), fcntl.F_GETFL) | os.O_NONBLOCK,
        )

        while process.poll() is None:
            try:
                readx = select.select([process.stdout.fileno()], [], [])[0]
            except OSError:
                readx = None

            if readx:
                chunk = process.stdout.read()
                chunk = _bytes_to_str(chunk)
                if chunk and chunk != '\n':
                    if getattr(settings, 'JSON_OUTPUT', False):
                        for line in chunk.splitlines():
                            if line.strip():
                                sys.stdout.write(json.dumps({'type': 'log', 'stage': 'pms', 'message': line}) + '\n')
                        sys.stdout.flush()
                    else:
                        sys.stdout.write(chunk)
                        sys.stdout.flush()
                    logger.info(chunk)
                output_buffer = f'{output_buffer}{chunk}'

    return output_buffer


def execute(cmd, verbose=False, interactive=True, input_data=None, **kwargs):
    """Execute a shell command.

    Args:
        cmd: Command string or list to execute. Using a list forces shell=False for safety.
        verbose: If True, print command and output
        interactive: If True, let output inherit to terminal; if False, capture it
        input_data: Optional string to send to stdin

    Returns:
        Tuple of (returncode, stdout, stderr)
    """
    if verbose:
        logger.info(' '.join(cmd) if isinstance(cmd, (list, tuple)) else cmd)

    process = _create_subprocess(cmd, capture_output=not interactive, input_data=input_data, **kwargs)
    output_buffer = ''

    if not interactive and verbose:
        output_buffer = _stream_output_nonblocking(process)

    if input_data and isinstance(input_data, str):
        input_data = input_data.encode('utf-8')

    output, error = process.communicate(input=input_data)

    output = output_buffer if not interactive and output_buffer else _bytes_to_str(output)

    error = _bytes_to_str(error)

    return process.returncode, output, error


def _kill_process(process):
    """Kill a process in a platform-specific way."""
    if is_linux():
        os.kill(process.pid, signal.SIGKILL)
        os.waitpid(-1, os.WNOHANG)
    else:
        import psutil

        psutil.Process(process.pid).kill()


def timeout_execute(cmd, timeout=60, **kwargs):
    """Execute a command with a timeout.

    Args:
        cmd: Command string or list to execute. Using a list forces shell=False for safety.
        timeout: Maximum execution time in seconds (0 for no timeout)

    Returns:
        Tuple of (returncode, stdout, stderr)
    """
    process = _create_subprocess(cmd, capture_output=True, **kwargs)

    if timeout > 0:
        interval = 0.2
        seconds_elapsed = 0

        while process.poll() is None:
            time.sleep(interval)
            seconds_elapsed += interval

            if seconds_elapsed > timeout:
                _kill_process(process)
                return 1, '', _('"%s" command expired timeout') % cmd

    output, error = process.communicate()

    return process.returncode, _bytes_to_str(output), _bytes_to_str(error)


def demote(user_uid, user_gid):
    def result():
        os.setgid(user_gid)
        os.setuid(user_uid)

    return result
