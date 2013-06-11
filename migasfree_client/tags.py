#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Copyright (c) 2013 Jose Antonio Chavarría
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
import optparse
import logging
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
import utils
import server_errors

import settings

from .client import MigasFreeClient
from .command import (
    MigasFreeCommand,
    __version__,
)


class MigasFreeTags(MigasFreeCommand):
    CMD = 'migasfree-tags'  # /usr/bin/migasfree-tags

    def _usage_examples(self):
        print('\n' + _('Examples:'))

        print('  ' + _('Get assigned tags in server:'))
        print('\t%s -g' % self.CMD)
        print('\t%s --get\n' % self.CMD)

        print('  ' + _('Set tags (command line):'))
        print('\t%s -s tag1 tag2' % self.CMD)
        print('\t%s --set tag1 tag2\n' % self.CMD)

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
        tag_list[:] = [_item.replace('"', '') for _item in tag_list]
        logging.info('Sanitized list: %s' % tag_list)

        return tag_list

    def _select_tags(self, tags):
        _selected_tags = []

        # Change tags with gui
        _title = _("Change tags")
        _text = _("Please, select tags for this computer")
        _cmd = "zenity --title='%s' \
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
                _title,
                _text,
                os.path.join(settings.ICON_PATH, self.ICON)
            )
        for _key, _value in tags["available"].items():
            for _item in _value:
                _tag_active = _item in tags["selected"]
                _cmd += " '%s' '%s' '%s'" % (_tag_active, _item, _key)

        logging.debug('Change tags command: %s' % _cmd)
        (_ret, _out, _err) = utils.execute(_cmd, interactive=False)
        if _ret == 0:
            if type(_out) is str and _out != "":
                _selected_tags = _out.replace("\n", "").split("|")
                logging.debug('Selected tags: %s' % _selected_tags)
        else:
            # no action chosed -> no change tags
            logging.debug('Return value command: %d' % _ret)
            sys.exit(_ret)

        return _selected_tags

    def _get_tags(self):
        logging.debug('Getting tags')
        _ret = self._url_request.run('get_computer_tags')

        logging.debug('Getting tags response: %s', _ret)
        if self._debug:
            print('Response: %s' % _ret)

        if 'errmfs' in _ret and _ret['errmfs']['code'] != server_errors.ALL_OK:
            _error_info = server_errors.error_info(
                _ret['errmfs']['code']
            )
            self.operation_failed(_error_info)
            logging.error('Error: %s', _error_info)
            sys.exit(errno.EINPROGRESS)

        return _ret

    def _set_tags(self):
        self._check_sign_keys()

        if not self._tags:
            self._tags = self._select_tags(self._get_tags())

        # unsettings all tags?
        if len(self._tags) == 1 and self._tags[0] == '':
            logging.debug('Unsetting all tags')
            self._tags = []

        logging.debug('Setting tags: %s', self._tags)
        _ret = self._url_request.run(
            'set_computer_tags',
            data={'tags': self._tags}
        )

        print('')
        self.operation_ok(_('Tags setted: %s') % self._tags)

        logging.debug('Setting tags response: %s', _ret)
        if self._debug:
            print('Response: %s' % _ret)

        return _ret

    def _apply_rules(self, rules):
        mfc = MigasFreeClient()

        # Update metadata
        mfc._clean_pms_cache()

        # Remove Packages
        mfc._uninstall_packages(rules["packages"]["remove"])

        # Pre-Install Packages
        mfc._install_mandatory_packages(rules["packages"]["preinstall"])

        # Update metadata
        mfc._clean_pms_cache()

        # Install Packages
        mfc._install_mandatory_packages(rules["packages"]["install"])

        mfc._send_message()

    def run(self):
        _program = 'migasfree tags'
        parser = optparse.OptionParser(
            description=_program,
            prog=self.CMD,
            version=__version__,
            usage='%prog [options] [tag]...'
        )

        parser.add_option(
            '--set', '-s',
            action='store_true',
            help=_('Set tags in server')
        )

        parser.add_option(
            '--get', '-g',
            action='store_true',
            help=_('Get assigned tags in server')
        )

        options, arguments = parser.parse_args()
        logging.info('Program options: %s' % options)
        logging.info('Program arguments: %s' % arguments)

        # check restrictions
        if not options.get and not options.set:
            self._usage_examples()
            parser.error(_('Get or Set options are mandatory!!!'))
        if options.get and options.set:
            self._usage_examples()
            parser.error(_('Get and Set options are exclusive!!!'))

        utils.check_lock_file(self.CMD, self.LOCK_FILE)

        # actions dispatcher
        if options.get:
            _response = self._get_tags()
            for _item in _response['selected']:
                print('"' + _item + '"'),
        elif options.set:
            self._tags = self._sanitize(arguments)

            print(_('%(program)s version: %(version)s') % {
                'program': _program,
                'version': __version__
            })
            self._show_running_options()

            _response = self._set_tags()
            self._apply_rules(_response)
        else:
            parser.print_help()
            self._usage_examples()

        utils.remove_file(self.LOCK_FILE)

        sys.exit(os.EX_OK)  # no error


def main():
    mft = MigasFreeTags()
    mft.run()

if __name__ == "__main__":
    main()
