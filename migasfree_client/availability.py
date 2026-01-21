# Copyright (c) 202-2026 Jose Antonio Chavarría <jachavar@gmail.com>
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

import logging
import re
import subprocess
import sys

import requests

logger = logging.getLogger('migasfree_client')

# Service name that provides the sync availability endpoint
AGENT_SERVICE_NAME = 'migasfree-agent'


def _extract_int(text):
    match = re.search(r'\d+', str(text))
    return int(match.group()) if match else None


def _is_service_running_linux(service_name):
    """
    Check if a service is running on Linux.

    Tries multiple init system commands in order:
    1. 'service' (works on systemd, sysvinit, upstart)
    2. 'systemctl' (systemd native)
    3. 'rc-service' (OpenRC - Alpine, Gentoo)

    Args:
        service_name: Name of the service to check

    Returns:
        bool: True if the service is running, False otherwise
    """
    # Try 'service' command first (most universal)
    try:
        result = subprocess.run(
            ['service', service_name, 'status'],
            capture_output=True,
            timeout=5,
        )
        # 'service' returns 0 if running, non-zero otherwise
        is_running = result.returncode == 0
        logger.debug('Service %s is %s (via service command)', service_name, 'running' if is_running else 'not running')
        return is_running
    except FileNotFoundError:
        pass  # Try next method
    except subprocess.TimeoutExpired:
        logger.warning('Timeout checking service %s status', service_name)
        return True
    except Exception as e:
        logger.debug('Error with service command: %s', e)

    # Try systemctl (systemd)
    try:
        result = subprocess.run(
            ['systemctl', 'is-active', '--quiet', service_name],
            capture_output=True,
            timeout=5,
        )
        is_running = result.returncode == 0
        logger.debug('Service %s is %s (via systemctl)', service_name, 'running' if is_running else 'not running')
        return is_running
    except FileNotFoundError:
        pass  # Try next method
    except subprocess.TimeoutExpired:
        logger.warning('Timeout checking service %s status via systemctl', service_name)
        return True
    except Exception as e:
        logger.debug('Error with systemctl: %s', e)

    # Try rc-service (OpenRC - Alpine, Gentoo)
    try:
        result = subprocess.run(
            ['rc-service', service_name, 'status'],
            capture_output=True,
            timeout=5,
        )
        # rc-service returns 0 if running
        is_running = result.returncode == 0
        logger.debug('Service %s is %s (via rc-service)', service_name, 'running' if is_running else 'not running')
        return is_running
    except FileNotFoundError:
        logger.debug('No service management command found (service, systemctl, rc-service)')
        return True
    except subprocess.TimeoutExpired:
        logger.warning('Timeout checking service %s status via rc-service', service_name)
        return True
    except Exception as e:
        logger.warning('Error checking service %s: %s', service_name, e)
        return True


def _is_service_running_windows(service_name):
    """
    Check if a Windows service is running.

    Uses 'sc query' command to check service status.

    Args:
        service_name: Name of the Windows service to check

    Returns:
        bool: True if the service is running, False otherwise
    """
    try:
        result = subprocess.run(
            ['sc', 'query', service_name],
            capture_output=True,
            timeout=5,
            text=True,
        )
        # Check if "RUNNING" appears in the output
        is_running = 'RUNNING' in result.stdout
        logger.debug('Service %s is %s (via sc query)', service_name, 'running' if is_running else 'not running')
        return is_running
    except FileNotFoundError:
        logger.debug('sc command not found, assuming service check not applicable')
        return True
    except subprocess.TimeoutExpired:
        logger.warning('Timeout checking Windows service %s status', service_name)
        return True
    except Exception as e:
        logger.warning('Error checking Windows service %s: %s', service_name, e)
        return True


def _is_service_running(service_name):
    """
    Check if a service is running (cross-platform).

    Args:
        service_name: Name of the service to check

    Returns:
        bool: True if the service is active/running, False otherwise.
               Returns True on errors to avoid blocking sync.
    """
    if sys.platform == 'win32':
        return _is_service_running_windows(service_name)
    elif sys.platform == 'linux':
        return _is_service_running_linux(service_name)
    else:
        # On other platforms (macOS, BSD, etc.), skip the check
        logger.debug('Service check not supported on %s, assuming available', sys.platform)
        return True


def check_availability(url_request, url, computer_id):
    """
    Check if the server is available for synchronization.

    This function first checks if the migasfree-agent service is running.
    If the service is not running (e.g., in development environments),
    the function assumes availability and allows sync to continue.

    If the service is running, it queries the sync availability endpoint
    to determine if the server can accept synchronization requests.

    Args:
        url_request: UrlRequest instance for making HTTP requests
        url: The availability endpoint URL
        computer_id: The computer's ID on the server

    Returns:
        tuple: (available (bool), retry_after (int or None))
            - available: True if sync can proceed, False if server is saturated
            - retry_after: Seconds to wait before retrying (if server returned 429)
    """
    if not computer_id:
        return True, None

    # First, check if the migasfree-agent service is running
    if not _is_service_running(AGENT_SERVICE_NAME):
        logger.info(
            'Service %s is not running. Skipping availability check.',
            AGENT_SERVICE_NAME,
        )
        return True, None

    logger.debug('Checking server availability...')
    response = url_request.run(
        url=url,
        data={'computer_id': computer_id},
        safe=True,
        exit_on_error=False,
    )

    if 'error' in response:
        error = response['error']
        error_code = error.get('code')

        # Handle 429 Too Many Requests - server is saturated
        if error_code == requests.codes.too_many_requests:
            info = error.get('info', '')
            try:
                retry_after = _extract_int(info)
            except ValueError:
                retry_after = None

            return False, retry_after

        # Other errors (e.g., connection errors, 500, 404) -> assume available
        logger.debug(
            'Availability check returned error (code: %s): %s. Assuming available.',
            error_code,
            error.get('info', 'unknown error'),
        )
        return True, None

    # response is {'data': ...} or {'content': ...}
    # If 200 OK -> Available
    logger.debug('Server availability check passed.')
    return True, None
