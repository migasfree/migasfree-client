# -*- coding: utf-8 -*-

# Copyright (c) 2016-2019 Jose Antonio Chavarría <jachavar@gmail.com>
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

import os
try:
    import cups
except ImportError:
    pass

from ..utils import write_file, md5sum
from ..settings import DEVICES_PATH

__author__ = 'Jose Antonio Chavarría'
__license__ = 'GPLv3'


class LogicalDevice(object):
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

    def __init__(self, device):
        if 'TCP' in device:
            self.conn = device['TCP']
            if 'PORT' in self.conn and not (self.conn['PORT'] == 'undefined' or self.conn['PORT'] == ''):
                self.port = self.conn['PORT']
            else:
                self.port = "9100"
            if 'IP' in self.conn and 'PORT' in self.conn and 'LOCATION' in self.conn:
                self.uri = 'socket://{0}:{1}'.format(
                    self.conn['IP'],
                    self.port
                )
                if self.conn['LOCATION'] != '':
                    self.location = self.conn['LOCATION']
        elif 'LPT' in device:
            self.conn = device['LPT']
            if 'PORT' in self.conn and not (self.conn['PORT'] == 'undefined' or self.conn['PORT'] == ''):
                self.port = self.conn['PORT']
            else:
                self.port = "0"
            self.uri = 'parallel:/dev/lp{0}'.format(self.port)
        elif 'USB' in device:
            self.conn = device['USB']
            if 'PORT' in self.conn and not (self.conn['PORT'] == 'undefined' or self.conn['PORT'] == ''):
                self.port = self.conn['PORT']
            else:
                self.port = "0"
            self.uri = 'parallel:/dev/usb/lp{0}'.format(self.port)
        elif 'SRL' in device:
            self.conn = device['SRL']
            if 'PORT' in self.conn and not (self.conn['PORT'] == 'undefined' or self.conn['PORT'] == ''):
                self.port = self.conn['PORT']
            else:
                self.port = "0"
            self.uri = 'serial:/dev/ttyS{0}'.format(self.port)
        elif 'LPD' in device:
            self.conn = device['LPD']
            if 'IP' in self.conn and 'PORT' in self.conn and 'LOCATION' in self.conn:
                self.uri = 'lpd://{0}/{1}'.format(
                    self.conn['IP'],
                    self.conn['PORT']
                )
                if self.conn['LOCATION'] != '':
                    self.location = self.conn['LOCATION']

        if 'CUPSWRAPPER' in self.conn and self.conn['CUPSWRAPPER']:
            self.uri = '{0}:{1}'.format(self.conn['CUPSWRAPPER'], self.uri)

        self.info = u'{0}__{1}__{2}__{3}__{4}'.format(
            device['manufacturer'],
            device['model'],
            device['feature'],
            device['name'],
            int(device['id'])
        )

        if 'NAME' in self.conn and not (self.conn['NAME'] == 'undefined' or self.conn['NAME'] == ''):
            self.name = u'{0}__{1}__{2}'.format(
                self.conn['NAME'],
                device['feature'],
                device['name'],
            )
        else:
            self.name = u'{0}__{1}__{2}__{3}'.format(
                device['manufacturer'],
                device['model'],
                device['feature'],
                device['name'],
            )

        self.logical_id = device['id']
        self.driver = device.get('driver', None)

    def md5_file(self):
        return os.path.join(DEVICES_PATH, '{0}.md5'.format(self.logical_id))

    def install(self):
        self.remove()

        try:
            conn = cups.Connection()
        except (RuntimeError, NameError):
            return False

        try:
            if self.driver:
                conn.addPrinter(
                    name=self.name,
                    filename=self.driver,
                    info=self.info,
                    location=self.location,
                    device=self.uri
                )
            else:
                conn.addPrinter(
                    name=self.name,
                    info=self.info,
                    location=self.location,
                    device=self.uri
                )
        except cups.IPPError as e:
            (status, description) = e.args
            print('CUPS Error: %d (%s)' % (status, description))
            return False

        conn.acceptJobs(self.name)
        conn.enablePrinter(self.name)

        write_file(self.md5_file(), md5sum(self.driver))

        return True

    def remove(self):
        if self.printer_name:
            try:
                conn = cups.Connection()
            except (RuntimeError, NameError):
                return False

            conn.deletePrinter(self.printer_name)
            if os.path.exists(self.md5_file()):
                os.remove(self.md5_file())
            return True

        return False

    def is_changed(self):
        if (
            len(self.printer_data) > 0 and
            self.printer_data['printer-info'] == self.info and
            self.printer_data['printer-location'] == self.location and
            self.printer_data['device-uri'] == self.uri and
            not self.is_driver_changed()
        ):
            return False
        else:
            return True

    def is_driver_changed(self):
        _md5file = self.md5_file()
        if not os.path.exists(_md5file):
            return True

        with open(_md5file) as handle:
            _md5 = handle.read()

        return md5sum(self.driver) != _md5

    @staticmethod
    def get_device_id(name):
        try:
            conn = cups.Connection()
        except (RuntimeError, NameError):
            return 0

        printers = conn.getPrinters()
        if name in printers:
            if len(printers[name]['printer-info'].split('__')) == 5:
                return int(printers[name]['printer-info'].split('__')[4])

        return 0
