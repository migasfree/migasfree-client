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
Tests for hardware collector mixin.
"""

import unittest
from unittest.mock import MagicMock, patch

from migasfree_client.mixins.hardware import HardwareCollectorMixin


class DummyHardwareCollector(HardwareCollectorMixin):
    def __init__(self):
        self._url_request = MagicMock()
        self._debug = False
        self._computer_id = 123
        self.console = MagicMock()
        self.URLS = {'get_hardware_required': '/hr/', 'upload_hardware': '/uh/'}

    def api_endpoint(self, url):
        return f'http://api{url}'

    def _show_message(self, msg):
        pass

    def _report_error(self, msg):
        pass

    def operation_ok(self):
        pass


class TestHardwareCollectorMixin(unittest.TestCase):
    """Tests for HardwareCollectorMixin class"""

    def setUp(self):
        self.collector = DummyHardwareCollector()

    @patch('migasfree_client.utils.execute', return_value=(0, '{"cpu": "intel"}', ''))
    def test_update_hardware_inventory(self, mock_exe):
        """Test gathered hardware info upload"""
        self.collector._url_request.run.return_value = {}
        self.collector.update_hardware_inventory()
        self.collector._url_request.run.assert_called_once()
        args = self.collector._url_request.run.call_args[1]
        self.assertEqual(args['data']['hardware'], {'cpu': 'intel'})

    def test_hardware_capture_is_required(self):
        """Test checking if hardware capture is required"""
        self.collector._url_request.run.return_value = {'capture': True}
        self.assertTrue(self.collector.hardware_capture_is_required())


if __name__ == '__main__':
    unittest.main()
