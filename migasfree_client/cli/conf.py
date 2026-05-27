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

import errno
import gettext
import json
import logging
import os
import re
import sys
from urllib.parse import urlparse

from .. import settings, utils
from ..command import MigasFreeCommand
from ..mtls import get_mtls_ca_file

_ = gettext.gettext
logger = logging.getLogger('migasfree_client')


class MigasFreeConf(MigasFreeCommand):
    CMD = 'migasfree conf'

    def run(self, args=None):
        # We don't need all the mtls/pms setup from _init_command for local config changes
        # self._init_command()

        if args is None:
            return

        # Determine if we are writing or just reading
        write_operations = {
            'Server': args.server,
            'Project': args.project,
            'Auto_Update_Packages': args.auto_update_packages,
            'Manage_Devices': args.manage_devices,
            'Upload_Hardware': args.upload_hardware,
            'Computer_Name': args.computer_name,
            'Debug': args.debug_mode,
            'Package_Proxy_Cache': args.package_proxy_cache,
            'Proxy': args.proxy,
        }

        # Filter out None values
        to_write = {k: v for k, v in write_operations.items() if v is not None}

        if to_write:
            self._check_user_is_root()

        if not to_write:
            if getattr(args, 'json', False):
                ret = {
                    'server': self.migas_server,
                    'project': self.migas_project,
                    'computer_name': self.migas_computer_name,
                    'user': utils.get_graphic_user(None),
                    'uuid': utils.get_hardware_uuid(),
                    'api_protocol': self.api_protocol(),
                    'manage_devices': self.migas_manage_devices,
                    'ca_file': get_mtls_ca_file(self.migas_server),
                }
                print(json.dumps(ret, ensure_ascii=False))
            else:
                self._show_config_options()
            return

        self._check_user_is_root()

        # Validate values before writing
        for key, value in to_write.items():
            if not self._validate_value(key, value):
                logger.error(_('Invalid value for %s: %s'), key, value)
                sys.exit(errno.EINVAL)

        # Write to file
        for key, value in to_write.items():
            self._set_config_value(settings.CONF_FILE, 'client', key, value)
            self._show_message(_('Set %s = %s') % (key, value))

    def _validate_value(self, key, value):
        if key == 'Server':
            if not value:
                return False
            # Check scheme
            if '://' not in value:
                value = 'https://' + value
            parsed = urlparse(value)
            return not (parsed.scheme not in ('http', 'https') or not parsed.hostname)

        elif key == 'Project':
            if not value:
                return False
            return bool(re.match(r'^[\w.-]+$', value))

        elif key == 'Computer_Name':
            if not value:
                return True
            # RFC 1123 loosely
            return bool(re.match(r'^[\w.-]+$', value))

        elif key in ('Package_Proxy_Cache', 'Proxy'):
            if not value:
                return True  # Empty to disable
            match = re.match(r'^([^:]+):(\d+)$', value)
            if not match:
                return False
            port = int(match.group(2))
            return 1 <= port <= 65535

        return True

    def _set_config_value(self, conf_file, section, key, value):
        """Update a specific configuration value in an ini file preserving comments."""
        if not os.path.isfile(conf_file):
            if value == '':
                return
            utils.write_file(conf_file, f'[{section}]\n{key} = {value}\n')
            return

        with open(conf_file, encoding='utf-8') as fh:
            content = fh.read()

        # Build regex for active key (allowing empty value after = with .*)
        _pat = r'^((?![ \t]*#)[ \t]*' + re.escape(key) + r'[ \t]*=[ \t]*)(.*)$'
        # Build regex for commented key
        _comment_pat = r'^([ \t]*#[ \t]*' + re.escape(key) + r'[ \t]*=.*)$'

        if value == '':
            if re.search(_pat, content, re.IGNORECASE | re.MULTILINE):
                # Comment out the active key
                new_content = re.sub(
                    _pat,
                    r'# \1\2',
                    content,
                    count=1,
                    flags=re.IGNORECASE | re.MULTILINE,
                )
            else:
                return
        else:
            # Format boolean correctly if choices was true/false
            if str(value).lower() == 'true':
                value = 'True'
            elif str(value).lower() == 'false':
                value = 'False'

            if re.search(_pat, content, re.IGNORECASE | re.MULTILINE):
                # Replace existing active value
                new_content = re.sub(
                    _pat,
                    lambda m: f'{m.group(1)}{value}',
                    content,
                    count=1,
                    flags=re.IGNORECASE | re.MULTILINE,
                )
            elif re.search(_comment_pat, content, re.IGNORECASE | re.MULTILINE):
                # Key is commented out, insert active key right below it
                new_content = re.sub(
                    _comment_pat,
                    r'\1' + f'\n{key} = {value}',
                    content,
                    count=1,
                    flags=re.IGNORECASE | re.MULTILINE,
                )
            else:
                # Key not found, append to section
                # Find the section and append
                section_pat = r'(\[' + re.escape(section) + r'\])'
                if re.search(section_pat, content, re.IGNORECASE):
                    new_content = re.sub(
                        section_pat,
                        f'\\1\n{key} = {value}',
                        content,
                        count=1,
                        flags=re.IGNORECASE,
                    )
                else:
                    # Section not found, append everything to end
                    new_content = content + f'\n[{section}]\n{key} = {value}\n'

        utils.write_file(conf_file, new_content)
