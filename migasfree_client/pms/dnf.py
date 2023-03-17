# -*- coding: UTF-8 -*-

# Copyright (c) 2023 Jose Antonio Chavarría <jachavar@gmail.com>
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

from .pms import Pms
from .yum import Yum

__author__ = 'Jose Antonio Chavarría'
__license__ = 'GPLv3'


@Pms.register('Yum')
class Dnf(Yum):
    """
    PMS for dnf based systems (Fedora, Red Hat, ...)
    """

    def __init__(self):
        super().__init__()

        self._name = 'dnf'  # Package Management System name
        self._pms = '/usr/bin/dnf'  # Package Management System command
