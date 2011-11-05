# -*- coding: UTF-8 -*-

# Copyright (c) 2011 Jose Antonio Chavarría
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
__file__   = 'printcolor.py'
__date__   = '2011-09-24'

# http://stackoverflow.com/questions/287871/print-in-terminal-with-colors-using-python

HEADER    = '\033[95m'
OK_BLUE   = '\033[94m'
OK_GREEN  = '\033[92m'
WARNING   = '\033[93m'
FAIL      = '\033[91m'
INFO      = '\033[32m'
END_COLOR = '\033[0m'

def header(text):
    print HEADER + str(text) + END_COLOR

def warning(text):
    print WARNING + str(text) + END_COLOR

def info(text):
    print INFO + str(text) + END_COLOR

def fail(text):
    print FAIL + str(text) + END_COLOR

def ok(text):
    print OK_GREEN + str(text) + END_COLOR

def ok_blue(text):
    print OK_BLUE + str(text) + END_COLOR
