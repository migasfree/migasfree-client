# -*- coding: utf-8 -*-

# Copyright (c) 2011 Jose Antonio Chavarría
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
# Author: Alberto Gacías <agacias@ono.com>

__author__ = "Jose Antonio Chavarría"
__file__   = "secure.py"
__date__   = '2011-09-26'

import os
import json

import utils
import server_errors

def sign(filename, private_key):
    '''
    void sign(string filename, string private_key)
    Creates a temporal file named 'filename.sign'
    TODO find python equivalent
    '''

    os.system(
        "openssl dgst -sha1 -sign %s -out %s %s" % (
            private_key,
            '%s.sign' % filename,
            filename
        )
    )

def verify(filename, public_key):
    '''
    bool verify(string filename, string public_key)
    TODO find python equivalent
    '''

    return (os.system(
        "openssl dgst -sha1 -verify %s -signature %s %s 1>/dev/null" % (
            public_key,
            '%s.sign' % filename,
            filename
        )) == 0)

'''
def genKeysRSA(filename):
    # Private Key
    os.system("openssl genrsa -out %s.pri 2048" % filename)
    # Public Key
    os.system("openssl rsa -in %s.pri -pubout > %s.pub" % (filename, filename))
'''

def wrap(filename, data, key = None):
    '''
    void wrap(string filename, data, string key = None)
    Creates a JSON file with data
    If key, signs JSON file
    '''

    _f = open(filename, 'wb')
    json.dump(data, _f)
    _f.close()

    #os.system('less %s; read' % filename) # DEBUG

    if key:
        sign(filename, key)
        _f = open(filename, 'ab')
        _f.write(open('%s.sign' % filename, 'rb').read())
        _f.close()
        os.remove('%s.sign' % filename) # remove temp file (sign function)

def unwrap(filename, key = None):
    '''
    dict unwrap(string filename, string key = None)
    filename is a JSON file (signed or not)
    If key, verifies JSON file
    Returns data from filename or {} if sign is not verificable
    '''

    if key:
        _content = open(filename, 'rb').read()
        _n = len(_content)
        utils.write_file('%s.sign' % filename, _content[_n - 256:_n])
        utils.write_file(filename, _content[0:_n - 256])

    try:
        _data = json.loads(open(filename, 'rb').read())
    except ValueError:
        print filename
        return {} # no response in JSON format

    if not key:
        return _data

    if not verify(filename, key):
        #return {} # Sign not OK
        return {'errmfs': {'code': server_errors.SIGN_NOT_OK, 'info': ''}} # Sign not OK

    os.remove('%s.sign' % filename) # remove temp file (verify function)
    return _data
