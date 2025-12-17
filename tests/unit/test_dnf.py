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
from unittest.mock import patch

from migasfree_client.pms.dnf import Dnf


class TestDnf(unittest.TestCase):
    def setUp(self):
        self.dnf = Dnf()

    def test_init(self):
        self.assertEqual(self.dnf._name, 'dnf')
        self.assertEqual(self.dnf._pms, '/usr/bin/dnf')
        self.assertEqual(self.dnf._pm, '/bin/rpm')

    @patch('migasfree_client.pms.yum.execute')
    def test_install(self, mock_execute):
        mock_execute.return_value = (0, '', '')
        self.assertTrue(self.dnf.install('package'))
        mock_execute.assert_called_with('/usr/bin/dnf install package')

    @patch('migasfree_client.pms.yum.execute')
    def test_install_with_whitespace(self, mock_execute):
        mock_execute.return_value = (0, '', '')
        self.assertTrue(self.dnf.install('  package  '))
        mock_execute.assert_called_with('/usr/bin/dnf install package')

    @patch('migasfree_client.pms.yum.execute')
    def test_install_failure(self, mock_execute):
        mock_execute.return_value = (1, '', 'error')
        self.assertFalse(self.dnf.install('package'))

    @patch('migasfree_client.pms.yum.execute')
    def test_remove(self, mock_execute):
        mock_execute.return_value = (0, '', '')
        self.assertTrue(self.dnf.remove('package'))
        mock_execute.assert_called_with('/usr/bin/dnf remove package')

    @patch('migasfree_client.pms.yum.execute')
    def test_remove_failure(self, mock_execute):
        mock_execute.return_value = (1, '', 'error')
        self.assertFalse(self.dnf.remove('package'))

    @patch('migasfree_client.pms.yum.execute')
    def test_search(self, mock_execute):
        mock_execute.return_value = (0, 'package - description', '')
        self.assertTrue(self.dnf.search('pattern'))
        mock_execute.assert_called_with('/usr/bin/dnf search pattern')

    @patch('migasfree_client.pms.yum.execute')
    def test_search_not_found(self, mock_execute):
        mock_execute.return_value = (1, '', '')
        self.assertFalse(self.dnf.search('nonexistent'))

    @patch('migasfree_client.pms.yum.execute')
    def test_update_silent(self, mock_execute):
        mock_execute.return_value = (0, 'output', '')
        ret, _ = self.dnf.update_silent()
        self.assertTrue(ret)
        self.assertIn('--assumeyes update', mock_execute.call_args[0][0])

    @patch('migasfree_client.pms.yum.execute')
    def test_update_silent_failure(self, mock_execute):
        mock_execute.return_value = (1, '', 'error')
        ret, error = self.dnf.update_silent()
        self.assertFalse(ret)
        self.assertEqual(error, 'error')

    @patch('migasfree_client.pms.yum.execute')
    def test_install_silent(self, mock_execute):
        with patch.object(self.dnf, 'is_installed', return_value=False):
            mock_execute.return_value = (0, 'output', '')
            ret, _ = self.dnf.install_silent(['package1', 'package2'])
            self.assertTrue(ret)
            self.assertIn('install', mock_execute.call_args[0][0])
            self.assertIn('package1', mock_execute.call_args[0][0])
            self.assertIn('package2', mock_execute.call_args[0][0])

    @patch('migasfree_client.pms.yum.execute')
    def test_install_silent_already_installed(self, mock_execute):
        with patch.object(self.dnf, 'is_installed', return_value=True):
            ret, error = self.dnf.install_silent(['package'])
            self.assertTrue(ret)
            self.assertIsNone(error)
            mock_execute.assert_not_called()

    def test_install_silent_invalid_input(self):
        ret, error = self.dnf.install_silent('not_a_list')
        self.assertFalse(ret)
        self.assertIn('not a list', error)

    @patch('migasfree_client.pms.yum.execute')
    def test_remove_silent(self, mock_execute):
        with patch.object(self.dnf, 'is_installed', return_value=True):
            mock_execute.return_value = (0, 'output', '')
            ret, _ = self.dnf.remove_silent(['package1', 'package2'])
            self.assertTrue(ret)
            self.assertIn('remove', mock_execute.call_args[0][0])
            self.assertIn('package1', mock_execute.call_args[0][0])
            self.assertIn('package2', mock_execute.call_args[0][0])

    @patch('migasfree_client.pms.yum.execute')
    def test_remove_silent_not_installed(self, mock_execute):
        with patch.object(self.dnf, 'is_installed', return_value=False):
            ret, error = self.dnf.remove_silent(['package'])
            self.assertTrue(ret)
            self.assertIsNone(error)
            mock_execute.assert_not_called()

    def test_remove_silent_invalid_input(self):
        ret, error = self.dnf.remove_silent('not_a_list')
        self.assertFalse(ret)
        self.assertIn('not a list', error)

    @patch('migasfree_client.pms.yum.execute')
    def test_is_installed_true(self, mock_execute):
        mock_execute.return_value = (0, 'package-1.0-1.x86_64', '')
        self.assertTrue(self.dnf.is_installed('package'))
        self.assertIn('-q', mock_execute.call_args[0][0])
        self.assertIn('package', mock_execute.call_args[0][0])

    @patch('migasfree_client.pms.yum.execute')
    def test_is_installed_false(self, mock_execute):
        mock_execute.return_value = (1, '', '')
        self.assertFalse(self.dnf.is_installed('package'))

    @patch('migasfree_client.pms.yum.execute')
    def test_clean_all_success(self, mock_execute):
        mock_execute.side_effect = [
            (0, '', ''),  # dnf clean all
            (0, '', ''),  # dnf check-update (no updates)
        ]
        self.assertTrue(self.dnf.clean_all())
        self.assertEqual(mock_execute.call_count, 2)

    @patch('migasfree_client.pms.yum.execute')
    def test_clean_all_with_updates_available(self, mock_execute):
        mock_execute.side_effect = [
            (0, '', ''),  # dnf clean all
            (100, '', ''),  # dnf check-update (updates available, exit code 100)
        ]
        self.assertTrue(self.dnf.clean_all())

    @patch('migasfree_client.pms.yum.execute')
    def test_clean_all_failure(self, mock_execute):
        mock_execute.return_value = (1, '', 'error')
        self.assertFalse(self.dnf.clean_all())
        self.assertEqual(mock_execute.call_count, 1)

    @patch('migasfree_client.pms.yum.execute')
    def test_query_all(self, mock_execute):
        mock_execute.return_value = (
            0,
            'vim_8.2-1_x86_64.rpm\nbash_5.0-1_x86_64.rpm',
            '',
        )
        result = self.dnf.query_all()
        self.assertEqual(result, ['bash_5.0-1_x86_64.rpm', 'vim_8.2-1_x86_64.rpm'])  # sorted

    @patch('migasfree_client.pms.yum.execute')
    def test_query_all_empty(self, mock_execute):
        mock_execute.return_value = (0, '', '')
        result = self.dnf.query_all()
        self.assertEqual(result, [])

    @patch('migasfree_client.pms.yum.execute')
    def test_query_all_failure(self, mock_execute):
        mock_execute.return_value = (1, '', 'error')
        result = self.dnf.query_all()
        self.assertEqual(result, [])

    @patch('migasfree_client.pms.yum.execute')
    def test_import_server_key(self, mock_execute):
        mock_execute.return_value = (0, '', '')
        self.assertTrue(self.dnf.import_server_key('/path/to/key'))
        self.assertIn('--import', mock_execute.call_args[0][0])
        self.assertIn('/path/to/key', mock_execute.call_args[0][0])

    @patch('migasfree_client.pms.yum.execute')
    def test_import_server_key_failure(self, mock_execute):
        mock_execute.return_value = (1, '', 'error')
        self.assertFalse(self.dnf.import_server_key('/path/to/key'))

    @patch('migasfree_client.pms.yum.execute')
    def test_get_system_architecture(self, mock_execute):
        mock_execute.return_value = (0, 'x86_64\n', '')
        result = self.dnf.get_system_architecture()
        self.assertEqual(result, 'x86_64')

    @patch('migasfree_client.pms.yum.execute')
    def test_get_system_architecture_failure(self, mock_execute):
        mock_execute.return_value = (1, '', 'error')
        result = self.dnf.get_system_architecture()
        self.assertEqual(result, '')

    @patch('migasfree_client.pms.yum.execute')
    def test_available_packages(self, mock_execute):
        mock_execute.return_value = (0, 'vim\nbash\ngit', '')
        result = self.dnf.available_packages()
        self.assertEqual(result, ['bash', 'git', 'vim'])  # sorted

    @patch('migasfree_client.pms.yum.execute')
    def test_available_packages_failure(self, mock_execute):
        mock_execute.return_value = (1, '', 'error')
        result = self.dnf.available_packages()
        self.assertEqual(result, [])

    @patch('migasfree_client.pms.yum.write_file')
    def test_create_repos_empty(self, mock_write_file):
        result = self.dnf.create_repos('https', 'server.example.com', [])
        self.assertTrue(result)
        mock_write_file.assert_not_called()

    @patch('migasfree_client.pms.yum.write_file')
    def test_create_repos(self, mock_write_file):
        mock_write_file.return_value = True

        repos = [{'source_template': '[migasfree]\nbaseurl={protocol}://{server}/repo'}]
        result = self.dnf.create_repos('https', 'server.example.com', repos)

        self.assertTrue(result)
        mock_write_file.assert_called_once()
        call_args = mock_write_file.call_args[0]
        self.assertIn('migasfree.repo', call_args[0])
        self.assertIn('[migasfree]', call_args[1])
        self.assertIn('https://server.example.com/repo', call_args[1])


if __name__ == '__main__':
    unittest.main()
