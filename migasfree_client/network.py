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

# based in http://stackoverflow.com/questions/4912523/python-network-cidr-calculations

import os
import socket
import fcntl
import struct

SIOCGIFNETMASK = 0x891b
SIOCGIFADDR = 0x8915

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


def get_iface_mask(iface):
    return struct.unpack('L', fcntl.ioctl(
        s,
        SIOCGIFNETMASK,
        struct.pack('256s', iface)
    )[20:24])[0]


def get_iface_address(iface):
    return struct.unpack('L', fcntl.ioctl(
        s,
        SIOCGIFADDR,
        struct.pack('256s', iface[:15])
    )[20:24])[0]


def get_iface_net(iface):
    net_address = get_iface_address(iface) & get_iface_mask(iface)

    return socket.inet_ntoa(struct.pack('L', net_address))


def get_iface_cidr(iface):
    bin_str = bin(get_iface_mask(iface))[2:]
    cidr = 0
    for c in bin_str:
        if c == '1':
            cidr += 1

    return cidr


def get_gateway(ifname):
    '''
    string get_gateway(string)
    http://thiagodefreitas.com/blog/2010/11/19/ip-netmask-gateway-python-unix/
    '''
    cmd = "ip route list dev %s | awk ' /^default/ {print $3}'" % ifname
    fin, fout = os.popen4(cmd)

    return fout.read()


def get_ifname():
    '''
    string get_ifname(void)
    http://webcache.googleusercontent.com/search?q=cache:jfKrstmk9w0J:pkgbuild.archlinux.org/~heftig/firefox-beta/source/src/mozilla-2.0/build/mobile/devicemanager.py+get_interface_ip%28ifname%29+if+ip.startswith%28%22127.%22%29+and+os.name+!%3D+%22nt%22&cd=4&hl=en&ct=clnk&source=www.google.com
    '''
    _ret = ''
    _interfaces = [
        "eth0", "eth1", "eth2", "eth3", "eth4",
        "eth5", "eth6", "eth7", "eth8", "eth9",
        "wlan0", "wlan1", "wlan2", "wlan3", "wlan4",
        "wifi0",
        "ath0", "ath1", "ath2", "ath3", "ath4",
        "ppp0"
    ]
    for _ifname in _interfaces:
        try:
            if get_iface_address(_ifname):
                _ret = _ifname
            break
        except IOError:
            pass

    return _ret


def get_network_info():
    '''
    dict get_network_info(void)
    '''
    _ifname = get_ifname()
    if not _ifname:
        return {}

    return {
        'ip': socket.inet_ntoa(struct.pack('L', get_iface_address(_ifname))),
        'netmask': socket.inet_ntoa(struct.pack('L', get_iface_mask(_ifname))),
        'net': '%s/%s' % (get_iface_net(_ifname), get_iface_cidr(_ifname))
    }
