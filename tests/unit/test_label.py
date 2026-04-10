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
Tests for MigasFreeLabel class.
"""

import unittest
from unittest.mock import MagicMock, patch

from migasfree_client.label import MigasFreeLabel


class TestMigasFreeLabel(unittest.TestCase):
    """Tests for MigasFreeLabel class"""

    @patch('migasfree_client.utils.is_root_user', return_value=True)
    @patch('migasfree_client.utils.get_config', return_value={})
    @patch('migasfree_client.command.logging.config.dictConfig')
    def setUp(self, mock_log_config, mock_config, mock_root):
        with patch('migasfree_client.utils.get_mfc_project', return_value='test-project'), patch(
            'migasfree_client.utils.get_mfc_computer_name', return_value='test-computer'
        ):
            self.label = MigasFreeLabel()
            self.label._url_request = MagicMock()
            self.label._init_url_request = MagicMock()
            self.label._init_mtls = MagicMock()
            self.label._computer_id = 123
            self.label._mtls_cert = 'cert-path'

    @patch('migasfree_client.label.MigasFreeLabel._api_call')
    @patch('migasfree_client.label.MigasFreeLabel._handle_response')
    def test_get_label(self, mock_handle, mock_api):
        """Test getting label data from API"""
        self.label.get_label()
        mock_api.assert_called_with('get_label', {'id': 123})

    @patch('migasfree_client.label.MigasFreeLabel.get_label')
    @patch('migasfree_client.label.write_file')
    @patch('migasfree_client.label.execute_as_user')
    @patch('migasfree_client.label.is_linux', return_value=True)
    @patch('migasfree_client.label.is_windows', return_value=False)
    def test_show_label_linux(self, mock_windows, mock_linux, mock_execute, mock_write, mock_get_label):
        """Test showing label on Linux (xdg-open)"""
        mock_get_label.return_value = {'search': 'TEST-SEARCH', 'uuid': 'TEST-UUID', 'helpdesk': 'Contact Support'}

        self.label._show_label()

        mock_write.assert_called_once()
        args, _ = mock_write.call_args
        self.assertIn('label.html', args[0])
        self.assertIn('TEST-SEARCH', args[1])
        self.assertIn('TEST-UUID', args[1])

        mock_execute.assert_called_once()
        self.assertEqual(mock_execute.call_args[0][0], ['xdg-open', args[0]])

    @patch('migasfree_client.label.MigasFreeLabel.get_label')
    @patch('migasfree_client.label.write_file')
    @patch('migasfree_client.label.execute_as_user')
    @patch('migasfree_client.label.is_linux', return_value=False)
    @patch('migasfree_client.label.is_windows', return_value=True)
    def test_show_label_windows(self, mock_windows, mock_linux, mock_execute, mock_write, mock_get_label):
        """Test showing label on Windows (cmd /c start)"""
        mock_get_label.return_value = {'search': 'TEST-SEARCH', 'uuid': 'TEST-UUID', 'helpdesk': 'Contact Support'}

        self.label._show_label()

        mock_execute.assert_called_once()
        self.assertEqual(mock_execute.call_args[0][0][0], 'cmd')
        # The path should be what was written to
        written_path = mock_write.call_args[0][0]
        self.assertEqual(mock_execute.call_args[0][0][3], written_path)
        # Wait, the path depends on settings.TMP_PATH which I didn't mock.
        # But it should be passed as the last argument to the command.


if __name__ == '__main__':
    unittest.main()
