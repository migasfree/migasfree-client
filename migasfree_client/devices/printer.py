# -*- coding: utf-8 -*-

# Copyright (c) 2014-2023 Jose Antonio Chavarría <jachavar@gmail.com>
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

__author__ = 'Jose Antonio Chavarría'
__license__ = 'GPLv3'


class Printer:
    """
    Interface class
    Abstract methods
    """

    conn = ''
    port = ''
    location = ''
    uri = ''
    info = ''
    name = ''
    logical_id = 0
    driver = ''
    printer_name = ''
    printer_data = {}

    platform = None

    # http://stackoverflow.com/questions/3786762/dynamic-base-class-and-factories
    _entity_ = None
    _entities_ = {}

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

    def __init__(self, device=None):
        if not device:
            return

        self.load_device(device)

    def load_device(self, device):
        if 'TCP' in device:
            self.conn = device['TCP']
            if 'PORT' in self.conn and not (self.conn['PORT'] == 'undefined' or self.conn['PORT'] == ''):
                self.port = self.conn['PORT']
            else:
                self.port = '9100'
            if 'IP' in self.conn and 'PORT' in self.conn and 'LOCATION' in self.conn:
                self.uri = f'socket://{self.conn["IP"]}:{self.port}'
                if self.conn['LOCATION'] != '':
                    self.location = self.conn['LOCATION']
        elif 'LPT' in device:
            self.conn = device['LPT']
            if 'PORT' in self.conn and not (self.conn['PORT'] == 'undefined' or self.conn['PORT'] == ''):
                self.port = self.conn['PORT']
            else:
                self.port = '0'
            self.uri = f'parallel:/dev/lp{self.port}'
        elif 'USB' in device:
            self.conn = device['USB']
            if 'PORT' in self.conn and not (self.conn['PORT'] == 'undefined' or self.conn['PORT'] == ''):
                self.port = self.conn['PORT']
            else:
                self.port = '0'
            self.uri = f'parallel:/dev/usb/lp{self.port}'
        elif 'SRL' in device:
            self.conn = device['SRL']
            if 'PORT' in self.conn and not (self.conn['PORT'] == 'undefined' or self.conn['PORT'] == ''):
                self.port = self.conn['PORT']
            else:
                self.port = '0'
            self.uri = f'serial:/dev/ttyS{self.port}'
        elif 'LPD' in device:
            self.conn = device['LPD']
            if 'IP' in self.conn and 'PORT' in self.conn and 'LOCATION' in self.conn:
                self.uri = f'lpd://{self.conn["IP"]}/{self.conn["PORT"]}'
                if self.conn['LOCATION'] != '':
                    self.location = self.conn['LOCATION']

        self.info = '{}__{}__{}__{}__{}'.format(
            device['manufacturer'],
            device['model'],
            device['capability'],
            device['name'],
            int(device['id'])
        )

        if 'NAME' in self.conn and not (self.conn['NAME'] == 'undefined' or self.conn['NAME'] == ''):
            self.name = f'{self.conn["NAME"]}__{device["capability"]}__{device["name"]}'
        else:
            self.name = '{}__{}__{}__{}'.format(
                device['manufacturer'],
                device['model'],
                device['capability'],
                device['name'],
            )

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
        if (
            len(self.printer_data) > 0 and
            self.printer_data['printer-info'] == self.info and
            self.printer_data['printer-location'] == self.location and
            self.printer_data['device-uri'] == self.uri
        ):
            return False
        else:
            return True

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
