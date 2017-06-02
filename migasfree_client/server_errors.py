# -*- coding: UTF-8 -*-

# Copyright (c) 2011-2017 Jose Antonio Chavarría <jachavar@gmail.com>
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

# TODO common code between server & client

import gettext
_ = gettext.gettext

__author__ = 'Jose Antonio Chavarría'
__license__ = 'GPLv3'

ALL_OK = 0
UNAUTHENTICATED = 1
CAN_NOT_REGISTER_COMPUTER = 2
GET_METHOD_NOT_ALLOWED = 3
COMMAND_NOT_FOUND = 4
INVALID_SIGNATURE = 5
COMPUTER_NOT_FOUND = 6
DEVICE_NOT_FOUND = 7
PROJECT_NOT_FOUND = 8
USER_DOES_NOT_HAVE_PERMISSION = 9
UNSUBSCRIBED_COMPUTER = 10
GENERIC = 100

ERROR_INFO = {
    ALL_OK: _("No errors"),
    UNAUTHENTICATED: _("User unauthenticated"),
    CAN_NOT_REGISTER_COMPUTER: _("User can not register computers"),
    GET_METHOD_NOT_ALLOWED: _("Method GET not allowed"),
    COMMAND_NOT_FOUND: _("Command not found"),
    INVALID_SIGNATURE: _("Signature is not valid"),
    COMPUTER_NOT_FOUND: _("Computer not found"),
    DEVICE_NOT_FOUND: _("Device not found"),
    PROJECT_NOT_FOUND: _("Project not found"),
    USER_DOES_NOT_HAVE_PERMISSION: _("User does not have permission"),
    UNSUBSCRIBED_COMPUTER: _("Unsubscribed computer"),
    GENERIC: _("Generic error")
}


def error_info(number):
    """
    string error_info(int number)
    """
    return ERROR_INFO.get(number, '')
