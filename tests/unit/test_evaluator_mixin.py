# Copyright (c) 2026 Jose Antonio Chavarría <jachavar@gmail.com>
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
Tests for evaluator mixin.
"""

import unittest
from unittest.mock import MagicMock, patch

from migasfree_client.mixins.evaluator import CodeEvaluatorMixin


class DummyEvaluator(CodeEvaluatorMixin):
    def __init__(self):
        self._url_request = MagicMock()
        self._debug = False
        self._computer_id = 123
        self.migas_computer_name = 'test-pc'
        self._graphic_user = 'test-user'
        self.console = MagicMock()
        self.URLS = {'get_properties': '/p/', 'get_fault_definitions': '/f/'}

    def api_endpoint(self, url):
        return f'http://api{url}'

    def _show_message(self, msg):
        pass

    def _report_error(self, msg):
        pass

    def operation_failed(self, msg):
        pass

    def operation_ok(self, msg=''):
        pass

    def _write_error(self, msg):
        pass


class TestCodeEvaluatorMixin(unittest.TestCase):
    """Tests for CodeEvaluatorMixin class"""

    def setUp(self):
        self.evaluator = DummyEvaluator()

    @patch('migasfree_client.network.get_network_info', return_value={'ip': '1.2.3.4'})
    @patch('migasfree_client.utils.get_user_info', return_value={'fullname': 'Test User'})
    @patch('migasfree_client.utils.get_hardware_uuid', return_value='uuid')
    @patch('migasfree_client.utils.timeout_execute', return_value=(0, 'attr_val', ''))
    @patch('migasfree_client.utils.write_file')
    @patch('os.remove')
    def test_eval_attributes(self, mock_remove, mock_write, mock_exe, mock_uuid, mock_user, mock_net):
        """Test evaluation of attribute rules via execution"""
        properties = [{'prefix': 'attr1', 'language': 'python', 'code': 'print("val")'}]
        result = self.evaluator._eval_attributes(properties)
        self.assertEqual(result['sync_attributes']['attr1'], 'attr_val')

    @patch('migasfree_client.utils.timeout_execute', return_value=(0, 'fault_occurred', ''))
    @patch('migasfree_client.utils.write_file')
    @patch('os.remove')
    def test_eval_faults(self, mock_remove, mock_write, mock_exe):
        """Test evaluation of fault definitions via execution"""
        faults = [{'name': 'fault1', 'language': 'python', 'code': 'exit(1)'}]
        result = self.evaluator._eval_faults(faults)
        self.assertEqual(result['faults']['fault1'], 'fault_occurred')


if __name__ == '__main__':
    unittest.main()
