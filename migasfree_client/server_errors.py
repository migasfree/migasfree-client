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
__file__ = 'server_errors.py'
__date__ = '2013-01-26'

# TODO common code between server & client

import gettext
_ = gettext.gettext

ALL_OK               = 0
NO_AUTHENTICATED     = 1
CAN_NOT_REGISTER     = 2
METHOD_GET_NOT_ALLOW = 3
COMMAND_NOT_FOUND    = 4
SIGN_NOT_OK          = 5
COMPUTER_NOT_FOUND   = 6
DEVICE_NOT_FOUND     = 7
VERSION_NOT_FOUND    = 8
GENERIC              = 100

ERROR_INFO = {
    ALL_OK              : _("No errors"),
    NO_AUTHENTICATED    : _("User not authenticated"),
    CAN_NOT_REGISTER    : _("User can not register computers"),
    METHOD_GET_NOT_ALLOW: _("Method GET not allowed"),
    COMMAND_NOT_FOUND   : _("Command not found"),
    SIGN_NOT_OK         : _("Signature is not valid"),
    COMPUTER_NOT_FOUND  : _("Computer not found"),
    DEVICE_NOT_FOUND    : _("Device not found"),
    VERSION_NOT_FOUND   : _("Version not found"),
    GENERIC             : _("Generic error")
}


def error_info(number):
    '''
    string error_info(int number)
    '''
    if number in ERROR_INFO:
        return ERROR_INFO[number]

    return ''  # if not found
