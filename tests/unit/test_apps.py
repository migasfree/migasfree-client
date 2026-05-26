"""
Tests for MigasFreeApps and MigasFreeCategories classes.
"""

import unittest
from unittest.mock import MagicMock, patch

from migasfree_client.apps import MigasFreeApps, MigasFreeCategories


class TestMigasFreeCategories(unittest.TestCase):
    """Tests for MigasFreeCategories class"""

    @patch('migasfree_client.utils.is_root_user', return_value=True)
    @patch('migasfree_client.utils.get_config', return_value={})
    @patch('migasfree_client.command.logging.config.dictConfig')
    def setUp(self, mock_log_config, mock_config, mock_root):
        with patch('migasfree_client.utils.get_mfc_project', return_value='test-project'), patch(
            'migasfree_client.utils.get_mfc_computer_name', return_value='test-computer'
        ):
            self.cmd = MigasFreeCategories()
            self.cmd._url_request = MagicMock()
            self.cmd._init_url_request = MagicMock()
            self.cmd._init_mtls = MagicMock()
            self.cmd._check_sign_keys = MagicMock(return_value=True)
            self.cmd.console = MagicMock()

    @patch('sys.exit')
    def test_run_json(self, mock_exit):
        """Test run with JSON output"""
        args = MagicMock()
        args.json = True

        mock_results = [{'id': 1, 'name': 'Graphics'}]
        with patch.object(self.cmd, 'get_categories', return_value=mock_results):
            self.cmd.run(args)
            self.cmd.console.print.assert_called()
            mock_exit.assert_called_once()

    @patch('sys.exit')
    def test_run_empty(self, mock_exit):
        """Test run with empty results"""
        args = MagicMock()
        args.json = False

        with patch.object(self.cmd, 'get_categories', return_value=[]):
            self.cmd.run(args)
            self.cmd.console.print.assert_called()
            mock_exit.assert_called_once()

    @patch('sys.exit')
    def test_run_table(self, mock_exit):
        """Test run displaying categories table"""
        args = MagicMock()
        args.json = False

        mock_results = [{'id': 1, 'name': 'Graphics'}]
        with patch.object(self.cmd, 'get_categories', return_value=mock_results):
            self.cmd.run(args)
            self.cmd.console.print.assert_called()
            mock_exit.assert_called_once()


class TestMigasFreeApps(unittest.TestCase):
    """Tests for MigasFreeApps class"""

    @patch('migasfree_client.utils.is_root_user', return_value=True)
    @patch('migasfree_client.utils.get_config', return_value={})
    @patch('migasfree_client.command.logging.config.dictConfig')
    def setUp(self, mock_log_config, mock_config, mock_root):
        with patch('migasfree_client.utils.get_mfc_project', return_value='test-project'), patch(
            'migasfree_client.utils.get_mfc_computer_name', return_value='test-computer'
        ):
            self.cmd = MigasFreeApps()
            self.cmd._url_request = MagicMock()
            self.cmd._init_url_request = MagicMock()
            self.cmd._init_mtls = MagicMock()
            self.cmd._computer_id = 123
            self.cmd._check_sign_keys = MagicMock(return_value=True)
            self.cmd.console = MagicMock()

    @patch('sys.exit')
    def test_run_json(self, mock_exit):
        """Test run with JSON output"""
        args = MagicMock()
        args.json = True
        args.category = None

        mock_results = [{'id': 1, 'name': 'InkScape'}]
        with patch.object(self.cmd, 'get_available_apps', return_value=mock_results):
            self.cmd.run(args)
            self.cmd.console.print.assert_called()
            mock_exit.assert_called_once()

    @patch('sys.exit')
    def test_run_empty(self, mock_exit):
        """Test run with empty results"""
        args = MagicMock()
        args.json = False
        args.category = 2

        with patch.object(self.cmd, 'get_available_apps', return_value=[]):
            self.cmd.run(args)
            self.cmd.console.print.assert_called()
            mock_exit.assert_called_once()

    @patch('sys.exit')
    def test_run_cards(self, mock_exit):
        """Test run displaying premium cards"""
        args = MagicMock()
        args.json = False
        args.category = None

        mock_results = [
            {
                'id': 1,
                'name': 'InkScape',
                'category': {'name': 'Graphics'},
                'level': {'name': 'User'},
                'description': 'Editor de gráficos vectoriales libre.',
                'score': 4,
                'packages_by_project': [
                    {
                        'project': {'name': 'test-project'},
                        'packages_to_install': ['inkscape', 'inkscape-data'],
                    },
                    {
                        'project': {'name': 'other-project'},
                        'packages_to_install': ['should-not-show-pkg'],
                    },
                ],
            },
            {
                'id': 2,
                'name': 'Logseq',
                'category': 'Accessories',
                'level': 'User',
                'description': 'Conecta tus notas.',
                'score': 5,
                'packages_by_project': [
                    {
                        'project': {'name': 'test-project'},
                        'packages_to_install': 'logseq-desktop',
                    }
                ],
            },
        ]
        with patch.object(self.cmd, 'get_available_apps', return_value=mock_results):
            self.cmd.run(args)
            self.cmd.console.print.assert_called()
            mock_exit.assert_called_once()
