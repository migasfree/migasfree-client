# Copyright (c) 2017-2026 Jose Antonio Chavarría <jachavar@gmail.com>
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

from unittest import mock

import requests

from migasfree_client import availability


class TestAvailability:
    @mock.patch('migasfree_client.availability.subprocess.run')
    def test_is_service_running_linux_service_command(self, mock_run):
        # Case 1: Service is running via 'service' command
        mock_run.return_value.returncode = 0
        assert availability._is_service_running_linux('test-service') is True
        mock_run.assert_called_with(['service', 'test-service', 'status'], capture_output=True, timeout=5)

    @mock.patch('migasfree_client.availability.subprocess.run')
    def test_is_service_running_linux_systemctl_fallback(self, mock_run):
        # Case 2: 'service' not found, fallback to systemctl
        mock_run.side_effect = [FileNotFoundError, mock.Mock(returncode=0)]
        assert availability._is_service_running_linux('test-service') is True
        assert mock_run.call_count == 2
        mock_run.assert_called_with(
            ['systemctl', 'is-active', '--quiet', 'test-service'], capture_output=True, timeout=5
        )

    @mock.patch('migasfree_client.availability.subprocess.run')
    def test_is_service_running_linux_rc_service_fallback(self, mock_run):
        # Case 3: 'service' and 'systemctl' not found, fallback to rc-service
        mock_run.side_effect = [FileNotFoundError, FileNotFoundError, mock.Mock(returncode=0)]
        assert availability._is_service_running_linux('test-service') is True
        assert mock_run.call_count == 3
        mock_run.assert_called_with(['rc-service', 'test-service', 'status'], capture_output=True, timeout=5)

    @mock.patch('migasfree_client.availability.subprocess.run')
    def test_is_service_running_linux_not_running(self, mock_run):
        # Case 4: Service not running (command returns non-zero)
        mock_run.return_value.returncode = 3
        assert availability._is_service_running_linux('test-service') is False

    @mock.patch('migasfree_client.availability.subprocess.run')
    def test_is_service_running_windows(self, mock_run):
        # Case 5: Windows service running
        mock_run.return_value.stdout = 'STATE              : 4  RUNNING'
        assert availability._is_service_running_windows('test-service') is True
        mock_run.assert_called_with(['sc', 'query', 'test-service'], capture_output=True, timeout=5, text=True)

        # Case 6: Windows service stopped
        mock_run.return_value.stdout = 'STATE              : 1  STOPPED'
        assert availability._is_service_running_windows('test-service') is False

    @mock.patch('migasfree_client.availability._is_service_running')
    def test_check_availability_service_not_running(self, mock_is_running):
        mock_is_running.return_value = False
        url_request = mock.Mock()

        available, retry = availability.check_availability(url_request, 'http://url', 123)

        assert available is True
        assert retry is None
        assert url_request.run.called is False

    @mock.patch('migasfree_client.availability._is_service_running')
    def test_check_availability_server_saturated(self, mock_is_running):
        mock_is_running.return_value = True
        url_request = mock.Mock()
        url_request.run.return_value = {
            'error': {'code': requests.codes.too_many_requests, 'info': 'Retry after 60 seconds'}
        }

        available, retry = availability.check_availability(url_request, 'http://url', 123)

        assert available is False
        assert retry == 60

    @mock.patch('migasfree_client.availability._is_service_running')
    def test_check_availability_connection_error(self, mock_is_running):
        mock_is_running.return_value = True
        url_request = mock.Mock()
        # Simulation of connection error caught in url_request
        url_request.run.return_value = {'error': {'code': 500, 'info': 'Connection refused'}}

        available, retry = availability.check_availability(url_request, 'http://url', 123)

        # Connection errors should enable fallback (continue sync)
        assert available is True
        assert retry is None
