# -*- coding: UTF-8 -*-

# Copyright (c) 2025 Jose Antonio Chavarría <jachavar@gmail.com>
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

__author__ = 'Jose Antonio Chavarría'
__license__ = 'GPLv3'
__all__ = ('MigasFreeInfo', 'main')

import os
import sys
import optparse
import logging
import json
import errno
import gettext

from . import utils, curl
from .command import MigasFreeCommand

_ = gettext.gettext


class MigasFreeInfo(MigasFreeCommand):
    CMD = 'migasfree-info'  # /usr/bin/migasfree-info

    def __init__(self):
        self._user_is_not_root()
        MigasFreeCommand.__init__(self)

    def _usage_examples(self):
        print('\n' + _('Examples:'))

        print('  ' + _('Get computer search info') + ':')
        print('\t%s -s' % self.CMD)
        print('\t%s --search\n' % self.CMD)

        print('  ' + _('Get computer ID') + ':')
        print('\t%s -i' % self.CMD)
        print('\t%s --id\n' % self.CMD)

        print('  ' + _('Get computer UUID') + ':')
        print('\t%s -u ' % self.CMD)
        print('\t%s --uuid\n' % self.CMD)

        print('  ' + _('Get computer name') + ':')
        print('\t%s -n' % self.CMD)
        print('\t%s --name\n' % self.CMD)

    def _show_running_options(self):
        MigasFreeCommand._show_running_options(self)

    def _get_computer_info(self):
        _url = '{0}/{1}/?uuid={2}'.format(
            self.migas_server,
            self.get_computer_info_command,
            utils.get_hardware_uuid()
        )
        _url = '{0}://{1}'.format('https' if self.migas_ssl_cert else 'http', _url)

        _curl = curl.Curl(
            _url,
            proxy=self.migas_proxy,
            cert=self.migas_ssl_cert,
        )
        _curl.run()

        _response = str(_curl.body)

        logging.debug('HTTP Code _get_computer_info: %d', _curl.http_code)
        logging.debug('Response _get_computer_info: %s', _response)

        return json.loads(_response) if _curl.http_code == 200 else {}

    def run(self):
        _program = 'migasfree info'
        parser = optparse.OptionParser(
            description=_program,
            prog=self.CMD,
            version=self.release,
            usage='%prog [option]'
        )

        parser.add_option(
            '--search', '-s',
            action='store_true',
            help=_('Get computer search info')
        )

        parser.add_option(
            '--id', '-i',
            action='store_true',
            help=_('Get computer ID')
        )

        parser.add_option(
            '--uuid', '-u',
            action='store_true',
            help=_('Get computer UUID')
        )

        parser.add_option(
            '--name', '-n',
            action='store_true',
            help=_('Get computer name')
        )

        options, arguments = parser.parse_args()
        logging.info('Program options: %s' % options)
        logging.info('Program arguments: %s' % arguments)

        # check restrictions
        if options.search and options.id:
            self._usage_examples()
            parser.error(_('Search and ID options are exclusive!!!'))
        if options.search and options.uuid:
            self._usage_examples()
            parser.error(_('Search and UUID options are exclusive!!!'))
        if options.search and options.name:
            self._usage_examples()
            parser.error(_('Search and Name options are exclusive!!!'))
        if options.id and options.uuid:
            self._usage_examples()
            parser.error(_('ID and UUID options are exclusive!!!'))
        if options.id and options.name:
            self._usage_examples()
            parser.error(_('ID and Name options are exclusive!!!'))
        if options.uuid and options.name:
            self._usage_examples()
            parser.error(_('UUID and Name options are exclusive!!!'))

        computer_info = self._get_computer_info()

        # actions dispatcher
        if options.search:
            print(computer_info.get('search', ''))
        elif options.id:
            print(computer_info.get('id', ''))
        elif options.uuid:
            print(computer_info.get('uuid', ''))
        elif options.name:
            print(computer_info.get('name', ''))
        else:
            print({
                'id': computer_info.get('id', ''),
                'uuid': computer_info.get('uuid', ''),
                'name': computer_info.get('name', ''),
                'search': computer_info.get('search', '')
            })

        sys.exit(os.EX_OK if computer_info else errno.ENOENT)


def main():
    mfi = MigasFreeInfo()
    mfi.run()


if __name__ == '__main__':
    main()
