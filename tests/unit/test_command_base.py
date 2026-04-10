# Copyright (c) 2026 Jose Antonio Chavarría <jachavar@gmail.com>
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

"""
Tests for MigasFreeCommand base class functionality.
"""

import errno
import unittest
from unittest.mock import MagicMock, patch

from migasfree_client.command import MigasFreeCommand


class TestMigasFreeCommandBase(unittest.TestCase):
    """Tests for MigasFreeCommand base class"""

    @patch('migasfree_client.utils.is_root_user', return_value=True)
    @patch('migasfree_client.utils.get_config', return_value={})
    @patch('migasfree_client.command.logging.config.dictConfig')
    def setUp(self, mock_log_config, mock_config, mock_root):
        with patch('migasfree_client.utils.get_mfc_project', return_value='test-project'), patch(
            'migasfree_client.utils.get_mfc_computer_name', return_value='test-computer'
        ):
            self.cmd = MigasFreeCommand()
            self.cmd._url_base = 'http://localhost'
            # Initialize missing attributes normally set during _init_command
            self.cmd.migas_ssl_cert = False
            self.cmd._mtls_cert = None
            self.cmd._mtls_key = None
            self.cmd._ca_cert = None

    def test_api_endpoint(self):
        """Test API endpoint construction"""
        endpoint = self.cmd.api_endpoint('/api/v1/test/')
        self.assertEqual(endpoint, 'http://localhost/api/v1/test/')

    @patch('sys.stderr')
    @patch('sys.exit')
    def test_check_user_is_root_fail(self, mock_exit, mock_stderr):
        """Test root check failure"""
        with patch('migasfree_client.utils.is_root_user', return_value=False):
            self.cmd._check_user_is_root()
            mock_exit.assert_called_with(errno.EACCES)

    @patch('migasfree_client.command.utils.is_windows', return_value=False)
    def test_operation_ok(self, mock_win):
        """Test operation_ok console output"""
        self.cmd.console = MagicMock()
        self.cmd.operation_ok('Success')
        self.cmd.console.log.assert_called()

    @patch('migasfree_client.command.utils.is_windows', return_value=False)
    def test_operation_failed(self, mock_win):
        """Test operation_failed console output"""
        self.cmd.error_console = MagicMock()
        self.cmd.operation_failed('Failure')
        self.cmd.error_console.log.assert_called()

    @patch('migasfree_client.command.UrlRequest')
    def test_init_url_request(self, mock_url_request_class):
        """Test URL request object initialization"""
        self.cmd.migas_proxy = 'http://proxy:8080'
        self.cmd._init_url_request()

        mock_url_request_class.assert_called_once()
        kwargs = mock_url_request_class.call_args[1]
        self.assertEqual(kwargs['proxy'], 'http://proxy:8080')
        self.assertEqual(kwargs['project'], 'test-project')

    @patch('migasfree_client.command.utils.write_file', return_value=True)
    def test_write_key_file_success(self, mock_write):
        """Test saving keys to disk"""
        self.cmd.console = MagicMock()
        result = self.cmd._write_key_file('key.pri', 'content')
        self.assertTrue(result)
        mock_write.assert_called_once()

    def test_handle_response_success(self):
        """Test handling successful API response"""
        self.cmd.console = MagicMock()
        response = {'status': 'ok', 'data': 'some-data'}
        result = self.cmd._handle_response(response)
        self.assertEqual(result, response)

    @patch('migasfree_client.command.utils.is_windows', return_value=False)
    @patch('sys.exit')
    def test_handle_response_error(self, mock_exit, mock_win):
        """Test handling API response with error"""
        self.cmd.error_console = MagicMock()
        response = {'error': {'info': 'API Error', 'code': 404}}
        self.cmd._handle_response(response)
        mock_exit.assert_called_with(errno.ENODATA)


if __name__ == '__main__':
    unittest.main()
