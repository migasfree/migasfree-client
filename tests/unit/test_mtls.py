"""
Unit tests for migasfree_client.mtls module
"""

import os
import tempfile
from unittest.mock import MagicMock, patch

from migasfree_client import mtls


class TestImportMtlsCertificate:
    """Tests for import_mtls_certificate function"""

    def test_import_nonexistent_file(self):
        """Test importing a file that doesn't exist"""
        result = mtls.import_mtls_certificate('/nonexistent/file.tar', 'test.server.com')

        assert result['success'] is False
        assert 'not found' in result['message'].lower()

    @patch('migasfree_client.mtls._extract_from_p12')
    @patch('os.makedirs')
    @patch('os.path.exists', return_value=False)
    @patch('tarfile.open')
    @patch('os.path.isfile', return_value=True)
    def test_import_creates_cert_directory(self, mock_isfile, mock_tar_open, mock_exists, mock_makedirs, mock_extract):
        """Test that import creates the certificate directory if it doesn't exist"""
        # Setup the mock tar file
        mock_tar = MagicMock()
        mock_tar_open.return_value.__enter__.return_value = mock_tar
        mock_tar.extractall = MagicMock()

        server = 'test.server.com'
        expected_mtls_path = mtls.get_mtls_path(server)

        # Mock os.listdir to return a .p12 file
        with patch('os.listdir', return_value=['certificate.p12']):
            mock_extract.return_value = {'success': True, 'message': 'Extracted'}

            with patch('tempfile.TemporaryDirectory') as mock_temp:
                mock_temp.return_value.__enter__.return_value = '/tmp/test'

                result = mtls.import_mtls_certificate('/path/to/cert.tar', server)

        # Verify directory creation was attempted
        mock_makedirs.assert_called_once_with(expected_mtls_path, mode=0o755)
        assert result['success'] is True

    @patch('migasfree_client.mtls._extract_from_p12')
    @patch('os.makedirs')
    @patch('os.path.exists', return_value=True)
    @patch('tarfile.open')
    @patch('os.path.isfile', return_value=True)
    def test_import_successful(self, mock_isfile, mock_tar_open, mock_exists, mock_makedirs, mock_extract):
        """Test successful certificate import"""
        # Setup the mock tar file
        mock_tar = MagicMock()
        mock_tar_open.return_value.__enter__.return_value = mock_tar
        mock_tar.extractall = MagicMock()

        server = 'test.server.com'

        # Mock os.listdir to return a .p12 file
        with patch('os.listdir', return_value=['certificate.p12']):
            mock_extract.return_value = {'success': True, 'message': 'Extracted'}

            with patch('tempfile.TemporaryDirectory') as mock_temp:
                mock_temp.return_value.__enter__.return_value = '/tmp/test'

                result = mtls.import_mtls_certificate('/path/to/cert.tar', server)

        assert result['success'] is True
        assert 'successfully' in result['message'].lower()

    @patch('os.path.exists', return_value=True)
    @patch('tarfile.open')
    @patch('os.path.isfile', return_value=True)
    def test_import_tar_without_p12(self, mock_isfile, mock_tar_open, mock_exists):
        """Test importing tar file without a .p12 file"""
        # Setup the mock tar file
        mock_tar = MagicMock()
        mock_tar_open.return_value.__enter__.return_value = mock_tar
        mock_tar.extractall = MagicMock()

        # Mock os.listdir to return no .p12 file
        with patch('os.listdir', return_value=['readme.txt', 'other.file']):
            with patch('tempfile.TemporaryDirectory') as mock_temp:
                mock_temp.return_value.__enter__.return_value = '/tmp/test'

                result = mtls.import_mtls_certificate('/path/to/cert.tar', 'test.server.com')

        assert result['success'] is False
        assert 'p12' in result['message'].lower()


