# Copyright (c) 2016-2025 Jose Antonio Chavarría <jachavar@gmail.com>
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

import argparse
import gettext
import sys

from .utils import ALL_OK, get_mfc_release

__author__ = 'Jose Antonio Chavarría <jachavar@gmail.com>'
__license__ = 'GPLv3'

_ = gettext.gettext

PROGRAM = 'migasfree'


def parse_args(argv):
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description=_('Systems Management System (client side)'),
    )

    parser.add_argument('-d', '--debug', action='store_true', help=_('Enable debug mode'))

    parser.add_argument('-q', '--quiet', action='store_true', help=_('Enable silent mode (no verbose)'))

    subparsers = parser.add_subparsers(dest='cmd')

    subparser_register = subparsers.add_parser('register', help=_('Register computer at server'))
    subparser_register.add_argument('-u', '--user', action='store', help=_('User to register computer at server'))

    subparser_search = subparsers.add_parser('search', help=_('Search package in repositories'))
    subparser_search.add_argument('pattern', nargs=1, action='store', metavar='STRING', help=_('Pattern to search'))

    subparser_sync = subparsers.add_parser('sync', help=_('Synchronize computer with server'))
    subparser_sync.add_argument('-f', '--force-upgrade', action='store_true', help=_('Force package upgrades'))

    group_sync = subparser_sync.add_mutually_exclusive_group(required=False)
    group_sync.add_argument(
        '-dev', '--devices', action='store_true', help=_('Synchronize computer devices with server')
    )
    group_sync.add_argument(
        '-hard', '--hardware', action='store_true', help=_('Synchronize computer hardware with server')
    )
    group_sync.add_argument('-soft', '--software', action='store_true', help=_('Upload computer software to server'))
    group_sync.add_argument(
        '-att', '--attributes', action='store_true', help=_('Upload attributes information to server')
    )
    group_sync.add_argument('-fau', '--faults', action='store_true', help=_('Upload faults information to server'))

    subparser_install = subparsers.add_parser('install', help=_('Install package'))
    subparser_install.add_argument(
        'pkg_install', nargs='+', action='store', metavar='PACKAGE', help=_('Package to install')
    )

    subparser_purge = subparsers.add_parser('purge', help=_('Purge package'))
    subparser_purge.add_argument('pkg_purge', nargs='+', action='store', metavar='PACKAGE', help=_('Package to purge'))

    subparser_traits = subparsers.add_parser('traits', help=_('Get computer traits at server'))
    subparser_traits.add_argument(
        'prefix', nargs='?', action='store', metavar='PREFIX', default='', help=_('Prefix to search')
    )
    subparser_traits.add_argument(
        'traits_key',
        nargs='?',
        choices=('id', 'description', 'name', 'value', 'prefix', 'sort'),
        help=_('Get individual value'),
    )

    subparsers.add_parser('label', help=_('Computer identification'))

    subparsers.add_parser('version', help=_('Show version info'))

    subparser_tags = subparsers.add_parser('tags', help=_('Computer tags'))
    group_tags = subparser_tags.add_mutually_exclusive_group(required=True)
    group_tags.add_argument('-g', '--get', action='store_true', help=_('Get tags in server (JSON format)'))
    group_tags.add_argument('-s', '--set', nargs='*', metavar='TAG', help=_('Set tags in server'))
    group_tags.add_argument('-c', '--communicate', nargs='*', metavar='TAG', help=_('Communicate tags to server'))

    subparser_upload = subparsers.add_parser('upload', help=_('Upload files to server'))
    subparser_upload.add_argument('-u', '--user', action='store', help=_('Authorized user to upload at server'))
    subparser_upload.add_argument('-p', '--pwd', action='store', help=_('User password'))
    subparser_upload.add_argument('-j', '--project', action='store', help=_('Project to upload files'))
    subparser_upload.add_argument('-s', '--store', action='store', help=_('Store at server'))

    group_upload = subparser_upload.add_mutually_exclusive_group(required=True)
    group_upload.add_argument('-f', '--file', action='store', help=_('File to upload at server'))
    group_upload.add_argument('-r', '--dir', action='store', help=_('Directory with files to upload at server'))

    subparser_info = subparsers.add_parser('info', help=_('Retrieve computer info at server'))

    subparser_info.add_argument(
        'key', nargs='?', choices=('id', 'uuid', 'name', 'search'), help=_('Get individual value')
    )

    subparser_remove_keys = subparsers.add_parser('remove-keys', help=_('Remove client keys'))

    subparser_remove_keys.add_argument(
        '-a', '--all', action='store_true', help=_('Remove client keys from all servers')
    )

    if len(argv) < 1:
        parser.print_help()
        sys.exit(ALL_OK)

    return parser.parse_args()


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    args = parse_args(argv)

    if hasattr(args, 'quiet') and not args.quiet:
        print(_('%(program)s version: %(version)s') % {'program': PROGRAM, 'version': get_mfc_release()})
        sys.stdout.flush()

    if args.cmd in ['register', 'sync', 'install', 'purge', 'search', 'traits']:
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
    elif args.cmd == 'version':
        from .command import MigasFreeCommand

        MigasFreeCommand().cmd_version(args)
    elif args.cmd == 'remove-keys':
        from .command import MigasFreeCommand

        MigasFreeCommand().cmd_remove_keys(args)

    return ALL_OK


if __name__ == '__main__':
    sys.exit(main() or ALL_OK)
