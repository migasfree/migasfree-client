# Copyright (c) 2025-2026 Jose Antonio Chavarría <jachavar@gmail.com>
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
from unittest.mock import patch

from migasfree_client.pms.apk import Apk


class TestApk(unittest.TestCase):
    def setUp(self):
        self.apk = Apk()

    def test_init(self):
        self.assertEqual(self.apk._name, 'apk')
        self.assertEqual(self.apk._pms, '/sbin/apk')

    @patch('migasfree_client.pms.apk.execute')
    def test_install(self, mock_execute):
        mock_execute.return_value = (0, '', '')
        self.assertTrue(self.apk.install('package'))
        self.assertIn('add', mock_execute.call_args[0][0])
        self.assertIn('package', mock_execute.call_args[0][0])

    @patch('migasfree_client.pms.apk.execute')
    def test_update_silent(self, mock_execute):
        mock_execute.return_value = (0, 'output', '')
        ret, _ = self.apk.update_silent()
        self.assertTrue(ret)
        self.assertEqual(mock_execute.call_count, 2)  # update and upgrade

    @patch('migasfree_client.pms.apk.execute')
    def test_install_silent(self, mock_execute):
        with patch.object(self.apk, '_get_installed_packages', return_value=set()):
            mock_execute.return_value = (0, 'output', '')
            ret, _ = self.apk.install_silent(['package1'])
            self.assertTrue(ret)
            self.assertIn('add', mock_execute.call_args[0][0])
            self.assertIn('package1', mock_execute.call_args[0][0])

    @patch('migasfree_client.pms.apk.execute')
    def test_remove_silent(self, mock_execute):
        with patch.object(self.apk, '_get_installed_packages', return_value={'package1'}):
            mock_execute.return_value = (0, 'output', '')
            ret, _ = self.apk.remove_silent(['package1'])
            self.assertTrue(ret)
            self.assertIn('del', mock_execute.call_args[0][0])
            self.assertIn('package1', mock_execute.call_args[0][0])

    @patch('migasfree_client.pms.apk.execute')
    def test_query_all(self, mock_execute):
        # Sample output from 'apk info -v'
        apk_info_output = """
vim-8.2.3456-r0
bash-5.1.008-r1
musl-1.2.2-r0
        """
        mock_execute.return_value = (0, apk_info_output.strip(), '')
        with patch.object(self.apk, 'get_system_architecture', return_value='x86_64'):
            result = self.apk.query_all()
            self.assertIn('vim-8.2.3456-r0_x86_64.apk', result)
            self.assertIn('bash-5.1.008-r1_x86_64.apk', result)

    @patch('migasfree_client.pms.apk.execute')
    def test_get_system_architecture(self, mock_execute):
        mock_execute.return_value = (0, 'x86_64\n', '')
        self.assertEqual(self.apk.get_system_architecture(), 'x86_64')


if __name__ == '__main__':
    unittest.main()
