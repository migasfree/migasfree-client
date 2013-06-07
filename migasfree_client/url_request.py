# -*- coding: UTF-8 -*-

# Copyright (c) 2011-2013 Jose Antonio Chavarría
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
__file__ = 'url_request.py'

import os
import sys
import errno
import logging
import pycurl

import secure
import curl
import utils
import server_errors

import gettext
_ = gettext.gettext

from settings import TMP_PATH


class UrlRequest(object):
    # default values
    _debug = False

    _sign = True
    _exit_on_error = True

    _proxy = ''
    _url_base = ''
    _cert = None

    def __init__(
        self,
        debug=False,
        proxy='',
        url_base='',
        info_keys={},
        cert=None
    ):
        self._debug = debug
        self._proxy = proxy
        self._url_base = url_base
        self._cert = cert

        logging.info('SSL certificate: %s', self._cert)

        if type(info_keys) is dict:
            self._path_keys = info_keys.get('path')
            self._private_key = info_keys.get('private')
            self._public_key = info_keys.get('public')

        if self._proxy:
            logging.info('Proxy selected: %s', self._proxy)

        if self._url_base:
            logging.info('URL base: %s', self._url_base)
        else:
            logging.critical('URL base not assigned!!!')

        if self._path_keys:
            logging.info('Path keys: %s', self._path_keys)

        if self._private_key:
            logging.info('Private key: %s', self._private_key)

        if self._public_key:
            logging.info('Public key: %s', self._public_key)

        # API changed in server 3.0
        self._filename_pattern = '%s.%s' % (
            utils.get_mfc_computer_name(),
            utils.get_hardware_uuid()
        )

    def run(
        self,
        cmd,
        data='',
        upload_file=None,
        sign=True,
        exit_on_error=True
    ):
        logging.debug('URL base: %s', self._url_base)
        logging.debug('URL command: %s', cmd)
        logging.debug('URL data: %s', data)
        logging.debug('URL upload file: %s', upload_file)
        logging.debug('Sign request: %s', sign)
        logging.debug('Exit on error: %s', exit_on_error)

        if not os.path.exists(TMP_PATH):
            try:
                os.makedirs(TMP_PATH, 0777)
            except:
                _msg = 'Error creating %s directory' % TMP_PATH
                logging.exception(_msg)
                return {
                    'errmfs': {
                        'info': _msg,
                        'code': server_errors.GENERIC
                    }
                }

        # API changed in server 3.0
        _filename = os.path.join(
            TMP_PATH,
            '%s.%s' % (
                self._filename_pattern,
                cmd
            )
        )
        if self._debug:
            print(_filename)
        if sign:
            secure.wrap(
                _filename,
                {cmd: data},
                key=os.path.join(self._path_keys, self._private_key)
            )
        else:
            secure.wrap(_filename, {cmd: data})

        _post = [
            ('message', (pycurl.FORM_FILE, _filename))
        ]
        if upload_file:
            _post.append(('package', (pycurl.FORM_FILE, upload_file)))

        logging.debug('Post data: %s', _post)

        _curl = curl.Curl(
            self._url_base,
            _post,
            proxy=self._proxy,
            cert=self._cert,
        )
        _curl.run()
        if not self._debug:
            os.remove(_filename)

        if _curl.error:
            _msg = _('Curl error: %s') % _curl.error
            logging.error(_msg)
            print(_msg)

            return {'errmfs': {'info': _msg, 'code': server_errors.GENERIC}}
            #sys.exit(errno.EBADRQC)

        if _curl.http_code >= 400:
            print(_('HTTP error code: %s') % _curl.http_code)
            if self._debug:
                _file = os.path.join(
                    TMP_PATH,
                    'response.%s.%s.html' % (
                        _curl.http_code,
                        cmd
                    )
                )
                utils.write_file(_file, str(_curl.body))
                print(_file)

            return {
                'errmfs': {
                    'info': str(_curl.body),
                    'code': server_errors.GENERIC
                }
            }
            #sys.exit(errno.EBADRQC)

        # evaluate response
        _response = '%s.return' % _filename
        utils.write_file(_response, str(_curl.body))
        if sign:
            _ret = secure.unwrap(
                _response,
                key=os.path.join(self._path_keys, self._public_key)
            )
        else:
            _ret = secure.unwrap(_response)

        if not self._debug:
            os.remove(_response)
        else:
            print(_response)

        if not type(_ret) is dict or not ('%s.return' % cmd) in _ret:
            if 'errmfs' in _ret:
    			_msg = server_errors.error_info(_ret['errmfs']['code'])
				logging.error(_msg)
				print(_msg)

            _msg = 'url_request unexpected response: %s. Expected: %s'
            if self._debug:
                print(_msg % (_ret, '%s.return' % cmd))

            logging.critical(_msg, _ret, '%s.return' % cmd)
            sys.exit(errno.EACCES)

        _ret = _ret['%s.return' % cmd]  # unwrapping cmd response
        if type(_ret) is dict and 'errmfs' in _ret:
            if _ret['errmfs']['code'] != server_errors.ALL_OK:
                _error = server_errors.error_info(_ret['errmfs']['code'])
                if self._debug:
                    print(_('Error: %s') % _error)
                    if _ret['errmfs']['info']:
                        print(_('Information: %s') % _ret['errmfs']['info'])
                logging.error(
                    'url_request server error response code: %s',
                    _error
                )
                logging.error(
                    'url_request server error response info: %s',
                    _ret['errmfs']['info']
                )
                if exit_on_error:
                    sys.exit(errno.EACCES)

        return _ret
