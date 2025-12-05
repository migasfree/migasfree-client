# Copyright (c) 2025 Jose Antonio Chavarría <jachavar@gmail.com>
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

import gettext
import logging
import os
import secrets
import tarfile
import tempfile

import requests
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12

from . import settings, utils

__author__ = 'Jose Antonio Chavarría'
__license__ = 'GPLv3'

_ = gettext.gettext
logger = logging.getLogger('migasfree_client')


def import_mtls_certificate(cert_tar_file, password=None):
    """
    Import mTLS certificate from a tar file.

    This function extracts the certificate and key from a tar file containing
    a .p12 (PKCS#12) file, converts them to PEM format, and saves them to
    the appropriate locations.

    Args:
        cert_tar_file: Path to the certificate tar file
        password: Password for the p12 file (if encrypted)

    Returns:
        dict: {'success': bool, 'message': str}
    """
    if not os.path.isfile(cert_tar_file):
        return {'success': False, 'message': _('Certificate file not found: %s') % cert_tar_file}

    logger.info('Importing mTLS certificate from: %s', cert_tar_file)

    try:
        if not os.path.exists(settings.CERT_PATH):
            os.makedirs(settings.CERT_PATH, mode=0o755)
            logger.info('Created certificate directory: %s', settings.CERT_PATH)

        with tempfile.TemporaryDirectory() as temp_dir:
            logger.debug('Extracting tar file to: %s', temp_dir)

            with tarfile.open(cert_tar_file, 'r') as tar:
                tar.extractall(path=temp_dir)

                p12_file = None
                for file in os.listdir(temp_dir):
                    if file.endswith('.p12'):
                        p12_file = os.path.join(temp_dir, file)
                        break

                if not p12_file:
                    return {'success': False, 'message': _('No .p12 file found in tar archive')}

                logger.info('Found p12 file: %s', p12_file)

                result = _extract_from_p12(p12_file, password=password)
                if not result['success']:
                    return result

                logger.info('Successfully imported mTLS certificate')
                return {
                    'success': True,
                    'message': _('mTLS certificate imported successfully.\nCertificate: %s\nKey: %s')
                    % (settings.MTLS_CERT_FILE, settings.MTLS_KEY_FILE),
                }

    except tarfile.TarError as e:
        logger.error('Error extracting tar file: %s', str(e))
        return {'success': False, 'message': _('Error extracting tar file: %s') % str(e)}
    except Exception as e:
        logger.error('Error importing certificate: %s', str(e))
        return {'success': False, 'message': _('Error importing certificate: %s') % str(e)}


def _extract_from_p12(p12_file, password=None):
    """
    Extract certificate and private key from a PKCS#12 file.

    Args:
        p12_file: Path to the .p12 file
        password: Password for the p12 file (if encrypted)

    Returns:
        dict: {'success': bool, 'message': str}
    """
    try:
        with open(p12_file, 'rb') as f:
            p12_data = f.read()

        try:
            password_bytes = password.encode() if password else None
            private_key, certificate, _additional_certs = pkcs12.load_key_and_certificates(
                p12_data, password=password_bytes, backend=default_backend()
            )
        except Exception as e:
            logger.error('Failed to load p12 file: %s', str(e))
            return {
                'success': False,
                'message': _('Failed to load p12 file: %s') % str(e),
            }

        if not certificate:
            return {'success': False, 'message': _('No certificate found in p12 file')}

        if not private_key:
            return {'success': False, 'message': _('No private key found in p12 file')}

        cert_pem = certificate.public_bytes(serialization.Encoding.PEM)
        key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )

        utils.write_file(settings.MTLS_CERT_FILE, cert_pem.decode('utf-8'))
        logger.info('Wrote certificate to: %s', settings.MTLS_CERT_FILE)

        utils.write_file(settings.MTLS_KEY_FILE, key_pem.decode('utf-8'))
        os.chmod(settings.MTLS_KEY_FILE, 0o600)  # Secure permissions for private key
        logger.info('Wrote private key to: %s', settings.MTLS_KEY_FILE)

        return {'success': True, 'message': _('Certificate and key extracted successfully')}

    except Exception as e:
        logger.error('Error extracting from p12: %s', str(e))
        return {'success': False, 'message': _('Error extracting from p12: %s') % str(e)}


def has_mtls_certificate():
    """
    Check if mTLS certificate and key files exist.

    Returns:
        bool: True if both certificate and key files exist, False otherwise
    """
    cert_exists = os.path.isfile(settings.MTLS_CERT_FILE)
    key_exists = os.path.isfile(settings.MTLS_KEY_FILE)

    if cert_exists and key_exists:
        logger.info('mTLS certificate found at: %s', settings.MTLS_CERT_FILE)
        return True

    if cert_exists and not key_exists:
        logger.warning('Certificate exists but key is missing at: %s', settings.MTLS_KEY_FILE)
    elif key_exists and not cert_exists:
        logger.warning('Key exists but certificate is missing at: %s', settings.MTLS_CERT_FILE)

    return False


