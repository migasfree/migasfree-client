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

from .settings import MTLS_DEFAULT_VALIDITY_DAYS, MTLS_PATH
from .utils import read_file, sanitize_path, write_file

__author__ = 'Jose Antonio Chavarría'
__license__ = 'GPLv3'

_ = gettext.gettext
logger = logging.getLogger('migasfree_client')


def get_mtls_path(server):
    """
    Get the mTLS certificate directory path for a specific server.

    Args:
        server: Server hostname or identifier

    Returns:
        str: Path to the mTLS directory for this server (MTLS_PATH/server/)
    """
    return os.path.join(MTLS_PATH, sanitize_path(server))


def get_mtls_cert_file(server):
    """
    Get the mTLS certificate file path for a specific server.

    Args:
        server: Server hostname or identifier

    Returns:
        str: Path to the certificate file (MTLS_PATH/server/cert.pem)
    """
    return os.path.join(get_mtls_path(server), 'cert.pem')


def get_mtls_key_file(server):
    """
    Get the mTLS key file path for a specific server.

    Args:
        server: Server hostname or identifier

    Returns:
        str: Path to the key file (MTLS_PATH/server/key.pem)
    """
    return os.path.join(get_mtls_path(server), 'key.pem')


def get_mtls_ca_file(server):
    """
    Get the CA certificate file path for a specific server.

    Args:
        server: Server hostname or identifier

    Returns:
        str: Path to the CA certificate file (MTLS_PATH/server/ca.pem)
    """
    return os.path.join(get_mtls_path(server), 'ca.pem')


def import_mtls_certificate(cert_tar_file, server, password=None):
    """
    Import mTLS certificate from a tar file.

    This function extracts the certificate and key from a tar file containing
    a .p12 (PKCS#12) file, converts them to PEM format, and saves them to
    the appropriate locations for the specified server.

    Args:
        cert_tar_file: Path to the certificate tar file
        server: Server hostname or identifier
        password: Password for the p12 file (if encrypted)

    Returns:
        dict: {'success': bool, 'message': str}
    """
    if not os.path.isfile(cert_tar_file):
        return {'success': False, 'message': _('Certificate file not found: %s') % cert_tar_file}

    logger.info('Importing mTLS certificate from: %s', cert_tar_file)

    mtls_path = get_mtls_path(server)
    cert_file = get_mtls_cert_file(server)
    key_file = get_mtls_key_file(server)

    try:
        if not os.path.exists(mtls_path):
            os.makedirs(mtls_path, mode=0o755)
            logger.info('Created certificate directory: %s', mtls_path)

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

                result = _extract_from_p12(p12_file, cert_file, key_file, password=password)
                if not result['success']:
                    return result

                logger.info('Successfully imported mTLS certificate')
                return {
                    'success': True,
                    'message': _('mTLS certificate imported successfully.\nCertificate: %s\nKey: %s')
                    % (cert_file, key_file),
                }

    except tarfile.TarError as e:
        logger.error('Error extracting tar file: %s', str(e))
        return {'success': False, 'message': _('Error extracting tar file: %s') % str(e)}
    except Exception as e:
        logger.error('Error importing certificate: %s', str(e))
        return {'success': False, 'message': _('Error importing certificate: %s') % str(e)}


