# -*- coding: UTF-8 -*-

# Copyright (c) 2018 Jose Antonio Chavarría <jachavar@gmail.com>
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

__author__ = 'Jose Antonio Chavarría <jachavar@gmail.com>'
__license__ = 'GPLv3'
__all__ = 'MigasFreeInfo'

import os
import sys
import errno

import gettext
_ = gettext.gettext

import logging
logger = logging.getLogger(__name__)

from . import settings, utils

from .command import MigasFreeCommand


class MigasFreeInfo(MigasFreeCommand):
    def __init__(self):
        self._user_is_not_root()
        MigasFreeCommand.__init__(self)

    def get_label(self):
        if not self._computer_id:
            self.get_computer_id()

        logger.debug('Getting label')
        response = self._url_request.run(
            url=self.api_endpoint(self.URLS['get_label']),
            data={
                'id': self._computer_id
            },
            debug=self._debug
        )

        logger.debug('Response get_label: {}'.format(response))
        if self._debug:
            print('Response: {}'.format(response))

        if 'error' in response:
            self.operation_failed(response['error']['info'])
            sys.exit(errno.ENODATA)

        return response

    def _show_info(self, key=None):
        self._check_sign_keys()

        info = self.get_label()

        if not key:
            if not self._quiet:
                print('ID\tNAME\tSEARCH\tUUID')
            print(
                '{}\t{}\t{}\t{}'.format(
                    self._computer_id,
                    info['name'],
                    info['search'],
                    info['uuid']
                )
            )
        elif key == 'id':
            if not self._quiet:
                print('ID')
            print(self._computer_id)
        else:
            if not self._quiet:
                print(key.upper())
            print(info[key])

    def run(self, args=None):
        if hasattr(args, 'debug') and args.debug:
            self._debug = True
            logger.setLevel(logging.DEBUG)

        if hasattr(args, 'quiet') and args.quiet:
            self._quiet = True
        else:
            self._show_running_options()

        self._show_info(key=args.key)
        self.end_of_transmission()

        sys.exit(os.EX_OK)