class TestExtractFromP12:
    """Tests for _extract_from_p12 function"""

    @patch('migasfree_client.utils.write_file')
    @patch('os.chmod')
    def test_extract_from_p12_success(self, mock_chmod, mock_write_file):
        """Test successful extraction from p12 file"""
        import datetime

        from cryptography import x509
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives.serialization import pkcs12
        from cryptography.x509.oid import NameOID

        # Create a test certificate and key
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())

        subject = issuer = x509.Name(
            [
                x509.NameAttribute(NameOID.COMMON_NAME, 'test.example.com'),
            ]
        )

        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(private_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.utcnow())
            .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
            .sign(private_key, None, default_backend())
        )

        # Serialize to PKCS12
        p12_data = pkcs12.serialize_key_and_certificates(
            b'test_cert', private_key, cert, None, serialization.NoEncryption()
        )

        # Create temporary p12 file
        with tempfile.NamedTemporaryFile(suffix='.p12', delete=False) as f:
            f.write(p12_data)
            p12_file = f.name

        try:
            mock_write_file.return_value = True
            cert_file = '/tmp/test_cert.pem'
            key_file = '/tmp/test_key.pem'
            result = mtls._extract_from_p12(p12_file, cert_file, key_file)

            assert result['success'] is True
            assert mock_write_file.call_count == 2  # Once for cert, once for key
            assert mock_chmod.called  # Key file should have permissions set
        finally:
            os.unlink(p12_file)

    def test_extract_from_p12_nonexistent_file(self):
        """Test extracting from nonexistent p12 file"""
        result = mtls._extract_from_p12('/nonexistent/file.p12', '/tmp/cert.pem', '/tmp/key.pem')

        assert result['success'] is False


class TestHasMtlsCertificate:
    """Tests for has_mtls_certificate function"""

    @patch('os.path.isfile')
    def test_both_files_exist(self, mock_isfile):
        """Test when both cert and key files exist"""
        mock_isfile.return_value = True

        result = mtls.has_mtls_certificate('test.server.com')

        assert result is True
        assert mock_isfile.call_count == 2

    @patch('os.path.isfile')
    def test_only_cert_exists(self, mock_isfile):
        """Test when only cert file exists"""
        mock_isfile.side_effect = [True, False]

        result = mtls.has_mtls_certificate('test.server.com')

        assert result is False

    @patch('os.path.isfile')
    def test_only_key_exists(self, mock_isfile):
        """Test when only key file exists"""
        mock_isfile.side_effect = [False, True]

        result = mtls.has_mtls_certificate('test.server.com')

        assert result is False

    @patch('os.path.isfile')
    def test_neither_file_exists(self, mock_isfile):
        """Test when neither file exists"""
        mock_isfile.return_value = False

        result = mtls.has_mtls_certificate('test.server.com')

        assert result is False


class TestGetMtlsCredentials:
    """Tests for get_mtls_credentials function"""

    @patch('migasfree_client.mtls.has_mtls_certificate')
    def test_credentials_exist(self, mock_has_cert):
        """Test getting credentials when they exist"""
        mock_has_cert.return_value = True
        server = 'test.server.com'

        cert, key = mtls.get_mtls_credentials(server)

        assert cert == mtls.get_mtls_cert_file(server)
        assert key == mtls.get_mtls_key_file(server)

    @patch('migasfree_client.mtls.has_mtls_certificate')
    def test_credentials_dont_exist(self, mock_has_cert):
        """Test getting credentials when they don't exist"""
        mock_has_cert.return_value = False

        cert, key = mtls.get_mtls_credentials('test.server.com')

        assert cert is None
        assert key is None


class TestRequestMtlsToken:
    """Tests for request_mtls_token function"""

    def test_request_token_success(self):
        """Test successful token request"""
        mock_url_request = MagicMock()
        mock_url_request.run_simple.return_value = {
            'data': {'token': 'test-token-12345'},
        }

        result = mtls.request_mtls_token(
            url_request=mock_url_request,
            server_url='https://test.server.com',
            uuid='test-uuid',
            project_name='test-project',
        )

        assert result['success'] is True
        assert result['token'] == 'test-token-12345'
        mock_url_request.run_simple.assert_called_once()

    def test_request_token_server_error(self):
        """Test token request with server error"""
        mock_url_request = MagicMock()
        mock_url_request.run_simple.return_value = {
            'error': {'info': 'Internal Server Error', 'code': 500},
        }

        result = mtls.request_mtls_token(
            url_request=mock_url_request,
            server_url='https://test.server.com',
            uuid='test-uuid',
            project_name='test-project',
        )

        assert result['success'] is False
        assert result['token'] is None

    def test_request_token_connection_error(self):
        """Test token request with connection error"""
        mock_url_request = MagicMock()
        mock_url_request.run_simple.return_value = {
            'error': {'info': 'Connection refused', 'code': 111},
        }

        result = mtls.request_mtls_token(
            url_request=mock_url_request,
            server_url='https://test.server.com',
            uuid='test-uuid',
            project_name='test-project',
        )

        assert result['success'] is False
        assert result['token'] is None
        assert 'Connection refused' in result['message']

    def test_request_token_not_available_404(self):
        """Test token request with 404 returns not_available flag"""
        mock_url_request = MagicMock()
        mock_url_request.run_simple.return_value = {
            'error': {'info': '', 'code': 404},
        }

        result = mtls.request_mtls_token(
            url_request=mock_url_request,
            server_url='https://test.server.com',
            uuid='test-uuid',
            project_name='test-project',
        )

        assert result['success'] is False
        assert result['token'] is None
        assert result.get('not_available') is True
        assert result['message'] == ''


