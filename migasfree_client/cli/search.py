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

from .. import utils
from ..command import MigasFreeCommand

__author__ = 'Jose Antonio Chavarría <jachavar@gmail.com>'
__license__ = 'GPLv3'
__all__ = ['MigasFreeSearch']

_ = gettext.gettext
logger = logging.getLogger('migasfree_client')


class MigasFreeSearch(MigasFreeCommand):
    CMD = 'migasfree search'

    def __init__(self):
        super().__init__()
        self.pms_selection()

    def run(self, args=None):
        super().run(args, init_command=False, show_config=False)

        if not self.pms:
            msg = _('No Package Management System (PMS) found on this system.')
            if self._quiet:
                self.console.print(json.dumps({'error': msg}), soft_wrap=True)
            else:
                self.console.print(msg, style='red')
            sys.exit(utils.ALL_OK)

        self._show_message(_('Searching: %s ...') % ' '.join(args.pattern))
        self.pms.search(' '.join(args.pattern))

        sys.exit(utils.ALL_OK)
