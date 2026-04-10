# Copyright (c) 2026 Jose Antonio Chavarría <jachavar@gmail.com>
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

import gettext
import logging
import os

from migasfree_client import settings, utils
from migasfree_client.command import require_computer_id

_ = gettext.gettext
logger = logging.getLogger('migasfree_client')


class SoftwareManagerMixin:
    """
    Mixin for managing software operations via the appropriate PMS.
    Assumes it is mixed into a class that has:
    - self.pms
    - self._computer_id
    - self.migas_server
    - self.migas_package_proxy_cache
    - self.migas_protocol
    - self._pms_status_ok
    - self.console
    - self._show_message()
    - self.operation_ok()
    - self.operation_failed()
    - self._report_error()
    - self._check_pms()
    - self.get_repositories()
    - self.get_mandatory_packages()
    - self._api_call()
    - self._handle_response()
    """

    @staticmethod
    def software_history(software):
        history = {}

        # if have been managed packages manually
        # information is uploaded to server
        if os.path.isfile(settings.SOFTWARE_FILE) and os.stat(settings.SOFTWARE_FILE).st_size:
            diff_software = utils.compare_lists(
                open(settings.SOFTWARE_FILE, encoding='utf_8').read().splitlines(),  # not readlines!!!  # noqa: SIM115
                software,
            )

            if diff_software:
                history = {
                    'installed': [x for x in diff_software if x.startswith('+')],
                    'uninstalled': [x for x in diff_software if x.startswith('-')],
                }
                logger.debug('Software diff: %s', history)

        return history

    def create_repositories(self):
        self._check_pms()

        repos = self.get_repositories()

        self._show_message(_('Creating repositories...'))

        server = self.migas_server
        if self.migas_package_proxy_cache:
            server = f'{self.migas_package_proxy_cache}/{server}'

        ret = self.pms.create_repos(self.migas_protocol, server, repos)

        if ret:
            self.operation_ok()
        else:
            self._pms_status_ok = False
            self._report_error(_('Error creating repositories: %s') % repos)

    def clean_pms_cache(self):
        """
        clean cache of Package Management System
        """
        self._check_pms()

        self._show_message(_('Getting repositories metadata...'))
        ret = self.pms.clean_all()

        if ret:
            self.operation_ok()
        else:
            self._report_error(_('Error getting repositories metadata'))

    def uninstall_packages(self, packages):
        self._check_pms()

        self._show_message(_('Uninstalling packages...'))
        ret, error = self.pms.remove_silent(packages)

        if ret:
            self.operation_ok()
        else:
            self._pms_status_ok = False
            self._report_error(_('Error uninstalling packages: %s') % error)

    def install_mandatory_packages(self, packages):
        self._check_pms()

        self._show_message(_('Installing mandatory packages...'))
        ret, error = self.pms.install_silent(packages)

        if ret:
            self.operation_ok()
        else:
            self._pms_status_ok = False
            self._report_error(_('Error installing packages: %s') % error)

        return ret

    def _update_packages(self):
        self._check_pms()

        self._show_message(_('Updating packages...'))
        ret, error = self.pms.update_silent()

        if ret:
            self.operation_ok()
        else:
            self._pms_status_ok = False
            self._report_error(_('Error updating packages: %s') % error)

        return ret

    def mandatory_pkgs(self):
        response = self.get_mandatory_packages()
        if not response:
            return

        if 'remove' in response:
            self.uninstall_packages(response['remove'])
        if 'install' in response:
            self.install_mandatory_packages(response['install'])

    @require_computer_id
    def upload_software(self, before, history):
        self._check_pms()

        after = self.pms.query_all()
        utils.write_file(settings.SOFTWARE_FILE, '\n'.join(after))

        diff_software = utils.compare_lists(before, after)
        if diff_software:
            data = {
                'installed': [x for x in diff_software if x.startswith('+')],
                'uninstalled': [x for x in diff_software if x.startswith('-')],
            }
            logger.debug('Software diff: %s', data)

            if data['installed']:
                if 'installed' in history:
                    history['installed'].extend(data['installed'])
                else:
                    history['installed'] = data['installed']
            if data['uninstalled']:
                if 'uninstalled' in history:
                    history['uninstalled'].extend(data['uninstalled'])
                else:
                    history['uninstalled'] = data['uninstalled']

            self._show_message(_('Software diff'))
            self.console.print(history)

        self._show_message(_('Uploading software...'))
        response = self._api_call(
            'upload_software',
            {'id': self._computer_id, 'inventory': after, 'history': history},
        )
        return self._handle_response(response)
