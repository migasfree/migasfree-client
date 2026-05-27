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
    subparser_register.add_argument('-p', '--password', action='store', help=_('User password'))
    subparser_register.add_argument('-y', '--assume-yes', action='store_true', help=_('Automatic yes to prompts'))

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

    subparser_label = subparsers.add_parser('label', help=_('Computer identification'))
    subparser_label.add_argument('-j', '--json', action='store_true', help=_('JSON format'))

    subparser_attributes = subparsers.add_parser('attributes', help=_('Assigned attributes to computer'))
    subparser_attributes.add_argument('-j', '--json', action='store_true', help=_('JSON format'))
    subparser_attributes.add_argument('-c', '--cid', action='store_true', help=_('Get only the CID attribute'))

    subparsers.add_parser('version', help=_('Show version info'))

    subparser_tags = subparsers.add_parser('tags', help=_('Computer tags'))
    group_tags = subparser_tags.add_mutually_exclusive_group(required=True)
    group_tags.add_argument('-g', '--get', action='store_true', help=_('Get tags in server (JSON format)'))
    group_tags.add_argument('-s', '--set', nargs='*', metavar='TAG', help=_('Set tags in server'))
    group_tags.add_argument('-c', '--communicate', nargs='*', metavar='TAG', help=_('Communicate tags to server'))

    subparser_upload = subparsers.add_parser('upload', help=_('Upload files to server'))
    subparser_upload.add_argument('-u', '--user', action='store', help=_('Authorized user to upload at server'))
    subparser_upload.add_argument('-p', '--password', action='store', help=_('User password'))
    subparser_upload.add_argument('-j', '--project', action='store', help=_('Project to upload files'))
    subparser_upload.add_argument('-s', '--store', action='store', help=_('Store at server'))

    group_upload = subparser_upload.add_mutually_exclusive_group(required=True)
    group_upload.add_argument('-f', '--file', action='store', help=_('File to upload at server'))
    group_upload.add_argument('-r', '--dir', action='store', help=_('Directory with files to upload at server'))

    subparser_info = subparsers.add_parser('info', help=_('Retrieve computer info at server'))

    subparser_info.add_argument(
        'key',
        nargs='?',
        choices=(
            'id',
            'uuid',
            'name',
            'search',
            'status',
            'sync_end_date',
            'fqdn',
            'mac_address',
            'ip_address',
            'cpu',
            'architecture',
            'ram',
            'storage',
            'disks',
            'product',
            'product_system',
        ),
        help=_('Get individual value'),
    )
    subparser_info.add_argument('-j', '--json', action='store_true', help=_('Output as JSON'))

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
    subparser_conf.add_argument('-j', '--json', action='store_true', help=_('Return current configuration as JSON'))

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
    subparser_user_check.add_argument('-p', '--password', action='store', required=True, help=_('Password to verify'))

    subparser_network = subparsers.add_parser('network', help=_('View network information'))
    subparser_network.add_argument(
        '-j', '--json', action='store_true', help=_('Return current network information as JSON')
    )

    subparser_apps = subparsers.add_parser('apps', help=_('Get available applications from catalog'))
    subparser_apps.add_argument('-c', '--category', action='store', metavar='ID', help=_('Filter by category ID'))
    subparser_apps.add_argument('-j', '--json', action='store_true', help=_('Return applications as JSON'))

    subparser_categories = subparsers.add_parser('categories', help=_('Get software catalog categories'))
    subparser_categories.add_argument('-j', '--json', action='store_true', help=_('Return categories as JSON'))

    subparser_devices = subparsers.add_parser('devices', help=_('Get hardware and logical device information'))
    group_devices = subparser_devices.add_mutually_exclusive_group()
    group_devices.add_argument(
        '-a', '--available', action='store_true', help=_('Get available (unassigned) physical devices')
    )
    group_devices.add_argument('-l', '--logical', action='store_true', help=_('Get logical device relations'))
    group_devices.add_argument('-c', '--capabilities', action='store', metavar='ID', help=_('Get capabilities by ID'))
    group_devices.add_argument('--assign', action='store', metavar='ID', help=_('Assign logical device to computer'))
    group_devices.add_argument(
        '--unassign', action='store', metavar='ID', help=_('Unassign logical device from computer')
    )
    group_devices.add_argument(
        '--set-default', action='store', metavar='ID', help=_('Set default logical device for computer')
    )
    subparser_devices.add_argument(
        '--device-id', action='store', metavar='ID', help=_('Filter logical relations by device ID')
    )
    subparser_devices.add_argument('-j', '--json', action='store_true', help=_('Return data as JSON'))

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

    if args.cmd in ('sync', 'install', 'purge'):
        from .cli.sync import MigasFreeSync

        MigasFreeSync().run(args)
    elif args.cmd == 'register':
        from .cli.register import MigasFreeRegister

        MigasFreeRegister().run(args)
    elif args.cmd == 'search':
        from .cli.search import MigasFreeSearch

        MigasFreeSearch().run(args)
    elif args.cmd == 'traits':
        from .cli.traits import MigasFreeTraits

        MigasFreeTraits().run(args)
    elif args.cmd == 'label':
        from .cli.label import MigasFreeLabel

        MigasFreeLabel().run(args)
    elif args.cmd == 'tags':
        from .cli.tags import MigasFreeTags

        MigasFreeTags().run(args)
    elif args.cmd == 'upload':
        from .cli.upload import MigasFreeUpload

        MigasFreeUpload().run(args)
    elif args.cmd == 'info':
        from .cli.info import MigasFreeInfo

        MigasFreeInfo().run(args)
    elif args.cmd == 'attributes':
        from .cli.attributes import MigasFreeAttributes

        MigasFreeAttributes().run(args)
    elif args.cmd in ('version', 'remove-keys', 'network'):
        from .command import MigasFreeCommand

        cmd = MigasFreeCommand()
        if args.cmd == 'version':
            cmd.cmd_version(args)
        elif args.cmd == 'remove-keys':
            cmd.cmd_remove_keys(args)
        elif args.cmd == 'network':
            cmd.cmd_network(args)
    elif args.cmd == 'import-mtls':
        from .command import MigasFreeCommand

        MigasFreeCommand().cmd_import_mtls(args.cert_file)
    elif args.cmd == 'conf':
        from .cli.conf import MigasFreeConf

        MigasFreeConf().run(args)
    elif args.cmd == 'packages':
        from .cli.packages import MigasFreePackages

        MigasFreePackages().run(args)
    elif args.cmd == 'user-check':
        from .cli.usercheck import MigasFreeUserCheck

        MigasFreeUserCheck().run(args)
    elif args.cmd == 'apps':
        from .cli.apps import MigasFreeApps

        MigasFreeApps().run(args)
    elif args.cmd == 'categories':
        from .cli.apps import MigasFreeCategories

        MigasFreeCategories().run(args)
    elif args.cmd == 'devices':
        from .cli.device import MigasFreeDevices

        MigasFreeDevices().run(args)

    return ALL_OK


if __name__ == '__main__':
    sys.exit(main() or ALL_OK)
