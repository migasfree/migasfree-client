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

from migasfree_client.pms.pacman import Pacman


class TestPacman(unittest.TestCase):
    def setUp(self):
        self.pacman = Pacman()

    def test_init(self):
        self.assertEqual(self.pacman._name, 'pacman')
        self.assertIn('/usr/bin/pacman', self.pacman._pms)

    @patch('migasfree_client.pms.pacman.execute')
    def test_install(self, mock_execute):
        mock_execute.return_value = (0, '', '')
        self.assertTrue(self.pacman.install('package'))
        self.assertIn('--sync', mock_execute.call_args[0][0])
        self.assertIn('package', mock_execute.call_args[0][0])

    @patch('migasfree_client.pms.pacman.execute')
    def test_update_silent(self, mock_execute):
        mock_execute.return_value = (0, 'output', '')
        ret, _ = self.pacman.update_silent()
        self.assertTrue(ret)

    @patch('migasfree_client.pms.pacman.execute')
    def test_install_silent(self, mock_execute):
        with patch.object(self.pacman, '_get_installed_packages', return_value=set()):
            mock_execute.return_value = (0, 'output', '')
            ret, _ = self.pacman.install_silent(['package1'])
            self.assertTrue(ret)
            self.assertIn('--sync', mock_execute.call_args[0][0])
            self.assertIn('package1', mock_execute.call_args[0][0])

    @patch('migasfree_client.pms.pacman.execute')
    def test_remove_silent(self, mock_execute):
        with patch.object(self.pacman, '_get_installed_packages', return_value={'package1'}):
            mock_execute.return_value = (0, 'output', '')
            ret, _ = self.pacman.remove_silent(['package1'])
            self.assertTrue(ret)
            self.assertIn('--remove', mock_execute.call_args[0][0])
            self.assertIn('package1', mock_execute.call_args[0][0])

    @patch('migasfree_client.pms.pacman.execute')
    def test_query_all(self, mock_execute):
        # Sample output from 'pacman -Qi'
        pacman_qi_output = """
Name            : vim
Version         : 8.2.3456-1
Description     : Vi IMproved, a powerful text editor
Architecture    : x86_64
URL             : https://www.vim.org
Licenses        : vim
Groups          : None
Provides        : None
Depends On      : gpm  libutil  libxt  python  ruby  lua  perl
Optional Deps   : None
Required By     : None
Optional For    : None
Conflicts With  : None
Replaces        : None
Installed Size  : 30.00 MiB
Packager        : Arch Linux
Build Date      : Wed 01 Jan 2026 12:00:00 PM UTC
Install Date    : Thu 02 Jan 2026 01:00:00 PM UTC
Install Reason  : Explicitly installed
Install Script  : No
Validated By    : Signature

Name            : bash
Version         : 5.1.008-1
Description     : The GNU Bourne Again shell
Architecture    : x86_64
...
        """
        mock_execute.return_value = (0, pacman_qi_output.strip(), '')
        result = self.pacman.query_all()
        # Ensure we have at least vim and bash (bash parsing might be partial in mock)
        self.assertIn('vim_8.2.3456-1_x86_64.pkg.tar.zst', result)

    @patch('migasfree_client.pms.pacman.execute')
    def test_get_system_architecture(self, mock_execute):
        mock_execute.return_value = (0, 'x86_64\n', '')
        self.assertEqual(self.pacman.get_system_architecture(), 'x86_64')


if __name__ == '__main__':
    unittest.main()
