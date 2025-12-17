# Copyright (c) 2013-2025 Jose Antonio Chavarría <jachavar@gmail.com>
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

import collections
import errno
import gettext
import json
import logging
import os
import sys

from .command import MigasFreeCommand, lock_file_context, require_computer_id, require_sign_keys
from .settings import ICON_PATH
from .sync import MigasFreeSync
from .utils import (
    ALL_OK,
    execute,
    is_linux,
    is_windows,
    is_xsession,
    is_zenity,
)

__author__ = 'Jose Antonio Chavarría <jachavar@gmail.com>'
__license__ = 'GPLv3'
__all__ = ['MigasFreeTags']

_ = gettext.gettext
logger = logging.getLogger('migasfree_client')


class MigasFreeTags(MigasFreeCommand):
    _tags = None

    def __init__(self):
        self._check_user_is_root()
        super().__init__()

    def _usage_examples(self):
        print('\n' + _('Examples:'))

        examples = [
            (_('Get tags in server (JSON format):'), [f'{self.CMD} tags -g', f'{self.CMD} tags --get']),
            (
                _('Communicate tags to server (command line):'),
                [f'{self.CMD} tags -c tag...', f'{self.CMD} tags --communicate tag...'],
            ),
            (_('Communicate tags to server (with GUI):'), [f'{self.CMD} tags -c', f'{self.CMD} tags --communicate']),
            (_('Set tags (command line):'), [f'{self.CMD} tags -s tag...', f'{self.CMD} tags --set tag...']),
            (_('Set tags (with GUI):'), [f'{self.CMD} tags -s', f'{self.CMD} tags --set']),
            (_('Unsetting all tags (command line):'), [f'{self.CMD} tags -s ""', f'{self.CMD} tags --set ""']),
        ]
        for title, cmds in examples:
            print(f'  {title}')
            for cmd in cmds:
                print(f'\t{cmd}')
            print()

    def _show_running_options(self):
        super()._show_running_options()

        print('\t{}: {}'.format(_('Tag list'), self._tags))
        print()

    def _sanitize(self, tag_list):
        if tag_list:
            for item in tag_list[:]:
                item = item.replace('"', '')
                try:
                    _prefix, _value = item.split('-', 1)
                except ValueError:
                    msg = _('Tags must be in "prefix-value" format')
                    self.operation_failed(msg)
                    sys.exit(errno.ENODATA)

            logger.info('Sanitized list: %s', tag_list)

        return tag_list

    def _select_tags(self, assigned, available):
        selected_tags = []

        if len(available) == 0:
            print()
            self.console.log(_('There is not available tags to select'), style='yellow')
            sys.exit(ALL_OK)

        available_tags = collections.OrderedDict(sorted(available.items()))

        # Change tags with gui
        title = _('Change tags')
        text = _('Please, select tags for this computer')
        if is_windows() or (is_xsession() and is_zenity()):
            cmd = 'zenity --title="{}" \
                --text="{}" \
                {} \
                --window-icon="{}" \
                --list \
                --width 600 \
                --height 400 \
                --checklist \
                --multiple \
                --print-column=2 \
                --column=" " \
                --column=TAG \
                --column=TYPE'.format(
                title,
                text,
                '--separator="\n"' if is_linux() else '',
                os.path.join(ICON_PATH, self.ICON),
            )
            if is_linux():
                cmd += ' 2> /dev/null'
            for key, value in available_tags.items():
                value.sort()
                for item in value:
                    tag_active = item in assigned
                    cmd += f' "{tag_active}" "{item}" "{key}"'
        else:
            cmd = f"dialog --backtitle '{title}' \
                --separate-output --stdout --checklist '{text}' 0 0 8"
            for key, value in available_tags.items():
                value.sort()
                for item in value:
                    tag_active = 'on' if item in assigned else 'off'
                    cmd += f" '{item}' '{key}' {tag_active}"

        logger.debug('Change tags command: %s', cmd)
        ret, out, _error = execute(cmd, interactive=False)
        if ret == 0:
            selected_tags = list(filter(None, out.split('\n')))
            logger.debug('Selected tags: %s', selected_tags)
        else:
            # no action chosen -> no change tags
            logger.debug('Return value command: %d', ret)
            sys.exit(ret)

        return selected_tags

    @require_sign_keys
    @require_computer_id
    def get_assigned_tags(self):
        logger.debug('Getting assigned tags')
        response = self._url_request.run(
            url=self.api_endpoint(self.URLS['get_assigned_tags']),
            data={'id': self._computer_id},
            debug=self._debug,
        )

        logger.debug('Response get_assigned_tags: %s', response)
        if self._debug:
            self.console.log(f'Response: {response}')

        if 'error' in response:
            self.operation_failed(response['error']['info'])
            sys.exit(errno.ENODATA)

        return response

    @require_sign_keys
    @require_computer_id
    def get_available_tags(self):
        logger.debug('Getting available tags')
        response = self._url_request.run(
            url=self.api_endpoint(self.URLS['get_available_tags']),
            data={'id': self._computer_id},
            exit_on_error=False,
            debug=self._debug,
        )

        logger.debug('Response get_available_tags: %s', response)
        if self._debug:
            self.console.log(f'Response: {response}')

        if 'error' in response:
            self.operation_failed(response['error']['info'])
            sys.exit(errno.ENODATA)

        return response

    @require_sign_keys
    def set_tags(self):
        if not self._tags and not self._quiet:
            self._tags = self._select_tags(
                assigned=self.get_assigned_tags(),
                available=self.get_available_tags(),
            )

        logger.debug('Setting tags: %s', self._tags)
        response = self._url_request.run(
            url=self.api_endpoint(self.URLS['upload_tags']),
            data={'id': self._computer_id, 'tags': self._tags},
            exit_on_error=False,
            debug=self._debug,
        )

        logger.debug('Setting tags response: %s', response)
        if self._debug:
            self.console.log(f'Response: {response}')

        if 'error' in response:
            self.operation_failed(response['error']['info'])
            sys.exit(errno.ENODATA)

        print()
        self.operation_ok(_('Tags setted: %s') % self._tags)

        return response

    @require_sign_keys
    def _apply_rules(self, rules):
        mfs = MigasFreeSync()

        # Update metadata
        mfs.upload_attributes()
        mfs.upload_faults()
        if self.pms:
            mfs.create_repositories()
            mfs.clean_pms_cache()

            software_before = self.pms.query_all()
            software_history = mfs.software_history(software_before)

            mfs.uninstall_packages(rules['remove'])
            mfs.install_mandatory_packages(rules['preinstall'])

            # Update metadata
            mfs.clean_pms_cache()

            mfs.install_mandatory_packages(rules['install'])

            mfs.upload_software(software_before, software_history)

    def run(self, args=None):
        super().run(args)
        if not self._quiet:
            print()

        if not args or not hasattr(args, 'cmd'):
            self._usage_examples()
            sys.exit(ALL_OK)

        # actions dispatcher
        if args.get:
            with lock_file_context(self.CMD, self.LOCK_FILE):
                response = {
                    'assigned': self.get_assigned_tags(),
                    'available': self.get_available_tags(),
                }

            print(json.dumps(response, ensure_ascii=False))
            self.end_of_transmission()

        elif isinstance(args.set, list) or isinstance(args.communicate, list):
            self._tags = []
            if args.set is not None:
                self._tags = self._sanitize(args.set)
            elif args.communicate is not None:
                self._tags = self._sanitize(args.communicate)

            if not self._quiet:
                self._show_running_options()

            with lock_file_context(self.CMD, self.LOCK_FILE):
                rules = self.set_tags()
                if args.set:
                    self._apply_rules(rules)

            self.end_of_transmission()

        sys.exit(ALL_OK)

