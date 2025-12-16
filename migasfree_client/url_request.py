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

import errno
import gettext
import json
import logging
import os
import sys

import requests
from requests_toolbelt import MultipartEncoder

from .secure import unwrap, wrap
from .settings import TMP_PATH
from .utils import build_magic, get_mfc_release, read_file, write_file

__author__ = 'Jose Antonio Chavarría'
__license__ = 'GPLv3'

_ = gettext.gettext
logger = logging.getLogger('migasfree_client')


class UrlRequest:
    __slots__ = (
        '_debug', '_safe', '_exit_on_error', '_proxy', '_cert',
        '_mtls_cert', '_mtls_key', '_ca_cert', '_timeout',
        '_private_key', '_public_key', '_project',
    )

    _ok_codes = frozenset([
        requests.codes.ok,
        requests.codes.created,
        requests.codes.moved,
        requests.codes.found,
        requests.codes.temporary_redirect,
        requests.codes.resume,
    ])

    def __init__(
        self, debug=False, proxy='', project='', keys=None, cert=False,
        mtls_cert=None, mtls_key=None, ca_cert=None, timeout=60,
    ):
        if keys is None:
            keys = {}

        self._debug = debug
        self._safe = True
        self._exit_on_error = True
        self._proxy = proxy
        self._project = project
        self._cert = cert
        self._mtls_cert = mtls_cert
        self._mtls_key = mtls_key
        self._ca_cert = ca_cert
        self._timeout = timeout
        self._private_key = keys.get('private')
        self._public_key = keys.get('public')

        logger.info('SSL certificate: %s', self._cert)
        if self._mtls_cert and self._mtls_key:
            logger.info('mTLS client certificate: %s', self._mtls_cert)
            logger.info('mTLS client key: %s', self._mtls_key)
            if self._ca_cert:
                logger.info('CA certificate for verification: %s', self._ca_cert)

        if self._proxy:
            logger.info('Proxy selected: %s', self._proxy)

    @staticmethod
    def _check_tmp_path():
        if not os.path.exists(TMP_PATH):
            try:
                os.makedirs(TMP_PATH, 0o0777)
            except OSError:
                return False

        return True

    def _build_default_headers(self):
        """Build default headers for HTTP requests."""
        return {
            'user-agent': f'migasfree-client/{get_mfc_release()} {requests.utils.default_user_agent()}',
            'accept-language': os.getenv('LANGUAGE', os.getenv('LANG', 'en')),
        }

    def run(self, url, data='', upload_files=None, safe=True, exit_on_error=True, debug=False, keys=None):
        """
        Make an HTTP POST request with signature/encryption support.

        This method wraps data using the migasfree signature/encryption protocol
        when safe=True. It also supports file uploads and mTLS client certificates.

        Args:
            url: The URL to send the request to
            data: Data to send (will be wrapped if safe=True)
            upload_files: List of file paths to upload
            safe: If True, wrap data with signature/encryption
            exit_on_error: If True, exit the program on error
            debug: Enable debug mode
            keys: Optional dict with 'private' and 'public' key paths

        Returns:
            On success: The unwrapped response data
            On error: {'error': {'info': str, 'code': int}}
        """
        if keys is None:
            keys = {}

        self._debug = debug

        self._exit_on_error = exit_on_error
        if 'private' in keys:
            self._private_key = keys.get('private')
        if 'public' in keys:
            self._public_key = keys.get('public')

        logger.debug('URL: %s', url)
        logger.debug('URL data: %s', data)
        logger.debug('Safe request: %s', safe)
        logger.debug('Exit on error: %s', exit_on_error)

        if self._private_key:
            logger.info('Private key: %s', self._private_key)

        if self._public_key:
            logger.info('Public key: %s', self._public_key)

        headers = self._build_default_headers()
        if safe:
            data = json.dumps(
                {'msg': wrap(data, sign_key=self._private_key, encrypt_key=self._public_key), 'project': self._project}
            )
            headers['content-type'] = 'application/json'

        if upload_files:
            data, headers = self._prepare_upload_files(upload_files, data, safe, headers)

        proxies = None
        if self._proxy:
            proxies = {
                'http': self._proxy,
                'https': self._proxy,
            }

        if not url.endswith('/'):
            url += '/'

        cert_param = None
        verify_param = False
        if self._mtls_cert and self._mtls_key:
            cert_param = (self._mtls_cert, self._mtls_key)
            verify_param = self._ca_cert if self._ca_cert else False

        try:
            req = requests.post(
                url,
                data=data,
                headers=headers,
                proxies=proxies,
                timeout=self._timeout,
                cert=cert_param,
                verify=verify_param,
            )
        except requests.exceptions.ConnectionError as e:
            logger.error('Connection error: %s', e)
            return {'error': {'info': str(e), 'code': errno.ECONNREFUSED}}
        except requests.exceptions.Timeout as e:
            logger.error('Request timeout: %s', e)
            return {'error': {'info': str(e), 'code': errno.ETIMEDOUT}}
        except requests.exceptions.RequestException as e:
            logger.error('Request error: %s', e)
            return {'error': {'info': str(e), 'code': errno.EIO}}

        if req.status_code not in self._ok_codes:
            return self._error_response(req, url)

        return self._evaluate_response(req.json(), safe)

    def _prepare_upload_files(self, upload_files, data, safe, headers):
        """Prepare files for multipart upload."""
        my_magic = build_magic()
        files = []

        for _file in upload_files:
            content = read_file(_file)
            tmp_file = os.path.join(TMP_PATH, os.path.basename(_file))
            write_file(tmp_file, content[0:1023])  # only header
            mime = my_magic.file(tmp_file)
            os.remove(tmp_file)
            files.append(('file', (_file, content, mime)))

        logger.debug('URL upload files: %s', files)

        if safe:
            data = json.loads(data)

        fields = data
        fields.update(dict(files))
        data = MultipartEncoder(fields=fields)
        headers['content-type'] = data.content_type

        return data, headers

    def run_simple(self, url, data=None, json_data=None, headers=None, timeout=None, download=False):
        """
        Make a simple HTTP POST request without signature/encryption logic.

        This method is useful for public endpoints that don't require
        the migasfree signature/encryption protocol.

        Args:
            url: The URL to send the request to
            data: Form data to send (for application/x-www-form-urlencoded)
            json_data: JSON data to send (for application/json)
            headers: Optional additional headers
            timeout: Request timeout in seconds (default: self._timeout)
            download: If True, return raw response content for binary downloads

        Returns:
            dict: On success: {'data': response_data} or {'data': response_data, 'content': bytes}
                  On error: {'error': {'info': str, 'code': int}}
        """
        if timeout is None:
            timeout = self._timeout

        request_headers = self._build_default_headers()
        if headers:
            request_headers.update(headers)

        proxies = None
        if self._proxy:
            proxies = {
                'http': self._proxy,
                'https': self._proxy,
            }

        logger.debug('Simple request URL: %s', url)
        logger.debug('Simple request data: %s', data)
        logger.debug('Simple request json: %s', json_data)

        try:
            req = requests.post(
                url,
                data=data,
                json=json_data,
                headers=request_headers,
                proxies=proxies,
                timeout=timeout,
                verify=self._cert if self._cert else False,
            )

            # Handle 404 as "not available" (e.g., mTLS service not deployed)
            if req.status_code == requests.codes.not_found:
                logger.debug('Endpoint not available (404): %s', url)
                return {'error': {'info': '', 'code': requests.codes.not_found}}

            if req.status_code in self._ok_codes:
                if download:
                    return {'data': None, 'content': req.content}
                try:
                    return {'data': req.json()}
                except ValueError:
                    return {'data': None, 'content': req.content}

            logger.error('Simple request failed with status %d: %s', req.status_code, req.text)
            return {'error': {'info': req.text, 'code': req.status_code}}

        except requests.exceptions.ConnectionError as e:
            logger.error('Connection error: %s', str(e))
            return {'error': {'info': str(e), 'code': errno.ECONNREFUSED}}
        except requests.exceptions.Timeout as e:
            logger.error('Request timeout: %s', str(e))
            return {'error': {'info': str(e), 'code': errno.ETIMEDOUT}}
        except Exception as e:
            logger.error('Request error: %s', str(e))
            return {'error': {'info': str(e), 'code': errno.EIO}}

    def _evaluate_response(self, json_response, safe=True):
        if safe and 'msg' in json_response:
            response = unwrap(json_response['msg'], decrypt_key=self._private_key, verify_key=self._public_key)
        else:
            response = json_response.get('detail', json_response) if isinstance(json_response, dict) else json_response

        logger.debug('Response text: %s', response)

        return response

    def _error_response(self, request, url):
        logger.error('url_request server error response code: %s', request.status_code)
        logger.error('url_request server error response info: %s', request.text)

        content_type = request.headers.get('content-type', '')
        is_json = 'json' in content_type
        info = self._evaluate_response(request.json()) if is_json else request.text

        if self._debug:
            print(_('HTTP error code: %s') % request.status_code)

            if not self._check_tmp_path():
                msg = _('Error creating %s directory') % TMP_PATH
                logger.exception(msg)
                print(msg)
                if self._exit_on_error:
                    sys.exit(errno.EPERM)

                return {'error': {'info': msg, 'code': errno.EPERM}}

            extension = 'txt' if is_json else 'html'
            _file = os.path.join(
                TMP_PATH,
                f'response.{request.status_code}.{url.replace("/", ".").replace(":", ".").rstrip(".")}.{extension}',
            )
            write_file(_file, str(info))
            print(_file)

        if self._exit_on_error:
            if 'html' not in content_type:
                print(_('Error: %s') % info)
            else:
                print(_('Status code: %s') % request.status_code)
            sys.exit(errno.EACCES)

        return {'error': {'info': str(info), 'code': request.status_code}}
