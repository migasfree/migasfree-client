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

import json
import os
import tempfile
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
        test_tmp = tempfile.gettempdir()
        with patch('migasfree_client.settings.TMP_PATH', test_tmp), patch(
            'migasfree_client.settings.CONF_FILE', os.path.join(test_tmp, 'migasfree.conf')
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

    def test_upload_attributes(self):
        """Test upload_attributes evaluates and sends data"""
        mock_props = {'p1': 'v1'}
        mock_eval = {'attr1': 'val1'}
        with patch.object(self.sync, 'get_properties', return_value=mock_props), patch.object(
            self.sync, '_eval_attributes', return_value=mock_eval
        ):
            self.sync.upload_attributes()
            self.sync._url_request.run.assert_called_once()
            args = self.sync._url_request.run.call_args[1]
            self.assertEqual(args['data'], mock_eval)

    def test_upload_faults(self):
        """Test upload_faults evaluates and sends data when rules exist"""
        mock_defs = [{'id': 1}]
        mock_eval = {'fault1': True}
        with patch.object(self.sync, 'get_fault_definitions', return_value=mock_defs), patch.object(
            self.sync, '_eval_faults', return_value=mock_eval
        ):
            self.sync.upload_faults()
            self.sync._url_request.run.assert_called_once()
            args = self.sync._url_request.run.call_args[1]
            self.assertEqual(args['data'], mock_eval)

    def test_upload_faults_empty(self):
        """Test upload_faults does nothing if no definitions"""
        with patch.object(self.sync, 'get_fault_definitions', return_value=None):
            self.sync.upload_faults()
            self.sync._url_request.run.assert_not_called()

    def test_end_synchronization(self):
        """Test end_synchronization sends correct parameters"""
        start_date = "2026-04-10T10:00:00"
        with patch('migasfree_client.utils.get_mfc_release', return_value='1.0'):
            self.sync.end_synchronization(start_date, consumer='test-cmd')
            self.sync._url_request.run.assert_called_once()
            args = self.sync._url_request.run.call_args[1]
            self.assertEqual(args['data']['start_date'], start_date)
            self.assertEqual(args['data']['consumer'], 'test-cmd 1.0')

    @patch('os.path.isfile', return_value=True)
    @patch('os.stat')
    @patch('migasfree_client.utils.read_file', return_value='some errors')
    @patch('os.remove')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    def test_upload_old_errors(self, mock_open, mock_remove, mock_read, mock_stat, mock_isfile):
        """Test uploading accumulated errors from previous run"""
        mock_stat.return_value.st_size = 100
        self.sync.ERROR_FILE = '/tmp/errors'
        self.sync.upload_old_errors()

        self.sync._url_request.run.assert_called_once()
        self.assertTrue(mock_remove.called)
        self.assertTrue(mock_open.called)

    @patch('os.stat')
    @patch('migasfree_client.utils.read_file', return_value='new errors')
    @patch('os.remove')
    def test_upload_execution_errors(self, mock_remove, mock_read, mock_stat):
        """Test uploading errors generated during current run"""
        mock_stat.return_value.st_size = 50
        self.sync.ERROR_FILE = '/tmp/errors'
        mock_descriptor = MagicMock()

        with patch.object(self.sync, '_error_file_descriptor', mock_descriptor):
            self.sync.upload_execution_errors()
            mock_descriptor.close.assert_called_once()
            self.sync._url_request.run.assert_called_once()
            self.assertTrue(mock_remove.called)

    def test_get_repos_key_success(self):
        """Test fetching and importing repository keys"""
        self.sync._url_request.run.return_value = 'gpg-key-content'
        with patch('migasfree_client.utils.write_file', return_value=True), patch.object(
            self.sync, '_check_path', return_value=True
        ):
            self.sync.pms.import_server_key.return_value = True
            result = self.sync.get_repos_key()
            self.assertTrue(result)
            self.sync.pms.import_server_key.assert_called()

    def test_traits_management(self):
        """Test traits fetching, showing and saving to file"""
        mock_traits = [{'prefix': 'p1', 'value': 'v1'}]
        self.sync._quiet = False
        self.sync.console = MagicMock()
        with patch.object(self.sync, 'get_traits', return_value=mock_traits), patch(
            'migasfree_client.utils.write_file'
        ) as mock_write, patch('os.path.isfile', return_value=False):
            result = self.sync._traits(show=True)
            self.assertEqual(result, mock_traits)
            self.assertTrue(mock_write.called)

    @patch('os.path.isdir', return_value=True)
    @patch('migasfree_client.utils.read_file', return_value='{"after": []}')
    @patch('migasfree_client.utils.write_file')
    @patch('migasfree_client.utils.execute', return_value=(0, '', ''))
    @patch('os.path.exists', return_value=True)
    @patch('os.listdir', return_value=['event.sh'])
    def test_events_execution(self, mock_ls, mock_exists, mock_exe, mock_write, mock_read, mock_isdir):
        """Test event execution when traits change"""
        # Simulate traits transition
        traits_json = json.dumps({'before': [{'prefix': 'p1', 'value': 'v1'}], 'after': [{'prefix': 'p1', 'value': 'v2'}]})
        with patch('migasfree_client.utils.read_file', return_value=traits_json):
            self.sync._events()
            self.assertTrue(mock_exe.called)

    @patch('sys.exit')
    @patch('migasfree_client.sync.MigasFreeSync._handle_sync_command')
    def test_run_dispatch_sync(self, mock_handle, mock_exit):
        """Test main run method dispatches to sync handler"""
        args = MagicMock()
        args.cmd = 'sync'
        self.sync.run(args)
        mock_handle.assert_called_with(args)

    @patch('sys.exit', side_effect=SystemExit)
    def test_run_usage_on_no_cmd(self, mock_exit):
        """Test show usage when no command is provided"""
        self.sync.console = MagicMock()
        with self.assertRaises(SystemExit):
            self.sync.run(None)
        self.assertTrue(self.sync.console.print.called)

    def test_get_devices(self):
        """Test fetching devices from API"""
        mock_devices = [{'id': 1}]
        with patch.object(self.sync, '_api_call', return_value=mock_devices):
            result = self.sync.get_devices()
            self.assertEqual(result, mock_devices)

    @patch('migasfree_client.command.get_network_info', return_value={'ip': '1.1.1.1'})
    @patch('migasfree_client.utils.get_hardware_uuid', return_value='uuid')
    def test_save_computer_success(self, mock_uuid, mock_net):
        """Test computer registration flow"""
        self.sync._url_request.run.return_value = {'id': 123}
        with patch.object(self.sync, 'api_endpoint', return_value='http://api'):
            result = self.sync._save_computer('user', 'pass')
            self.assertEqual(result, 123)


if __name__ == '__main__':
    unittest.main()
