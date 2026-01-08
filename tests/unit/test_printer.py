"""
Unit tests for migasfree_client.devices.printer module

These tests ensure the Printer.load_device method works correctly
before refactoring to reduce cyclomatic complexity.
"""

import pytest

from migasfree_client.devices.printer import Printer


class TestPrinterInit:
    """Tests for Printer initialization"""

    def test_init_without_device(self):
        """Test Printer initialization without device"""
        printer = Printer(server='test.server.com')
        assert printer.server == 'test.server.com'
        assert printer.printer_data == {}
        assert printer.conn == ''
        assert printer.port == ''
        assert printer.uri == ''

    def test_init_with_device(self):
        """Test Printer initialization with device calls load_device"""
        device = {
            'TCP': {
                'IP': '192.168.1.100',
                'PORT': '9100',
                'LOCATION': 'Office',
                'NAME': 'TestPrinter',
            },
            'manufacturer': 'HP',
            'model': 'LaserJet',
            'capability': 'print',
            'name': 'printer1',
            'id': 42,
        }
        printer = Printer(server='test.server.com', device=device)
        assert printer.server == 'test.server.com'
        assert printer.logical_id == 42


class TestLoadDeviceTCP:
    """Tests for load_device with TCP connection"""

    def test_tcp_with_all_fields(self):
        """Test TCP connection with all fields present"""
        device = {
            'TCP': {
                'IP': '192.168.1.100',
                'PORT': '9100',
                'LOCATION': 'Office A',
                'NAME': 'PrinterA',
            },
            'manufacturer': 'HP',
            'model': 'LaserJet',
            'capability': 'print',
            'name': 'printer1',
            'id': 1,
        }
        printer = Printer()
        printer.load_device(device)

        assert printer.conn == device['TCP']
        assert printer.port == '9100'
        assert printer.uri == 'socket://192.168.1.100:9100'
        assert printer.location == 'Office A'
        assert printer.logical_id == 1

    def test_tcp_with_custom_port(self):
        """Test TCP connection with custom port"""
        device = {
            'TCP': {
                'IP': '10.0.0.50',
                'PORT': '515',
                'LOCATION': 'Reception',
            },
            'manufacturer': 'Canon',
            'model': 'MX920',
            'capability': 'print',
            'name': 'reception_printer',
            'id': 5,
        }
        printer = Printer()
        printer.load_device(device)

        assert printer.port == '515'
        assert printer.uri == 'socket://10.0.0.50:515'

    def test_tcp_with_default_port(self):
        """Test TCP connection defaults to port 9100 when PORT is empty"""
        device = {
            'TCP': {
                'IP': '192.168.1.100',
                'PORT': '',
                'LOCATION': 'Office',
            },
            'manufacturer': 'HP',
            'model': 'LaserJet',
            'capability': 'print',
            'name': 'printer1',
            'id': 1,
        }
        printer = Printer()
        printer.load_device(device)

        assert printer.port == '9100'

    def test_tcp_with_undefined_port(self):
        """Test TCP connection defaults to port 9100 when PORT is 'undefined'"""
        device = {
            'TCP': {
                'IP': '192.168.1.100',
                'PORT': 'undefined',
                'LOCATION': 'Office',
            },
            'manufacturer': 'HP',
            'model': 'LaserJet',
            'capability': 'print',
            'name': 'printer1',
            'id': 1,
        }
        printer = Printer()
        printer.load_device(device)

        assert printer.port == '9100'

    def test_tcp_without_port_key(self):
        """Test TCP connection without PORT key defaults to 9100"""
        device = {
            'TCP': {
                'IP': '192.168.1.100',
                'LOCATION': 'Office',
            },
            'manufacturer': 'HP',
            'model': 'LaserJet',
            'capability': 'print',
            'name': 'printer1',
            'id': 1,
        }
        printer = Printer()
        printer.load_device(device)

        assert printer.port == '9100'


