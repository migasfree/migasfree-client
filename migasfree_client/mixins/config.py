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
import logging
import os
import ssl
import sys
from urllib.parse import urljoin

from .. import mtls, settings, utils
from ..devices import Printer, get_available_devices_classes
from ..pms import Pms, get_available_pms
from ..url_request import UrlRequest

_ = gettext.gettext
logger = logging.getLogger('migasfree_client')


class ConfigMixin:
    """
    Mixin for configuration loading and initialization.
    Assumes it is mixed into a class that has:
    - self.migas_server, self.migas_protocol, self.migas_port
    - self.migas_project, self.migas_ssl_cert
    - self._debug, self.migas_proxy
    - self._url_base, self._url_request
    - self._mtls_cert, self._mtls_key, self._ca_cert
    - self.PRIVATE_KEY, self.PUBLIC_KEY
    - self.pms, self.devices_class
    - self.operation_failed()
    - self.operation_ok()
    - self._show_message()
    - self._write_error()
    - self.get_server_info()
    """

    def _ssl_cert(self):
        self.migas_ssl_cert = False
        if self.migas_protocol == 'https':
            port = self.migas_port if self.migas_port else 443

            if os.path.isfile(settings.CERT_FILE):
                os.remove(settings.CERT_FILE)

            try:
                cert = ssl.get_server_certificate((self.migas_server, port), ssl.PROTOCOL_SSLv23)
                if utils.write_file(settings.CERT_FILE, cert):
                    self.migas_ssl_cert = settings.CERT_FILE
            except ssl.SSLError:
                pass
            except OSError as e:
                _msg = _('Error getting server certificate: %s') % e
                self.operation_failed(_msg)
                sys.exit(errno.ECONNREFUSED)

    def _get_keys_path(self):
        return os.path.join(settings.KEYS_PATH, utils.sanitize_path(self.migas_server))

    def _init_url_base(self):
        self._url_base = '{}://{}{}'.format(
            self.migas_protocol, self.migas_server, f':{self.migas_port}' if self.migas_port else ''
        )

    def _init_mtls(self):
        """Initialize mTLS certificate paths, fetching from server if needed."""
        self._mtls_cert, self._mtls_key, self._ca_cert = mtls.get_mtls_credentials(self.migas_server)

        if self._mtls_cert and self._mtls_key:
            self._update_ca_certificate()
            self._enable_mtls()
            return

        self._fetch_mtls_from_server()

    def _update_ca_certificate(self):
        """Check and update CA certificate from server."""
        logger.info('Checking CA certificate...')
        ca_result = mtls.download_ca_certificate(self._url_base, self.migas_server)

        if ca_result['success']:
            self._ca_cert = ca_result['ca_file']
            if ca_result.get('updated'):
                logger.info('CA certificate updated')
        elif not ca_result.get('not_available'):
            logger.warning('Failed to download CA certificate: %s', ca_result['message'])

    def _enable_mtls(self):
        """Enable mTLS mode: force https protocol and update URL base."""
        self.migas_protocol = 'https'
        self._init_url_base()
        logger.info('mTLS enabled, protocol: https')

    def _fetch_mtls_from_server(self):
        """Attempt to fetch mTLS certificates from server."""
        logger.info('No mTLS credentials found, attempting to fetch from server...')

        url_request = UrlRequest(
            debug=self._debug,
            proxy=self.migas_proxy,
            cert=self.migas_ssl_cert,
        )

        result = mtls.fetch_and_install_mtls_certificate(
            url_request=url_request,
            server=self.migas_server,
            server_url=self._url_base,
            uuid=utils.get_hardware_uuid(),
            project_name=self.migas_project,
        )

        if result['success']:
            self._mtls_cert, self._mtls_key, self._ca_cert = mtls.get_mtls_credentials(self.migas_server)
            self._enable_mtls()
            logger.info('mTLS credentials installed successfully')
        elif not result.get('not_available'):
            logger.warning('Failed to fetch mTLS credentials: %s', result['message'])

    def _init_url_request(self):
        keys_path = self._get_keys_path()
        self._url_request = UrlRequest(
            debug=self._debug,
            proxy=self.migas_proxy,
            project=self.migas_project,
            keys={
                'private': os.path.join(keys_path, self.PRIVATE_KEY),
                'public': os.path.join(keys_path, self.PUBLIC_KEY),
            },
            cert=self.migas_ssl_cert,
            mtls_cert=self._mtls_cert,
            mtls_key=self._mtls_key,
            ca_cert=self._ca_cert,
        )

    def _fetch_mtls_certificates(self):
        """Fetch mTLS and CA certificates from server."""
        # Download CA certificate
        ca_result = mtls.download_ca_certificate(self._url_base, self.migas_server)
        if ca_result['success']:
            self._ca_cert = ca_result['ca_file']
            if ca_result.get('updated'):
                self.operation_ok(_('CA certificate downloaded'))
            else:
                self.operation_ok(_('CA certificate is up to date'))
        elif ca_result.get('not_available'):
            logger.info('CA certificate endpoint not available')
        else:
            self.operation_failed(_('Failed to download CA certificate: %s') % ca_result['message'])

        # Download mTLS certificates
        url_request = UrlRequest(
            debug=self._debug,
            proxy=self.migas_proxy,
            cert=self.migas_ssl_cert,
        )

        result = mtls.fetch_and_install_mtls_certificate(
            url_request=url_request,
            server=self.migas_server,
            server_url=self._url_base,
            uuid=utils.get_hardware_uuid(),
            project_name=self.migas_project,
        )

        if result['success']:
            self._mtls_cert, self._mtls_key, self._ca_cert = mtls.get_mtls_credentials(self.migas_server)
            self.operation_ok(_('mTLS certificates downloaded'))
        elif result.get('not_available'):
            logger.info('mTLS endpoint not available')
        else:
            self.operation_failed(_('Failed to download mTLS certificates: %s') % result['message'])

    def _init_command(self):
        self._ssl_cert()
        self._init_url_base()
        self._init_mtls()
        self.pms_selection()
        self._init_url_request()
        self.get_server_info()

    def api_protocol(self):
        return self.migas_protocol

    def api_endpoint(self, path):
        return urljoin(self._url_base, path)

    def _check_path(self, path):
        if not os.path.isdir(path):
            try:
                os.makedirs(path)
            except OSError:
                _msg = _('Error creating %s directory') % path
                self.operation_failed(_msg)
                logger.error(_msg)
                return False

        return True

    def _execute_path(self, path):
        self._check_path(path)
        files = os.listdir(path)
        for file_ in sorted(files):
            self._show_message(_('Running command %s...') % file_)
            _ret, _output, _error = utils.execute(os.path.join(path, file_), verbose=True, interactive=False)
            if _ret == 0:
                self.operation_ok()
            else:
                _msg = _('Command %s failed: %s') % (file_, _error)
                self.operation_failed(_msg)
                logger.error(_msg)
                self._write_error(_msg)

    def _check_user_is_root(self):
        if not utils.is_root_user():
            self.operation_failed(_('User has insufficient privileges to execute this command'))
            sys.exit(errno.EACCES)

    @staticmethod
    def _search_pms():
        cmd_to_find = 'command -v'
        if utils.is_windows():
            cmd_to_find = 'where'

        for item in get_available_pms():
            cmd = f'{cmd_to_find} {item[0]}'
            ret, _, _ = utils.execute(cmd, interactive=False)
            if ret == 0:
                return item[1]

        return None

    def pms_selection(self):
        pms_info = self._search_pms()
        logger.debug('PMS info: %s', pms_info)
        if not pms_info:
            return

        self.pms = Pms.factory(pms_info)()

    def _devices_class_selection(self):
        _class = None
        for item in get_available_devices_classes():
            _class = Printer.factory(item[1])(self.migas_server)
            if _class.platform == sys.platform:
                self.devices_class = _class
                return

    def _check_pms(self):
        if not self.pms:
            msg = _('Any PMS was not found. Cannot continue.')
            self.operation_failed(msg)
            logger.critical(msg)
            sys.exit(errno.EINPROGRESS)
