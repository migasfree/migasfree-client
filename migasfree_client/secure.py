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

__author__ = 'Jose Antonio Chavarría'
__license__ = 'GPLv3'

import json
import logging
from gettext import gettext

from jwcrypto import jwe, jwk, jws
from jwcrypto.common import json_encode

from .utils import read_file

ALG_SIGN = 'RS256'
ALG_ENC = 'RSA-OAEP-256'
ENC_CONTENT = 'A256CBC-HS512'
TYPE_JWE = 'JWE'

logger = logging.getLogger('migasfree_client')


def load_jwk(filename):
    """
    Loads a JWK from a PEM file

    Args:
        filename (str)

    Returns:
        jwk.JWK: loaded JWK object
    """
    return jwk.JWK.from_pem(read_file(filename))


def sign(claims, priv_key):
    """
    string sign(dict claims, string priv_key)
    """
    priv_jwk = load_jwk(priv_key)

    # Normalize to JSON string
    payload = json.dumps(claims) if isinstance(claims, dict) else claims
    payload_bytes = str(payload).encode('utf-8')

    jws_token = jws.JWS(payload_bytes)
    jws_token.add_signature(priv_jwk, header=json_encode({'alg': ALG_SIGN, 'kid': priv_jwk.thumbprint()}))

    return jws_token.serialize()


def verify(jwt, pub_key):
    """
    dict verify(string jwt, string pub_key)
    """
    pub_jwk = load_jwk(pub_key)

    jws_token = jws.JWS()
    jws_token.deserialize(jwt)
    jws_token.verify(pub_jwk)

    return jws_token.payload


def encrypt(claims, pub_key):
    """
    string encrypt(dict claims, string pub_key)
    """
    pub_jwk = load_jwk(pub_key)

    protected_header = {
        'alg': ALG_ENC,
        'enc': ENC_CONTENT,
        'typ': TYPE_JWE,
        'kid': pub_jwk.thumbprint(),
    }
    jwe_token = jwe.JWE(json.dumps(claims).encode('utf-8'), recipient=pub_jwk, protected=protected_header)

    return jwe_token.serialize()


def decrypt(jwt, priv_key):
    """
    string decrypt(string jwt, string priv_key)
    """
    priv_jwk = load_jwk(priv_key)

    jwe_token = jwe.JWE()
    jwe_token.deserialize(jwt, key=priv_jwk)
    payload = jwe_token.payload

    return payload.decode('utf-8') if isinstance(payload, bytes) else str(payload)


def wrap(data, sign_key, encrypt_key):
    """
    string wrap(dict data, string sign_key, string encrypt_key)
    """
    claims = {'data': data, 'sign': sign(data, sign_key)}

    return encrypt(claims, encrypt_key)


def unwrap(data, decrypt_key, verify_key):
    """
    dict unwrap(string data, string decrypt_key, string verify_key)
    """
    try:
        jwt = json.loads(decrypt(data, decrypt_key))
    except jwe.InvalidJWEData as e:
        logger.debug('exception: %s', str(e))
        logger.debug('data: %s', data)
        logger.debug('decrypt key: %s', decrypt_key)
        return gettext('Invalid Data')

    try:
        jws_token = verify(jwt['sign'], verify_key)
    except jws.InvalidJWSSignature as e:
        logger.debug('exception: %s', str(e))
        logger.debug('sign: %s', jwt['sign'])
        logger.debug('verify key: %s', verify_key)
        return gettext('Invalid Signature')

    return jwt['data'] if jws_token else None
