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

import gettext
import json
import logging
import os
import sys
import time

from .. import settings, utils

_ = gettext.gettext
logger = logging.getLogger('migasfree_client')


_STAGE_PERCENTAGES = {
    'connection': 5,
    'attributes': 10,
    'faults': 20,
    'repositories': 30,
    'metadata': 40,
    'uninstall': 50,
    'install': 65,
    'update': 75,
    'software': 85,
    'hardware': 90,
    'finish': 100,
}


def show_stage(obj, msg, stage):
    try:
        obj._show_message(msg, stage=stage)
    except (TypeError, AttributeError):
        if hasattr(obj, '_show_message'):
            obj._show_message(msg)


class RendererMixin:
    """
    Mixin for console output and formatting.
    Assumes it is mixed into a class that has:
    - self.console
    - self.error_console
    - self.ERROR_FILE
    - self._error_file_descriptor
    - self._server_info
    - self.migas_*
    - self.pms
    """

    def show_stage(self, msg, stage):
        show_stage(self, msg, stage)

    def _show_message(self, msg, stage=None):
        if getattr(self, '_json', False):
            if stage is None:
                stage = getattr(self, '_sync_stage', 'sync')
                percent = getattr(self, '_sync_progress', 0)
            else:
                percent = _STAGE_PERCENTAGES.get(stage, getattr(self, '_sync_progress', 0))
                self._sync_stage = stage

            self._sync_progress = percent

            payload = {'type': 'progress', 'stage': stage, 'percent': percent, 'detail': msg, 'message': msg}
            sys.stdout.write(json.dumps(payload) + '\n')
            sys.stdout.flush()
        else:
            self.console.print()
            self.console.print('[bright_black]' + '⎯' * 76 + '[/bright_black]')
            self.console.print(f'[bold blue]➔[/bold blue] [bold]{msg}[/bold]\n')

    def _show_config_options(self):
        conf_file = settings.CONF_FILE if os.path.isfile(settings.CONF_FILE) else ''

        self.console.print()
        self.console.print(_('Config options: %s') % conf_file)

        # Config options: (label, value, env_var_name, file_key, show_if_truthy)
        config_options = [
            (_('Project'), self.migas_project, 'MIGASFREE_CLIENT_PROJECT', None, True),
            (_('Server'), self._url_base or self.migas_server, 'MIGASFREE_CLIENT_SERVER', 'server', True),
            (
                _('Auto update packages'),
                self.migas_auto_update_packages,
                'MIGASFREE_CLIENT_AUTO_UPDATE_PACKAGES',
                'auto_update_packages',
                True,
            ),
            (_('Manage devices'), self.migas_manage_devices, 'MIGASFREE_CLIENT_MANAGE_DEVICES', 'manage_devices', True),
            (
                _('Upload hardware'),
                self.migas_upload_hardware,
                'MIGASFREE_CLIENT_UPLOAD_HARDWARE',
                'upload_hardware',
                True,
            ),
            (_('Proxy'), self.migas_proxy, 'MIGASFREE_CLIENT_PROXY', 'proxy', True),
            (
                _('Package Proxy Cache'),
                self.migas_package_proxy_cache,
                'MIGASFREE_CLIENT_PACKAGE_PROXY_CACHE',
                'package_proxy_cache',
                True,
            ),
            (_('Debug'), self._debug, 'MIGASFREE_CLIENT_DEBUG', 'debug', True),
            (_('Computer name'), self.migas_computer_name, 'MIGASFREE_CLIENT_COMPUTER_NAME', None, True),
        ]

        for label, value, env_var, file_key, show in config_options:
            if show:
                indicator = ''
                if env_var in os.environ:
                    indicator = _('(ENV)')
                elif file_key and file_key in getattr(self, '_config_client_raw', {}):
                    indicator = _('(FILE)')
                else:
                    indicator = _('(DEFAULT)')

                if indicator:
                    self.console.print(f'\t{label}: {value} {indicator}')
                else:
                    self.console.print(f'\t{label}: {value}')

    def _show_running_options(self):
        self.console.print()
        self.console.print(_('Running options:'))
        self.console.print(
            '\t{}: {}'.format(_('migasfree server version'), self._server_info.get('version', _('None')))
        )
        self.console.print('\t{}: {}'.format(_('SSL certificate'), self.migas_ssl_cert))
        if (
            self.migas_ssl_cert is not None
            and not isinstance(self.migas_ssl_cert, bool)
            and not os.path.exists(self.migas_ssl_cert)
        ):
            self.console.print(
                '\t\t{}: {}'.format(_('Warning'), _('Certificate does not exist and authentication is not guaranteed'))
            )
        self.console.print('\t{}: {}'.format(_('PMS'), self.pms))
        if self.pms:
            self.console.print('\t{}: {}'.format(_('Architecture'), self.pms.get_system_architecture()))

    def _write_error(self, msg, append=False):
        _mode = 'ab' if append else 'wb'

        if not self._error_file_descriptor:
            self._error_file_descriptor = open(self.ERROR_FILE, _mode)  # noqa: SIM115

        _text = '{}\n{}\n{}\n\n'.format('-' * 20, time.strftime('%Y-%m-%d %H:%M:%S'), str(msg))
        _text = bytes(_text, encoding='utf8')

        self._error_file_descriptor.write(_text)

    def _usage_examples(self):
        raise NotImplementedError

    def operation_ok(self, info=''):
        if getattr(self, '_json', False):
            msg = str(info) if info else _('Ok')
            payload = {'type': 'status', 'stage': 'ok', 'message': msg}
            sys.stdout.write(json.dumps(payload) + '\n')
            sys.stdout.flush()
        else:
            msg = str(info) if info else _('Ok')
            self.console.print(rf'[bold green]✓ \[OK] {msg}[/bold green]')

    def operation_failed(self, info=''):
        if getattr(self, '_json', False):
            payload = {'type': 'status', 'stage': 'failed', 'message': str(info)}
            sys.stdout.write(json.dumps(payload) + '\n')
            sys.stdout.flush()
        else:
            msg = str(info) if info else _('Failed')
            console = self.error_console
            if utils.is_windows():
                console = self.console
            console.print(rf'[bold red]✗ \[ERROR] {msg}[/bold red]')

    def _report_error(self, msg):
        """Report error to console, logger and error file."""
        self.operation_failed(msg)
        logger.error(msg)
        self._write_error(msg)
