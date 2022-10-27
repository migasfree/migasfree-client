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
            width: 20em;
            height: 7em;
            margin: 0;
            border: 1px solid #000;
            padding: .5em 1em;
            font-family: Dosis, "Roboto", "-apple-system", "Helvetica Neue", Helvetica, Arial, sans-serif;
            font-size: 16px;
        }
        h1 {
            margin: 0;
            font-size: 16px;
            font-weight: normal;
        }
        h2 {
            font-size: 16px;
            font-weight: normal;
            margin: 0;
        }
        p {
            margin: 4px 0 0 0;
            border-top: 1px solid rgba(0, 0, 0, 0.12);
            padding: 8px;
            text-align: center;
        }
        img {
            width: 40px;
        }
        .row, .column {
            display: flex;
            flex-wrap: wrap;
        }
        .column {
            flex-direction: column;
        }
        .text-caption {
            font-size: 0.75rem;
            padding-top: 4px;
        }
        .avatar {
            min-width: 56px;
        }
        .justify-center {
            justify-content: center;
        }
        </style>
    </head>
    <body>
        <div class="row">
            <div class="column avatar">
                <img src="file:///usr/share/icons/hicolor/scalable/apps/migasfree-logo-mini.svg" />
            </div>
            <div class="column">
                <h1>%(search)s</h1>
                <h2 class="text-caption">%(uuid)s</h2>
            </div>
        </div>

        <div class="row">
            <div class="column avatar">
                <img src="file:///usr/share/icons/hicolor/scalable/apps/server-network.svg" />
            </div>
            <div class="column justify-center">
                <h2>%(server)s</h2>
            </div>
        </div>

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

        app_icon_path = os.path.join(ICON_PATH, self.ICON_MINI)
        server_icon_path = os.path.join(ICON_PATH, self.ICON_SERVER)
        if is_windows():
            app_icon_path = app_icon_path.replace('\\', '/')
            server_icon_path = server_icon_path.replace('\\', '/')
        app_icon = f'file://{app_icon_path}'
        server_icon = f'file://{server_icon_path}'

        html = HTML_TEMPLATE % {
            'search': info.get('search'),
            'uuid': info.get('uuid'),
            'server': self.migas_server,
            'helpdesk': info.get('helpdesk'),
            'app_icon': app_icon,
            'server_icon': server_icon,
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
