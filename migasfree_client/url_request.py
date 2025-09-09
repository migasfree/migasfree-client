# -*- coding: UTF-8 -*-

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

import os
import sys
import errno
import json
import gettext
import logging
import requests

from requests_toolbelt import MultipartEncoder

from .settings import TMP_PATH
from .secure import wrap, unwrap
from .utils import get_mfc_release, build_magic, read_file, write_file

__author__ = 'Jose Antonio Chavarría'
__license__ = 'GPLv3'

_ = gettext.gettext
logger = logging.getLogger('migasfree_client')


class UrlRequest:
    _debug = False

    _safe = True
    _exit_on_error = True

    _proxy = ''
    _cert = False

    _timeout = 60  # seconds

    _ok_codes = [
        requests.codes.ok,
        requests.codes.created,
        requests.codes.moved,
        requests.codes.found,
        requests.codes.temporary_redirect,
        requests.codes.resume,
    ]

    def __init__(self, debug=False, proxy='', project='', keys=None, cert=False):
        if keys is None:
            keys = {}

        self._debug = debug
        self._proxy = proxy
        self._project = project
        self._cert = cert

        logger.info('SSL certificate: %s', self._cert)

        if isinstance(keys, dict):
            self._private_key = keys.get('private')
            self._public_key = keys.get('public')

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

    def run(self, url, data='', upload_files=None, safe=True, exit_on_error=True, debug=False, keys=None):
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

        headers = {
            'user-agent': f'migasfree-client/{get_mfc_release()} {requests.utils.default_user_agent()}',
            'accept-language': os.getenv('LANGUAGE', os.getenv('LANG', 'en')),
        }
        if safe:
            data = json.dumps(
                {'msg': wrap(data, sign_key=self._private_key, encrypt_key=self._public_key), 'project': self._project}
            )
            headers['content-type'] = 'application/json'

        if upload_files:
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
            # http://stackoverflow.com/questions/19439961/python-requests-post-json-and-file-in-single-request
            if safe:
                data = json.loads(data)

            fields = data
            fields.update(dict(files))
            data = MultipartEncoder(fields=fields)
            headers['content-type'] = data.content_type

        proxies = None
        if self._proxy:
            proxies = {
                'http': self._proxy,
                'https': self._proxy,
            }

        if not url.endswith('/'):
            url += '/'

        try:
            req = requests.post(url, data=data, headers=headers, proxies=proxies, timeout=self._timeout)
        except requests.exceptions.ConnectionError as e:
            logger.error(str(e))
            return {'error': {'info': e, 'code': errno.ECONNREFUSED}}
        except requests.exceptions.ReadTimeout as e:
            logger.error(str(e))
            return {'error': {'info': e, 'code': errno.ETIMEDOUT}}

        if req.status_code not in self._ok_codes:
            return self._error_response(req, url)

        return self._evaluate_response(req.json(), safe)

    def _evaluate_response(self, json_response, safe=True):
        if safe and 'msg' in json_response:
            response = unwrap(json_response['msg'], decrypt_key=self._private_key, verify_key=self._public_key)
        else:
            if isinstance(json_response, dict):
                response = json_response.get('detail', json_response)
            else:
                response = json_response

        logger.debug('Response text: %s', response)

        return response

    def _error_response(self, request, url):
        logger.error('url_request server error response code: %s', str(request.status_code))
        logger.error('url_request server error response info: %s', str(request.text))

        info = request.text
        if 'json' in request.headers['content-type']:
            info = self._evaluate_response(request.json())

        if self._debug:
            print(_('HTTP error code: %s') % request.status_code)

            if not self._check_tmp_path():
                msg = _('Error creating %s directory') % TMP_PATH
                logger.exception(msg)
                print(msg)
                if self._exit_on_error:
                    sys.exit(errno.EPERM)

                return {'error': {'info': msg, 'code': errno.EPERM}}

            extension = 'txt' if 'json' in request.headers['content-type'] else 'html'
            _file = os.path.join(
                TMP_PATH,
                'response.{}.{}.{}'.format(
                    request.status_code, url.replace('/', '.').replace(':', '.').rstrip('.'), extension
                ),
            )
            write_file(_file, str(info))
            print(_file)

        if self._exit_on_error:
            if 'html' not in request.headers['content-type']:
                print(_('Error: %s') % str(info))
            else:
                print(_('Status code: %s') % str(request.status_code))
            sys.exit(errno.EACCES)

        return {'error': {'info': str(info), 'code': request.status_code}}
