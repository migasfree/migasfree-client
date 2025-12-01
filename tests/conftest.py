# -*- coding: utf-8 -*-

"""
Pytest configuration and shared fixtures
"""

import os
import tempfile
import pytest


@pytest.fixture
def tmp_dir():
    """Create a temporary directory for tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_file(tmp_dir):
    """Create a sample file for testing"""
    file_path = os.path.join(tmp_dir, "test_file.txt")
    content = "This is a test file\nWith multiple lines\n"
    with open(file_path, "w") as f:
        f.write(content)
    return file_path


@pytest.fixture
def test_keys_dir():
    """Return path to test keys directory"""
    return os.path.join(os.path.dirname(__file__), "fixtures", "test_keys")


@pytest.fixture
def private_key_path(test_keys_dir):
    """Return path to test private key"""
    return os.path.join(test_keys_dir, "private_key.pem")


@pytest.fixture
def public_key_path(test_keys_dir):
    """Return path to test public key"""
    return os.path.join(test_keys_dir, "public_key.pem")


@pytest.fixture
def mock_network_interfaces():
    """Mock network interface data"""
    return {
        "eth0": {
            17: [{"addr": "00:11:22:33:44:55"}],  # AF_LINK
            2: [{"addr": "192.168.1.100", "netmask": "255.255.255.0"}],  # AF_INET
        },
        "wlan0": {
            17: [{"addr": "aa:bb:cc:dd:ee:ff"}],
            2: [{"addr": "10.0.0.50", "netmask": "255.255.0.0"}],
        },
        "lo": {
            17: [{"addr": "00:00:00:00:00:00"}],
            2: [{"addr": "127.0.0.1", "netmask": "255.0.0.0"}],
        },
    }
