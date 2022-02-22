# -*- coding: UTF-8 -*-

# Copyright (c) 2015-2022 Jose Antonio Chavarría <jachavar@gmail.com>
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

import os
import sys
import errno
import gettext
import logging

from .command import MigasFreeCommand
from .settings import ICON_PATH, TMP_PATH
from .utils import ALL_OK, is_windows, is_linux, write_file, execute_as_user

__author__ = 'Jose Antonio Chavarría <jachavar@gmail.com>'
__license__ = 'GPLv3'
__all__ = 'MigasFreeLabel'

_ = gettext.gettext
logger = logging.getLogger(__name__)

HTML_TEMPLATE = """<!doctype html>
<html>
    <head>
        <title>%(search)s</title>
        <meta charset="utf-8" />
        <style type="text/css">
        body {
            width: 30em;
            height: 10em;
            border: 1px solid #000;
            padding: .5em 1em;
            font-family: sans-serif;
        }
        h1 {
            margin: 0 .5em;
            text-align: right;
            background: url('%(image)s') left center no-repeat;
        }
        h2 {
            font-size: 100%%;
            text-align: center;
        }
        p {
            border-top: 1px solid #000;
            text-align: center;
        }
        </style>
    </head>
    <body>
        <h1>%(search)s</h1>
        <h2>%(uuid)s</h2>
        <h2>%(server)s</h2>
        <p>%(helpdesk)s</p>
    </body>
</html>"""


class MigasFreeLabel(MigasFreeCommand):
    def __init__(self):
        self._user_is_not_root()
        super().__init__()

    def get_label(self):
        if not self._computer_id:
            self.get_computer_id()

        logger.debug('Getting label')
        with self.console.status(''):
            response = self._url_request.run(
                url=self.api_endpoint(self.URLS['get_label']),
                data={
                    'id': self._computer_id
                },
                debug=self._debug
            )

        logger.debug('Response get_label: %s', response)
        if self._debug:
            self.console.log(f'Response: {response}')

        if 'error' in response:
            self.operation_failed(response['error']['info'])
            sys.exit(errno.ENODATA)

        return response

    def _show_label(self):
        if not self._check_sign_keys():
            sys.exit(errno.EPERM)

        info = self.get_label()

        image_path = os.path.join(ICON_PATH, self.ICON)
        if is_windows():
            image_path = image_path.replace('\\', '/')
        image = f'file://{image_path}'

        html = HTML_TEMPLATE % {
            'search': info.get('search'),
            'uuid': info.get('uuid'),
            'server': f'{_("Server")}: {self.migas_server}',
            'helpdesk': info.get('helpdesk'),
            'image': image
        }

        _file = os.path.join(TMP_PATH, 'label.html')
        write_file(_file, html)

        if is_linux():
            execute_as_user(['xdg-open', _file])
        else:
            execute_as_user(['cmd', '/c', 'start', _file])

    def run(self, args=None):
        super().run(args)

        self._show_label()
        self.end_of_transmission()

        sys.exit(ALL_OK)
