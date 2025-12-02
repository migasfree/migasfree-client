# Copyright (c) 2011-2025 Jose Antonio Chavarría <jachavar@gmail.com>
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

import importlib
import inspect
import pkgutil
import sys

from . import plugins
from .apt import Apt
from .dnf import Dnf
from .pacman import Pacman
from .pms import Pms
from .wpt import Wpt
from .yum import Yum
from .zypper import Zypper

__author__ = 'Jose Antonio Chavarría'
__license__ = 'GPLv3'
__all__ = ['Apt', 'Dnf', 'Pacman', 'Pms', 'Wpt', 'Yum', 'Zypper']


def iter_namespace(ns_pkg):
    if not hasattr(ns_pkg, '__path__'):
        return []

    return pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + '.')


def get_discovered_plugins():
    ret = {}
    for _finder, name, _ispkg in iter_namespace(plugins):
        try:
            module = importlib.import_module(name)
            ret[name] = module
        except ImportError as e:
            print(f'Error importing {name} module: {e}', file=sys.stderr)

    return ret


def get_available_pms():
    ret = [
        ('apt', 'Apt'),
        ('dnf', 'Dnf'),
        ('pacman', 'Pacman'),
        ('wpt', 'Wpt'),
        ('yum', 'Yum'),
        ('zypper', 'Zypper'),
    ]

    discovered_plugins = get_discovered_plugins()
    for _module_name, module in discovered_plugins.items():
        for class_name, class_ in inspect.getmembers(module, inspect.isclass):
            if issubclass(class_, Pms) and class_ != Pms:
                try:
                    ret.append((class_()._name, class_name))
                except Exception as e:
                    print(f'Error processing {class_name} class: {e}', file=sys.stderr)

    return sorted(ret, key=lambda x: x[0])
