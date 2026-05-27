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

from ..command import MigasFreeCommand, lock_file_context

__author__ = 'Jose Antonio Chavarría <jachavar@gmail.com>'
__license__ = 'GPLv3'
__all__ = ['MigasFreeRegister']


class MigasFreeRegister(MigasFreeCommand):
    CMD = 'migasfree register'

    def run(self, args=None):
        self._check_user_is_root()
        super().run(args)

        with lock_file_context(self.CMD, self.LOCK_FILE):
            self.cmd_register_computer(args.user, getattr(args, 'password', None), getattr(args, 'assume_yes', False))
