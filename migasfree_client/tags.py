# -*- coding: UTF-8 -*-

# Copyright (c) 2013-2021 Jose Antonio Chavarría <jachavar@gmail.com>
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

__author__ = 'Jose Antonio Chavarría'
__license__ = 'GPLv3'
__all__ = ('MigasFreeTags', 'main')

import os
import sys
import optparse
import logging
import errno
import collections
import json

import gettext
_ = gettext.gettext

from . import (
    settings,
    utils,
    server_errors,
)

from .client import MigasFreeClient
from .command import MigasFreeCommand


class MigasFreeTags(MigasFreeCommand):
    CMD = 'migasfree-tags'  # /usr/bin/migasfree-tags

    def __init__(self):
        self._user_is_not_root()
        MigasFreeCommand.__init__(self)

    def _usage_examples(self):
        print('\n' + _('Examples:'))

        print('  ' + _('Get available tags in server:'))
        print('\t%s -a' % self.CMD)
        print('\t%s --available\n' % self.CMD)

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
        tag_list[:] = [_item.replace('"', '') for _item in tag_list]
        logging.info('Sanitized list: %s' % tag_list)

        return tag_list

    def _select_tags(self, tags):
        _selected_tags = []

        if len(tags["available"]) == 0:
            print(_('There is not available tags to select'))
            sys.exit(os.EX_OK)

        _available_tags = collections.OrderedDict(
            sorted(tags["available"].items())
        )

        # Change tags with gui
        _title = _("Change tags")
        _text = _("Please, select tags for this computer")
        if utils.is_xsession() and utils.is_zenity():
            _cmd = "zenity --title='%s' \
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
                --column='TYPE' 2> /dev/null" % (
                    _title,
                    _text,
                    os.path.join(settings.ICON_PATH, self.ICON)
                )
            for _key, _value in _available_tags.items():
                _value.sort()
                for _item in _value:
                    _tag_active = _item in tags["selected"]
                    _cmd += " '%s' '%s' '%s'" % (_tag_active, _item, _key)
        else:
            _cmd = "dialog --backtitle '%s' \
                --separate-output \
                --stdout \
                --checklist '%s' \
                0 0 8" % (_title, _text)
            for _key, _value in _available_tags.items():
                _value.sort()
                for _item in _value:
                    _tag_active = 'on' if _item in tags["selected"] else 'off'
                    _cmd += " '%s' '%s' %s" % (_item, _key, _tag_active)

        logging.debug('Change tags command: %s' % _cmd)
        _ret, _out, _err = utils.execute(_cmd, interactive=False)
        if _ret == 0:
            _selected_tags = list(filter(None, _out.split("\n")))
            logging.debug('Selected tags: %s' % _selected_tags)
        else:
            # no action chosen -> no change tags
            logging.debug('Return value command: %d' % _ret)
            sys.exit(_ret)

        return _selected_tags

    def _get_tags(self):
        self._check_sign_keys()

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
        mfc._update_system()

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
            version=self.release,
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

        parser.add_option(
            '--available', '-a',
            action='store_true',
            help=_('Get available tags in server (JSON format)')
        )

        parser.add_option(
            '--communicate', '-c',
            action='store_true',
            help=_('Communicate tags to server')
        )

        options, arguments = parser.parse_args()
        logging.info('Program options: %s' % options)
        logging.info('Program arguments: %s' % arguments)

        # check restrictions
        if not options.get and not options.set and not options.communicate \
                and not options.available:
            self._usage_examples()
            parser.error(_('Get or Set or Communicate options are mandatory!!!'))
        if options.get and options.set:
            self._usage_examples()
            parser.error(_('Get and Set options are exclusive!!!'))
        if options.get and options.communicate:
            self._usage_examples()
            parser.error(_('Get and Communicate options are exclusive!!!'))
        if options.get and options.available:
            self._usage_examples()
            parser.error(_('Get assigned and Get available tags options are exclusive!!!'))
        if options.set and options.communicate:
            self._usage_examples()
            parser.error(_('Set and Communicate options are exclusive!!!'))
        if options.available and options.communicate:
            self._usage_examples()
            parser.error(_('Get available tags and Communicate options are exclusive!!!'))
        if options.available and options.set:
            self._usage_examples()
            parser.error(_('Get available tags and Set options are exclusive!!!'))

        # actions dispatcher
        if options.get or options.available:
            _response = self._get_tags()
            if options.get:
                for _item in _response['selected']:
                    print('"{0}"'.format(_item))
            if options.available:
                print(json.dumps(_response['available'], ensure_ascii=False))
        elif options.set or options.communicate:
            self._tags = self._sanitize(arguments)

            print(_('%(program)s version: %(version)s') % {
                'program': _program,
                'version': self.release
            })
            self._show_running_options()

            _response = self._set_tags()
            if options.set:
                utils.check_lock_file(self.CMD, self.LOCK_FILE)
                self._apply_rules(_response)
                utils.remove_file(self.LOCK_FILE)
        else:
            parser.print_help()
            self._usage_examples()

        sys.exit(os.EX_OK)


def main():
    mft = MigasFreeTags()
    mft.run()


if __name__ == "__main__":
    main()
