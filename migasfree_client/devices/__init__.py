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

import importlib
import inspect
import logging
import os
import pkgutil
import sys

from . import plugins
from .cupswrapper import Cupswrapper
from .printer import Printer

__author__ = 'Jose Antonio Chavarría'
__license__ = 'GPLv3'
__all__ = ['Cupswrapper', 'Printer']
logger = logging.getLogger('migasfree_client')


def iter_namespace(ns_pkg):
    if not hasattr(ns_pkg, '__path__'):
        return []

    paths = list(ns_pkg.__path__)

    # If frozen (packaged), add the real filesystem folder so custom untracked plugins can be discovered
    if getattr(sys, 'frozen', False):
        real_dir = os.path.join(os.path.dirname(sys.executable), 'migasfree_client', 'devices', 'plugins')
        if os.path.isdir(real_dir) and real_dir not in paths:
            paths.append(real_dir)

    return pkgutil.iter_modules(paths, ns_pkg.__name__ + '.')


def get_discovered_plugins():
    ret = {}
    for _finder, name, _ispkg in iter_namespace(plugins):
        try:
            module = importlib.import_module(name)
            ret[name] = module
        except ImportError as e:
            logger.error('Error importing %s module: %s', name, e)

    return ret


def get_available_devices_classes():
    ret = [
        ('cupswrapper', 'Cupswrapper'),
    ]

    discovered_plugins = get_discovered_plugins()
    for _module_name, module in discovered_plugins.items():
        for class_name, class_ in inspect.getmembers(module, inspect.isclass):
            if issubclass(class_, Printer) and class_ != Printer:
                try:
                    ret.append((class_()._name, class_name))
                except Exception as e:
                    logger.error('Error processing %s class: %s', class_name, e)

    return sorted(ret, key=lambda x: x[0])
