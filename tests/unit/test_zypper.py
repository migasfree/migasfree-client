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

from migasfree_client.pms.zypper import Zypper


class TestZypper(unittest.TestCase):
    def setUp(self):
        self.zypper = Zypper()

    def test_init(self):
        self.assertEqual(self.zypper._name, 'zypper')
        self.assertEqual(self.zypper._pms, '/usr/bin/zypper')

    @patch('migasfree_client.pms.zypper.execute')
    def test_install(self, mock_execute):
        mock_execute.return_value = (0, '', '')
        self.assertTrue(self.zypper.install('package'))
        self.assertIn('install', mock_execute.call_args[0][0])
        self.assertIn('package', mock_execute.call_args[0][0])

    @patch('migasfree_client.pms.zypper.execute')
    def test_update_silent(self, mock_execute):
        mock_execute.side_effect = [
            (0, 'output1', ''),
            (0, 'output2', ''),
        ]
        ret, _ = self.zypper.update_silent()
        self.assertTrue(ret)
        self.assertEqual(mock_execute.call_count, 2)

    @patch('migasfree_client.pms.zypper.execute')
    def test_install_silent(self, mock_execute):
        with patch.object(self.zypper, '_get_installed_packages', return_value=set()):
            mock_execute.return_value = (0, 'output', '')
            ret, _ = self.zypper.install_silent(['package1'])
            self.assertTrue(ret)
            self.assertIn('install', mock_execute.call_args[0][0])
            self.assertIn('package1', mock_execute.call_args[0][0])

    @patch('migasfree_client.pms.zypper.execute')
    def test_remove_silent(self, mock_execute):
        with patch.object(self.zypper, '_get_installed_packages', return_value={'package1'}):
            mock_execute.return_value = (0, 'output', '')
            ret, _ = self.zypper.remove_silent(['package1'])
            self.assertTrue(ret)
            self.assertIn('remove', mock_execute.call_args[0][0])
            self.assertIn('package1', mock_execute.call_args[0][0])

    @patch('migasfree_client.pms.zypper.execute')
    def test_available_packages(self, mock_execute):
        # Sample output from 'zypper pa'
        zypper_pa_output = """
Loading repository data...
Reading installed packages...
S | Repository | Name         | Version   | Arch
--+------------+--------------+-----------+-------
  | repo1      | vim          | 8.2       | x86_64
i | repo1      | bash         | 5.0       | x86_64
  | repo2      | git          | 2.30      | x86_64
        """
        mock_execute.return_value = (0, zypper_pa_output, '')
        result = self.zypper.available_packages()
        self.assertEqual(result, ['bash', 'git', 'vim'])

    @patch('migasfree_client.pms.zypper.execute')
    def test_clean_all(self, mock_execute):
        mock_execute.side_effect = [
            (0, '', ''),
            (0, '', ''),
        ]
        self.assertTrue(self.zypper.clean_all())
        self.assertEqual(mock_execute.call_count, 2)


if __name__ == '__main__':
    unittest.main()
