# Copyright (c) 2014-2025 Jose Antonio Chavarría <jachavar@gmail.com>
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

from typing import ClassVar

__author__ = 'Jose Antonio Chavarría'
__license__ = 'GPLv3'


class Printer:
    """
    Interface class
    Abstract methods
    """

    server = ''

    conn = ''
    port = ''
    location = ''
    uri = ''
    info = ''
    name = ''
    logical_id = 0
    driver = ''
    printer_name = ''

    platform = None

    # http://stackoverflow.com/questions/3786762/dynamic-base-class-and-factories
    _entity_ = None
    _entities_: ClassVar[dict] = {}

    @classmethod
    def factory(cls, entity):
        return cls._entities_[entity]

    @classmethod
    def register(cls, entity):
        def decorator(subclass):
            cls._entities_[entity] = subclass
            subclass._entity_ = entity
            return subclass

        return decorator

    def __init__(self, server='', device=None):
        self.server = server
        self.printer_data = {}

        if not device:
            return

        self.load_device(device)

    def _is_valid_port(self, port_value):
        """Check if a port value is valid (not empty or 'undefined')."""
        return port_value and port_value != 'undefined'

    def _get_port(self, default='0'):
        """Get port from connection, returning default if invalid."""
        port_value = self.conn.get('PORT', '')
        return port_value if self._is_valid_port(port_value) else default

    def _load_tcp(self, conn_data):
        """Load TCP/IP socket connection."""
        self.conn = conn_data
        self.port = self._get_port(default='9100')
        if all(key in self.conn for key in ('IP', 'PORT', 'LOCATION')):
            self.uri = f'socket://{self.conn["IP"]}:{self.port}'

    def _load_lpt(self, conn_data):
        """Load parallel port (LPT) connection."""
        self.conn = conn_data
        self.port = self._get_port(default='0')
        self.uri = f'parallel:/dev/lp{self.port}'

    def _load_usb(self, conn_data):
        """Load USB connection."""
        self.conn = conn_data
        self.port = self._get_port(default='0')
        self.uri = f'parallel:/dev/usb/lp{self.port}'

    def _load_srl(self, conn_data):
        """Load serial port connection."""
        self.conn = conn_data
        self.port = self._get_port(default='0')
        self.uri = f'serial:/dev/ttyS{self.port}'

    def _load_lpd(self, conn_data):
        """Load LPD (Line Printer Daemon) connection."""
        self.conn = conn_data
        if all(key in self.conn for key in ('IP', 'PORT', 'LOCATION')):
            self.uri = f'lpd://{self.conn["IP"]}/{self.conn["PORT"]}'

    def _load_connection(self, device):
        """Load connection data based on device type."""
        connection_handlers = {
            'TCP': self._load_tcp,
            'LPT': self._load_lpt,
            'USB': self._load_usb,
            'SRL': self._load_srl,
            'LPD': self._load_lpd,
        }
        for conn_type, handler in connection_handlers.items():
            if conn_type in device:
                handler(device[conn_type])
                break

    def _build_device_name(self, device):
        """Build device name from connection NAME or device metadata."""
        conn_name = self.conn.get('NAME', '') if self.conn else ''
        if self._is_valid_port(conn_name):  # Reuse validation logic
            return f'{conn_name}__{device["capability"]}__{device["name"]}'
        return f'{device["manufacturer"]}__{device["model"]}__{device["capability"]}__{device["name"]}'

    def load_device(self, device):
        """Load device configuration from device dictionary."""
        self._load_connection(device)

        if self.conn and self.conn.get('LOCATION'):
            self.location = self.conn['LOCATION']

        self.info = (
            f'{device["manufacturer"]}__{device["model"]}__{device["capability"]}'
            f'__{device["name"]}__{int(device["id"])}'
        )

        self.name = self._build_device_name(device)
        self.logical_id = device['id']
        self.driver = device.get('driver', None)

        return self

    def get_connection(self):
        raise NotImplementedError

    def install(self):
        raise NotImplementedError

    def remove(self):
        raise NotImplementedError

    @staticmethod
    def delete(name):
        raise NotImplementedError

    def is_changed(self):
        return not (
            len(self.printer_data) > 0
            and self.printer_data['printer-info'] == self.info
            and self.printer_data['printer-location'] == self.location
            and self.printer_data['device-uri'] == self.uri
        )

    @staticmethod
    def get_printer_id(name):
        raise NotImplementedError

    def get_printers(self):
        raise NotImplementedError

    def get_default(self):
        raise NotImplementedError

    @staticmethod
    def set_default(name):
        raise NotImplementedError