def _extract_from_p12(p12_file, cert_file, key_file, password=None):
    """
    Extract certificate and private key from a PKCS#12 file.

    Args:
        p12_file: Path to the .p12 file
        cert_file: Path where to save the certificate
        key_file: Path where to save the private key
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

        write_file(cert_file, cert_pem.decode('utf-8'))
        logger.info('Wrote certificate to: %s', cert_file)

        write_file(key_file, key_pem.decode('utf-8'))
        os.chmod(key_file, 0o600)  # Secure permissions for private key
        logger.info('Wrote private key to: %s', key_file)

        return {'success': True, 'message': _('Certificate and key extracted successfully')}

    except Exception as e:
        logger.error('Error extracting from p12: %s', str(e))
        return {'success': False, 'message': _('Error extracting from p12: %s') % str(e)}


def download_ca_certificate(server_url, server):
    """
    Download the CA certificate from the server and update if changed.

    This certificate is needed to verify the server identity when making
    mTLS requests. The download must use verify=False because we don't
    have the CA certificate yet (or need to check for updates).

    If the CA certificate already exists locally, it will only be updated
    if the remote certificate is different.

    Args:
        server_url: Base URL of the migasfree server
        server: Server hostname or identifier (for certificate storage path)

    Returns:
        dict: {'success': bool, 'message': str, 'ca_file': str or None, 'updated': bool}
    """
    endpoint = f'{server_url}/manager/v1/public/ca'

    logger.info('Checking CA certificate from: %s', endpoint)

    try:
        # Must use verify=False because we don't have the CA cert yet
        # Suppress the InsecureRequestWarning since this is intentional
        import warnings

        import urllib3

        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', category=urllib3.exceptions.InsecureRequestWarning)
            response = requests.get(endpoint, verify=False, timeout=30)

        if response.status_code == requests.codes.not_found:
            logger.debug('CA certificate endpoint not available (404): %s', endpoint)
            return {'success': False, 'message': '', 'ca_file': None, 'not_available': True, 'updated': False}

        if response.status_code not in [requests.codes.ok]:
            logger.error('Failed to download CA certificate: %d', response.status_code)
            return {
                'success': False,
                'message': _('Failed to download CA certificate: %s') % response.text,
                'ca_file': None,
                'updated': False,
            }

        # Get paths
        mtls_path = get_mtls_path(server)
        ca_file = get_mtls_ca_file(server)
        remote_ca_content = response.text

        # Check if local CA exists and compare
        if os.path.isfile(ca_file):
            local_ca_content = read_file(ca_file)
            if local_ca_content == remote_ca_content:
                logger.info('CA certificate is up to date')
                return {
                    'success': True,
                    'message': _('CA certificate is up to date'),
                    'ca_file': ca_file,
                    'updated': False,
                }
            else:
                logger.info('CA certificate has changed, updating...')

        # Save the CA certificate
        if not os.path.exists(mtls_path):
            os.makedirs(mtls_path, mode=0o755)
            logger.info('Created certificate directory: %s', mtls_path)

        write_file(ca_file, remote_ca_content)
        logger.info('CA certificate saved to: %s', ca_file)

        return {
            'success': True,
            'message': _('CA certificate downloaded successfully'),
            'ca_file': ca_file,
            'updated': True,
        }

    except requests.exceptions.ConnectionError as e:
        logger.error('Connection error downloading CA certificate: %s', str(e))
        return {'success': False, 'message': str(e), 'ca_file': None, 'updated': False}
    except Exception as e:
        logger.error('Error downloading CA certificate: %s', str(e))
        return {'success': False, 'message': str(e), 'ca_file': None, 'updated': False}


def has_mtls_certificate(server):
    """
    Check if mTLS certificate and key files exist for a specific server.

    Args:
        server: Server hostname or identifier

    Returns:
        bool: True if both certificate and key files exist, False otherwise
    """
    cert_file = get_mtls_cert_file(server)
    key_file = get_mtls_key_file(server)

    cert_exists = os.path.isfile(cert_file)
    key_exists = os.path.isfile(key_file)

    if cert_exists and key_exists:
        logger.info('mTLS certificate found at: %s', cert_file)
        return True

    if cert_exists and not key_exists:
        logger.warning('Certificate exists but key is missing at: %s', key_file)
    elif key_exists and not cert_exists:
        logger.warning('Key exists but certificate is missing at: %s', cert_file)

    return False


def get_mtls_credentials(server):
    """
    Get the paths to mTLS certificate, key, and CA files if they exist for a server.

    Args:
        server: Server hostname or identifier

    Returns:
        tuple: (cert_path, key_path, ca_path) or (None, None, None) if files don't exist
    """
    if has_mtls_certificate(server):
        ca_file = get_mtls_ca_file(server)
        ca_path = ca_file if os.path.isfile(ca_file) else None
        return get_mtls_cert_file(server), get_mtls_key_file(server), ca_path

    return None, None, None


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
        validity_days = MTLS_DEFAULT_VALIDITY_DAYS

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
        write_file(output_path, content)
        logger.info('Certificate downloaded to: %s', output_path)
        return {
            'success': True,
            'file_path': output_path,
            'message': _('Certificate downloaded successfully'),
            'password': password,
        }

    return {'success': False, 'file_path': None, 'message': _('No content in response')}


def fetch_and_install_mtls_certificate(url_request, server, server_url, uuid, project_name):
    """
    Complete workflow: request token, download certificate, download CA, and install.

    Args:
        url_request: UrlRequest instance to use for the requests
        server: Server hostname or identifier (for certificate storage path)
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

    # Step 2: Download CA certificate
    ca_result = download_ca_certificate(server_url, server)
    if not ca_result['success'] and not ca_result.get('not_available'):
        logger.warning('Failed to download CA certificate: %s', ca_result['message'])
        # Continue anyway, CA might not be required

    # Step 3: Download mTLS certificate
    with tempfile.NamedTemporaryFile(suffix='.tar', delete=False) as tmp_file:
        tar_path = tmp_file.name

    try:
        download_result = download_mtls_certificate(url_request, server_url, token_result['token'], tar_path)
        if not download_result['success']:
            return {'success': False, 'message': download_result['message']}

        # Step 4: Import certificate
        import_result = import_mtls_certificate(tar_path, server, password=download_result.get('password'))
        return import_result
    finally:
        if os.path.exists(tar_path):
            os.unlink(tar_path)
            logger.debug('Cleaned up temporary file: %s', tar_path)
