# Copyright (c) 2025-2026 Jose Antonio Chavarría <jachavar@gmail.com>
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

import logging.config
import os
import ssl
import sys
import tempfile
from unittest.mock import MagicMock

import pytest
from jwcrypto import jwk

import migasfree_client.settings as settings

# Force locale to C to avoid translated error messages in tests
os.environ['LC_ALL'] = 'C'
os.environ['LANGUAGE'] = 'C'
os.environ['LANG'] = 'C'

# Create temporary directory for tests
TEST_TMP_DIR = os.path.join(tempfile.gettempdir(), 'migasfree-tests')
if not os.path.exists(TEST_TMP_DIR):
    os.makedirs(TEST_TMP_DIR)

# Override critical paths
settings.LOG_FILE = os.path.join(TEST_TMP_DIR, 'migasfree.log')
settings.TMP_PATH = TEST_TMP_DIR
settings.CERT_FILE = os.path.join(TEST_TMP_DIR, 'cert.pem')
settings.KEYS_PATH = os.path.join(TEST_TMP_DIR, 'keys')
settings.CONF_FILE = os.path.join(TEST_TMP_DIR, 'migasfree.conf')
settings.SOFTWARE_FILE = os.path.join(TEST_TMP_DIR, 'installed_software.txt')
settings.TRAITS_FILE = os.path.join(TEST_TMP_DIR, 'computer_traits.json')
settings.MTLS_PATH = os.path.join(TEST_TMP_DIR, 'mtls')

# Prevent MigasFreeCommand from re-opening stdout/stderr which breaks pytest
original_fdopen = os.fdopen


def mocked_fdopen(fd, *args, **kwargs):
    try:
        if fd in (sys.stdout.fileno(), sys.stderr.fileno()):
            return sys.stdout if fd == sys.stdout.fileno() else sys.stderr
    except (AttributeError, ValueError):
        pass
    return original_fdopen(fd, *args, **kwargs)


os.fdopen = mocked_fdopen

# Mock logging config to avoid EACCES or other issues during import
logging.config.dictConfig = MagicMock()

# Mock ssl.get_server_certificate globally to avoid real network calls during tests
ssl.get_server_certificate = MagicMock(return_value='-----BEGIN CERTIFICATE-----\nDummy\n-----END CERTIFICATE-----')


@pytest.fixture
def tmp_dir(tmp_path):
    return str(tmp_path)


@pytest.fixture
def private_key_path(tmp_path):
    key = jwk.JWK.generate(kty='RSA', size=2048)
    export = key.export_to_pem(private_key=True, password=None)
    key_file = tmp_path / 'private.pem'
    key_file.write_bytes(export)
    return str(key_file)


@pytest.fixture
def public_key_path(tmp_path, private_key_path):
    with open(private_key_path, 'rb') as f:
        key = jwk.JWK.from_pem(f.read())
    export = key.export_to_pem(private_key=False)
    key_file = tmp_path / 'public.pem'
    key_file.write_bytes(export)
    return str(key_file)
