# -*- coding: UTF-8 -*-

# Copyright (c) 2011-2021 Jose Antonio Chavarría <jachavar@gmail.com>
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

import sys
import inspect
import importlib
import pkgutil

from .pms import Pms
from .apt import Apt
from .yum import Yum
from .zypper import Zypper
from . import plugins


def iter_namespace(ns_pkg):
    return pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + '.')


def get_discovered_plugins():
    return {
        name: importlib.import_module(name)
        for finder, name, ispkg
        in iter_namespace(plugins)
    }


def get_available_pms():
    ret = [
        ('apt', 'Apt'),
        ('yum', 'Yum'),
        ('zypper', 'Zypper'),
    ]

    discovered_plugins = get_discovered_plugins()

    for item in discovered_plugins.keys():
        for class_ in inspect.getmembers(sys.modules[item], inspect.isclass):
            if class_[0] != 'Pms':
                ret.append((class_[1]()._name, class_[0]))

    return sorted(ret, key=lambda x: x[0])
