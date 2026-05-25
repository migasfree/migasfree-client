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

import gettext
import json
import logging
import sys

from .command import MigasFreeCommand, lock_file_context, require_computer_id, require_sign_keys
from .utils import ALL_OK

__author__ = 'Jose Antonio Chavarría <jachavar@gmail.com>'
__license__ = 'GPLv3'
__all__ = ['MigasFreeApps', 'MigasFreeCategories']

_ = gettext.gettext
logger = logging.getLogger('migasfree_client')


class MigasFreeCategories(MigasFreeCommand):
    def __init__(self):
        super().__init__()

    @require_sign_keys
    def get_categories(self):
        logger.debug('Getting categories')
        response = self._api_call('get_categories', exit_on_error=True)
        return self._handle_response(response, success_msg=False)

    def run(self, args=None):
        super().run(args)

        with lock_file_context(self.CMD, self.LOCK_FILE):
            categories = self.get_categories()

        if getattr(args, 'json', False):
            self.console.print(json.dumps(categories, ensure_ascii=False), soft_wrap=True)
        else:
            self.console.print()
            self.console.print(_('Categories:'))
            for cat in categories:
                self.console.print(f'  {cat.get("id", "")}: {cat.get("name", "")}')

        sys.exit(ALL_OK)


class MigasFreeApps(MigasFreeCommand):
    def __init__(self):
        super().__init__()

    @require_sign_keys
    @require_computer_id
    def get_available_apps(self, category_id=None):
        logger.debug('Getting available apps')
        data = {'cid': self._computer_id}
        if category_id:
            data['category'] = category_id

        response = self._api_call('get_available_apps', data=data)

        return self._handle_response(response, success_msg=False)

    def run(self, args=None):
        super().run(args)

        category_id = getattr(args, 'category', None)

        with lock_file_context(self.CMD, self.LOCK_FILE):
            apps = self.get_available_apps(category_id=category_id)

        if getattr(args, 'json', False):
            self.console.print(json.dumps(apps, ensure_ascii=False), soft_wrap=True)
        else:
            self.console.print()
            self.console.print(_('Applications:'))
            for app in apps:
                self.console.print(f'  {app.get("id", "")}: {app.get("name", "")}')

        sys.exit(ALL_OK)