class TestDownloadMtlsCertificate:
    """Tests for download_mtls_certificate function"""

    @patch('migasfree_client.utils.write_file')
    def test_download_certificate_success(self, mock_write_file):
        """Test successful certificate download"""
        mock_url_request = MagicMock()
        mock_url_request.run_simple.return_value = {
            'data': None,
            'content': b'fake tar content',
        }
        mock_write_file.return_value = True

        result = mtls.download_mtls_certificate(
            url_request=mock_url_request,
            server_url='https://test.server.com',
            token='test-token',
            output_path='/tmp/test.tar',
        )

        assert result['success'] is True
        assert result['file_path'] == '/tmp/test.tar'
        mock_write_file.assert_called_once()

    def test_download_certificate_invalid_token(self):
        """Test certificate download with invalid token"""
        mock_url_request = MagicMock()
        mock_url_request.run_simple.return_value = {
            'error': {'info': 'Invalid token', 'code': 401},
        }

        result = mtls.download_mtls_certificate(
            url_request=mock_url_request,
            server_url='https://test.server.com',
            token='invalid-token',
            output_path='/tmp/test.tar',
        )

        assert result['success'] is False
        assert result['file_path'] is None


class TestFetchAndInstallMtlsCertificate:
    """Tests for fetch_and_install_mtls_certificate function"""

    @patch('migasfree_client.mtls.import_mtls_certificate')
    @patch('migasfree_client.mtls.download_mtls_certificate')
    @patch('migasfree_client.mtls.request_mtls_token')
    @patch('os.path.exists', return_value=True)
    @patch('os.unlink')
    def test_fetch_and_install_success(self, mock_unlink, mock_exists, mock_request, mock_download, mock_import):
        """Test successful fetch and install workflow"""
        mock_url_request = MagicMock()
        mock_request.return_value = {'success': True, 'token': 'test-token', 'message': 'OK'}
        mock_download.return_value = {'success': True, 'file_path': '/tmp/cert.tar', 'message': 'OK'}
        mock_import.return_value = {'success': True, 'message': 'Imported'}

        result = mtls.fetch_and_install_mtls_certificate(
            url_request=mock_url_request,
            server='test.server.com',
            server_url='https://test.server.com',
            uuid='test-uuid',
            project_name='test-project',
        )

        assert result['success'] is True
        mock_request.assert_called_once()
        mock_download.assert_called_once()
        mock_import.assert_called_once()

    @patch('migasfree_client.mtls.request_mtls_token')
    def test_fetch_and_install_token_failure(self, mock_request):
        """Test fetch and install with token request failure"""
        mock_url_request = MagicMock()
        mock_request.return_value = {'success': False, 'token': None, 'message': 'Connection error'}

        result = mtls.fetch_and_install_mtls_certificate(
            url_request=mock_url_request,
            server='test.server.com',
            server_url='https://test.server.com',
            uuid='test-uuid',
            project_name='test-project',
        )

        assert result['success'] is False
        assert 'Connection error' in result['message']

    @patch('migasfree_client.mtls.download_mtls_certificate')
    @patch('migasfree_client.mtls.request_mtls_token')
    @patch('os.path.exists', return_value=True)
    @patch('os.unlink')
    def test_fetch_and_install_download_failure(self, mock_unlink, mock_exists, mock_request, mock_download):
        """Test fetch and install with download failure"""
        mock_url_request = MagicMock()
        mock_request.return_value = {'success': True, 'token': 'test-token', 'message': 'OK'}
        mock_download.return_value = {'success': False, 'file_path': None, 'message': 'Download failed'}

        result = mtls.fetch_and_install_mtls_certificate(
            url_request=mock_url_request,
            server='test.server.com',
            server_url='https://test.server.com',
            uuid='test-uuid',
            project_name='test-project',
        )

        assert result['success'] is False
        assert 'Download failed' in result['message']
