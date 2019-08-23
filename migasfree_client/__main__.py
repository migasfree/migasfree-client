# -*- coding: UTF-8 -*-

# Copyright (c) 2016-2019 Jose Antonio Chavarría <jachavar@gmail.com>
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

import os
import sys
import argparse

import gettext
_ = gettext.gettext

from .utils import get_mfc_release

PROGRAM = 'migasfree'


def parse_args(argv):
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description=_('GNU/Linux Management System (client side)'),
    )

    parser.add_argument(
        '-d', '--debug',
        action='store_true',
        help=_('Enable debug mode')
    )

    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help=_('Enable silent mode (no verbose)')
    )

    subparsers = parser.add_subparsers(dest='cmd')

    subparser_register = subparsers.add_parser(
        'register',
        help=_('Register computer at server')
    )
    subparser_register.add_argument(
        '-u', '--user',
        action='store',
        help=_('User to register computer at server')
    )

    subparser_search = subparsers.add_parser(
        'search',
        help=_('Search package in repositories')
    )
    subparser_search.add_argument(
        'pattern',
        nargs=1,
        action='store',
        metavar='STRING',
        help=_('Pattern to search')
    )

    subparser_sync = subparsers.add_parser(
        'sync',
        help=_('Synchronize computer with server')
    )
    subparser_sync.add_argument(
        '-f', '--force-upgrade',
        action='store_true',
        help=_('Force package upgrades')
    )

    subparser_install = subparsers.add_parser(
        'install',
        help=_('Install package')
    )
    subparser_install.add_argument(
        'pkg_install',
        nargs='+',
        action='store',
        metavar='PACKAGE',
        help=_('Package to install')
    )

    subparser_purge = subparsers.add_parser(
        'purge',
        help=_('Purge package')
    )
    subparser_purge.add_argument(
        'pkg_purge',
        nargs='+',
        action='store',
        metavar='PACKAGE',
        help=_('Package to purge')
    )

    subparsers.add_parser(
        'label',
        help=_('Computer identification')
    )

    subparser_tags = subparsers.add_parser(
        'tags',
        help=_('Computer tags')
    )
    group_tags = subparser_tags.add_mutually_exclusive_group(required=True)
    group_tags.add_argument(
        '-g', '--get',
        action='store_true',
        help=_('Get tags in server (JSON format)')
    )
    group_tags.add_argument(
        '-s', '--set',
        nargs='?',
        action='append',
        default=[],
        metavar='TAG',
        help=_('Set tags in server')
    )
    group_tags.add_argument(
        '-c', '--communicate',
        nargs='?',
        action='append',
        default=[],
        metavar='TAG',
        help=_('Communicate tags to server')
    )

    subparser_upload = subparsers.add_parser(
        'upload',
        help=_('Upload files to server')
    )
    subparser_upload.add_argument(
        '-u', '--user',
        action='store',
        help=_('Authorized user to upload at server')
    )
    subparser_upload.add_argument(
        '-p', '--pwd',
        action='store',
        help=_('User password')
    )
    subparser_upload.add_argument(
        '-j', '--project',
        action='store',
        help=_('Project to upload files')
    )
    subparser_upload.add_argument(
        '-s', '--store',
        action='store',
        help=_('Store at server')
    )

    group_upload = subparser_upload.add_mutually_exclusive_group(required=True)
    group_upload.add_argument(
        '-f', '--file',
        action='store',
        help=_('File to upload at server')
    )
    group_upload.add_argument(
        '-r', '--dir',
        action='store',
        help=_('Directory with files to upload at server')
    )

    subparser_info = subparsers.add_parser(
        'info',
        help=_('Retrieve computer info at server')
    )

    subparser_info.add_argument(
        'key',
        nargs='?',
        choices=('id', 'uuid', 'name', 'search'),
        help=_('Get individual value')
    )

    if len(argv) < 1:
        parser.print_help()
        sys.exit(os.EX_OK)

    return parser.parse_args()


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    args = parse_args(argv)

    if hasattr(args, 'quiet') and not args.quiet:
        print(_('%(program)s version: %(version)s') % {
            'program': PROGRAM,
            'version': get_mfc_release()
        })
        sys.stdout.flush()

    if args.cmd in ['register', 'sync', 'install', 'purge']:
        from .sync import MigasFreeSync
        MigasFreeSync().run(args)
    elif args.cmd == 'label':
        from .label import MigasFreeLabel
        MigasFreeLabel().run(args)
    elif args.cmd == 'tags':
        from .tags import MigasFreeTags
        MigasFreeTags().run(args)
    elif args.cmd == 'upload':
        from .upload import MigasFreeUpload
        MigasFreeUpload().run(args)
    elif args.cmd == 'info':
        from .info import MigasFreeInfo
        MigasFreeInfo().run(args)

    return os.EX_OK


if __name__ == '__main__':
    sys.exit(main() or os.EX_OK)