class TestLoadDeviceLPT:
    """Tests for load_device with LPT (parallel) connection"""

    def test_lpt_with_port(self):
        """Test LPT connection with specified port"""
        device = {
            'LPT': {
                'PORT': '1',
                'LOCATION': 'Workshop',
            },
            'manufacturer': 'Epson',
            'model': 'FX-890',
            'capability': 'print',
            'name': 'dot_matrix',
            'id': 10,
        }
        printer = Printer()
        printer.load_device(device)

        assert printer.conn == device['LPT']
        assert printer.port == '1'
        assert printer.uri == 'parallel:/dev/lp1'
        assert printer.location == 'Workshop'

    def test_lpt_with_empty_port(self):
        """Test LPT connection defaults to port 0 when empty"""
        device = {
            'LPT': {
                'PORT': '',
                'LOCATION': 'Workshop',
            },
            'manufacturer': 'Epson',
            'model': 'FX-890',
            'capability': 'print',
            'name': 'dot_matrix',
            'id': 10,
        }
        printer = Printer()
        printer.load_device(device)

        assert printer.port == '0'
        assert printer.uri == 'parallel:/dev/lp0'

    def test_lpt_with_undefined_port(self):
        """Test LPT connection defaults to port 0 when 'undefined'"""
        device = {
            'LPT': {
                'PORT': 'undefined',
                'LOCATION': 'Workshop',
            },
            'manufacturer': 'Epson',
            'model': 'FX-890',
            'capability': 'print',
            'name': 'dot_matrix',
            'id': 10,
        }
        printer = Printer()
        printer.load_device(device)

        assert printer.port == '0'
        assert printer.uri == 'parallel:/dev/lp0'


class TestLoadDeviceUSB:
    """Tests for load_device with USB connection"""

    def test_usb_with_port(self):
        """Test USB connection with specified port"""
        device = {
            'USB': {
                'PORT': '2',
                'LOCATION': 'Desk',
            },
            'manufacturer': 'Brother',
            'model': 'HL-2270',
            'capability': 'print',
            'name': 'usb_printer',
            'id': 20,
        }
        printer = Printer()
        printer.load_device(device)

        assert printer.conn == device['USB']
        assert printer.port == '2'
        assert printer.uri == 'parallel:/dev/usb/lp2'

    def test_usb_with_empty_port(self):
        """Test USB connection defaults to port 0"""
        device = {
            'USB': {
                'PORT': '',
                'LOCATION': 'Desk',
            },
            'manufacturer': 'Brother',
            'model': 'HL-2270',
            'capability': 'print',
            'name': 'usb_printer',
            'id': 20,
        }
        printer = Printer()
        printer.load_device(device)

        assert printer.port == '0'
        assert printer.uri == 'parallel:/dev/usb/lp0'


class TestLoadDeviceSRL:
    """Tests for load_device with Serial connection"""

    def test_srl_with_port(self):
        """Test Serial connection with specified port"""
        device = {
            'SRL': {
                'PORT': '1',
                'LOCATION': 'Lab',
            },
            'manufacturer': 'OKI',
            'model': 'ML320',
            'capability': 'print',
            'name': 'serial_printer',
            'id': 30,
        }
        printer = Printer()
        printer.load_device(device)

        assert printer.conn == device['SRL']
        assert printer.port == '1'
        assert printer.uri == 'serial:/dev/ttyS1'

    def test_srl_with_empty_port(self):
        """Test Serial connection defaults to port 0"""
        device = {
            'SRL': {
                'PORT': '',
                'LOCATION': 'Lab',
            },
            'manufacturer': 'OKI',
            'model': 'ML320',
            'capability': 'print',
            'name': 'serial_printer',
            'id': 30,
        }
        printer = Printer()
        printer.load_device(device)

        assert printer.port == '0'
        assert printer.uri == 'serial:/dev/ttyS0'


