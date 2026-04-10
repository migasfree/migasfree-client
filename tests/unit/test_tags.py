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

"""
Tests for tag-related functionality using the MigasFreeTags class.
"""

import unittest
from unittest.mock import MagicMock, patch

from migasfree_client.tags import MigasFreeTags


class TestMigasFreeTags(unittest.TestCase):
    """Tests for MigasFreeTags class"""

    @patch('migasfree_client.utils.is_root_user', return_value=True)
    @patch('migasfree_client.utils.get_config', return_value={})
    @patch('migasfree_client.command.logging.config.dictConfig')
    def setUp(self, mock_log_config, mock_config, mock_root):
        with patch('migasfree_client.utils.get_mfc_project', return_value='test-project'), patch(
            'migasfree_client.utils.get_mfc_computer_name', return_value='test-computer'
        ):
            self.tags = MigasFreeTags()
            # Prevent network/file interaction by mocking internal init methods
            self.tags._init_url_request = MagicMock()
            self.tags._init_mtls = MagicMock()
            self.tags._url_request = MagicMock()

    def test_sanitize_valid_tags(self):
        """Test sanitization of valid tag list"""
        tag_list = ['LOC-office1', '"DEP-marketing"']
        result = self.tags._sanitize(tag_list)
        self.assertEqual(result, ['LOC-office1', 'DEP-marketing'])

    @patch('sys.exit')
    @patch('migasfree_client.tags.MigasFreeTags.operation_failed')
    def test_sanitize_invalid_format(self, mock_failed, mock_exit):
        """Test sanitization fails when tag format is incorrect"""
        tag_list = ['invalidtag']
        self.tags._sanitize(tag_list)
        mock_failed.assert_called_once()
        mock_exit.assert_called_once()

    @patch('migasfree_client.tags.execute')
    @patch('migasfree_client.tags.is_zenity', return_value=True)
    @patch('migasfree_client.tags.is_xsession', return_value=True)
    @patch('migasfree_client.tags.is_windows', return_value=False)
    @patch('migasfree_client.tags.is_linux', return_value=True)
    def test_select_tags_zenity_linux(self, mock_linux, mock_windows, mock_xsession, mock_zenity, mock_execute):
        """Test tag selection using zenity on Linux"""
        mock_execute.return_value = (0, 'LOC-office1\nDEP-marketing\n', '')
        available = {'LOC': ['LOC-office1', 'LOC-office2'], 'DEP': ['DEP-marketing']}
        assigned = ['LOC-office1']

        selected = self.tags._select_tags(assigned, available)

        self.assertEqual(selected, ['LOC-office1', 'DEP-marketing'])
        # Check if zenity was called with correct icon from base class
        args, _ = mock_execute.call_args
        self.assertEqual(args[0][0], 'zenity')
        icon_arg = next(arg for arg in args[0] if '--window-icon=' in arg)
        self.assertIn('migasfree.svg', icon_arg)
        self.assertIn('--separator=\n', args[0])

    @patch('migasfree_client.tags.execute')
    @patch('migasfree_client.tags.is_windows', return_value=False)
    @patch('migasfree_client.tags.is_zenity', return_value=False)
    @patch('migasfree_client.tags.is_xsession', return_value=False)
    def test_select_tags_dialog(self, mock_xsession, mock_zenity, mock_windows, mock_execute):
        """Test tag selection using dialog when GUI is not available"""
        mock_execute.return_value = (0, 'LOC-office1\nDEP-office2\n', '')
        available = {'LOC': ['LOC-office1', 'LOC-office2']}
        assigned = []

        self.tags._select_tags(assigned, available)

        args, _ = mock_execute.call_args
        self.assertEqual(args[0][0], 'dialog')
        self.assertIn('--checklist', args[0])

    @patch('migasfree_client.tags.MigasFreeTags._api_call')
    @patch('migasfree_client.tags.MigasFreeTags._handle_response')
    def test_get_assigned_tags(self, mock_handle, mock_api):
        """Test getting assigned tags from API"""
        self.tags._computer_id = 123
        self.tags.get_assigned_tags()
        mock_api.assert_called_with('get_assigned_tags', {'id': 123})

    @patch('migasfree_client.tags.MigasFreeSync')
    def test_apply_rules(self, mock_sync_class):
        """Test applying rules initializes MigasFreeSync and calls its methods"""
        mock_sync_instance = mock_sync_class.return_value
        self.tags.pms = MagicMock()

        rules = {'remove': ['pkg1'], 'preinstall': ['pkg2'], 'install': ['pkg3']}

        self.tags._apply_rules(rules)

        mock_sync_instance.upload_attributes.assert_called_once()
        mock_sync_instance.uninstall_packages.assert_called_with(['pkg1'])
        mock_sync_instance.install_mandatory_packages.assert_any_call(['pkg2'])
        mock_sync_instance.install_mandatory_packages.assert_any_call(['pkg3'])


if __name__ == '__main__':
    unittest.main()
