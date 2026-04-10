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

import unittest
from unittest.mock import patch

from migasfree_client.pms.wpt import Wpt


class TestWpt(unittest.TestCase):
    def setUp(self):
        self.wpt = Wpt()

    def test_init(self):
        self.assertEqual(self.wpt._name, 'wpt')
        self.assertEqual(self.wpt._pms, 'wpt')

    @patch('migasfree_client.pms.wpt.execute')
    def test_install(self, mock_execute):
        mock_execute.return_value = (0, '', '')
        self.assertTrue(self.wpt.install('package'))
        self.assertIn('install', mock_execute.call_args[0][0])
        self.assertIn('package', mock_execute.call_args[0][0])

    @patch('migasfree_client.pms.wpt.execute')
    def test_update_silent(self, mock_execute):
        mock_execute.return_value = (0, 'output', '')
        ret, _ = self.wpt.update_silent()
        self.assertTrue(ret)
        self.assertIn('upgrade', mock_execute.call_args[0][0])

    @patch('migasfree_client.pms.wpt.execute')
    def test_install_silent(self, mock_execute):
        with patch.object(self.wpt, '_get_installed_packages', return_value=set()):
            mock_execute.return_value = (0, 'output', '')
            ret, _ = self.wpt.install_silent(['package1'])
            self.assertTrue(ret)
            self.assertIn('install', mock_execute.call_args[0][0])
            self.assertIn('--assume-yes', mock_execute.call_args[0][0])
            self.assertIn('package1', mock_execute.call_args[0][0])

    @patch('migasfree_client.pms.wpt.execute')
    def test_remove_silent(self, mock_execute):
        with patch.object(self.wpt, '_get_installed_packages', return_value={'package1'}):
            mock_execute.return_value = (0, 'output', '')
            ret, _ = self.wpt.remove_silent(['package1'])
            self.assertTrue(ret)
            self.assertIn('remove', mock_execute.call_args[0][0])
            self.assertIn('--assume-yes', mock_execute.call_args[0][0])
            self.assertIn('package1', mock_execute.call_args[0][0])

    @patch('migasfree_client.pms.wpt.execute')
    def test_query_all(self, mock_execute):
        # Sample output from 'wpt list --all --summary'
        wpt_list_output = """
vim-8.2.3456-1
bash-5.1.008-1
        """
        mock_execute.return_value = (0, wpt_list_output.strip(), '')
        result = self.wpt.query_all()
        self.assertIn('vim-8.2.3456-1.tar.gz', result)
        self.assertIn('bash-5.1.008-1.tar.gz', result)

    def test_get_system_architecture(self):
        self.assertEqual(self.wpt.get_system_architecture(), 'x64')


if __name__ == '__main__':
    unittest.main()
