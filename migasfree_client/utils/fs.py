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

import hashlib
import importlib
import inspect
import logging
import os
import pkgutil
import sys

import magic

from .data import compare_lists

logger = logging.getLogger('migasfree_client')


def read_file(filename, mode='rb'):
    with open(filename, mode) as _file:
        ret = _file.read()

    return ret


def write_file(filename, content):
    """
    bool write_file(string filename, string content)
    """
    _dir = os.path.dirname(filename)
    if not os.path.exists(_dir):
        try:
            os.makedirs(_dir, 0o0777)
        except OSError:
            return False

    try:
        with open(filename, 'wb') as _file:
            try:
                _file.write(content.encode('utf-8'))
            except AttributeError:
                _file.write(content)

            _file.flush()
            os.fsync(_file.fileno())

        return True
    except OSError:
        return False


def write_file_if_changed(filename, content):
    """
    bool write_file_if_changed(string filename, string content)
    Writes file only if content is different from existing file content.
    Returns True if written or not changed, False if error.
    """
    if os.path.exists(filename):
        try:
            current_content = read_file(filename)
            # handle encoding like write_file does
            try:
                c_content = content.encode('utf-8')
            except AttributeError:
                c_content = content

            if current_content == c_content:
                return True
        except OSError:
            pass

    return write_file(filename, content)


def remove_file(archive):
    if os.path.isfile(archive):
        os.remove(archive)


def compare_files(a, b):
    """
    list compare_files(a, b)
    returns ordered diff list
    """
    if not os.path.isfile(a) or not os.path.isfile(b):
        return None

    with open(a, encoding='utf-8') as f:
        _list_a = f.readlines()
    with open(b, encoding='utf-8') as f:
        _list_b = f.readlines()

    return compare_lists(_list_a, _list_b)


def md5sum(archive):
    if not archive:
        return ''

    with open(archive, encoding='utf-8') as handle:
        _md5 = handle.read().encode()

    return hashlib.md5(_md5).hexdigest()


def build_magic():
    # http://www.zak.co.il/tddpirate/2013/03/03/the-python-module-for-file-type-identification-called-magic-is-not-standardized/
    try:
        my_magic = magic.open(magic.MAGIC_MIME_TYPE)
        my_magic.load()
    except AttributeError:
        my_magic = magic.Magic(mime=True)
        my_magic.file = my_magic.from_file

    return my_magic


def iter_namespace(ns_pkg, subfolder=None):
    if not hasattr(ns_pkg, '__path__'):
        return []

    paths = list(ns_pkg.__path__)

    # If frozen (packaged), add the real filesystem folder so custom untracked plugins can be discovered
    if getattr(sys, 'frozen', False) and subfolder:
        real_dir = os.path.join(os.path.dirname(sys.executable), 'migasfree_client', subfolder, 'plugins')
        if os.path.isdir(real_dir) and real_dir not in paths:
            paths.append(real_dir)

    return pkgutil.iter_modules(paths, ns_pkg.__name__ + '.')


def get_discovered_plugins(ns_pkg, subfolder=None):
    ret = {}
    for _finder, name, _ispkg in iter_namespace(ns_pkg, subfolder):
        try:
            module = importlib.import_module(name)
            ret[name] = module
        except ImportError as e:
            logger.error('Error importing %s module: %s', name, e)

    return ret


def get_available_classes(base_class, ns_pkg, subfolder, initial_classes=None):
    ret = list(initial_classes) if initial_classes else []

    discovered_plugins = get_discovered_plugins(ns_pkg, subfolder)
    for _module_name, module in discovered_plugins.items():
        for class_name, class_ in inspect.getmembers(module, inspect.isclass):
            if issubclass(class_, base_class) and class_ != base_class:
                try:
                    ret.append((class_()._name, class_name))
                except Exception as e:
                    logger.error('Error processing %s class: %s', class_name, e)

    return sorted(ret, key=lambda x: x[0])
