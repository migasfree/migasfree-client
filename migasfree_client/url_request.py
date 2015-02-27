# -*- coding: UTF-8 -*-

# Copyright (c) 2011-2015 Jose Antonio Chavarría
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
#
# Author: Jose Antonio Chavarría <jachavar@gmail.com>

__author__ = 'Jose Antonio Chavarría'
__license__ = 'GPLv3'

import os
import sys
import errno
import logging
import requests
import json

import secure
import utils

import gettext
_ = gettext.gettext

from . import settings


class UrlRequest(object):
    _debug = False

    _safe = True
    _exit_on_error = True

    _proxy = ''
    _url_base = ''
    _cert = None

    def __init__(
        self,
        debug=False,
        proxy='',
        url_base='',
        project='',
        keys={},
        cert=None
    ):
        self._debug = debug
        self._proxy = proxy
        self._url_base = url_base
        self._project = project
        self._cert = cert

        logging.info('SSL certificate: %s', self._cert)

        if type(keys) is dict:
            self._private_key = keys.get('private')
            self._public_key = keys.get('public')

        if self._proxy:
            logging.info('Proxy selected: %s', self._proxy)

        if self._url_base:
            logging.info('URL base: %s', self._url_base)
        else:
            logging.critical('URL base not assigned!!!')

        if self._private_key:
            logging.info('Private key: %s', self._private_key)

        if self._public_key:
            logging.info('Public key: %s', self._public_key)

    def _check_tmp_path(self):
        if not os.path.exists(settings.TMP_PATH):
            try:
                os.makedirs(settings.TMP_PATH, 0777)
            except:
                return False

        return True

    def run(
        self,
        end_point,
        data='',
        upload_file=None,
        safe=True,
        exit_on_error=True
    ):
        self._exit_on_error = exit_on_error

        logging.debug('URL base: %s', self._url_base)
        logging.debug('URL end point: %s', end_point)
        logging.debug('URL data: %s', data)
        logging.debug('URL upload file: %s', upload_file)
        logging.debug('Safe request: %s', safe)
        logging.debug('Exit on error: %s', exit_on_error)

        headers = None
        if safe:
            data = json.dumps({
                'msg': secure.wrap(
                    data,
                    sign_key=self._private_key,
                    encrypt_key=self._public_key
                ),
                'project': self._project
            })
            headers = {'content-type': 'application/json'}

        # FIXME multiple files
        files = None
        if upload_file:
            files = {'file': utils.read_file(upload_file)}

        proxies = None
        if self._proxy:
            proxies = {
              "http": self._proxy,
              "https": self._proxy,
            }

        url = self._url_base + end_point
        if not url.endswith('/'):
            url += '/'

        r = requests.post(
            url, data=data, headers=headers,
            files=files, proxies=proxies, cert=self._cert
        )

        if r.status_code != requests.codes.ok:
            self._error_response(r, end_point)

        return self._evaluate_response(r.json(), safe)

    def _evaluate_response(self, json, safe):
        if safe:
            response = secure.unwrap(
                json['msg'],
                decrypt_key=self._private_key,
                verify_key=self._public_key
            )
        else:
            response = json

        logging.debug('Response text: %s' % response)
        if self._debug:
            print(response)

        return response

    def _error_response(self, request, end_point):
        logging.error(
            'url_request server error response code: %s',
            str(request.status_code)
        )
        logging.error(
            'url_request server error response info: %s',
            str(request.text)
        )

        print(_('HTTP error code: %s') % request.status_code)
        if self._debug:
            if not self._check_tmp_path():
                msg = _('Error creating %s directory') % settings.TMP_PATH
                logging.exception(_msg)
                print(msg)
                if self._exit_on_error:
                    sys.exit(errno.EPERM)

                return {
                    'error': {
                        'info': msg,
                        'code': errno.EPERM
                    }
                }

            extension = 'txt' if 'json' in request.headers['content-type'] else 'html'
            _file = os.path.join(
                settings.TMP_PATH,
                'response.%s.%s.%s' % (
                    request.status_code,
                    end_point.replace('/', '.').rstrip('.'),
                    extension
                )
            )
            utils.write_file(_file, str(request.text))
            print(_file)

        if exit_on_error:
            print(_('Error: %s') % str(request.text))
            sys.exit(errno.EACCES)

        return {
            'error': {
                'info': str(request.text),
                'code': request.status_code
            }
        }
