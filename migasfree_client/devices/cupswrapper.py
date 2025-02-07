# -*- coding: utf-8 -*-

# Copyright (c) 2021-2025 Jose Antonio Chavarría <jachavar@gmail.com>
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

from ..utils import write_file, md5sum, sanitize_path
from ..settings import DEVICES_PATH

from .printer import Printer

__author__ = 'Jose Antonio Chavarría'
__license__ = 'GPLv3'


@Printer.register('Cupswrapper')
class Cupswrapper(Printer):
    def __init__(self, server='', device=None):
        super().__init__(server, device)
        self.platform = 'linux'  # sys.platform value

        if 'CUPSWRAPPER' in self.conn and self.conn['CUPSWRAPPER']:
            self.uri = f'{self.conn["CUPSWRAPPER"]}:{self.uri}'

    def get_connection(self):
        try:
            return cups.Connection()
        except RuntimeError:
            raise RuntimeError
        except NameError:
            raise NameError

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
            print(f'CUPS Error: {status} ({description})')
            return False

        conn.acceptJobs(self.name)
        conn.enablePrinter(self.name)

        write_file(self.md5_file(), md5sum(self.driver))

        return True

    def remove(self):
        if self.printer_name:
            try:
                Cupswrapper.delete(self.printer_name)
            except RuntimeError:
                return False

            if os.path.exists(self.md5_file()):
                os.remove(self.md5_file())
            return True

        return False

    @staticmethod
    def delete(name):
        try:
            conn = cups.Connection()
        except (RuntimeError, NameError):
            raise RuntimeError

        try:
            conn.deletePrinter(name)
        except cups.IPPError:
            raise RuntimeError

    def is_changed(self):
        return super().is_changed() or self.is_driver_changed()

    def is_driver_changed(self):
        _md5file = self.md5_file()
        if not os.path.exists(_md5file):
            return True

        with open(_md5file, encoding='utf_8') as handle:
            _md5 = handle.read()

        return md5sum(self.driver) != _md5

    @staticmethod
    def get_printer_id(name):
        try:
            conn = cups.Connection()
        except (RuntimeError, NameError):
            return 0

        printers = conn.getPrinters()
        if name in printers:
            if len(printers[name]['printer-info'].split('__')) == 5:
                return int(printers[name]['printer-info'].split('__')[4])

        return 0

    def get_printers(self):
        try:
            conn = cups.Connection()
        except (RuntimeError, NameError):
            return {}

        try:
            return conn.getPrinters()
        except cups.IPPError:
            raise RuntimeError

    def get_default(self):
        try:
            conn = cups.Connection()
        except (RuntimeError, NameError):
            raise RuntimeError

        return conn.getDefault()

    @staticmethod
    def set_default(name):
        try:
            conn = cups.Connection()
        except (RuntimeError, NameError):
            raise RuntimeError

        try:
            conn.setDefault(name)
        except (RuntimeError, cups.IPPError):
            raise RuntimeError

    def md5_file(self):
        return os.path.join(
            DEVICES_PATH,
            sanitize_path(self.server),
            f'{self.logical_id}.md5'
        )