class TestLoadDeviceLPD:
    """Tests for load_device with LPD connection"""

    def test_lpd_with_all_fields(self):
        """Test LPD connection with all required fields"""
        device = {
            'LPD': {
                'IP': '192.168.1.200',
                'PORT': 'queue1',
                'LOCATION': 'Print Room',
            },
            'manufacturer': 'Kyocera',
            'model': 'TASKalfa',
            'capability': 'print',
            'name': 'lpd_printer',
            'id': 40,
        }
        printer = Printer()
        printer.load_device(device)

        assert printer.conn == device['LPD']
        assert printer.uri == 'lpd://192.168.1.200/queue1'
        assert printer.location == 'Print Room'

    def test_lpd_missing_ip(self):
        """Test LPD connection without IP does not set URI"""
        device = {
            'LPD': {
                'PORT': 'queue1',
                'LOCATION': 'Print Room',
            },
            'manufacturer': 'Kyocera',
            'model': 'TASKalfa',
            'capability': 'print',
            'name': 'lpd_printer',
            'id': 40,
        }
        printer = Printer()
        printer.load_device(device)

        assert printer.uri == ''


class TestLoadDeviceMetadata:
    """Tests for device metadata extraction in load_device"""

    def test_info_format(self):
        """Test info is formatted correctly"""
        device = {
            'TCP': {
                'IP': '192.168.1.100',
                'PORT': '9100',
                'LOCATION': 'Office',
            },
            'manufacturer': 'HP',
            'model': 'LaserJet Pro',
            'capability': 'print',
            'name': 'main_printer',
            'id': 100,
        }
        printer = Printer()
        printer.load_device(device)

        expected_info = 'HP__LaserJet Pro__print__main_printer__100'
        assert printer.info == expected_info

    def test_name_with_custom_name(self):
        """Test name uses custom NAME from connection"""
        device = {
            'TCP': {
                'IP': '192.168.1.100',
                'PORT': '9100',
                'LOCATION': 'Office',
                'NAME': 'CustomPrinterName',
            },
            'manufacturer': 'HP',
            'model': 'LaserJet',
            'capability': 'print',
            'name': 'device_name',
            'id': 1,
        }
        printer = Printer()
        printer.load_device(device)

        expected_name = 'CustomPrinterName__print__device_name'
        assert printer.name == expected_name

    def test_name_without_custom_name(self):
        """Test name uses manufacturer/model when NAME is missing"""
        device = {
            'TCP': {
                'IP': '192.168.1.100',
                'PORT': '9100',
                'LOCATION': 'Office',
            },
            'manufacturer': 'Canon',
            'model': 'PIXMA',
            'capability': 'scan',
            'name': 'scanner1',
            'id': 2,
        }
        printer = Printer()
        printer.load_device(device)

        expected_name = 'Canon__PIXMA__scan__scanner1'
        assert printer.name == expected_name

    def test_name_with_empty_name(self):
        """Test name uses manufacturer/model when NAME is empty"""
        device = {
            'TCP': {
                'IP': '192.168.1.100',
                'PORT': '9100',
                'LOCATION': 'Office',
                'NAME': '',
            },
            'manufacturer': 'Canon',
            'model': 'PIXMA',
            'capability': 'scan',
            'name': 'scanner1',
            'id': 2,
        }
        printer = Printer()
        printer.load_device(device)

        expected_name = 'Canon__PIXMA__scan__scanner1'
        assert printer.name == expected_name

    def test_name_with_undefined_name(self):
        """Test name uses manufacturer/model when NAME is 'undefined'"""
        device = {
            'TCP': {
                'IP': '192.168.1.100',
                'PORT': '9100',
                'LOCATION': 'Office',
                'NAME': 'undefined',
            },
            'manufacturer': 'Canon',
            'model': 'PIXMA',
            'capability': 'scan',
            'name': 'scanner1',
            'id': 2,
        }
        printer = Printer()
        printer.load_device(device)

        expected_name = 'Canon__PIXMA__scan__scanner1'
        assert printer.name == expected_name

    def test_driver_from_device(self):
        """Test driver is extracted from device"""
        device = {
            'TCP': {
                'IP': '192.168.1.100',
                'PORT': '9100',
                'LOCATION': 'Office',
            },
            'manufacturer': 'HP',
            'model': 'LaserJet',
            'capability': 'print',
            'name': 'printer1',
            'id': 1,
            'driver': 'gutenprint',
        }
        printer = Printer()
        printer.load_device(device)

        assert printer.driver == 'gutenprint'

    def test_driver_missing(self):
        """Test driver is None when missing from device"""
        device = {
            'TCP': {
                'IP': '192.168.1.100',
                'PORT': '9100',
                'LOCATION': 'Office',
            },
            'manufacturer': 'HP',
            'model': 'LaserJet',
            'capability': 'print',
            'name': 'printer1',
            'id': 1,
        }
        printer = Printer()
        printer.load_device(device)

        assert printer.driver is None

    def test_load_device_returns_self(self):
        """Test load_device returns self for chaining"""
        device = {
            'TCP': {
                'IP': '192.168.1.100',
                'PORT': '9100',
                'LOCATION': 'Office',
            },
            'manufacturer': 'HP',
            'model': 'LaserJet',
            'capability': 'print',
            'name': 'printer1',
            'id': 1,
        }
        printer = Printer()
        result = printer.load_device(device)

        assert result is printer

    def test_location_empty_when_not_present(self):
        """Test location is empty when LOCATION not in conn"""
        device = {
            'TCP': {
                'IP': '192.168.1.100',
                'PORT': '9100',
            },
            'manufacturer': 'HP',
            'model': 'LaserJet',
            'capability': 'print',
            'name': 'printer1',
            'id': 1,
        }
        printer = Printer()
        printer.load_device(device)

        assert printer.location == ''


