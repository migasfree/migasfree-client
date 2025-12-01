"""
Unit tests for migasfree_client.network module
"""

from unittest.mock import mock_open, patch

from migasfree_client import network


class TestInterfaceInformation:
    """Tests for network interface information functions"""

    @patch('netifaces.ifaddresses')
    def test_get_iface_address(self, mock_ifaddresses):
        """Test getting IP address of interface"""
        mock_ifaddresses.return_value = {2: [{'addr': '192.168.1.100', 'netmask': '255.255.255.0'}]}
        result = network.get_iface_address('eth0')
        assert result == '192.168.1.100'

    @patch('netifaces.ifaddresses')
    def test_get_iface_address_no_ipv4(self, mock_ifaddresses):
        """Test getting IP address when no IPv4 address exists"""
        mock_ifaddresses.return_value = {}
        result = network.get_iface_address('eth0')
        assert result == ''

    @patch('netifaces.ifaddresses')
    def test_get_iface_mask(self, mock_ifaddresses):
        """Test getting netmask of interface"""
        mock_ifaddresses.return_value = {2: [{'addr': '192.168.1.100', 'netmask': '255.255.255.0'}]}
        result = network.get_iface_mask('eth0')
        assert result == '255.255.255.0'

    @patch('netifaces.ifaddresses')
    def test_get_iface_mask_no_ipv4(self, mock_ifaddresses):
        """Test getting netmask when no IPv4 address exists"""
        mock_ifaddresses.return_value = {}
        result = network.get_iface_mask('eth0')
        assert result == ''

    @patch('migasfree_client.network.get_iface_address')
    @patch('migasfree_client.network.get_iface_mask')
    def test_get_iface_net(self, mock_mask, mock_address):
        """Test getting network address of interface"""
        mock_address.return_value = '192.168.1.100'
        mock_mask.return_value = '255.255.255.0'

        result = network.get_iface_net('eth0')
        assert result == '192.168.1.0'

    @patch('migasfree_client.network.get_iface_address')
    @patch('migasfree_client.network.get_iface_mask')
    def test_get_iface_net_different_subnet(self, mock_mask, mock_address):
        """Test getting network address for different subnet"""
        mock_address.return_value = '10.20.30.40'
        mock_mask.return_value = '255.255.0.0'

        result = network.get_iface_net('eth0')
        assert result == '10.20.0.0'

    @patch('migasfree_client.network.get_iface_mask')
    def test_get_iface_cidr_24(self, mock_mask):
        """Test calculating CIDR for /24 network"""
        mock_mask.return_value = '255.255.255.0'
        result = network.get_iface_cidr('eth0')
        assert result == 24

    @patch('migasfree_client.network.get_iface_mask')
    def test_get_iface_cidr_16(self, mock_mask):
        """Test calculating CIDR for /16 network"""
        mock_mask.return_value = '255.255.0.0'
        result = network.get_iface_cidr('eth0')
        assert result == 16

    @patch('migasfree_client.network.get_iface_mask')
    def test_get_iface_cidr_8(self, mock_mask):
        """Test calculating CIDR for /8 network"""
        mock_mask.return_value = '255.0.0.0'
        result = network.get_iface_cidr('eth0')
        assert result == 8


