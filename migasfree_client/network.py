#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Copyright (c) 2011-2013 Jose Antonio Chavarría
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

import socket
import struct
import netifaces

# http://bytes.com/topic/python/answers/504342-struct-unpack-64-bit-platforms


def get_iface_mask(iface):
    '''
    string get_iface_mask(string)
    returns a dotted-quad string
    '''
    _addresses = netifaces.ifaddresses(iface)
    if netifaces.AF_INET in _addresses:
        return _addresses[netifaces.AF_INET][0]['netmask']

    return ''  # empty string


def get_iface_address(iface):
    '''
    string get_iface_address(string)
    returns a dotted-quad string
    '''
    _addresses = netifaces.ifaddresses(iface)
    if netifaces.AF_INET in _addresses:
        return _addresses[netifaces.AF_INET][0]['addr']

    return ''  # empty string


def get_iface_net(iface):
    '''
    string get_iface_net(string)
    returns a dotted-quad string
    '''
    iface_address = struct.unpack(
        '=L',
        socket.inet_aton(get_iface_address(iface))
    )[0]
    iface_mask = struct.unpack(
        '=L',
        socket.inet_aton(get_iface_mask(iface))
    )[0]

    return socket.inet_ntoa(struct.pack('=L', iface_address & iface_mask))


def get_iface_cidr(iface):
    '''
    int get_iface_cidr(string)
    returns an integer number between 0 and 32
    '''
    bin_str = bin(
        struct.unpack(
            '=L',
            socket.inet_aton(get_iface_mask(iface))
        )[0]
    )[2:]
    cidr = 0
    for c in bin_str:
        if c == '1':
            cidr += 1

    return cidr


def get_gateway():
    '''
    string get_gateway(void)
    reads the default gateway directly from /proc
    from http://stackoverflow.com/questions/2761829/
        python-get-default-gateway-for-a-local-interface-ip-address-in-linux
    '''
    with open('/proc/net/route') as fh:
        for line in fh:
            fields = line.strip().split()
            if fields[1] != '00000000' or not int(fields[3], 16) & 2:
                continue

            return socket.inet_ntoa(struct.pack('<L', int(fields[2], 16)))


def get_ifname():
    '''
    string get_ifname(void)
    '''
    _ret = ''
    _interfaces = netifaces.interfaces()
    if 'lo' in _interfaces:
        _interfaces.remove('lo')  # loopback interface is not interesting
    for _interface in _interfaces:
        if get_iface_address(_interface) != '':
            _ret = _interface
            break

    return _ret


def get_network_info():
    '''
    dict get_network_info(void)
    '''
    _ifname = get_ifname()
    if not _ifname:
        return {}

    return {
        'ip': get_iface_address(_ifname),
        'netmask': get_iface_mask(_ifname),
        'net': '%s/%s' % (get_iface_net(_ifname), get_iface_cidr(_ifname))
    }
