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
Tests for CodeEvaluatorMixin.
"""

import unittest
from unittest.mock import MagicMock, patch

from migasfree_client.mixins.evaluator import CodeEvaluatorMixin


class ConcreteEvaluator(CodeEvaluatorMixin):
    """Concrete class to test the mixin"""

    def __init__(self):
        self._computer_id = 123
        self.migas_computer_name = 'test-comp'
        self._graphic_user = 'test-user'
        self.console = MagicMock()
        self.operation_ok = MagicMock()
        self.operation_failed = MagicMock()
        self._write_error = MagicMock()
        self._show_message = MagicMock()


class TestCodeEvaluatorMixin(unittest.TestCase):
    """Tests for CodeEvaluatorMixin"""

    def setUp(self):
        self.evaluator = ConcreteEvaluator()

    @patch('migasfree_client.utils.write_file')
    @patch('migasfree_client.utils.timeout_execute')
    @patch('migasfree_client.utils.is_linux', return_value=True)
    def test_eval_code_python_linux(self, mock_linux, mock_execute, mock_write):
        """Test evaluating Python code on Linux"""
        mock_execute.return_value = (0, 'execution output', '')

        ret, output, _error = self.evaluator._eval_code('test-trait', 'python', 'print("hello")')

        self.assertEqual(ret, 0)
        self.assertEqual(output, 'execution output')
        mock_execute.assert_called()
        cmd = mock_execute.call_args[0][0]
        self.assertEqual(cmd[0], 'python3')

    @patch('socket.getfqdn', return_value='test.host')
    @patch('migasfree_client.network.get_network_info', return_value={'ip': '192.168.1.10'})
    @patch('migasfree_client.utils.get_user_info', return_value={'fullname': 'Test User'})
    @patch('migasfree_client.utils.get_hardware_uuid', return_value='UUID-123')
    def test_eval_attributes(self, mock_uuid, mock_user, mock_net, mock_fqdn):
        """Test evaluating multiple attributes (traits)"""
        with patch.object(ConcreteEvaluator, '_eval_code', return_value=(0, 'trait-value', '')):
            properties = [{'prefix': 'TRAIT1', 'language': 'python', 'code': '...'}]

            result = self.evaluator._eval_attributes(properties)

            self.assertEqual(result['sync_attributes']['TRAIT1'], 'trait-value')
            self.assertEqual(result['name'], 'test-comp')
            self.assertEqual(result['fqdn'], 'test.host')

    def test_eval_faults_with_output(self):
        """Test evaluating faults that return output (active faults)"""
        with patch.object(ConcreteEvaluator, '_eval_code', return_value=(0, 'System in error', '')):
            fault_definitions = [{'name': 'DISK_FULL', 'language': 'bash', 'code': '...'}]

            result = self.evaluator._eval_faults(fault_definitions)

            self.assertIn('DISK_FULL', result['faults'])
            self.assertEqual(result['faults']['DISK_FULL'], 'System in error')
            self.evaluator.operation_failed.assert_called()

    def test_eval_faults_no_output(self):
        """Test evaluating faults with no output (healthy state)"""
        with patch.object(ConcreteEvaluator, '_eval_code', return_value=(0, '', '')):
            fault_definitions = [{'name': 'DISK_FULL', 'language': 'bash', 'code': '...'}]

            result = self.evaluator._eval_faults(fault_definitions)

            self.assertEqual(result['faults'], {})
            self.evaluator.operation_ok.assert_called()


if __name__ == '__main__':
    unittest.main()
