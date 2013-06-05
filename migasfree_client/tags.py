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

    def _set_tags(self):
        logging.debug('Set tags operation...')

        self._check_sign_keys()

        if not self._silent:
            logging.debug('Set tags: %s', self._tags)
            _ret = self._url_request.run(
                'set_computer_tags',
                data={'tags': self._tags, 'select': True},
            )

            logging.debug('Uploading tags response: %s', _ret)
            if self._debug:
                print('Response: %s' % _ret)

            if _ret['errmfs']['code'] != server_errors.ALL_OK:
                _error_info = server_errors.error_info(
                    _ret['errmfs']['code']
                )
                self.operation_failed(_error_info)
                logging.error('Uploading file error: %s', _error_info)
                sys.exit(errno.EINPROGRESS)

            # Change tags with gui
            if "select" in _ret:
                _title = _("Change tags")
                _text = _("Please, select tags for this computer")
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
                        _title,
                        _text,
                        os.path.join(settings.ICON_PATH, self.ICON)
                    )
                for key, value in _ret["select"]["availables"].items():
                    for tag in value:
                        _tag_active = tag in _ret["select"]["tags"]
                        cmd += " '%s' '%s' '%s'" % (_tag_active, tag, key)

                (_ret, _out, _err) = utils.execute(cmd, interactive=False)
                if _ret == 0:
                    if type(_out) is str and _out != "":
                        self._tags = _out.replace("\n", "").split("|")
                    else:
                        self._tags = []
                else:
                    return _ret
            else:
                return True

        logging.debug('Set tags: %s', self._tags)
        _ret = self._url_request.run(
            'set_computer_tags',
            data={
                'tags': self._tags,
                'select': False
            }
        )

        logging.debug('Uploading tags response: %s', _ret)
        if self._debug:
            print('Response: %s' % _ret)

        mfc = MigasFreeClient()

        # Update metadata
        mfc._clean_pms_cache()

        # Remove Packages
        mfc._uninstall_packages(_ret["packages"]["remove"])

        # Pre-Install Packages
        mfc._install_mandatory_packages(_ret["packages"]["preinstall"])

        # Update metadata
        mfc._clean_pms_cache()

        # Install Packages
        mfc._install_mandatory_packages(_ret["packages"]["install"])

        mfc._send_message()

        return True

    def run(self):
        _program = 'migasfree tags'
        parser = optparse.OptionParser(
            description=_program,
            prog=self.CMD,
            version=__version__,
            usage='%prog [options] [tag]...'
        )

        print(_('%(program)s version: %(version)s') % {
            'program': _program,
            'version': __version__
        })

        parser.add_option(
            '--silent', '-s',
            action='store_true',
            help=_('Silent mode')
        )

        options, arguments = parser.parse_args()

        self._silent = options.silent

        utils.check_lock_file(self.CMD, self.LOCK_FILE)

        self._show_running_options()

        self._tags = arguments

        self._set_tags()

        utils.remove_file(self.LOCK_FILE)

        sys.exit(os.EX_OK)  # no error


def main():
    mft = MigasFreeTags()
    mft.run()

if __name__ == "__main__":
    main()
