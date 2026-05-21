# Copyright (c) 2016-2026 Jose Antonio Chavarría <jachavar@gmail.com>
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

from rich import print as rprint

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

    subparser_conf = subparsers.add_parser('conf', help=_('View or update configuration file'))
    subparser_conf.add_argument(
        '-s', '--server', action='store', metavar='VALUE', help=_('Set Server in configuration file')
    )
    subparser_conf.add_argument(
        '-p', '--project', action='store', metavar='VALUE', help=_('Set Project in configuration file')
    )
    subparser_conf.add_argument(
        '-a', '--auto-update-packages', choices=['true', 'false'], help=_('Set Auto_Update_Packages')
    )
    subparser_conf.add_argument('-m', '--manage-devices', choices=['true', 'false'], help=_('Set Manage_Devices'))
    subparser_conf.add_argument('-u', '--upload-hardware', choices=['true', 'false'], help=_('Set Upload_Hardware'))
    subparser_conf.add_argument('-c', '--computer-name', action='store', metavar='VALUE', help=_('Set Computer_Name'))
    subparser_conf.add_argument('--debug-mode', choices=['true', 'false'], help=_('Set Debug in configuration file'))
    subparser_conf.add_argument(
        '-x', '--proxy', action='store', metavar='VALUE', help=_('Set Proxy in configuration file')
    )
    subparser_conf.add_argument(
        '-k', '--package-proxy-cache', action='store', metavar='VALUE', help=_('Set Package_Proxy_Cache')
    )

    subparser_import_mtls = subparsers.add_parser('import-mtls', help=_('Import mTLS certificate from tar file'))
    subparser_import_mtls.add_argument(
        'cert_file', action='store', metavar='FILE', help=_('Certificate tar file to import')
    )

    subparser_packages = subparsers.add_parser('packages', help=_('Local and remote package information'))
    group_packages = subparser_packages.add_mutually_exclusive_group(required=True)
    group_packages.add_argument(
        '-a', '--available', action='store_true', help=_('Get available packages in repositories')
    )
    group_packages.add_argument(
        '-i', '--installed', action='store_true', help=_('Get all installed packages on the system')
    )
    group_packages.add_argument(
        '-c', '--check', nargs=1, metavar='JSON_ARRAY', help=_('Check which of the given packages are installed')
    )

    subparser_user_check = subparsers.add_parser(
        'user-check', help=_('Verify local credentials and administrative privileges')
    )
    subparser_user_check.add_argument('-u', '--user', action='store', required=True, help=_('Username to verify'))
    subparser_user_check.add_argument('-p', '--pwd', action='store', required=True, help=_('Password to verify'))

    if len(argv) < 1:
        parser.print_help()
        sys.exit(ALL_OK)

    return parser.parse_args()


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    args = parse_args(argv)

    if hasattr(args, 'quiet') and not args.quiet:
        rprint(_('%(program)s version: %(version)s') % {'program': PROGRAM, 'version': get_mfc_release()})
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
    elif args.cmd == 'import-mtls':
        from .command import MigasFreeCommand

        MigasFreeCommand().cmd_import_mtls(args.cert_file)
    elif args.cmd == 'conf':
        from .conf import MigasFreeConf

        MigasFreeConf().run(args)
    elif args.cmd == 'packages':
        from .packages import MigasFreePackages

        MigasFreePackages().run(args)
    elif args.cmd == 'user-check':
        from .usercheck import MigasFreeUserCheck

        MigasFreeUserCheck().run(args)

    return ALL_OK


if __name__ == '__main__':
    sys.exit(main() or ALL_OK)
