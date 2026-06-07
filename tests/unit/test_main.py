"""
Unit tests for migasfree_client.__main__
"""

import contextlib
import os
import sys
import tempfile
from unittest.mock import patch

from migasfree_client.__main__ import main, parse_args
from migasfree_client.utils import ALL_OK


class TestParseArgs:
    """Tests for CLI argument parsing"""

    def test_global_flags(self):
        """Test global --debug and --quiet flags"""
        args = parse_args(['--debug', '--quiet', 'version'])
        assert args.debug is True
        assert args.quiet is True
        assert args.cmd == 'version'

    def test_register_command(self):
        """Test parsing of register command and its arguments"""
        args = parse_args(['register', '-u', 'testuser', '-p', 'testpass', '-y'])
        assert args.cmd == 'register'
        assert args.user == 'testuser'
        assert args.password == 'testpass'
        assert args.assume_yes is True

    def test_sync_command(self):
        """Test parsing of sync command and its arguments"""
        args = parse_args(['sync', '-f', '-dev'])
        assert args.cmd == 'sync'
        assert args.force_upgrade is True
        assert args.devices is True

    def test_apps_command(self):
        """Test parsing of apps command"""
        args = parse_args(['apps', '-c', '123', '-j'])
        assert args.cmd == 'apps'
        assert args.category == '123'
        assert args.json is True

    def test_info_command(self):
        """Test parsing of info command"""
        args = parse_args(['info', 'id', '-j'])
        assert args.cmd == 'info'
        assert args.key == 'id'
        assert args.json is True


class TestMainRouting:
    """Tests for main() command dispatching"""

    @patch('migasfree_client.cli.sync.MigasFreeSync.run')
    def test_route_sync(self, mock_run):
        """Test routing to MigasFreeSync"""
        result = main(['sync'])
        assert result == ALL_OK
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args.cmd == 'sync'

    @patch('migasfree_client.cli.register.MigasFreeRegister.run')
    def test_route_register(self, mock_run):
        """Test routing to MigasFreeRegister"""
        result = main(['register', '-u', 'u', '-p', 'p'])
        assert result == ALL_OK
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args.cmd == 'register'

    @patch('migasfree_client.cli.apps.MigasFreeApps.run')
    def test_route_apps(self, mock_run):
        """Test routing to MigasFreeApps"""
        result = main(['apps'])
        assert result == ALL_OK
        mock_run.assert_called_once()

    @patch('migasfree_client.cli.info.MigasFreeInfo.run')
    def test_route_info(self, mock_run):
        """Test routing to MigasFreeInfo"""
        result = main(['info', 'id'])
        assert result == ALL_OK
        mock_run.assert_called_once()

    @patch('migasfree_client.command.MigasFreeCommand.cmd_version')
    def test_route_version(self, mock_version):
        """Test routing to MigasFreeCommand.cmd_version"""
        result = main(['version'])
        assert result == ALL_OK
        mock_version.assert_called_once()

    @patch('migasfree_client.command.MigasFreeCommand.cmd_import_mtls')
    def test_route_import_mtls(self, mock_import):
        """Test routing to MigasFreeCommand.cmd_import_mtls"""
        result = main(['import-mtls', '/path/to/cert.tar'])
        assert result == ALL_OK
        mock_import.assert_called_once_with('/path/to/cert.tar')

    @patch('migasfree_client.cli.device.MigasFreeDevices.run')
    def test_route_devices(self, mock_run):
        """Test routing to MigasFreeDevices"""
        result = main(['devices'])
        assert result == ALL_OK
        mock_run.assert_called_once()

    @patch('sys.exit')
    @patch('migasfree_client.__main__.argparse.ArgumentParser.print_help')
    def test_main_no_args(self, mock_help, mock_exit):
        """Test main behavior when called without arguments"""
        # Patch sys.argv to simulate running with no arguments
        with patch.object(sys, 'argv', ['migasfree']):
            # parse_args should print help and exit
            parse_args([])
            mock_help.assert_called_once()
            mock_exit.assert_called_once_with(ALL_OK)

    def test_route_eval_with_exit(self):
        """Test routing to eval command and executing a script that uses exit"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('exit(0)\n')
            temp_name = f.name

        try:
            try:
                main(['eval', temp_name])
                raise AssertionError('SystemExit should be raised')
            except SystemExit as e:
                assert e.code == 0
        finally:
            if os.path.exists(temp_name):
                os.remove(temp_name)

    def test_route_eval_with_quit(self):
        """Test routing to eval command and executing a script that uses quit"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('quit(0)\n')
            temp_name = f.name

        try:
            try:
                main(['eval', temp_name])
                raise AssertionError('SystemExit should be raised')
            except SystemExit as e:
                assert e.code == 0
        finally:
            if os.path.exists(temp_name):
                os.remove(temp_name)

    @patch('migasfree_client.__main__.rprint')
    def test_route_eval_does_not_print_version(self, mock_rprint):
        """Test that eval subcommand does not print the program version"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('exit(0)\n')
            temp_name = f.name

        try:
            with contextlib.suppress(SystemExit):
                main(['eval', temp_name])
            mock_rprint.assert_not_called()
        finally:
            if os.path.exists(temp_name):
                os.remove(temp_name)
