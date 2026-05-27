"""
Tests for MigasFreeDevices class.
"""

import unittest
from unittest.mock import MagicMock, patch

from migasfree_client.cli.device import MigasFreeDevices


class TestMigasFreeDevices(unittest.TestCase):
    """Tests for MigasFreeDevices class"""

    @patch('migasfree_client.utils.is_root_user', return_value=True)
    @patch('migasfree_client.utils.get_config', return_value={})
    @patch('migasfree_client.command.logging.config.dictConfig')
    def setUp(self, mock_log_config, mock_config, mock_root):
        with patch('migasfree_client.utils.get_mfc_project', return_value='test-project'), patch(
            'migasfree_client.utils.get_mfc_computer_name', return_value='test-computer'
        ):
            self.devices = MigasFreeDevices()
            self.devices._url_request = MagicMock()
            self.devices._init_url_request = MagicMock()
            self.devices._init_mtls = MagicMock()
            self.devices._computer_id = 123
            self.devices._mtls_cert = 'cert-path'
            self.devices.console = MagicMock()
            self.devices._check_sign_keys = MagicMock(return_value=True)
            self.devices._check_user_is_root = MagicMock()

    @patch('sys.exit')
    def test_run_json(self, mock_exit):
        """Test run with JSON output"""
        args = MagicMock()
        args.json = True
        args.available = False
        args.logical = False
        args.capabilities = None

        mock_results = [{'id': 1}]
        with patch.object(self.devices, 'get_assigned_devices', return_value=mock_results):
            self.devices.run(args)
            self.devices.console.print.assert_called()
            mock_exit.assert_called_once()

    @patch('sys.exit')
    def test_run_available_devices(self, mock_exit):
        """Test run displaying available physical devices"""
        args = MagicMock()
        args.json = False
        args.available = True
        args.logical = False
        args.capabilities = None

        mock_results = [
            {
                'id': 1032,
                'name': 'HP DesignJet_1050C',
                'model': {'name': 'DesignJet 1050C', 'manufacturer': {'name': 'HP'}},
                'connection': {'name': 'cups'},
                'location': 'Seminario PLB',
            }
        ]
        with patch.object(self.devices, 'get_available_devices', return_value=mock_results):
            self.devices.run(args)
            self.devices.console.print.assert_called()
            mock_exit.assert_called_once()

    @patch('sys.exit')
    def test_run_logical_devices(self, mock_exit):
        """Test run displaying logical devices cards"""
        args = MagicMock()
        args.json = False
        args.available = False
        args.logical = True
        args.device_id = None
        args.capabilities = None

        mock_logical = [
            {
                'id': 1,
                'device': {'id': 1032, 'name': 'HP DesignJet_1050C'},
                'capability': {'name': 'Color'},
                'alternative_capability_name': 'Color',
                '__str__': 'HP_DesignJet_1050C__Color__cups',
            }
        ]
        mock_available = [{'id': 1032, 'name': 'HP DesignJet_1050C', 'location': 'Seminario PLB'}]
        with patch.object(self.devices, 'get_logical_devices', return_value=mock_logical), patch.object(
            self.devices, 'get_available_devices', return_value=mock_available
        ):
            self.devices.run(args)
            self.devices.console.print.assert_called()
            mock_exit.assert_called_once()

    @patch('sys.exit')
    def test_run_capabilities(self, mock_exit):
        """Test run displaying capabilities table"""
        args = MagicMock()
        args.json = False
        args.available = False
        args.logical = False
        args.capabilities = 'Color'

        mock_results = [{'id': 1, 'name': 'Color'}]
        with patch.object(self.devices, 'get_capabilities', return_value=mock_results):
            self.devices.run(args)
            self.devices.console.print.assert_called()
            mock_exit.assert_called_once()

    @patch('sys.exit')
    def test_run_assigned_devices(self, mock_exit):
        """Test run displaying assigned devices cards"""
        args = MagicMock()
        args.json = False
        args.available = False
        args.logical = False
        args.capabilities = None

        mock_results = {
            'logical': [
                {
                    'printer': {
                        'id': 99,
                        'name': 'HP DesignJet_1050C',
                        'model': 'DesignJet 1050C',
                        'driver': 'hp-laserjet',
                        'capability': 'color',
                        'manufacturer': 'HP',
                        'connection': {'LOCATION': 'Seminario PLB', 'IP': '192.168.1.103', 'NAME': 'Fotocopiadora'},
                        '__str__': 'HP_DesignJet_1050C__color__cups',
                    }
                }
            ],
            'default': 99,
        }
        with patch.object(self.devices, 'get_assigned_devices', return_value=mock_results):
            self.devices.run(args)
            self.devices.console.print.assert_called()
            mock_exit.assert_called_once()

    @patch('sys.exit')
    def test_run_no_results(self, mock_exit):
        """Test run when no results are found"""
        args = MagicMock()
        args.json = False
        args.available = False
        args.logical = False
        args.capabilities = None

        with patch.object(self.devices, 'get_assigned_devices', return_value=None):
            self.devices.run(args)
            self.devices.console.print.assert_called_with('No results found.')
            mock_exit.assert_called_once()

    @patch('sys.exit')
    def test_run_available_devices_edge_cases(self, mock_exit):
        """Test run available devices with different formats of manufacturer, model, and location"""
        args = MagicMock()
        args.json = False
        args.available = True
        args.logical = False
        args.capabilities = None

        mock_results = [
            {
                'id': 1032,
                'name': 'HP DesignJet_1050C',
                'model': 'DesignJet 1050C',
                'manufacturer': 'HP',
                'location': None,
                'data': {'LOCATION': 'Seminario PLB', 'IP': '192.168.1.103', 'NAME': 'Fotocopiadora'},
            }
        ]
        with patch.object(self.devices, 'get_available_devices', return_value=mock_results):
            self.devices.run(args)
            self.devices.console.print.assert_called()
            mock_exit.assert_called_once()

    @patch('sys.exit')
    def test_run_logical_devices_edge_cases(self, mock_exit):
        """Test run logical devices with exceptions and missing device ID"""
        args = MagicMock()
        args.json = False
        args.available = False
        args.logical = True
        args.device_id = None
        args.capabilities = None

        mock_logical = [{'id': 1, 'device': {'name': 'No ID Device'}, 'capability': {'name': 'Color'}}]
        with patch.object(self.devices, 'get_logical_devices', return_value=mock_logical), patch.object(
            self.devices, 'get_available_devices', side_effect=Exception('WMI Error')
        ):
            self.devices.run(args)
            self.devices.console.print.assert_called()
            mock_exit.assert_called_once()

    @patch('sys.exit')
    def test_run_assigned_devices_edge_cases(self, mock_exit):
        """Test run assigned devices in list mode with empty/invalid structures"""
        args = MagicMock()
        args.json = False
        args.available = False
        args.logical = False
        args.capabilities = None

        # Test results as a list, including an invalid non-dict item, empty dict, and non-dict inner item
        mock_results = [
            'not-a-dict',
            {},
            {'invalid_inner': 'not-a-dict'},
            {
                'printer': {
                    'id': 99,
                    'name': 'HP DesignJet_1050C',
                    'capability': 'color',
                    '__str__': 'HP_DesignJet_1050C__color__cups',
                }
            },
        ]
        with patch.object(self.devices, 'get_assigned_devices', return_value=mock_results):
            self.devices.run(args)
            self.devices.console.print.assert_called()
            mock_exit.assert_called_once()

    def test_get_assigned_devices(self):
        """Test get_assigned_devices method calls API correctly"""
        mock_response = {'logical': [], 'default': 0}
        with patch.object(self.devices, '_api_call', return_value=mock_response), patch.object(
            self.devices, '_handle_response', return_value=mock_response
        ):
            result = self.devices.get_assigned_devices()
            self.assertEqual(result, mock_response)

    def test_get_available_devices(self):
        """Test get_available_devices method calls API correctly"""
        mock_response = [{'id': 1}]
        with patch.object(self.devices, '_api_call', return_value=mock_response), patch.object(
            self.devices, '_handle_response', return_value=mock_response
        ):
            result = self.devices.get_available_devices()
            self.assertEqual(result, mock_response)

    def test_get_logical_devices(self):
        """Test get_logical_devices method calls API correctly"""
        mock_response = [{'id': 2}]
        with patch.object(self.devices, '_api_call', return_value=mock_response), patch.object(
            self.devices, '_handle_response', return_value=mock_response
        ):
            result = self.devices.get_logical_devices(device_id=10)
            self.assertEqual(result, mock_response)

    def test_get_capabilities(self):
        """Test get_capabilities method calls API correctly"""
        mock_response = [{'id': 3}]
        with patch.object(self.devices, '_api_call', return_value=mock_response), patch.object(
            self.devices, '_handle_response', return_value=mock_response
        ):
            result = self.devices.get_capabilities(capability_id=5)
            self.assertEqual(result, mock_response)

    def test_assign_logical(self):
        """Test assign_logical method calls API correctly"""
        mock_response = {'id': 99, 'attributes': []}
        with patch.object(self.devices, '_api_call', return_value=mock_response), patch.object(
            self.devices, '_handle_response', return_value=mock_response
        ):
            result = self.devices.assign_logical(logical_id='99', assigned=True)
            self.assertEqual(result, mock_response)

    def test_set_default_logical(self):
        """Test set_default_logical method calls API correctly"""
        mock_response = {'id': 99}
        with patch.object(self.devices, '_api_call', return_value=mock_response), patch.object(
            self.devices, '_handle_response', return_value=mock_response
        ):
            result = self.devices.set_default_logical(logical_id='99')
            self.assertEqual(result, mock_response)

    @patch('sys.exit')
    def test_run_assign(self, mock_exit):
        """Test run with --assign"""
        args = MagicMock()
        args.json = False
        args.available = False
        args.logical = False
        args.capabilities = None
        args.assign = '99'
        args.unassign = None
        args.set_default = None

        mock_results = {'id': 99}
        with patch.object(self.devices, 'assign_logical', return_value=mock_results):
            self.devices.run(args)
            self.devices.console.print.assert_called_with('Logical device assigned successfully.')
            mock_exit.assert_called_once()

    @patch('sys.exit')
    def test_run_unassign(self, mock_exit):
        """Test run with --unassign"""
        args = MagicMock()
        args.json = False
        args.available = False
        args.logical = False
        args.capabilities = None
        args.assign = None
        args.unassign = '99'
        args.set_default = None

        mock_results = {}
        with patch.object(self.devices, 'assign_logical', return_value=mock_results):
            self.devices.run(args)
            self.devices.console.print.assert_called_with('Logical device unassigned successfully.')
            mock_exit.assert_called_once()

    @patch('sys.exit')
    def test_run_set_default(self, mock_exit):
        """Test run with --set-default"""
        args = MagicMock()
        args.json = False
        args.available = False
        args.logical = False
        args.capabilities = None
        args.assign = None
        args.unassign = None
        args.set_default = '99'

        mock_results = {'id': 99}
        with patch.object(self.devices, 'set_default_logical', return_value=mock_results):
            self.devices.run(args)
            self.devices.console.print.assert_called_with('Default logical device updated successfully.')
            mock_exit.assert_called_once()


if __name__ == '__main__':
    unittest.main()
