# Copyright (c) 2011-2026 Jose Antonio Chavarría <jachavar@gmail.com>
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

from ..utils import get_available_classes
from . import plugins
from .apk import Apk
from .apt import Apt
from .dnf import Dnf
from .pacman import Pacman
from .pms import Pms
from .wpt import Wpt
from .yum import Yum
from .zypper import Zypper

__author__ = 'Jose Antonio Chavarría'
__license__ = 'GPLv3'
__all__ = ['Apk', 'Apt', 'Dnf', 'Pacman', 'Pms', 'Wpt', 'Yum', 'Zypper']


def get_available_pms():
    return get_available_classes(
        Pms,
        plugins,
        'pms',
        [
            ('apk', 'Apk'),
            ('apt', 'Apt'),
            ('dnf', 'Dnf'),
            ('pacman', 'Pacman'),
            ('wpt', 'Wpt'),
            ('yum', 'Yum'),
            ('zypper', 'Zypper'),
        ],
    )
