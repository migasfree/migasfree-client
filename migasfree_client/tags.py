#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Copyright (c) 2013-2015 Jose Antonio Chavarría
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
__all__ = ('MigasFreeTags', 'main')

import os
import sys
import argparse
import errno

import gettext
_ = gettext.gettext

import logging
logger = logging.getLogger(__name__)

from datetime import datetime

from . import (
    settings,
    utils,
    url_request
)

from .client import MigasFreeClient
from .command import (
    MigasFreeCommand,
    __version__,
)


class MigasFreeTags(MigasFreeCommand):
    CMD = 'migasfree-tags'  # /usr/bin/migasfree-tags

    _tags = None

    def __init__(self):
        self._user_is_not_root()
        MigasFreeCommand.__init__(self)

    def _usage_examples(self):
        print('\n' + _('Examples:'))

        print('  ' + _('Get assigned tags in server:'))
        print('\t%s -g' % self.CMD)
        print('\t%s --get\n' % self.CMD)

        print('  ' + _('Communicate tags to server (command line):'))
        print('\t%s -c tag... ' % self.CMD)
        print('\t%s --communicate tag...\n' % self.CMD)

        print('  ' + _('Communicate tags to server (with GUI):'))
        print('\t%s -c' % self.CMD)
        print('\t%s --communicate\n' % self.CMD)

        print('  ' + _('Set tags (command line):'))
        print('\t%s -s tag...' % self.CMD)
        print('\t%s --set tag...\n' % self.CMD)

        print('  ' + _('Set tags (with GUI):'))
        print('\t%s -s' % self.CMD)
        print('\t%s --set\n' % self.CMD)

        print('  ' + _('Unsetting all tags (command line):'))
        print('\t%s -s ""' % self.CMD)
        print('\t%s --set ""\n' % self.CMD)

    def _show_running_options(self):
        MigasFreeCommand._show_running_options(self)
        print('\t%s: %s' % (_('Tag list'), self._tags))

    def _sanitize(self, tag_list):
        if tag_list:
            for item in tag_list[:]:
                item = item.replace('"', '')
                try:
                    prefix, value = item.split('-', 1)
                except:
                    msg = _('Tags must be in "prefix-value" format')
                    self.operation_failed(msg)
                    sys.exit(errno.ENODATA)

            logger.info('Sanitized list: %s' % tag_list)

        return tag_list

    def _select_tags(self, assigned, available):
        selected_tags = []

        # Change tags with gui
        title = _("Change tags")
        text = _("Please, select tags for this computer")
        cmd = "zenity --title='%s' \
            --text='%s' \
            --window-icon=%s \
            --list \
            --width 600 \
            --height 400 \
            --checklist \
            --multiple \
            --print-column=2 \
            --column=' ' \
            --column='TAG' \
            --column='TYPE'" % (
                title,
                text,
                os.path.join(settings.ICON_PATH, self.ICON)
            )
        for key, value in available.items():
            for item in value:
                tag_active = item in assigned
                cmd += " '%s' '%s' '%s'" % (tag_active, item, key)

        logger.debug('Change tags command: %s' % cmd)
        ret, out, err = utils.execute(cmd, interactive=False)
        if ret == 0:
            if type(out) is str and out != "":
                selected_tags = out.replace("\n", "").split("|")
                logger.debug('Selected tags: %s' % selected_tags)
        else:
            # no action chosed -> no change tags
            logger.debug('Return value command: %d' % ret)
            sys.exit(ret)

        return selected_tags

    def _get_assigned_tags(self):
        if not self._computer_id:
            self.get_computer_id()

        logger.debug('Getting assigned tags')
        response = self._url_request.run(
            url=self._url_base + 'safe/computers/tags/assigned/',
            data={
                'id': self._computer_id
            },
            debug=self._debug
        )

        logger.debug('Response _get_assigned_tags: %s', response)
        if self._debug:
            print('Response: %s' % response)

        if 'error' in response:
            self.operation_failed(response['error']['info'])
            sys.exit(errno.ENODATA)

        if not response:
            self.operation_failed(_('There are not assigned tags'))
            sys.exit(errno.ENODATA)

        return response

    def _get_available_tags(self):
        if not self._computer_id:
            self.get_computer_id()

        logger.debug('Getting avaiable tags')
        response = self._url_request.run(
            url=self._url_base + 'safe/computers/tags/available/',
            data={
                'id': self._computer_id
            },
            exit_on_error=False,
            debug=self._debug
        )

        logger.debug('Response _get_available_tags: %s', response)

        if 'error' in response:
            self.operation_failed(response['error']['info'])
            sys.exit(errno.ENODATA)

        if self._debug:
            print('Response: %s' % response)

        return response

    def _set_tags(self):
        self._check_sign_keys()

        if not self._tags:
            self._tags = self._select_tags(
                assigned=self._get_assigned_tags(),
                available=self._get_available_tags(),
            )

        # unsettings all tags?
        if len(self._tags) == 1 and self._tags[0] == '':
            logger.debug('Unsetting all tags')
            self._tags = []

        logger.debug('Setting tags: %s', self._tags)
        response = self._url_request.run(
            url=self._url_base + 'safe/computers/tags/',
            data={
                'id': self._computer_id,
                'tags': self._tags
            },
            exit_on_error=False,
            debug=self._debug
        )

        if 'error' in response:
            self.operation_failed(response['error']['info'])
            sys.exit(errno.ENODATA)

        logger.debug('Setting tags response: %s', response)
        if self._debug:
            print('Response: %s' % response)

        print('')
        self.operation_ok(_('Tags setted: %s') % self._tags)

        return response

    def _apply_rules(self, rules):
        mfc = MigasFreeClient()

        # Update metadata
        mfc.synchronize()

        start_date = datetime.now().isoformat()

        mfc._uninstall_packages(rules["remove"])
        mfc._install_mandatory_packages(rules["preinstall"])

        # Update metadata
        mfc._clean_pms_cache()

        mfc._install_mandatory_packages(rules["install"])

    def _parse_args(self):
        program = 'migasfree tags'
        print(_('%(program)s version: %(version)s') % {
            'program': self.CMD,
            'version': __version__
        })

        parser = argparse.ArgumentParser(
            prog=self.CMD,
            description=program
        )

        parser.add_argument(
            '-d', '--debug',
            action='store_true',
            help=_('Enable debug mode')
        )

        group = parser.add_mutually_exclusive_group(required=True)

        group.add_argument(
            '-s', '--set',
            action='store_true',
            help=_('Set tags in server')
        )

        group.add_argument(
            '-g', '--get',
            action='store_true',
            help=_('Get assigned tags in server')
        )

        group.add_argument(
            '-c', '--communicate',
            action='store_true',
            help=_('Communicate tags to server')
        )

        parser.add_argument(
            'tag',
            nargs='*',
            action='store'
        )

        return parser.parse_args()

    def run(self):
        args = self._parse_args()

        if args.debug:
            self._debug = True
            logger.setLevel(logging.DEBUG)

        # actions dispatcher
        if args.get:
            response = self._get_assigned_tags()
            for item in response:
                print('"' + item + '"'),

            self.end_of_transmission()
        elif args.set or args.communicate:
            if args.tag:
                self._tags = self._sanitize(args.tag)

            self._show_running_options()

            rules = self._set_tags()
            if args.set:
                utils.check_lock_file(self.CMD, self.LOCK_FILE)
                self._apply_rules(rules)
                utils.remove_file(self.LOCK_FILE)

            self.end_of_transmission()
        else:
            self._usage_examples()

        sys.exit(os.EX_OK)


def main():
    mft = MigasFreeTags()
    mft.run()

if __name__ == "__main__":
    main()