class TestNetworkUtilities:
    """Tests for network utility functions"""

    @patch('netifaces.interfaces')
    def test_get_interfaces(self, mock_interfaces):
        """Test getting list of interfaces without loopback"""
        mock_interfaces.return_value = ['lo', 'eth0', 'wlan0']
        result = network.get_interfaces()
        assert 'lo' not in result
        assert 'eth0' in result
        assert 'wlan0' in result

    @patch('netifaces.interfaces')
    def test_get_interfaces_no_loopback(self, mock_interfaces):
        """Test getting interfaces when no loopback exists"""
        mock_interfaces.return_value = ['eth0', 'wlan0']
        result = network.get_interfaces()
        assert result == ['eth0', 'wlan0']

    @patch('migasfree_client.network.get_interfaces')
    @patch('migasfree_client.network.get_iface_address')
    def test_get_ifname(self, mock_address, mock_interfaces):
        """Test getting first active interface name"""
        mock_interfaces.return_value = ['eth0', 'wlan0']
        mock_address.side_effect = ['192.168.1.100', '']

        result = network.get_ifname()
        assert result == 'eth0'

    @patch('migasfree_client.network.get_interfaces')
    @patch('migasfree_client.network.get_iface_address')
    def test_get_ifname_no_active(self, mock_address, mock_interfaces):
        """Test getting interface name when none are active"""
        mock_interfaces.return_value = ['eth0', 'wlan0']
        mock_address.return_value = ''

        result = network.get_ifname()
        assert result == ''

    @patch('migasfree_client.network.get_ifname')
    @patch('migasfree_client.network.get_iface_address')
    @patch('migasfree_client.network.get_iface_mask')
    @patch('migasfree_client.network.get_iface_net')
    @patch('migasfree_client.network.get_iface_cidr')
    def test_get_network_info(self, mock_cidr, mock_net, mock_mask, mock_address, mock_ifname):
        """Test getting complete network information"""
        mock_ifname.return_value = 'eth0'
        mock_address.return_value = '192.168.1.100'
        mock_mask.return_value = '255.255.255.0'
        mock_net.return_value = '192.168.1.0'
        mock_cidr.return_value = 24

        result = network.get_network_info()
        assert result['ip'] == '192.168.1.100'
        assert result['netmask'] == '255.255.255.0'
        assert result['net'] == '192.168.1.0/24'

    @patch('migasfree_client.network.get_ifname')
    def test_get_network_info_no_interface(self, mock_ifname):
        """Test getting network info when no interface is active"""
        mock_ifname.return_value = ''
        result = network.get_network_info()
        assert result == {}


class TestMACAddress:
    """Tests for MAC address functions"""

    @patch('netifaces.ifaddresses')
    def test_get_mac(self, mock_ifaddresses):
        """Test getting MAC address of interface"""
        mock_ifaddresses.return_value = {17: [{'addr': '00:11:22:33:44:55'}]}
        result = network.get_mac('eth0')
        assert result == '00:11:22:33:44:55'

    @patch('migasfree_client.network.get_interfaces')
    @patch('migasfree_client.network.get_mac')
    def test_get_first_mac(self, mock_get_mac, mock_interfaces):
        """Test getting first MAC address"""
        mock_interfaces.return_value = ['eth0', 'wlan0']
        mock_get_mac.return_value = 'aa:bb:cc:dd:ee:ff'

        result = network.get_first_mac()
        assert result == 'AABBCCDDEEFF'

    @patch('migasfree_client.network.get_interfaces')
    def test_get_first_mac_no_interfaces(self, mock_interfaces):
        """Test getting first MAC when no interfaces exist"""
        mock_interfaces.return_value = []
        result = network.get_first_mac()
        assert result == ''


class TestGateway:
    """Tests for gateway detection"""

    @patch(
        'builtins.open',
        new_callable=mock_open,
        read_data="""Iface\tDestination\tGateway \tFlags\tRefCnt\tUse\tMetric\tMask\t\tMTU\tWindow\tIRTT
eth0\t00000000\tC0A80101\t0003\t0\t0\t0\t00000000\t0\t0\t0
eth0\tC0A80100\t00000000\t0001\t0\t0\t0\tFFFFFF00\t0\t0\t0
""",
    )
    def test_get_gateway(self, mock_file):
        """Test getting default gateway from /proc/net/route"""
        result = network.get_gateway()
        # C0A80101 in hex = 192.168.1.1 in little-endian
        assert result == '1.1.168.192'  # Due to little-endian byte order

    @patch(
        'builtins.open',
        new_callable=mock_open,
        read_data="""Iface\tDestination\tGateway \tFlags\tRefCnt\tUse\tMetric\tMask\t\tMTU\tWindow\tIRTT
eth0\tC0A80100\t00000000\t0001\t0\t0\t0\tFFFFFF00\t0\t0\t0
""",
    )
    def test_get_gateway_no_default_route(self, mock_file):
        """Test getting gateway when no default route exists"""
        result = network.get_gateway()
        assert result is None
