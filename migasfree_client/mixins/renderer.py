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
import logging
import os
import time

from .. import settings, utils

_ = gettext.gettext
logger = logging.getLogger('migasfree_client')


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

    def _show_message(self, msg):
        self.console.print()
        self.console.rule(msg)

    def _show_config_options(self):
        conf_file = settings.CONF_FILE if os.path.isfile(settings.CONF_FILE) else ''

        self.console.print()
        self.console.print(_('Config options: %s') % conf_file)

        # Config options: (label, value, env_var_name, show_if_truthy)
        config_options = [
            (_('Project'), self.migas_project, 'MIGASFREE_CLIENT_PROJECT', True),
            (_('Server'), self._url_base or self.migas_server, 'MIGASFREE_CLIENT_SERVER', True),
            (_('Auto update packages'), self.migas_auto_update_packages, 'MIGASFREE_CLIENT_AUTO_UPDATE_PACKAGES', True),
            (_('Manage devices'), self.migas_manage_devices, 'MIGASFREE_CLIENT_MANAGE_DEVICES', True),
            (_('Upload hardware'), self.migas_upload_hardware, 'MIGASFREE_CLIENT_UPLOAD_HARDWARE', True),
            (_('Proxy'), self.migas_proxy, 'MIGASFREE_CLIENT_PROXY', True),
            (_('Package Proxy Cache'), self.migas_package_proxy_cache, 'MIGASFREE_CLIENT_PACKAGE_PROXY_CACHE', True),
            (_('Debug'), self._debug, 'MIGASFREE_CLIENT_DEBUG', True),
            (_('Computer name'), self.migas_computer_name, 'MIGASFREE_CLIENT_COMPUTER_NAME', True),
        ]

        for label, value, env_var, show in config_options:
            if show:
                env_indicator = '(ENV)' if env_var in os.environ else ''
                self.console.print(f'\t{label}: {value} {env_indicator}')

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
                '\t\t{}: {}'.format(
                    _('Warning'), _('Certificate does not exist and authentication is not guaranteed')
                )
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
        msg = str(info) if info else _('Ok')
        self.console.log(msg, style='green')

    def operation_failed(self, info=''):
        console = self.error_console
        if utils.is_windows():
            console = self.console
            console.style = 'bright_red'

        console.rule(_('Failed'))
        if info:
            console.log(info)

        if utils.is_windows():
            console.style = ''

    def _report_error(self, msg):
        """Report error to console, logger and error file."""
        self.operation_failed(msg)
        logger.error(msg)
        self._write_error(msg)
