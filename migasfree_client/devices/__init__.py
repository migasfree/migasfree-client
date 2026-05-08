# -*- coding: UTF-8 -*-

# Copyright (c) 2014-2026 Jose Antonio Chavarría
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

import inspect
import logging

from ..utils import get_discovered_plugins
from . import plugins
from .cupswrapper import Cupswrapper
from .printer import Printer

__author__ = 'Jose Antonio Chavarría'
__license__ = 'GPLv3'
__all__ = ['Cupswrapper', 'Printer']
logger = logging.getLogger('migasfree_client')


def get_available_devices_classes():
    ret = [
        ('cupswrapper', 'Cupswrapper'),
    ]

    discovered_plugins = get_discovered_plugins(plugins, 'devices')
    for _module_name, module in discovered_plugins.items():
        for class_name, class_ in inspect.getmembers(module, inspect.isclass):
            if issubclass(class_, Printer) and class_ != Printer:
                try:
                    ret.append((class_()._name, class_name))
                except Exception as e:
                    logger.error('Error processing %s class: %s', class_name, e)

    return sorted(ret, key=lambda x: x[0])
