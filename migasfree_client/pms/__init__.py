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

import inspect
import logging

from ..utils import get_discovered_plugins
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
logger = logging.getLogger('migasfree_client')


def get_available_pms():
    ret = [
        ('apk', 'Apk'),
        ('apt', 'Apt'),
        ('dnf', 'Dnf'),
        ('pacman', 'Pacman'),
        ('wpt', 'Wpt'),
        ('yum', 'Yum'),
        ('zypper', 'Zypper'),
    ]

    discovered_plugins = get_discovered_plugins(plugins, 'pms')
    for _module_name, module in discovered_plugins.items():
        for class_name, class_ in inspect.getmembers(module, inspect.isclass):
            if issubclass(class_, Pms) and class_ != Pms:
                try:
                    ret.append((class_()._name, class_name))
                except Exception as e:
                    logger.error('Error processing %s class: %s', class_name, e)

    return sorted(ret, key=lambda x: x[0])
