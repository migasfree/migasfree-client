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

import unittest
from unittest.mock import MagicMock, patch

from migasfree_client.tags import MigasFreeTags


class TestMigasFreeTags(unittest.TestCase):
    @patch('migasfree_client.utils.is_root_user', return_value=True)
    @patch('migasfree_client.utils.get_config', return_value={})
    @patch('migasfree_client.command.logging.config.dictConfig')
    @patch('migasfree_client.url_request.UrlRequest')
    def setUp(self, mock_url_req_class, mock_log_config, mock_config, mock_root):
        self.mock_url_request = MagicMock()
        mock_url_req_class.return_value = self.mock_url_request

        with patch('migasfree_client.utils.get_mfc_project', return_value='test-project'), patch(
            'migasfree_client.utils.get_mfc_computer_name', return_value='test-computer'
        ):
            self.tags = MigasFreeTags()
            self.tags.console = MagicMock()
            self.tags._computer_id = '123'
            self.tags.LOCK_FILE = 'test.lock'
            self.tags.CMD = 'migasfree'
            self.tags._url_request = self.mock_url_request
            self.tags._private_key = 'priv'
            self.tags._public_key = 'pub'
            # Globally mock end_of_transmission to avoid security key reading
            self.tags.end_of_transmission = MagicMock()

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
        self.assertIn('dialog', mock_execute.call_args[0][0])

    def test_get_assigned_tags(self):
        """Test getting assigned tags from API"""
        with patch.object(self.tags, '_api_call') as mock_api:
            mock_api.return_value = ['T1']
            self.tags.get_assigned_tags()
            mock_api.assert_called_with('get_assigned_tags', {'id': '123'})

    def test_get_available_tags(self):
        """Test getting available tags from API"""
        with patch.object(self.tags, '_api_call') as mock_api:
            mock_api.return_value = {'T': ['T1']}
            self.tags.get_available_tags()
            mock_api.assert_called_with('get_available_tags', {'id': '123'}, exit_on_error=False)

    @patch('migasfree_client.tags.MigasFreeSync')
    def test_apply_rules(self, mock_sync_class):
        """Test applying rules initializes MigasFreeSync and calls its methods"""
        mock_sync_instance = mock_sync_class.return_value
        self.tags.pms = MagicMock()
        rules = {'remove': ['pkg1'], 'preinstall': ['pkg2'], 'install': ['pkg3']}
        self.tags._apply_rules(rules)
        mock_sync_instance.upload_attributes.assert_called_once()

    @patch('sys.exit')
    @patch('migasfree_client.tags.MigasFreeTags._init_command')
    @patch('migasfree_client.tags.lock_file_context')
    def test_run_set_tags(self, mock_lock, mock_init, mock_exit):
        """Test run dispatcher for setting tags"""
        args = MagicMock()
        args.set = ['T1-V1']
        args.get = False
        args.communicate = False
        args.cmd = 'tags'

        with patch.object(self.tags, 'set_tags') as mock_set, patch.object(self.tags, '_apply_rules') as mock_apply:
            self.tags.run(args)
            mock_set.assert_called_once()
            mock_apply.assert_called_once()

    def test_set_tags_success(self):
        """Test set_tags successful flow"""
        self.tags._tags = ['T1-V1']
        with patch.object(self.tags, '_api_call') as mock_api:
            mock_api.return_value = {'remove': [], 'preinstall': [], 'install': []}
            self.tags.set_tags()
            mock_api.assert_called_with('upload_tags', {'id': '123', 'tags': ['T1-V1']}, exit_on_error=False)


if __name__ == '__main__':
    unittest.main()
