# Copyright (c) 2025 Jose Antonio Chavarría <jachavar@gmail.com>
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

import unittest
from unittest.mock import mock_open, patch

from migasfree_client.pms.apk import Apk


class TestApk(unittest.TestCase):
    def setUp(self):
        self.apk = Apk()

    @patch('migasfree_client.pms.apk.execute')
    def test_install(self, mock_execute):
        mock_execute.return_value = (0, '', '')
        self.assertTrue(self.apk.install('package'))
        mock_execute.assert_called_with('/sbin/apk add package')

    @patch('migasfree_client.pms.apk.execute')
    def test_remove(self, mock_execute):
        mock_execute.return_value = (0, '', '')
        self.assertTrue(self.apk.remove('package'))
        mock_execute.assert_called_with('/sbin/apk del package')

    @patch('migasfree_client.pms.apk.execute')
    def test_search(self, mock_execute):
        mock_execute.return_value = (0, '', '')
        self.assertTrue(self.apk.search('pattern'))
        mock_execute.assert_called_with('/sbin/apk search pattern')

    @patch('migasfree_client.pms.apk.execute')
    def test_update_silent(self, mock_execute):
        mock_execute.side_effect = [(0, '', ''), (0, '', '')]
        ret, _error = self.apk.update_silent()
        self.assertTrue(ret)
        self.assertEqual(mock_execute.call_count, 2)

    @patch('migasfree_client.pms.apk.execute')
    def test_install_silent(self, mock_execute):
        # Mock is_installed to return False (package not installed)
        with patch.object(self.apk, 'is_installed', return_value=False):
            mock_execute.return_value = (0, '', '')
            ret, _error = self.apk.install_silent(['package'])
            self.assertTrue(ret)
            mock_execute.assert_called_with('/sbin/apk add package', interactive=False, verbose=True)

    @patch('migasfree_client.pms.apk.execute')
    def test_remove_silent(self, mock_execute):
        # Mock is_installed to return True (package installed)
        with patch.object(self.apk, 'is_installed', return_value=True):
            mock_execute.return_value = (0, '', '')
            ret, _error = self.apk.remove_silent(['package'])
            self.assertTrue(ret)
            mock_execute.assert_called_with('/sbin/apk del package', interactive=False, verbose=True)

    @patch('migasfree_client.pms.apk.execute')
    def test_is_installed(self, mock_execute):
        mock_execute.return_value = (0, '', '')
        self.assertTrue(self.apk.is_installed('package'))
        mock_execute.assert_called_with('/sbin/apk info -e package', interactive=False)

    @patch('migasfree_client.pms.apk.execute')
    def test_clean_all(self, mock_execute):
        mock_execute.return_value = (0, '', '')
        self.assertTrue(self.apk.clean_all())
        mock_execute.assert_called_with('/sbin/apk cache clean')

    @patch('migasfree_client.pms.apk.execute')
    def test_query_all(self, mock_execute):
        mock_execute.side_effect = [
            (0, 'pkg1-1.0\npkg2-2.0', ''),  # info -v
            (0, 'x86_64', ''),  # get_system_architecture
        ]
        result = self.apk.query_all()
        self.assertEqual(result, ['pkg1-1.0_x86_64.apk', 'pkg2-2.0_x86_64.apk'])

    @patch('migasfree_client.pms.apk.execute')
    def test_available_packages(self, mock_execute):
        mock_execute.return_value = (0, 'pkg1\npkg2', '')
        result = self.apk.available_packages()
        self.assertEqual(result, ['pkg1', 'pkg2'])
        mock_execute.assert_called_with('/sbin/apk search -q', interactive=False)

    @patch('migasfree_client.pms.apk.os.path.exists')
    def test_create_repos(self, mock_exists):
        mock_exists.return_value = True
        repos = [{'source_template': '{protocol}://{server}/repo'}]

        m = mock_open(read_data='existing_repo')
        with patch('builtins.open', m):
            self.apk.create_repos('http', 'server', repos)

            # Check if file was opened for reading
            m.assert_any_call('/etc/apk/repositories', encoding='utf-8')
            # Check if file was opened for appending
            m.assert_any_call('/etc/apk/repositories', 'a', encoding='utf-8')

            # Check write
            handle = m()
            handle.write.assert_called_with('\nhttp://server/repo\n')

    @patch('migasfree_client.pms.apk.execute')
    def test_import_server_key(self, mock_execute):
        mock_execute.return_value = (0, '', '')
        self.assertTrue(self.apk.import_server_key('key.pub'))
        mock_execute.assert_called_with('cp key.pub /etc/apk/keys/')

    @patch('migasfree_client.pms.apk.execute')
    def test_get_system_architecture(self, mock_execute):
        mock_execute.return_value = (0, 'x86_64\n', '')
        self.assertEqual(self.apk.get_system_architecture(), 'x86_64')
        mock_execute.assert_called_with('/sbin/apk --print-arch', interactive=False)
