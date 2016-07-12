# -*- coding: UTF-8 -*-

# Copyright (c) 2013-2016 Jose Antonio Chavarría <jachavar@gmail.com>
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
__all__ = 'MigasFreeTags'

import os
import sys
import errno

import gettext
_ = gettext.gettext

import logging
logger = logging.getLogger(__name__)

from . import settings, utils

from .sync import MigasFreeSync
from .command import MigasFreeCommand


class MigasFreeTags(MigasFreeCommand):
    _tags = None

    def __init__(self):
        self._user_is_not_root()
        MigasFreeCommand.__init__(self)

    def _usage_examples(self):
        print('\n' + _('Examples:'))

        print('  ' + _('Get assigned tags in server:'))
        print('\t%s tags -g' % self.CMD)
        print('\t%s tags --get\n' % self.CMD)

        print('  ' + _('Communicate tags to server (command line):'))
        print('\t%s tags -c tag... ' % self.CMD)
        print('\t%s tags --communicate tag...\n' % self.CMD)

        print('  ' + _('Communicate tags to server (with GUI):'))
        print('\t%s tags -c' % self.CMD)
        print('\t%s tags --communicate\n' % self.CMD)

        print('  ' + _('Set tags (command line):'))
        print('\t%s tags -s tag...' % self.CMD)
        print('\t%s tags --set tag...\n' % self.CMD)

        print('  ' + _('Set tags (with GUI):'))
        print('\t%s tags -s' % self.CMD)
        print('\t%s tags --set\n' % self.CMD)

        print('  ' + _('Unsetting all tags (command line):'))
        print('\t%s tags -s ""' % self.CMD)
        print('\t%s tags --set ""\n' % self.CMD)

    def _show_running_options(self):
        MigasFreeCommand._show_running_options(self)
        print('\t%s: %s' % (_('Tag list'), self._tags))

    def _sanitize(self, tag_list):
        if tag_list:
            for item in tag_list[:]:
                item = item.replace('"', '')
                try:
                    prefix, value = item.split('-', 1)
                except ValueError:
                    msg = _('Tags must be in "prefix-value" format')
                    self.operation_failed(msg)
                    sys.exit(errno.ENODATA)

            logger.info('Sanitized list: %s' % tag_list)

        return tag_list

    def _select_tags(self, assigned, available):
        selected_tags = []

        if len(available) == 0:
            print(_('There is not available tags to select'))
            sys.exit(os.EX_OK)

        # Change tags with gui
        title = _("Change tags")
        text = _("Please, select tags for this computer")
        if utils.is_xsession() and utils.is_zenity():
            cmd = "zenity --title='%s' \
                --text='%s' \
                --separator='\n' \
                --window-icon=%s \
                --list \
                --width 600 \
                --height 400 \
                --checklist \
                --multiple \
                --print-column=2 \
                --column=' ' \
                --column='TAG' \
                --column='TYPE'" % \
                (
                    title,
                    text,
                    os.path.join(settings.ICON_PATH, self.ICON)
                )
            for key, value in available.items():
                for item in value:
                    tag_active = item in assigned
                    cmd += " '%s' '%s' '%s'" % (tag_active, item, key)
        else:
            cmd = "dialog --backtitle '%s' \
                --separate-output \
                --stdout \
                --checklist '%s' \
                0 0 8" % (_title, _text)
            for key, value in available.items():
                for item in value:
                    tag_active = 'on' if _item in tags["selected"] else 'off'
                    cmd += " '%s' '%s' %s" % (item, key, tag_active)

        logger.debug('Change tags command: %s' % cmd)
        ret, out, error = utils.execute(cmd, interactive=False)
        if ret == 0:
            selected_tags = filter(None, out.split("\n"))
            logger.debug('Selected tags: %s' % selected_tags)
        else:
            # no action chose -> no change tags
            logger.debug('Return value command: %d' % ret)
            sys.exit(ret)

        return selected_tags

    def _get_assigned_tags(self):
        if not self._computer_id:
            self.get_computer_id()

        logger.debug('Getting assigned tags')
        response = self._url_request.run(
            url=self.api_endpoint(self.URLS['get_assigned_tags']),
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

        logger.debug('Getting available tags')
        response = self._url_request.run(
            url=self.api_endpoint(self.URLS['get_available_tags']),
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

        logger.debug('Setting tags: %s', self._tags)
        response = self._url_request.run(
            url=self.api_endpoint(self.URLS['upload_tags']),
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

    @staticmethod
    def _apply_rules(rules):
        mfs = MigasFreeSync()

        # Update metadata
        mfs.synchronize()

        mfs._uninstall_packages(rules["remove"])
        mfs._install_mandatory_packages(rules["preinstall"])

        # Update metadata
        mfs._clean_pms_cache()

        mfs._install_mandatory_packages(rules["install"])

    def run(self, args=None):
        if not args or not hasattr(args, 'cmd'):
            self._usage_examples()
            sys.exit(os.EX_OK)

        if hasattr(args, 'debug') and args.debug:
            self._debug = True
            logger.setLevel(logging.DEBUG)

        # actions dispatcher
        if args.get:
            response = self._get_assigned_tags()
            for item in response:
                print('"' + item + '"'),

            self.end_of_transmission()
        elif args.set or args.communicate:
            if args.set != [] and args.set != [None]:
                self._tags = self._sanitize(args.set)
            elif args.communicate != [] and args.communicate != [None]:
                self._tags = self._sanitize(args.communicate)

            self._show_running_options()

            rules = self._set_tags()
            if args.set != []:
                utils.check_lock_file(self.CMD, self.LOCK_FILE)
                self._apply_rules(rules)
                utils.remove_file(self.LOCK_FILE)

            self.end_of_transmission()

        sys.exit(os.EX_OK)
