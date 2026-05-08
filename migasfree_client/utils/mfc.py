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

import errno
import json
import logging
import os
import re
import sys
import uuid

from .. import settings
from .data import get_config, remove_commented_lines
from .fs import read_file, write_file
from .process import execute
from .system import get_distro_project, get_hostname, is_linux, is_windows

logger = logging.getLogger('migasfree_client')


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
                import gettext

                _ = gettext.gettext
                logger.warning(_('Another instance of %(cmd)s is running: %(pid)d') % {'cmd': cmd, 'pid': int(_pid)})
                sys.exit(errno.EPERM)
        except OSError:
            pass
    else:
        write_file(lock_file, str(os.getpid()))


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
    if is_windows():
        _ret, _out, _ = execute('wmic bios get smbiosbiosversion', interactive=False)
        if _ret == 0 and _out:
            _lines = [line.strip() for line in _out.splitlines() if line.strip()]
            if len(_lines) > 1:
                try:
                    return tuple(int(x) for x in _lines[1].split('.'))
                except (ValueError, IndexError):
                    pass
        return 0, 0

    _cmd = 'LC_ALL=C sudo dmidecode -t 0 | grep SMBIOS | grep present'
    _ret, _smbios, _ = execute(_cmd, interactive=False)
    if _ret != 0 or _smbios == '' or _smbios is None:
        return 0, 0

    _smbios = _smbios.split()[1]  # expected: "SMBIOS x.x present."
    return tuple(int(x) for x in _smbios.split('.'))


def get_uuid_from_mac():
    from .. import network

    return f'00000000-0000-0000-0000-{network.get_first_mac()}'


def get_hardware_uuid():
    _uuid_format = '%s%s%s%s-%s%s-%s%s-%s-%s'

    if is_windows():
        _ret, _out, _ = execute('wmic csproduct get uuid', interactive=False)
        if _ret == 0 and _out:
            _lines = [line.strip() for line in _out.splitlines() if line.strip()]
            _uuid = _lines[1] if len(_lines) > 1 else ''
        else:
            _uuid = ''
    else:
        _cmd = ['sudo', 'dmidecode', '--string', 'system-uuid']
        _ret, _uuid, _ = execute(_cmd, interactive=False)

    _uuid = remove_commented_lines(_uuid)
    _uuid = _uuid.strip()
    if _uuid == '' or _uuid is None:
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


def get_mfc_release():
    from .. import __version__

    return __version__


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


def migrate_legacy_server_config(conf_file):
    """Rewrite conf_file merging legacy Protocol/Port keys into Server.

    Detects uncommented Protocol and/or Port keys in the [client] section,
    builds the new unified Server URL, updates the Server line, and comments
    out the obsolete keys in-place preserving all other content and comments.

    Returns the new Server URL string if migration was performed, '' otherwise.
    """
    if not os.path.isfile(conf_file):
        return ''

    try:
        with open(conf_file, encoding='utf-8') as fh:
            content = fh.read()
    except OSError:
        return ''

    _pat = r'^(?![ \t]*#)[ \t]*{key}[ \t]*=[ \t]*(.+)$'

    server_m = re.search(_pat.format(key='Server'), content, re.IGNORECASE | re.MULTILINE)
    protocol_m = re.search(_pat.format(key='Protocol'), content, re.IGNORECASE | re.MULTILINE)
    port_m = re.search(_pat.format(key='Port'), content, re.IGNORECASE | re.MULTILINE)

    if not (protocol_m or port_m):
        return ''  # nothing to migrate

    server = server_m.group(1).strip() if server_m else 'localhost'
    protocol = protocol_m.group(1).strip() if protocol_m else 'https'
    port = port_m.group(1).strip() if port_m else ''

    new_server = f'{protocol}://{server}' if '://' not in server else server

    host_part = new_server.split('://', 1)[1]
    if port and f':{port}' not in host_part:
        new_server = f'{new_server}:{port}'

    new_content = content

    if server_m:
        new_content = re.sub(
            r'^((?![ \t]*#)[ \t]*Server[ \t]*=[ \t]*)(.+)$',
            lambda m: f'{m.group(1)}{new_server}',
            new_content,
            count=1,
            flags=re.IGNORECASE | re.MULTILINE,
        )
    else:
        new_content = re.sub(
            r'(\[client\])',
            f'\\1\nServer = {new_server}',
            new_content,
            count=1,
            flags=re.IGNORECASE,
        )

    for key in ('Protocol', 'Port'):
        new_content = re.sub(
            r'^((?![ \t]*#)([ \t]*' + key + r'[ \t]*=.+))$',
            r'# \2  # migrated to Server',
            new_content,
            flags=re.IGNORECASE | re.MULTILINE,
        )

    if new_content == content:
        return ''

    if write_file(conf_file, new_content):
        logger.info('Migrated legacy config: Server = %s in %s', new_server, conf_file)
        return new_server

    logger.warning('Could not write migrated config to %s', conf_file)
    return ''
