#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Copyright (c) 2011-2013 Jose Antonio Chavarría
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
__file__ = 'upload.py'
__date__ = '2013-01-26'
__version__ = '2.0'
__license__ = 'GPLv3'
__all__ = ('MigasFreeUpload', 'main')

import os
import sys
import optparse
import logging
import getpass
import errno

import gettext
_ = gettext.gettext

# package imports
"""
from . import (
    settings,
    utils,
    server_errors,
    url_request
)
"""
import settings
import utils
import server_errors
import url_request


class MigasFreeUpload(object):
    CMD = 'migasfree-upload'  # /usr/bin/migasfree-upload
    LOCK_FILE = '/tmp/%s.pid' % CMD

    PUBLIC_KEY = 'migasfree-server.pub'
    PRIVATE_KEY = 'migasfree-packager.pri'

    migas_server = 'migasfree.org'
    migas_proxy = None

    packager_user = None
    packager_pwd = None
    packager_version = None
    packager_store = None

    _url_request = None

    _file = None
    _is_regular_file = False
    _directory = None
    _server_directory = None
    _create_repo = True

    _debug = False

    def __init__(self):
        #signal.signal(signal.SIGINT, self._exit_gracefully)
        #signal.signal(signal.SIGQUIT, self._exit_gracefully)
        #signal.signal(signal.SIGTERM, self._exit_gracefully)

        _config_client = utils.get_config(settings.CONF_FILE, 'client')

        _log_level = logging.INFO
        if type(_config_client) is dict:
            if 'server' in _config_client:
                self.migas_server = _config_client['server']
            if 'proxy' in _config_client:
                self.migas_proxy = _config_client['proxy']
            if 'debug' in _config_client:
                if _config_client['debug'] == 'True' \
                or _config_client['debug'] == '1' \
                or _config_client['debug'] == 'On':
                    self._debug = True
                    _log_level = logging.DEBUG

        _config_packager = utils.get_config(settings.CONF_FILE, 'packager')
        if type(_config_packager) is dict:
            if 'user' in _config_packager:
                self.packager_user = _config_packager['user']
            if 'password' in _config_packager:
                self.packager_pwd = _config_packager['password']
            if 'version' in _config_packager:
                self.packager_version = _config_packager['version']
            if 'store' in _config_packager:
                self.packager_store = _config_packager['store']

        logging.basicConfig(
            format='%(asctime)s - %(levelname)s - %(message)s',
            level=_log_level,
            filename=settings.LOG_FILE
        )
        logging.info('*' * 76)
        logging.info('%s in execution', self.CMD)
        logging.debug('Config client: %s', _config_client)
        logging.debug('Config packager: %s', _config_packager)

        _url_base = 'http://%s/migasfree/api/' % str(self.migas_server)

        # init UrlRequest
        self._url_request = url_request.UrlRequest(
            debug=self._debug,
            url_base=_url_base,
            proxy=self.migas_proxy,
            info_keys={
                'path': settings.KEYS_PATH,
                'private': self.PRIVATE_KEY,
                'public': self.PUBLIC_KEY
            }
        )

    def _usage_examples(self):
        print('\n' + _('Examples:'))

        print('  ' + _('Upload single package:'))
        print('\t%s -f archive.pkg' % self.CMD)
        print('\t%s --file=archive.pkg\n' % self.CMD)

        print('  ' + _('Upload single package but not create repository:'))
        print('\t%s -f archive.pkg -c ' % self.CMD)
        print('\t%s --file=archive.pkg --no-create-repo\n' % self.CMD)

        print('  ' + _('Upload a regular file:'))
        print('\t%s -f archive -r' % self.CMD)
        print('\t%s --file=archive --regular-file\n' % self.CMD)

        print('  ' + _('Upload package set:'))
        print('\t%s -d local_directory -n server_directory' % self.CMD)
        print('\t%s --dir=local_directory --name=server_directory\n' % self.CMD)

        print('  ' + _('Upload regular files:'))
        print('\t%s -d local_directory -n server_directory -c' % self.CMD)
        print('\t%s --dir=local_directory --name=server_directory --no-create-repo\n' % self.CMD)

    def _show_config_options(self):
        print
        print _('Config options:')
        print '\t%s: %s' % (_('Server'), self.migas_server)
        print '\t%s: %s' % (_('Proxy'), self.migas_proxy)
        print '\t%s: %s' % (_('Debug'), self._debug)
        print '\t%s: %s' % (_('Version'), self.packager_version)
        print '\t%s: %s' % (_('Store'), self.packager_store)
        print '\t%s: %s' % (_('User'), self.packager_user)
        #print '\t%s: %s' % (_('Password'), self.packager_pwd)
        if self._file:
            print '\t%s: %s' % (_('File'), self._file)
            print '\t%s: %s' % (_('Regular file'), self._is_regular_file)
        if self._directory:
            print '\t%s: %s' % (_('Directory'), self._directory)
            print '\t%s: %s' % (_('Server directory'), self._server_directory)
        print '\t%s: %s' % (_('Create repository'), self._create_repo)
        print

    def _left_parameters(self):
        if not self.packager_user:
            self.packager_user = raw_input('%s: ' % _('User to upload at server'))
            if not self.packager_user:
                print _('Empty user. Exiting %s.') % self.CMD
                logging.info('Empty user in upload operation')
                sys.exit(errno.EAGAIN)

        if not self.packager_pwd:
            self.packager_pwd = getpass.getpass('%s: ' % _('User password'))

        if not self.packager_version:
            self.packager_version = raw_input('%s: ' % _('Version to upload at server'))
            if not self.packager_version:
                print _('Empty version. Exiting %s.') % self.CMD
                logging.info('Empty version in upload operation')
                sys.exit(errno.EAGAIN)

        if not self.packager_store:
            self.packager_store = raw_input('%s: ' % _('Store to upload at server'))
            if not self.packager_store:
                print _('Empty store. Exiting %s.') % self.CMD
                logging.info('Empty store in upload operation')
                sys.exit(errno.EAGAIN)

    def _check_sign_keys(self):
        _private_key = os.path.join(settings.KEYS_PATH, self.PRIVATE_KEY)
        _public_key = os.path.join(settings.KEYS_PATH, self.PUBLIC_KEY)
        if os.path.isfile(_private_key) and os.path.isfile(_public_key):
            return  # all OK

        logging.warning('Packager keys are not present!!!')
        self._auto_register()

    def _auto_register(self):
        # try to get keys
        _data = {
            'username': self.packager_user,
            'password': self.packager_pwd
        }
        print(_('Getting packager keys...'))

        return self._save_sign_keys(_data)

    def _save_sign_keys(self, data):
        if not os.path.isdir(os.path.abspath(settings.KEYS_PATH)):
            try:
                os.makedirs(os.path.abspath(settings.KEYS_PATH))
            except:
                logging.error('Error creating %s directory', settings.KEYS_PATH)
                sys.exit(errno.ENOTDIR)

        _response = self._url_request.run('get_key_packager', data, sign=False)
        logging.debug('Response _save_sign_keys: %s', _response)

        for _file, _content in list(_response.items()):
            _path_file = os.path.join(settings.KEYS_PATH, _file)
            logging.debug('Trying writing file: %s', _path_file)
            _ret = utils.write_file(_path_file, str(_content))
            if _ret:
                print(_('Key %s created!') % _path_file)
            else:
                _msg = _('Error writing key file!!!')
                print(_msg)
                logging.error(_msg)
                sys.exit(errno.ENOENT)

        return True

    def _upload_file(self):
        logging.debug('Upload file operation...')
        if not os.path.isfile(self._file):
            print(_('File not found'))
            logging.error('File not found %s', self._file)
            sys.exit(errno.ENOENT)

        self._check_sign_keys()

        logging.debug('Uploading file: %s', self._file)
        _ret = self._url_request.run(
            'upload_server_package',
            data={
                'version': self.packager_version,
                'store': self.packager_store,
                'source': self._is_regular_file
            },
            upload_file=os.path.abspath(self._file)
        )

        logging.debug('Uploading response: %s', _ret)
        if self._debug:
            print('Response: %s' % _ret)

        if _ret['errmfs']['code'] != server_errors.ALL_OK:
            _error_info = server_errors.error_info(_ret['errmfs']['code'])
            print(_error_info)
            logging.error('Uploading file error: %s', _error_info)
            sys.exit(errno.EINPROGRESS)

        return self._create_repository()

    def _upload_set(self):
        logging.debug('Upload set operation...')
        if not os.path.isdir(self._directory):
            print(_('Directory not found'))
            logging.error('Directory not found %s', self._directory)
            sys.exit(errno.ENOENT)

        self._check_sign_keys()

        for _root, _subfolders, _files in os.walk(self._directory):
            for _file in _files:
                _filename = os.path.join(_root, _file)

                if os.path.isfile(_filename):
                    logging.debug('Uploading server set: %s', _filename)
                    if self._debug:
                        print('Uploading file: %s' % os.path.abspath(_filename))

                    _ret = self._url_request.run(
                        'upload_server_set',
                        data={
                            'version': self.packager_version,
                            'store': self.packager_store,
                            'packageset': self._server_directory,
                            'path': os.path.dirname(
                                os.path.join(
                                    _root,
                                    _file
                                )[len(self._directory) + 1:]
                            )
                        },
                        upload_file=os.path.abspath(_filename)
                    )

                    logging.debug('Uploading set response: %s', _ret)
                    if self._debug:
                        print('Response: %s' % _ret)

                    if _ret['errmfs']['code'] != server_errors.ALL_OK:
                        _error_info = server_errors.error_info(
                            _ret['errmfs']['code']
                        )
                        print(_error_info)
                        logging.error('Uploading set error: %s', _error_info)
                        sys.exit(errno.EINPROGRESS)

        return self._create_repository()

    def _create_repository(self):
        if not self._create_repo:
            return True

        logging.debug('Creating repository operation...')

        if self._file:
            _packageset = self._file
        else:
            _packageset = self._server_directory

        _ret = self._url_request.run(
            'create_repositories_of_packageset',
            data={
                'version': self.packager_version,
                'packageset': _packageset
            }
        )

        logging.debug('Creating repository response: %s', _ret)
        if self._debug:
            print('Response: %s' % _ret)

        if _ret['errmfs']['code'] != server_errors.ALL_OK:
            _error_info = server_errors.error_info(_ret['errmfs']['code'])
            print(_error_info)
            logging.error('Creating repository error: %s', _error_info)
            sys.exit(errno.EINPROGRESS)

        return True

    def run(self):
        _program = 'migasfree upload'
        parser = optparse.OptionParser(
            description=_program,
            prog=self.CMD,
            version=__version__,
            usage='%prog options'
        )

        print(_('%(program)s version: %(version)s') % {
            'program': _program,
            'version': __version__
        })

        # migasfree-upload {-f file [--regular-file] | -d dir [-n name]} [[-u user] [-p pwd] [--main-version version] [-s store] [--no-create-repo]]

        parser.add_option("--file", "-f", action="store",
            help=_('File to upload at server'))
        parser.add_option("--regular-file", "-r", action="store_true",
            help=_('File is not a software package'))

        parser.add_option("--dir", "-d", action="store",
            help=_('Directory with files to upload at server'))
        parser.add_option("--name", "-n", action="store",
            help=_('Name of the directory at server'))

        parser.add_option("--user", "-u", action="store",
            help=_('Authorized user to upload at server'))
        parser.add_option("--pwd", "-p", action="store",
            help=_('User password'))
        parser.add_option("--main-version", "-m", action="store",
            help=_('Version to upload files'))
        parser.add_option("--store", "-s", action="store",
            help=_('Main version repository at server'))
        parser.add_option("--no-create-repo", "-c", action="store_true",
            help=_('No create repository after upload file at server'))

        options, arguments = parser.parse_args()

        # check restrictions
        if not options.file and not options.dir:
            self._usage_examples()
            parser.error(_('File or Dir options are mandatory!!!'))
        if options.file and options.dir:
            self._usage_examples()
            parser.error(_('File and Dir options are exclusive!!!'))
        if options.regular_file and options.dir:
            self._usage_examples()
            parser.error(_('This option does not apply with Dir option!!!'))
        if options.name and options.file:
            self._usage_examples()
            parser.error(_('This option does not apply with File option!!!'))

        utils.check_lock_file(self.CMD, self.LOCK_FILE)

        # assign config options
        if options.user:
            self.packager_user = options.user
        if options.pwd:
            self.packager_pwd = options.pwd
        if options.main_version:
            self.packager_version = options.main_version
        if options.store:
            self.packager_store = options.store

        if options.no_create_repo:
            self._create_repo = not options.no_create_repo

        # actions dispatcher
        if options.file:
            self._file = options.file
            self._is_regular_file = options.regular_file
            if self._is_regular_file:
                self._create_repo = False
        elif options.dir:
            self._directory = options.dir
            if options.name:
                self._server_directory = options.name
            else:
                self._server_directory = options.dir
        else:
            parser.print_help()
            self._usage_examples()

        self._left_parameters()
        self._show_config_options()

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
