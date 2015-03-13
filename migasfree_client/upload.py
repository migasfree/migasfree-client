#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Copyright (c) 2011-2015 Jose Antonio Chavarría
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
#
# Author: Jose Antonio Chavarría <jachavar@gmail.com>

__author__ = 'Jose Antonio Chavarría'
__license__ = 'GPLv3'
__all__ = ('MigasFreeUpload', 'main')

import os
import sys
import argparse
import getpass
import errno
import magic

import gettext
_ = gettext.gettext

import logging
logger = logging.getLogger(__name__)

from . import (
    settings,
    utils,
    url_request
)

from .command import (
    MigasFreeCommand,
    __version__,
)


class MigasFreeUpload(MigasFreeCommand):
    CMD = 'migasfree-upload'  # /usr/bin/migasfree-upload

    PACKAGER_PRIVATE_KEY = 'migasfree-packager.pri'

    _file = None
    _is_regular_file = False
    _directory = None
    _server_directory = None
    _create_repo = True

    def _usage_examples(self):
        print('\n' + _('Examples:'))

        print('  ' + _('Upload single package:'))
        print('\t%s -f archive.pkg' % self.CMD)
        print('\t%s --file=archive.pkg\n' % self.CMD)

        print('  ' + _('Upload single package but not create repository:'))
        print('\t%s -f archive.pkg -c ' % self.CMD)
        print('\t%s --file=archive.pkg --no-create-repo\n' % self.CMD)

        print('  ' + _('Upload package set:'))
        print('\t%s -r local_directory' % self.CMD)
        print('\t%s --dir=local_directory\n' % self.CMD)

        print('  ' + _('Upload regular files:'))
        print('\t%s -r local_directory -c' % self.CMD)
        print('\t%s --dir=local_directory --no-create-repo\n' % self.CMD)

    def _show_running_options(self):
        MigasFreeCommand._show_running_options(self)

        print('\t%s: %s' % (_('Project'), self.packager_project))
        print('\t%s: %s' % (_('Store'), self.packager_store))
        print('\t%s: %s' % (_('User'), self.packager_user))
        # print('\t%s: %s' % (_('Password'), self.packager_pwd))
        if self._file:
            print('\t%s: %s' % (_('File'), self._file))
        if self._directory:
            print('\t%s: %s' % (_('Directory'), self._directory))
            print('\t%s: %s' % (_('Server directory'), self._server_directory))
        print('\t%s: %s' % (_('Create repository'), self._create_repo))
        print('')

    def _left_parameters(self):
        if not self.packager_user:
            self.packager_user = raw_input(
                '%s: ' % _('User to upload at server')
            )
            if not self.packager_user:
                print(_('Empty user. Exiting %s.') % self.CMD)
                logger.info('Empty user in upload operation')
                sys.exit(errno.EAGAIN)

        if not self.packager_pwd:
            self.packager_pwd = getpass.getpass('%s: ' % _('User password'))

        if not self.packager_project:
            self.packager_project = raw_input(
                '%s: ' % _('Project to upload at server')
            )
            if not self.packager_project:
                print(_('Empty project. Exiting %s.') % self.CMD)
                logger.info('Empty project in upload operation')
                sys.exit(errno.EAGAIN)

        if not self.packager_store:
            self.packager_store = raw_input(
                '%s: ' % _('Store to upload at server')
            )
            if not self.packager_store:
                print(_('Empty store. Exiting %s.') % self.CMD)
                logger.info('Empty store in upload operation')
                sys.exit(errno.EAGAIN)

    def _upload_file(self):
        logger.debug('Upload file operation...')
        if not os.path.isfile(self._file):
            print(_('File not found'))
            logger.error('File not found %s', self._file)
            sys.exit(errno.ENOENT)

        self._check_sign_keys()

        logger.debug('Uploading file: %s', self._file)

        mime = magic.from_buffer(utils.read_file(self._file), mime=True)
        is_package = mime in self.pms._mimetype
        response = self._url_request.run(
            url=self._url_base + 'safe/packages/',
            data={
                'project': self.packager_project,
                'store': self.packager_store,
                'is_package': is_package
            },
            upload_files=[os.path.abspath(self._file)],
            debug=self._debug,
            keys={
                'private': self.PACKAGER_PRIVATE_KEY,
                'public': self.PUBLIC_KEY
            }
        )

        logger.debug('Uploading response: %s', response)
        if self._debug:
            print('Response: %s' % response)

        if 'error' in response:
            self.operation_failed(response['error']['info'])
            sys.exit(errno.EINPROGRESS)

        return self._create_repository() if is_package else True

    def _upload_set(self):
        logger.debug('Upload set operation...')
        if not os.path.isdir(self._directory):
            print(_('Directory not found'))
            logger.error('Directory not found %s', self._directory)
            sys.exit(errno.ENOENT)

        self._check_sign_keys()

        for _root, _subfolders, _files in os.walk(self._directory):
            for _file in _files:
                _filename = os.path.join(_root, _file)

                if os.path.isfile(_filename):
                    logger.debug('Uploading server set: %s', _filename)
                    print('Uploading file: %s' % os.path.abspath(_filename))

                    response = self._url_request.run(
                        url=self._url_base + 'safe/packages/set/',
                        data={
                            'project': self.packager_project,
                            'store': self.packager_store,
                            'packageset': self._server_directory,
                            'path': os.path.dirname(
                                os.path.join(
                                    _root,
                                    _file
                                )[len(self._directory) + 1:]
                            )
                        },
                        upload_files=[os.path.abspath(_filename)],
                        keys={
                            'private': self.PACKAGER_PRIVATE_KEY,
                            'public': self.PUBLIC_KEY
                        },
                        debug=self._debug,
                    )

                    logger.debug('Uploading set response: %s', response)
                    if self._debug:
                        print('Response: %s' % response)

                    if 'error' in response:
                        self.operation_failed(response['error']['info'])
                        logger.error(
                            'Uploading set error: %s', response['error']['info']
                        )
                        sys.exit(errno.EINPROGRESS)

        return self._create_repository()

    def _create_repository(self):
        if not self._create_repo:
            return True

        print(_('Creating repository operation...'))

        if self._file:
            packageset = self._file
        else:
            packageset = self._server_directory

        response = self._url_request.run(
            url=self._url_base + 'safe/packages/repos/',
            data={
                'project': self.packager_project,
                'packageset': packageset
            },
            keys={
                'private': self.PACKAGER_PRIVATE_KEY,
                'public': self.PUBLIC_KEY
            },
            debug=self._debug
        )

        logger.debug('Creating repository response: %s', response)
        if self._debug:
            print('Response: %s' % response)

        if 'error' in response:
            self.operation_failed(response['error']['info'])
            logger.error(
                'Creating repository error: %s', response['error']['info']
            )
            sys.exit(errno.EINPROGRESS)

        return True

    def _parse_args(self):
        program = 'migasfree upload'
        print(_('%(program)s version: %(version)s') % {
            'program': program,
            'version': __version__
        })

        parser = argparse.ArgumentParser(
            prog=self.CMD,
            description=program,
            usage=self._usage_examples()
        )

        parser.add_argument(
            '-d', '--debug',
            action='store_true',
            help=_('Enable debug mode')
        )

        parser.add_argument(
            '-u', '--user',
            action='store',
            help=_('Authorized user to upload at server')
        )

        parser.add_argument(
            '-p', '--pwd',
            action='store',
            help=_('User password')
        )

        parser.add_argument(
            '-j', '--project',
            action='store',
            help=_('Project to upload files')
        )

        parser.add_argument(
            '-s', '--store',
            action='store',
            help=_('Store at server')
        )

        parser.add_argument(
            '-c', '--no-create-repo',
            action='store_true',
            help=_('No create repository after upload file(s) at server')
        )

        group = parser.add_mutually_exclusive_group(required=True)

        group.add_argument(
            '-f', '--file',
            action='store',
            help=_('File to upload at server')
        )

        group.add_argument(
            '-r', '--dir',
            action='store',
            help=_('Directory with files to upload at server')
        )

        return parser.parse_args()

    def run(self):
        args = self._parse_args()

        if args.debug:
            self._debug = True
            logger.setLevel(logging.DEBUG)

        # assign config options
        if args.user:
            self.packager_user = args.user
        if args.pwd:
            self.packager_pwd = args.pwd
        if args.project:
            self.packager_project = args.project
        if args.store:
            self.packager_store = args.store
        if args.no_create_repo:
            self._create_repo = not args.no_create_repo

        # actions dispatcher
        if args.file:
            self._file = args.file
        elif args.dir:
            self._directory = args.dir.split('/')[-1]
        else:
            self._usage_examples()

        self._left_parameters()
        self.auto_register_user = self.packager_user
        self.auto_register_password = self.packager_pwd
        self.auto_register_end_point = 'public/keys/packager/'

        self._show_running_options()

        utils.check_lock_file(self.CMD, self.LOCK_FILE)
        if self._file:
            self._upload_file()
        else:
            self._upload_set()
        utils.remove_file(self.LOCK_FILE)

        sys.exit(os.EX_OK)  # no error


def main():
    mfu = MigasFreeUpload()
    mfu.run()

if __name__ == "__main__":
    main()
