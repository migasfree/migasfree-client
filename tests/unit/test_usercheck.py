import json
import sys
import unittest
from unittest.mock import MagicMock, patch

# Mock pwd and grp on Windows to avoid ModuleNotFoundError during patch decoration
if sys.platform == 'win32':
    sys.modules['pwd'] = MagicMock()
    sys.modules['grp'] = MagicMock()

from migasfree_client.usercheck import MigasFreeUserCheck


class TestMigasFreeUserCheck(unittest.TestCase):
    @patch('migasfree_client.utils.is_root_user', return_value=True)
    @patch('migasfree_client.utils.get_config', return_value={})
    @patch('migasfree_client.command.logging.config.dictConfig')
    def setUp(self, mock_log_config, mock_config, mock_root):
        with patch('migasfree_client.utils.get_mfc_project', return_value='test-project'), patch(
            'migasfree_client.utils.get_mfc_computer_name', return_value='test-computer'
        ):
            self.cmd = MigasFreeUserCheck()
            self.cmd.console = MagicMock()

    @patch('sys.exit')
    @patch('builtins.print')
    @patch('platform.system', return_value='Linux')
    @patch('pwd.getpwnam')
    @patch('grp.getgrgid')
    @patch('grp.getgrall', return_value=[])
    @patch('subprocess.run')
    def test_run_auth_sudo_success_quiet(
        self, mock_sub_run, mock_grall, mock_grgid, mock_pwnam, mock_sys, mock_print, mock_exit
    ):
        """Test user-check success via sudo_auth in quiet mode"""
        args = MagicMock()
        args.user = 'tux'
        args.pwd = 'secret'
        args.quiet = True
        args.debug = False

        # Mock pwd info
        mock_pw = MagicMock()
        mock_pw.pw_gid = 1000
        mock_pwnam.return_value = mock_pw

        mock_gr = MagicMock()
        mock_gr.gr_name = 'tux'
        mock_grgid.return_value = mock_gr

        # Mock subprocess successful authentication (sudo -S)
        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_sub_run.return_value = mock_res

        self.cmd.run(args)

        mock_sub_run.assert_called_once()
        # Verify JSON output structure
        args_called = mock_print.call_args[0][0]
        res_json = json.loads(args_called)
        self.assertTrue(res_json['authenticated'])
        self.assertTrue(res_json['is_privileged'])
        self.assertEqual(res_json['username'], 'tux')
        self.assertEqual(res_json['platform'], 'linux')
        self.assertEqual(res_json['groups'], ['tux'])
        mock_exit.assert_called_once()

    @patch('sys.exit')
    @patch('platform.system', return_value='Linux')
    @patch('pwd.getpwnam')
    @patch('grp.getgrgid')
    @patch('grp.getgrall', return_value=[])
    @patch('subprocess.run')
    def test_run_auth_sudo_success_interactive(
        self, mock_sub_run, mock_grall, mock_grgid, mock_pwnam, mock_sys, mock_exit
    ):
        """Test user-check success via sudo_auth in interactive mode (verbose)"""
        args = MagicMock()
        args.user = 'tux'
        args.pwd = 'secret'
        args.quiet = False
        args.debug = False

        # Mock pwd info
        mock_pw = MagicMock()
        mock_pw.pw_gid = 1000
        mock_pwnam.return_value = mock_pw

        mock_gr = MagicMock()
        mock_gr.gr_name = 'tux'
        mock_grgid.return_value = mock_gr

        # Mock subprocess successful authentication (sudo -S)
        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_sub_run.return_value = mock_res

        self.cmd.run(args)

        args_called = [
            call.args[0] for call in self.cmd.console.print.mock_calls if call.args and isinstance(call.args[0], str)
        ]
        self.assertTrue(any('tux' in arg for arg in args_called))
        self.assertTrue(any('linux' in arg for arg in args_called))
        mock_exit.assert_called_once()


if __name__ == '__main__':
    unittest.main()
