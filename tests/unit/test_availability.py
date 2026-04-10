# Copyright (c) 2025-2026 Jose Antonio Chavarría <jachavar@gmail.com>
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
Tests for server availability check functionality.
"""

import unittest
from unittest.mock import MagicMock, patch

from migasfree_client.availability import (
    _extract_int,
    _is_service_running_linux,
    _is_service_running_windows,
    check_availability,
)


class TestAvailability(unittest.TestCase):
    """Tests for availability check"""

    def test_extract_int(self):
        """Test extraction of integers from strings"""
        self.assertEqual(_extract_int('Try again in 300 seconds'), 300)
        self.assertEqual(_extract_int('123'), 123)
        self.assertIsNone(_extract_int('No numbers here'))

    @patch('subprocess.run')
    def test_is_service_running_linux_service(self, mock_run):
        """Test service check on Linux using 'service' command"""
        mock_run.return_value = MagicMock(returncode=0)
        self.assertTrue(_is_service_running_linux('test-service'))
        mock_run.assert_called_with(['service', 'test-service', 'status'], capture_output=True, timeout=5)

    @patch('subprocess.run')
    def test_is_service_running_linux_systemctl(self, mock_run):
        """Test service check on Linux using 'systemctl' when 'service' is missing"""
        mock_run.side_effect = [FileNotFoundError(), MagicMock(returncode=0)]
        self.assertTrue(_is_service_running_linux('test-service'))
        self.assertEqual(mock_run.call_count, 2)

    @patch('subprocess.run')
    def test_is_service_running_windows(self, mock_run):
        """Test service check on Windows using 'sc query'"""
        mock_run.return_value = MagicMock(stdout='STATE : 4 RUNNING')
        self.assertTrue(_is_service_running_windows('test-service'))

        mock_run.return_value = MagicMock(stdout='STATE : 1 STOPPED')
        self.assertFalse(_is_service_running_windows('test-service'))

    @patch('migasfree_client.availability._is_service_running', return_value=True)
    def test_check_availability_available(self, mock_service):
        """Test server availability successful (200 OK)"""
        url_request = MagicMock()
        url_request.run.return_value = {'data': 'available'}

        available, retry = check_availability(url_request, 'http://api/avail', 123)

        self.assertTrue(available)
        self.assertIsNone(retry)

    @patch('migasfree_client.availability._is_service_running', return_value=True)
    def test_check_availability_too_many_requests(self, mock_service):
        """Test server saturated (429 Too Many Requests)"""
        url_request = MagicMock()
        import requests

        url_request.run.return_value = {
            'error': {'code': requests.codes.too_many_requests, 'info': 'Retry after 60 seconds'}
        }

        available, retry = check_availability(url_request, 'http://api/avail', 123)

        self.assertFalse(available)
        self.assertEqual(retry, 60)

    @patch('migasfree_client.availability._is_service_running', return_value=False)
    def test_check_availability_service_not_running(self, mock_service):
        """Test skipping check when agent service is not running locally"""
        url_request = MagicMock()
        available, _retry = check_availability(url_request, 'http://api/avail', 123)

        self.assertTrue(available)
        url_request.run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
