import json
import unittest
from unittest.mock import MagicMock, patch

from migasfree_client.cli.register import MigasFreeRegister
from migasfree_client.cli.search import MigasFreeSearch
from migasfree_client.cli.traits import MigasFreeTraits


class TestSubcommands(unittest.TestCase):
    @patch('migasfree_client.utils.is_root_user', return_value=True)
    @patch('migasfree_client.utils.get_config', return_value={})
    @patch('migasfree_client.command.logging.config.dictConfig')
    def setUp(self, mock_log_config, mock_config, mock_root):
        with patch('migasfree_client.utils.get_mfc_project', return_value='test-project'), patch(
            'migasfree_client.utils.get_mfc_computer_name', return_value='test-computer'
        ):
            # Instantiate commands
            self.search_cmd = MigasFreeSearch()
            self.search_cmd.console = MagicMock()
            self.search_cmd.pms = MagicMock()
            self.search_cmd._init_command = MagicMock()
            self.search_cmd._check_sign_keys = MagicMock(return_value=True)
            self.search_cmd.end_of_transmission = MagicMock()

            self.traits_cmd = MigasFreeTraits()
            self.traits_cmd.console = MagicMock()
            self.traits_cmd._computer_id = 123
            self.traits_cmd._init_command = MagicMock()
            self.traits_cmd._check_sign_keys = MagicMock(return_value=True)
            self.traits_cmd.end_of_transmission = MagicMock()

            self.register_cmd = MigasFreeRegister()
            self.register_cmd.console = MagicMock()
            self.register_cmd._init_command = MagicMock()
            self.register_cmd._check_sign_keys = MagicMock(return_value=True)
            self.register_cmd.end_of_transmission = MagicMock()

    @patch('sys.exit')
    def test_search_run(self, mock_exit):
        args = MagicMock()
        args.pattern = ['firefox']
        args.quiet = True
        args.debug = False

        self.search_cmd.run(args)

        self.search_cmd.pms.search.assert_called_once_with('firefox')
        mock_exit.assert_called_once()

    @patch('sys.exit')
    @patch('migasfree_client.utils.write_file')
    @patch('os.path.isfile', return_value=False)
    def test_traits_run(self, mock_isfile, mock_write, mock_exit):
        args = MagicMock()
        args.prefix = 'p1'
        args.traits_key = 'value'
        args.quiet = True
        args.debug = False

        mock_traits = [{'prefix': 'p1', 'value': 'v1'}, {'prefix': 'p2', 'value': 'v2'}]

        with patch.object(self.traits_cmd, 'get_traits', return_value=mock_traits):
            self.traits_cmd.run(args)

            self.traits_cmd.console.print.assert_called_once_with(
                json.dumps(['v1'], indent=4, ensure_ascii=False), soft_wrap=True
            )

    @patch('sys.exit')
    @patch('migasfree_client.cli.register.lock_file_context')
    def test_register_run(self, mock_lock, mock_exit):
        args = MagicMock()
        args.user = 'test-user'
        args.password = 'test-pass'
        args.assume_yes = True
        args.quiet = True
        args.debug = False

        with patch.object(self.register_cmd, 'cmd_register_computer') as mock_register:
            self.register_cmd.run(args)
            mock_register.assert_called_once_with('test-user', 'test-pass', True)
