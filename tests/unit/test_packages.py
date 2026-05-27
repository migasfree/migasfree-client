import json
import unittest
from unittest.mock import MagicMock, patch

from migasfree_client.cli.packages import MigasFreePackages


class TestMigasFreePackages(unittest.TestCase):
    @patch('migasfree_client.utils.is_root_user', return_value=True)
    @patch('migasfree_client.utils.get_config', return_value={})
    @patch('migasfree_client.command.logging.config.dictConfig')
    def setUp(self, mock_log_config, mock_config, mock_root):
        with patch('migasfree_client.utils.get_mfc_project', return_value='test-project'), patch(
            'migasfree_client.utils.get_mfc_computer_name', return_value='test-computer'
        ):
            self.cmd = MigasFreePackages()
            self.cmd.console = MagicMock()
            self.cmd.pms = MagicMock()

    @patch('sys.exit')
    def test_run_available_quiet(self, mock_exit):
        """Test packages --available with quiet/silent mode"""
        args = MagicMock()
        args.available = True
        args.installed = False
        args.check = False
        args.quiet = True
        args.debug = False

        self.cmd.pms.available_packages.return_value = ['google-chrome-stable', 'firefox-esr']

        self.cmd.run(args)

        self.cmd.pms.available_packages.assert_called_once()
        self.cmd.console.print.assert_called_once_with(
            json.dumps(['google-chrome-stable', 'firefox-esr']), soft_wrap=True
        )
        mock_exit.assert_called_once()

    @patch('sys.exit')
    def test_run_available_interactive(self, mock_exit):
        """Test packages --available in interactive mode (verbose)"""
        args = MagicMock()
        args.available = True
        args.installed = False
        args.check = False
        args.quiet = False
        args.debug = False

        self.cmd.pms.available_packages.return_value = ['google-chrome-stable', 'firefox-esr']

        self.cmd.run(args)

        self.cmd.pms.available_packages.assert_called_once()
        self.cmd.console.print.assert_any_call('Total Available Packages: 2', style='bold')
        mock_exit.assert_called_once()

    @patch('sys.exit')
    def test_run_installed_quiet(self, mock_exit):
        """Test packages --installed with quiet/silent mode"""
        args = MagicMock()
        args.available = False
        args.installed = True
        args.check = False
        args.quiet = True
        args.debug = False

        self.cmd.pms.query_all.return_value = ['firefox-esr_115.8_amd64.deb']

        self.cmd.run(args)

        self.cmd.pms.query_all.assert_called_once()
        self.cmd.console.print.assert_called_once_with(json.dumps(['firefox-esr_115.8_amd64.deb']), soft_wrap=True)
        mock_exit.assert_called_once()

    @patch('sys.exit')
    def test_run_check_quiet(self, mock_exit):
        """Test packages --check with quiet/silent mode"""
        args = MagicMock()
        args.available = False
        args.installed = False
        args.check = ['["firefox-esr", "non-existent"]']
        args.quiet = True
        args.debug = False

        self.cmd.pms.is_installed.side_effect = lambda pkg: pkg == 'firefox-esr'

        self.cmd.run(args)

        self.cmd.pms.is_installed.assert_any_call('firefox-esr')
        self.cmd.pms.is_installed.assert_any_call('non-existent')
        self.cmd.console.print.assert_called_once_with(json.dumps(['firefox-esr']), soft_wrap=True)
        mock_exit.assert_called_once()


if __name__ == '__main__':
    unittest.main()