def get_mtls_credentials():
    """
    Get the paths to mTLS certificate and key files if they exist.

    Returns:
        tuple: (cert_path, key_path) or (None, None) if files don't exist
    """
    if has_mtls_certificate():
        return settings.MTLS_CERT_FILE, settings.MTLS_KEY_FILE

    return None, None


def request_mtls_token(url_request, server_url, uuid, project_name, validity_days=None):
    """
    Request an mTLS token from the server.

    Args:
        url_request: UrlRequest instance to use for the request
        server_url: Base URL of the migasfree server
        uuid: Computer's hardware UUID
        project_name: Name of the project
        validity_days: Certificate validity in days (default from settings)

    Returns:
        dict: {'success': bool, 'token': str or None, 'message': str}
    """
    if validity_days is None:
        validity_days = settings.MTLS_DEFAULT_VALIDITY_DAYS

    endpoint = f'{server_url}/manager/v1/public/mtls/computer-tokens'
    payload = {
        'uuid': uuid,
        'project_name': project_name,
        'validity_days': validity_days,
    }

    logger.info('Requesting mTLS token from: %s', endpoint)
    logger.debug('Token request payload: %s', payload)

    result = url_request.run_simple(
        endpoint,
        json_data=payload,
        headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
    )

    if 'error' in result:
        # Handle not available (404) - silently skip
        if result['error'].get('code') == requests.codes.not_found:
            return {'success': False, 'token': None, 'message': '', 'not_available': True}

        return {
            'success': False,
            'token': None,
            'message': _('Token request failed: %s') % result['error'].get('info', ''),
        }

    token = result.get('data', {}).get('token')
    if token:
        logger.info('Successfully obtained mTLS token')
        return {'success': True, 'token': token, 'message': _('Token obtained successfully')}

    return {'success': False, 'token': None, 'message': _('No token in server response')}


def download_mtls_certificate(url_request, server_url, token, output_path):
    """
    Download the mTLS certificate tar file from the server.

    Args:
        url_request: UrlRequest instance to use for the request
        server_url: Base URL of the migasfree server
        token: Token obtained from request_mtls_token()
        output_path: Path where to save the downloaded tar file

    Returns:
        dict: {'success': bool, 'file_path': str or None, 'message': str, 'password': str}
    """
    password = secrets.token_urlsafe(16)

    endpoint = f'{server_url}/manager/v1/public/mtls/computer-certificates'
    payload = {
        'token': token,
        'email': '',
        'password': password,
    }

    logger.info('Downloading mTLS certificate from: %s', endpoint)

    result = url_request.run_simple(
        endpoint,
        data=payload,
        timeout=120,
        download=True,
    )

    if 'error' in result:
        return {
            'success': False,
            'file_path': None,
            'message': _('Download failed: %s') % result['error'].get('info', ''),
        }

    content = result.get('content')
    if content:
        utils.write_file(output_path, content)
        logger.info('Certificate downloaded to: %s', output_path)
        return {
            'success': True,
            'file_path': output_path,
            'message': _('Certificate downloaded successfully'),
            'password': password,
        }

    return {'success': False, 'file_path': None, 'message': _('No content in response')}


def fetch_and_install_mtls_certificate(url_request, server_url, uuid, project_name):
    """
    Complete workflow: request token, download certificate, and install it.

    Args:
        url_request: UrlRequest instance to use for the requests
        server_url: Base URL of the migasfree server
        uuid: Computer's hardware UUID
        project_name: Name of the project

    Returns:
        dict: {'success': bool, 'message': str}
    """
    logger.info('Starting automatic mTLS certificate fetch for project: %s', project_name)

    # Step 1: Request token
    token_result = request_mtls_token(url_request, server_url, uuid, project_name)
    if not token_result['success']:
        return {
            'success': False,
            'message': token_result['message'],
            'not_available': token_result.get('not_available', False),
        }

    # Step 2: Download certificate
    with tempfile.NamedTemporaryFile(suffix='.tar', delete=False) as tmp_file:
        tar_path = tmp_file.name

    try:
        download_result = download_mtls_certificate(url_request, server_url, token_result['token'], tar_path)
        if not download_result['success']:
            return {'success': False, 'message': download_result['message']}

        # Step 3: Import certificate
        import_result = import_mtls_certificate(tar_path, password=download_result.get('password'))
        return import_result
    finally:
        if os.path.exists(tar_path):
            os.unlink(tar_path)
            logger.debug('Cleaned up temporary file: %s', tar_path)