class TestPrinterIsChanged:
    """Tests for Printer.is_changed method"""

    def test_is_changed_when_printer_data_empty(self):
        """Test is_changed returns True when printer_data is empty"""
        printer = Printer()
        printer.printer_data = {}
        assert printer.is_changed() is True

    def test_is_changed_when_all_match(self):
        """Test is_changed returns False when all printer_data matches"""
        printer = Printer()
        printer.info = 'HP__LaserJet__print__printer1__1'
        printer.location = 'Office'
        printer.uri = 'socket://192.168.1.100:9100'
        printer.printer_data = {
            'printer-info': 'HP__LaserJet__print__printer1__1',
            'printer-location': 'Office',
            'device-uri': 'socket://192.168.1.100:9100',
        }
        assert printer.is_changed() is False

    def test_is_changed_when_info_differs(self):
        """Test is_changed returns True when printer-info differs"""
        printer = Printer()
        printer.info = 'HP__LaserJet__print__printer1__1'
        printer.location = 'Office'
        printer.uri = 'socket://192.168.1.100:9100'
        printer.printer_data = {
            'printer-info': 'Canon__PIXMA__print__printer1__1',
            'printer-location': 'Office',
            'device-uri': 'socket://192.168.1.100:9100',
        }
        assert printer.is_changed() is True

    def test_is_changed_when_location_differs(self):
        """Test is_changed returns True when printer-location differs"""
        printer = Printer()
        printer.info = 'HP__LaserJet__print__printer1__1'
        printer.location = 'Office A'
        printer.uri = 'socket://192.168.1.100:9100'
        printer.printer_data = {
            'printer-info': 'HP__LaserJet__print__printer1__1',
            'printer-location': 'Office B',
            'device-uri': 'socket://192.168.1.100:9100',
        }
        assert printer.is_changed() is True

    def test_is_changed_when_uri_differs(self):
        """Test is_changed returns True when device-uri differs"""
        printer = Printer()
        printer.info = 'HP__LaserJet__print__printer1__1'
        printer.location = 'Office'
        printer.uri = 'socket://192.168.1.100:9100'
        printer.printer_data = {
            'printer-info': 'HP__LaserJet__print__printer1__1',
            'printer-location': 'Office',
            'device-uri': 'socket://192.168.1.101:9100',
        }
        assert printer.is_changed() is True


class TestPrinterFactory:
    """Tests for Printer factory pattern"""

    def test_register_and_factory(self):
        """Test registering and retrieving a printer subclass"""

        @Printer.register('test_printer')
        class TestPrinter(Printer):
            pass

        result = Printer.factory('test_printer')
        assert result is TestPrinter

    def test_factory_unknown_entity_raises(self):
        """Test factory raises KeyError for unknown entity"""
        with pytest.raises(KeyError):
            Printer.factory('unknown_printer')
