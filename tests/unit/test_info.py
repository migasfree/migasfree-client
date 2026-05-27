"""
Tests for MigasFreeInfo class.
"""

import unittest
from unittest.mock import MagicMock, patch

from rich.table import Table

from migasfree_client.cli.info import MigasFreeInfo


class TestMigasFreeInfo(unittest.TestCase):
    """Tests for MigasFreeInfo class"""

    @patch('migasfree_client.utils.is_root_user', return_value=True)
    @patch('migasfree_client.utils.get_config', return_value={})
    @patch('migasfree_client.command.logging.config.dictConfig')
    def setUp(self, mock_log_config, mock_config, mock_root):
        with patch('migasfree_client.utils.get_mfc_project', return_value='test-project'), patch(
            'migasfree_client.utils.get_mfc_computer_name', return_value='test-computer'
        ):
            self.info = MigasFreeInfo()
            self.info._url_request = MagicMock()
            self.info._init_url_request = MagicMock()
            self.info._init_mtls = MagicMock()
            self.info._computer_id = 123
            self.info._mtls_cert = 'cert-path'
            self.info.console = MagicMock()
            self.info._check_sign_keys = MagicMock(return_value=True)

    @patch('migasfree_client.cli.info.MigasFreeInfo.get_info')
    def test_show_info_all(self, mock_get_info):
        """Test showing all computer info (table mode)"""
        mock_get_info.return_value = {'name': 'test-comp', 'search': 'TEST-SEARCH', 'uuid': 'TEST-UUID'}
        self.info._quiet = False
        self.info._show_info()

        self.info.console.print.assert_called()
        # Find the call that contains the Table object, skipping empty calls
        table_call = next(
            call for call in self.info.console.print.call_args_list if call[0] and isinstance(call[0][0], Table)
        )
        self.assertIsNotNone(table_call)

    @patch('migasfree_client.cli.info.MigasFreeInfo.get_info')
    def test_show_info_quiet(self, mock_get_info):
        """Test showing information in quiet mode (tab separated)"""
        mock_get_info.return_value = {'name': 'test-comp', 'search': 'TEST-SEARCH', 'uuid': 'TEST-UUID'}
        self.info._quiet = True
        self.info._show_info()

        self.info.console.print.assert_called_with('123\ttest-comp\tTEST-SEARCH\tTEST-UUID')

    @patch('migasfree_client.cli.info.MigasFreeInfo.get_info')
    def test_show_info_specific_key(self, mock_get_info):
        """Test showing only a specific key"""
        mock_get_info.return_value = {'search': 'TEST-SEARCH'}
        self.info._quiet = True
        self.info._show_info(key='search')

        self.info.console.print.assert_called_with('TEST-SEARCH')

    @patch('migasfree_client.cli.info.MigasFreeInfo.get_info')
    def test_show_info_id_only(self, mock_get_info):
        """Test showing only computer ID"""
        self.info._quiet = True
        self.info._show_info(key='id')

        self.info.console.print.assert_called_with('123')

    def test_get_info_success(self):
        """Test get_info calls API correctly"""
        mock_response = {'name': 'test'}
        with patch.object(self.info, '_api_call', return_value=mock_response), patch.object(
            self.info, '_handle_response', return_value=mock_response
        ):
            result = self.info.get_info()
            self.assertEqual(result, mock_response)

    @patch('sys.exit')
    def test_run(self, mock_exit):
        """Test the run method dispatcher"""
        args = MagicMock()
        args.key = 'search'
        args.json = False
        self.info._quiet = True

        with patch.object(self.info, '_show_info') as mock_show:
            self.info.run(args)
            mock_show.assert_called_with(key='search', output_json=False)
            mock_exit.assert_called_once()


if __name__ == '__main__':
    unittest.main()
