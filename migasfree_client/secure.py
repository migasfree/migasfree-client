# -*- coding: utf-8 -*-

# Copyright (c) 2011-2019 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2011-2019 Alberto Gacías <alberto@migasfree.org>
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
import json

from . import utils, server_errors

__author__ = 'Jose Antonio Chavarría'
__license__ = 'GPLv3'

# TODO common code between server & client


def sign(filename, private_key):
    """
    void sign(string filename, string private_key)
    Creates a temporal file named 'filename.sign'
    TODO find python equivalent
    """

    os.system(
        "openssl dgst -sha1 -sign %s -out %s %s" % (
            private_key,
            '{0}.sign'.format(filename),
            filename
        )
    )


def verify(filename, public_key):
    """
    bool verify(string filename, string public_key)
    TODO find python equivalent
    """

    return (os.system(
        "openssl dgst -sha1 -verify %s -signature %s %s 1>/dev/null" % (
            public_key,
            '{0}.sign'.format(filename),
            filename
        )) == 0)


def wrap(filename, data, key=None):
    """
    void wrap(string filename, data, string key = None)
    Creates a JSON file with data
    If key, signs JSON file
    """

    data = json.dumps(data)
    if sys.version_info.major > 2:
        data = data.encode()

    with open(filename, 'wb') as _fp:
        _fp.write(data)

    # os.system('less %s; read' % filename)  # DEBUG

    if key:
        sign(filename, key)
        with open(filename, 'ab') as _fp:
            _fp.write(open('{0}.sign'.format(filename), 'rb').read())
        os.remove('{0}.sign'.format(filename))  # remove temp file (sign function)


def unwrap(filename, key=None):
    """
    dict unwrap(string filename, string key = None)
    filename is a JSON file (signed or not)
    If key, verifies JSON file
    Returns data from filename or {} if sign is not verificable
    """

    if key:
        _content = open(filename, 'rb').read()
        _n = len(_content)
        utils.write_file('{0}.sign'.format(filename), _content[_n - 256:_n])
        utils.write_file(filename, _content[0:_n - 256])

    try:
        _content = open(filename, 'rb').read()
        if sys.version_info.major < 3:
            _data = json.loads(_content)
        else:
            _data = json.loads(str(_content, encoding='utf8'))
    except ValueError:
        print(_('No response'), filename)
        return {}  # no response in JSON format

    if not key:
        return _data

    if not verify(filename, key):
        return {
            'errmfs': {
                'code': server_errors.INVALID_SIGNATURE,
                'info': ''
            }
        }

    os.remove('{0}.sign'.format(filename))  # remove temp file (verify function)
    return _data
