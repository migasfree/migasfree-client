# -*- coding: UTF-8 -*-

# Copyright (c) 2011-2015 Jose Antonio Chavarría
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
__license__ = 'GPLv3'


class Pms(object):
    '''
    PMS: Package Management System
    Interface class
    Abstract methods
    '''

    # http://stackoverflow.com/questions/3786762/dynamic-base-class-and-factories
    _entity_ = None
    _entities_ = {}

    @classmethod
    def factory(cls, entity):
        return cls._entities_[entity]

    @classmethod
    def register(cls, entity):
        def decorator(subclass):
            cls._entities_[entity] = subclass
            subclass._entity_ = entity
            return subclass
        return decorator

    def __init__(self):
        self._name = ''      # Package Management System name
        self._pm = ''        # Package Manager command
        self._pms = ''       # Package Management System command
        self._repo = ''      # Repositories file
        self._cmd = ''       # Command to execute
        self._mimetype = []  # Allowed mimetypes for packages

    def __str__(self):
        '''
        string __str__(void)
        '''

        return self._name

    def install(self, package):
        '''
        bool install(string package)
        '''

        raise NotImplementedError

    def remove(self, package):
        '''
        bool remove(string package)
        '''

        raise NotImplementedError

    def search(self, pattern):
        '''
        bool search(string pattern)
        '''

        raise NotImplementedError

    def update_silent(self):
        '''
        (bool, string) update_silent(void)
        '''

        raise NotImplementedError

    def install_silent(self, package_set):
        '''
        (bool, string) install_silent(list package_set)
        '''

        raise NotImplementedError

    def remove_silent(self, package_set):
        '''
        (bool, string) remove_silent(list package_set)
        '''

        raise NotImplementedError

    def is_installed(self, package):
        '''
        bool is_installed(string package)
        '''

        raise NotImplementedError

    def clean_all(self):
        '''
        bool clean_all(void)
        '''

        raise NotImplementedError

    def query_all(self):
        '''
        ordered list query_all(void)
        list format: name_version_architecture.extension
        '''

        raise NotImplementedError

    def create_repos(self, server, project, repositories):
        '''
        bool create_repos(string server, string project, list repositories)
        '''

        raise NotImplementedError
