# Copyright (c) 2026 Jose Antonio Chavarría <jachavar@gmail.com>
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

import errno
import gettext
import json
import logging
import os
import sys

from .. import settings, utils
from ..command import MigasFreeCommand, require_computer_id, require_sign_keys

__author__ = 'Jose Antonio Chavarría <jachavar@gmail.com>'
__license__ = 'GPLv3'
__all__ = ['MigasFreeTraits']

_ = gettext.gettext
logger = logging.getLogger('migasfree_client')


class MigasFreeTraits(MigasFreeCommand):
    CMD = 'migasfree traits'

    def run(self, args=None):
        super().run(args)
        self.cmd_traits(args.prefix, args.traits_key)

    @require_computer_id
    def get_traits(self):
        if not self._quiet:
            self._show_message(_('Getting traits...'))

        response = self._api_call('get_traits', {'id': self._computer_id})

        if 'error' in response:
            self.operation_failed(response['error']['info'])
            sys.exit(errno.ENODATA)

        if not self._quiet:
            self.operation_ok()

        return response

    def _traits(self, show=True):
        traits = self.get_traits()
        if show:
            self.console.print(json.dumps(traits, indent=settings.JSON_INDENT, ensure_ascii=False), soft_wrap=True)

        content = {}
        if os.path.isfile(settings.TRAITS_FILE):
            content = json.loads(utils.read_file(settings.TRAITS_FILE))

        before = content.get('after', [])

        content = {'before': before, 'after': traits}

        utils.write_file(settings.TRAITS_FILE, json.dumps(content, indent=settings.JSON_INDENT))

        return traits

    @require_sign_keys
    def cmd_traits(self, prefix, key):
        traits = self._traits(show=False)
        self.end_of_transmission()

        if prefix:
            ret = filter(lambda item: item['prefix'] == prefix, traits)
            if key:
                ret = [item.get(key) for item in ret]

            traits = list(ret)

        self.console.print(json.dumps(traits, indent=settings.JSON_INDENT, ensure_ascii=False), soft_wrap=True)
