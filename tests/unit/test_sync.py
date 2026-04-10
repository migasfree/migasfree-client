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
Tests for sync-related functionality.
"""

import unittest
from unittest.mock import MagicMock, patch

from migasfree_client.sync import MigasFreeSync


class TestMigasFreeSync(unittest.TestCase):
    """Tests for MigasFreeSync class"""

    @patch('migasfree_client.utils.is_root_user', return_value=True)
    @patch('signal.signal')
    @patch('migasfree_client.utils.get_config', return_value={})
    @patch('migasfree_client.command.logging.config.dictConfig')
    @patch('migasfree_client.utils.get_graphic_pid', return_value=(None, None))
    def setUp(self, mock_graphic, mock_log_config, mock_config, mock_signal, mock_root):
        # We need to mock settings.TMP_PATH and other paths to avoid local side effects
        with patch('migasfree_client.settings.TMP_PATH', '/tmp'), patch(
            'migasfree_client.settings.CONF_FILE', '/etc/migasfree.conf'
        ), patch('migasfree_client.utils.get_mfc_project', return_value='test-project'), patch(
            'migasfree_client.utils.get_mfc_computer_name', return_value='test-computer'
        ):
            self.sync = MigasFreeSync()
            self.sync.pms = MagicMock()
            self.sync._url_request = MagicMock()
            self.sync._computer_id = 123

    def test_software_history_no_file(self):
        """Test software_history when history file does not exist"""
        with patch('os.path.isfile', return_value=False):
            history = self.sync.software_history(['pkg1', 'pkg2'])
            self.assertEqual(history, {})

    @patch('migasfree_client.utils.compare_lists')
    def test_software_history_with_changes(self, mock_compare):
        """Test software_history correctly identifies changes"""
        mock_compare.return_value = ['+pkg3', '-pkg0']

        # We need to mock the file reading
        with patch('os.path.isfile', return_value=True), patch('os.stat') as mock_stat, patch(
            'builtins.open', unittest.mock.mock_open(read_data='pkg1\npkg2')
        ):
            mock_stat.return_value.st_size = 10

            history = self.sync.software_history(['pkg1', 'pkg2', 'pkg3'])

            self.assertEqual(history['installed'], ['+pkg3'])
            self.assertEqual(history['uninstalled'], ['-pkg0'])

    def test_get_repositories_success(self):
        """Test get_repositories successfully fetches repos"""
        expected_repos = [{'source_template': 'deb http://server/repo'}]
        # Mock get_repos_key to return True
        with patch.object(self.sync, 'get_repos_key', return_value=True), patch.object(
            self.sync, '_api_call', return_value=expected_repos
        ):
            repos = self.sync.get_repositories()
            self.assertEqual(repos, expected_repos)

    def test_get_mandatory_packages(self):
        """Test get_mandatory_packages fetches correct data"""
        expected = {'install': ['pkg1'], 'remove': ['pkg2']}
        with patch.object(self.sync, '_api_call', return_value=expected):
            result = self.sync.get_mandatory_packages()
            self.assertEqual(result, expected)

    def test_mandatory_pkgs_orchestration(self):
        """Test mandatory_pkgs calls install/uninstall correctly"""
        response = {'install': ['p1'], 'remove': ['p2']}
        with patch.object(self.sync, 'get_mandatory_packages', return_value=response), patch.object(
            self.sync, 'uninstall_packages'
        ) as mock_uninstall, patch.object(self.sync, 'install_mandatory_packages') as mock_install:
            self.sync.mandatory_pkgs()
            mock_uninstall.assert_called_with(['p2'])
            mock_install.assert_called_with(['p1'])

    def test_sync_logical_devices_no_devices(self):
        """Test sync_logical_devices returns False if no devices from API"""
        with patch.object(self.sync, 'get_devices', return_value=None):
            self.assertFalse(self.sync.sync_logical_devices())

    @patch('migasfree_client.utils.is_windows', return_value=False)
    def test_is_migasfree_printer(self, mock_win):
        """Test identification of Migasfree-formatted printer strings"""
        self.assertTrue(self.sync._is_migasfree_printer('HP__LJ__print__office__42'))
        self.assertFalse(self.sync._is_migasfree_printer('Plain Printer Name'))

    def test_get_printer_logical_id(self):
        """Test extraction of logical ID from printer info"""
        self.assertEqual(self.sync._get_printer_logical_id('A__B__C__D__99'), 99)

    def test_mandatory_packages_partial(self):
        """Test mandatory packages logic with partial data"""
        with patch.object(self.sync, 'get_mandatory_packages', return_value={'install': ['pkg1']}), patch.object(
            self.sync, 'uninstall_packages'
        ) as mock_uninstall, patch.object(self.sync, 'install_mandatory_packages') as mock_install:
            self.sync.mandatory_pkgs()
            mock_uninstall.assert_not_called()
            mock_install.assert_called_with(['pkg1'])


if __name__ == '__main__':
    unittest.main()
