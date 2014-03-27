# -*- coding: UTF-8 -*-

# Copyright (c) 2014 Jose Antonio Chavarría
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
#
# Author: Jose Antonio Chavarría <jachavar@gmail.com>

__author__ = 'Jose Antonio Chavarría'
__license__ = 'GPLv3'

from migasfree_client.utils import execute


class Printer(object):
    @staticmethod
    def install(device):
        '''
        (bool, string/int) install(dict device)

        {
            'id': 135,
            'name': '1000',
            'model': 'IRC-5000',
            'driver': '/usr/share/ppd/IRC-5000.ppd',
            'feature': 'DEFAULT',
            'packages': ['azl-printers'],
            'TCP': {
                'IP': '192.168.100.254',
                'PORT': 9100,
                'LOCATION': 'Entry',
            }
        }
        '''
        _name = '%s__%s__%d' % (
            device['name'],
            device['model'],
            int(device['id'])
        )
        _connect = ''
        _location = ''

        if 'TCP' in device:
            _conn = device['TCP']
            if 'IP' in _conn and 'PORT' in _conn and 'LOCATION' in _conn:
                _connect = '-v socket://%s:%d' % (
                    _conn['IP'],
                    int(_conn['PORT'])
                )
                if _conn['LOCATION'] != '':
                    _location = '-L "%s"' % _conn['LOCATION']
        elif 'LPT' in device:
            _connect = '-v parallel:/dev/lp0'

        # depends cups-client
        _cmd = 'lpadmin -p %(name)s -P %(driver)s %(conn)s %(location)s -E' % {
            'name': _name,
            'driver': device['driver'],
            'conn': _connect,
            'location': _location
        }
        _ret, _output, _error = execute(_cmd)
        if _ret != 0:
            return (False, _error)

        return (True, int(device['id']))


    @staticmethod
    def remove(device_name):
        '''
        (bool, string) remove(string device_name)
        '''
        _cmd = 'lpadmin -x %s' % device_name
        _ret, _output, _error = execute(_cmd)
        if _ret != 0:
            return (False, _error)

        return (True, _output)


    @staticmethod
    def is_installed(device_name):
        '''
        bool is_installed(string device_name)
        '''
        _cmd = 'lpstat -a | grep %s' % device_name
        _ret, _, _ = execute(_cmd, interactive=False)

        return _ret == 0


    @staticmethod
    def search(pattern):
        '''
        string search(string pattern)
        '''
        # depends cups-client
        _cmd = 'lpstat -a | cut -d " " -f 1 | grep %s' % pattern
        _ret, _output, _error = execute(_cmd, interactive=False)
        if _ret != 0:
            return ''

        return _output
