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

import os
import unittest
from unittest.mock import MagicMock, mock_open, patch

from migasfree_client import mtls


class TestMtls(unittest.TestCase):
    def setUp(self):
        self.server = 'test-server'
        self.mtls_path = '/tmp/migasfree-tests/mtls/test-server'

    @patch('migasfree_client.mtls.MTLS_PATH', '/tmp/migasfree-tests/mtls')
    def test_get_mtls_path(self):
        self.assertEqual(mtls.get_mtls_path(self.server), self.mtls_path)

    @patch('migasfree_client.mtls.get_mtls_path')
    def test_get_mtls_cert_file(self, mock_get_path):
        mock_get_path.return_value = self.mtls_path
        self.assertEqual(mtls.get_mtls_cert_file(self.server), os.path.join(self.mtls_path, 'cert.pem'))

    @patch('migasfree_client.mtls.get_mtls_path')
    def test_get_mtls_key_file(self, mock_get_path):
        mock_get_path.return_value = self.mtls_path
        self.assertEqual(mtls.get_mtls_key_file(self.server), os.path.join(self.mtls_path, 'key.pem'))

    @patch('migasfree_client.mtls.get_mtls_path')
    def test_get_mtls_ca_file(self, mock_get_path):
        mock_get_path.return_value = self.mtls_path
        self.assertEqual(mtls.get_mtls_ca_file(self.server), os.path.join(self.mtls_path, 'ca.pem'))

    @patch('os.path.isfile', return_value=True)
    @patch('migasfree_client.mtls.get_mtls_cert_file', return_value='cert.pem')
    @patch('migasfree_client.mtls.get_mtls_key_file', return_value='key.pem')
    def test_has_mtls_certificate_true(self, mock_key, mock_cert, mock_isfile):
        self.assertTrue(mtls.has_mtls_certificate(self.server))

    @patch('os.path.isfile', return_value=False)
    @patch('migasfree_client.mtls.get_mtls_cert_file', return_value='cert.pem')
    @patch('migasfree_client.mtls.get_mtls_key_file', return_value='key.pem')
    def test_has_mtls_certificate_false(self, mock_key, mock_cert, mock_isfile):
        self.assertFalse(mtls.has_mtls_certificate(self.server))

    @patch('requests.get')
    @patch('os.path.isfile', return_value=False)
    @patch('os.path.exists', return_value=True)
    @patch('migasfree_client.mtls.write_file')
    def test_download_ca_certificate_success(self, mock_write, mock_exists, mock_isfile, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = 'CA CONTENT'
        mock_get.return_value = mock_response

        result = mtls.download_ca_certificate('http://server', self.server)

        self.assertTrue(result['success'])
        self.assertTrue(result['updated'])
        self.assertEqual(result['ca_file'], mtls.get_mtls_ca_file(self.server))
        mock_write.assert_called_once_with(result['ca_file'], 'CA CONTENT')

    @patch('requests.get')
    def test_download_ca_certificate_not_found(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = mtls.download_ca_certificate('http://server', self.server)

        self.assertFalse(result['success'])
        self.assertTrue(result.get('not_available'))

    @patch('migasfree_client.mtls.pkcs12')
    @patch('migasfree_client.mtls.write_file')
    @patch('os.chmod')
    def test_extract_from_p12(self, mock_chmod, mock_write, mock_pkcs12):
        mock_key = MagicMock()
        mock_key.private_bytes.return_value = b'KEY_PEM'
        mock_cert = MagicMock()
        mock_cert.public_bytes.return_value = b'CERT_PEM'

        mock_pkcs12.load_key_and_certificates.return_value = (mock_key, mock_cert, [])

        with patch('builtins.open', mock_open(read_data=b'p12data')):
            result = mtls._extract_from_p12('file.p12', 'cert.pem', 'key.pem')

        self.assertTrue(result['success'])
        self.assertEqual(mock_write.call_count, 2)
        mock_chmod.assert_called_once_with('key.pem', 0o600)

    def test_request_mtls_token_success(self):
        mock_url_request = MagicMock()
        mock_url_request.run_simple.return_value = {'data': {'token': 'secret-token'}}

        result = mtls.request_mtls_token(mock_url_request, 'http://server', 'uuid', 'project')

        self.assertTrue(result['success'])
        self.assertEqual(result['token'], 'secret-token')

    def test_request_mtls_token_failure(self):
        mock_url_request = MagicMock()
        mock_url_request.run_simple.return_value = {'error': {'info': 'Some error', 'code': 400}}

        result = mtls.request_mtls_token(mock_url_request, 'http://server', 'uuid', 'project')

        self.assertFalse(result['success'])
        self.assertIn('Token request failed', result['message'])

    @patch('migasfree_client.mtls.get_mtls_path', return_value='/tmp/mtls')
    @patch('migasfree_client.mtls.get_mtls_cert_file', return_value='/tmp/mtls/cert.pem')
    @patch('migasfree_client.mtls.get_mtls_key_file', return_value='/tmp/mtls/key.pem')
    @patch('os.path.isfile', return_value=True)
    @patch('os.makedirs')
    @patch('tarfile.open')
    @patch('migasfree_client.mtls._extract_from_p12')
    def test_import_mtls_certificate_success(
        self, mock_extract, mock_tar, mock_makedirs, mock_isfile, mock_key_file, mock_cert_file, mock_path
    ):
        mock_extract.return_value = {'success': True}

        # Mock tar content
        mock_p12 = MagicMock()
        mock_p12.name = 'cert.p12'
        mock_tar.return_value.__enter__.return_value.getmembers.return_value = [mock_p12]

        with patch('os.listdir', return_value=['cert.p12']):
            result = mtls.import_mtls_certificate('cert.tar', self.server)

        self.assertTrue(result['success'])
        self.assertIn('imported successfully', result['message'])

    @patch('migasfree_client.mtls.request_mtls_token')
    @patch('migasfree_client.mtls.download_ca_certificate')
    @patch('migasfree_client.mtls.download_mtls_certificate')
    @patch('migasfree_client.mtls.import_mtls_certificate')
    @patch('os.path.exists', return_value=True)
    @patch('os.unlink')
    def test_fetch_and_install_mtls_certificate_workflow(
        self, mock_unlink, mock_exists, mock_import, mock_download, mock_ca, mock_token
    ):
        mock_token.return_value = {'success': True, 'token': 'tk'}
        mock_ca.return_value = {'success': True}
        mock_download.return_value = {'success': True, 'password': 'pwd'}
        mock_import.return_value = {'success': True, 'message': 'OK'}

        result = mtls.fetch_and_install_mtls_certificate(MagicMock(), self.server, 'http://server', 'uuid', 'project')

        self.assertTrue(result['success'])
        mock_import.assert_called_once()
        mock_unlink.assert_called_once()


if __name__ == '__main__':
    unittest.main()
