# -*- coding: utf-8 -*-

# Copyright (c) 2011-2019 Jose Antonio Chavarría <jachavar@gmail.com>
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

__author__ = "Jose Antonio Chavarría"
__license__ = 'GPLv3'

import sys
import errno
import json

from jwcrypto import jwk, jwe, jws
from jwcrypto.common import json_encode

from .utils import read_file
from . import settings

import logging
try:
    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s',
        level=logging.ERROR,
        filename=settings.LOG_FILE
    )
except IOError:
    print('User has insufficient privileges to execute this command')
    sys.exit(errno.EACCES)
logger = logging.getLogger(__name__)


def sign(claims, priv_key):
    """
    string sign(dict claims, string priv_key)
    """
    priv_jwk = jwk.JWK.from_pem(read_file(priv_key))

    if isinstance(claims, dict):
        claims = json.dumps(claims)

    jws_token = jws.JWS(str(claims))
    jws_token.add_signature(
        priv_jwk,
        header=json_encode({'alg': 'RS256', "kid": priv_jwk.thumbprint()})
    )

    return jws_token.serialize()


def verify(jwt, pub_key):
    """
    dict verify(string jwt, string pub_key)
    """
    pub_jwk = jwk.JWK.from_pem(read_file(pub_key))

    jws_token = jws.JWS()
    jws_token.deserialize(jwt)
    jws_token.verify(pub_jwk)

    return jws_token.payload


def encrypt(claims, pub_key):
    """
    string encrypt(dict claims, string pub_key)
    """
    pub_jwk = jwk.JWK.from_pem(read_file(pub_key))

    protected_header = {
        "alg": "RSA-OAEP-256",
        "enc": "A256CBC-HS512",
        "typ": "JWE",
        "kid": pub_jwk.thumbprint(),
    }
    jwe_token = jwe.JWE(
        json.dumps(claims),
        recipient=pub_jwk,
        protected=protected_header
    )
    jwt = jwe_token.serialize()

    return jwt


def decrypt(jwt, priv_key):
    """
    string decrypt(string jwt, string priv_key)
    """
    priv_jwk = jwk.JWK.from_pem(read_file(priv_key))

    jwe_token = jwe.JWE()
    jwe_token.deserialize(jwt, key=priv_jwk)

    if isinstance(jwe_token.payload, bytes) \
            and not isinstance(jwe_token.payload, str):
        return str(jwe_token.payload, encoding='utf8')
    
    return jwe_token.payload


def wrap(data, sign_key, encrypt_key):
    """
    string wrap(dict data, string sign_key, string encrypt_key)
    """
    claims = {
        'data': data,
        'sign': sign(data, sign_key)
    }
    return encrypt(claims, encrypt_key)


def unwrap(data, decrypt_key, verify_key):
    """
    dict unwrap(string data, string decrypt_key, string verify_key)
    """
    jwt = json.loads(decrypt(data, decrypt_key))
    jws_token = verify(jwt['sign'], verify_key)
    if jws_token:
        return jwt['data']

    return None
