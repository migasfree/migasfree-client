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

from migasfree_client.pms.apt import Apt


class TestApt(unittest.TestCase):
    def setUp(self):
        self.apt = Apt()

    def test_init(self):
        self.assertEqual(self.apt._name, 'apt')
        self.assertEqual(self.apt._pm, '/usr/bin/dpkg')
        self.assertEqual(self.apt._pms, 'DEBIAN_FRONTEND=noninteractive /usr/bin/apt-get')
        self.assertEqual(self.apt._repo_dir, '/etc/apt/sources.list.d')
        self.assertEqual(self.apt._keyring_dir, '/etc/apt/trusted.gpg.d')

    @patch('migasfree_client.pms.apt.execute')
    def test_install(self, mock_execute):
        mock_execute.return_value = (0, '', '')
        self.assertTrue(self.apt.install('package'))
        mock_execute.assert_called_with(
            'DEBIAN_FRONTEND=noninteractive /usr/bin/apt-get install -o APT::Get::Purge=true package'
        )

    @patch('migasfree_client.pms.apt.execute')
    def test_install_with_whitespace(self, mock_execute):
        mock_execute.return_value = (0, '', '')
        self.assertTrue(self.apt.install('  package  '))
        mock_execute.assert_called_with(
            'DEBIAN_FRONTEND=noninteractive /usr/bin/apt-get install -o APT::Get::Purge=true package'
        )

    @patch('migasfree_client.pms.apt.execute')
    def test_install_failure(self, mock_execute):
        mock_execute.return_value = (1, '', 'error')
        self.assertFalse(self.apt.install('package'))

    @patch('migasfree_client.pms.apt.execute')
    def test_remove(self, mock_execute):
        mock_execute.return_value = (0, '', '')
        self.assertTrue(self.apt.remove('package'))
        mock_execute.assert_called_with('DEBIAN_FRONTEND=noninteractive /usr/bin/apt-get purge package')

    @patch('migasfree_client.pms.apt.execute')
    def test_remove_failure(self, mock_execute):
        mock_execute.return_value = (1, '', 'error')
        self.assertFalse(self.apt.remove('package'))

    @patch('migasfree_client.pms.apt.execute')
    def test_search(self, mock_execute):
        mock_execute.return_value = (0, 'package - description', '')
        self.assertTrue(self.apt.search('pattern'))
        mock_execute.assert_called_with('/usr/bin/apt-cache search pattern')

    @patch('migasfree_client.pms.apt.execute')
    def test_search_not_found(self, mock_execute):
        mock_execute.return_value = (1, '', '')
        self.assertFalse(self.apt.search('nonexistent'))

    @patch('migasfree_client.pms.apt.execute')
    def test_update_silent(self, mock_execute):
        mock_execute.return_value = (0, 'output', '')
        ret, error = self.apt.update_silent()
        self.assertTrue(ret)
        self.assertEqual(error, 'output')
        self.assertIn('dist-upgrade', mock_execute.call_args[0][0])

    @patch('migasfree_client.pms.apt.execute')
    def test_update_silent_failure(self, mock_execute):
        mock_execute.return_value = (1, '', 'error')
        ret, error = self.apt.update_silent()
        self.assertFalse(ret)
        self.assertEqual(error, 'error')

    @patch('migasfree_client.pms.apt.execute')
    def test_install_silent(self, mock_execute):
        with patch.object(self.apt, 'is_installed', return_value=False):
            mock_execute.return_value = (0, 'output', '')
            ret, _ = self.apt.install_silent(['package1', 'package2'])
            self.assertTrue(ret)
            self.assertIn('install', mock_execute.call_args[0][0])
            self.assertIn('package1', mock_execute.call_args[0][0])
            self.assertIn('package2', mock_execute.call_args[0][0])

    @patch('migasfree_client.pms.apt.execute')
    def test_install_silent_already_installed(self, mock_execute):
        with patch.object(self.apt, 'is_installed', return_value=True):
            ret, error = self.apt.install_silent(['package'])
            self.assertTrue(ret)
            self.assertIsNone(error)
            mock_execute.assert_not_called()

    def test_install_silent_invalid_input(self):
        ret, error = self.apt.install_silent('not_a_list')
        self.assertFalse(ret)
        self.assertIn('not a list', error)

    @patch('migasfree_client.pms.apt.execute')
    def test_remove_silent(self, mock_execute):
        with patch.object(self.apt, 'is_installed', return_value=True):
            mock_execute.return_value = (0, 'output', '')
            ret, _ = self.apt.remove_silent(['package1', 'package2'])
            self.assertTrue(ret)
            self.assertIn('purge', mock_execute.call_args[0][0])
            self.assertIn('package1', mock_execute.call_args[0][0])
            self.assertIn('package2', mock_execute.call_args[0][0])

    @patch('migasfree_client.pms.apt.execute')
    def test_remove_silent_not_installed(self, mock_execute):
        with patch.object(self.apt, 'is_installed', return_value=False):
            ret, error = self.apt.remove_silent(['package'])
            self.assertTrue(ret)
            self.assertIsNone(error)
            mock_execute.assert_not_called()

    def test_remove_silent_invalid_input(self):
        ret, error = self.apt.remove_silent('not_a_list')
        self.assertFalse(ret)
        self.assertIn('not a list', error)

    @patch('migasfree_client.pms.apt.execute')
    def test_is_installed_true(self, mock_execute):
        mock_execute.return_value = (0, 'Status: install ok installed', '')
        self.assertTrue(self.apt.is_installed('package'))
        self.assertIn('--status', mock_execute.call_args[0][0])
        self.assertIn('package', mock_execute.call_args[0][0])

    @patch('migasfree_client.pms.apt.execute')
    def test_is_installed_false(self, mock_execute):
        mock_execute.return_value = (1, '', '')
        self.assertFalse(self.apt.is_installed('package'))

    @patch('migasfree_client.pms.apt.execute')
    def test_clean_all_success(self, mock_execute):
        mock_execute.side_effect = [
            (0, '', ''),  # apt-get clean
            (0, '', ''),  # rm
            (0, '', ''),  # apt-get update
        ]
        self.assertTrue(self.apt.clean_all())
        self.assertEqual(mock_execute.call_count, 3)

    @patch('migasfree_client.pms.apt.execute')
    def test_clean_all_clean_failure(self, mock_execute):
        mock_execute.return_value = (1, '', 'error')
        self.assertFalse(self.apt.clean_all())
        self.assertEqual(mock_execute.call_count, 1)

    @patch('migasfree_client.pms.apt.execute')
    def test_query_all(self, mock_execute):
        mock_execute.return_value = (
            0,
            'ii  package1  1.0  amd64  description\nii  package2  2.0  i386  description',
            '',
        )
        result = self.apt.query_all()
        self.assertEqual(result, ['package1_1.0_amd64.deb', 'package2_2.0_i386.deb'])

    @patch('migasfree_client.pms.apt.execute')
    def test_query_all_empty(self, mock_execute):
        mock_execute.return_value = (0, '', '')
        result = self.apt.query_all()
        self.assertEqual(result, [])

    @patch('migasfree_client.pms.apt.execute')
    def test_query_all_with_non_matching_lines(self, mock_execute):
        mock_execute.return_value = (
            0,
            'Desired=Unknown/Install/Remove/Purge/Hold\nii  package1  1.0  amd64  description',
            '',
        )
        result = self.apt.query_all()
        self.assertEqual(result, ['package1_1.0_amd64.deb'])

    @patch('migasfree_client.pms.apt.execute')
    def test_import_server_key(self, mock_execute):
        mock_execute.return_value = (0, '', '')
        self.assertTrue(self.apt.import_server_key('/path/to/key.asc'))
        self.assertIn('gpg', mock_execute.call_args[0][0])
        self.assertIn('--dearmor', mock_execute.call_args[0][0])
        self.assertIn('/path/to/key.asc', mock_execute.call_args[0][0])

    @patch('migasfree_client.pms.apt.execute')
    def test_import_server_key_failure(self, mock_execute):
        mock_execute.return_value = (1, '', 'gpg error')
        self.assertFalse(self.apt.import_server_key('/path/to/key.asc'))

    @patch('migasfree_client.pms.apt.execute')
    def test_get_system_architecture(self, mock_execute):
        mock_execute.return_value = (0, 'amd64 i386', '')
        result = self.apt.get_system_architecture()
        self.assertEqual(result, 'amd64 i386')

    @patch('migasfree_client.pms.apt.execute')
    def test_get_system_architecture_failure(self, mock_execute):
        mock_execute.return_value = (1, '', 'error')
        result = self.apt.get_system_architecture()
        self.assertEqual(result, '')

    @patch('migasfree_client.pms.apt.execute')
    def test_available_packages(self, mock_execute):
        mock_execute.return_value = (0, 'vim\nbash\ngit', '')
        result = self.apt.available_packages()
        self.assertEqual(result, ['bash', 'git', 'vim'])  # sorted
        mock_execute.assert_called_with('/usr/bin/apt-cache pkgnames', interactive=False)

    @patch('migasfree_client.pms.apt.execute')
    def test_available_packages_failure(self, mock_execute):
        mock_execute.return_value = (1, '', 'error')
        result = self.apt.available_packages()
        self.assertEqual(result, [])

    @patch('migasfree_client.pms.apt.write_file')
    @patch('migasfree_client.pms.apt.execute')
    def test_create_repos_empty(self, mock_execute, mock_write_file):
        result = self.apt.create_repos('https', 'server.example.com', [])
        self.assertTrue(result)
        mock_write_file.assert_not_called()

    @patch('migasfree_client.pms.apt.write_file')
    @patch('migasfree_client.pms.apt.execute')
    def test_create_repos_apt2(self, mock_execute, mock_write_file):
        mock_execute.return_value = (0, '2.4.11', '')
        mock_write_file.return_value = True

        repos = [{'source_template': 'deb {protocol}://{server}/repo stable main'}]
        result = self.apt.create_repos('https', 'server.example.com', repos)

        self.assertTrue(result)
        mock_write_file.assert_called_once()
        call_args = mock_write_file.call_args[0]
        self.assertIn('migasfree.list', call_args[0])
        self.assertIn('deb https://server.example.com/repo stable main', call_args[1])

    def test_adapt_sources_adds_signed_by(self):
        sources_content = 'Types: deb\nURIs: http://example.com'
        result = self.apt._adapt_sources(sources_content, 'server.example.com')
        self.assertIn('Signed-By:', result)
        self.assertIn('server.example.com.gpg', result)

    def test_adapt_sources_replaces_empty_signed_by(self):
        sources_content = 'Types: deb\nURIs: http://example.com\nSigned-By:'
        result = self.apt._adapt_sources(sources_content, 'server.example.com')
        self.assertIn('Signed-By: /etc/apt/trusted.gpg.d/server.example.com.gpg', result)

    def test_adapt_sources_preserves_existing_signed_by(self):
        sources_content = 'Types: deb\nURIs: http://example.com\nSigned-By: /path/to/key.gpg'
        result = self.apt._adapt_sources(sources_content, 'server.example.com')
        self.assertIn('Signed-By: /path/to/key.gpg', result)

    @patch('migasfree_client.pms.apt.execute')
    def test_get_pms_version_success(self, mock_execute):
        mock_execute.return_value = (0, '2.4.11', '')
        result = self.apt._get_pms_version()
        self.assertEqual(result, (2, 4, 11))

    @patch('migasfree_client.pms.apt.execute')
    def test_get_pms_version_apt3(self, mock_execute):
        mock_execute.return_value = (0, '3.0.0', '')
        result = self.apt._get_pms_version()
        self.assertEqual(result, (3, 0, 0))

    @patch('migasfree_client.pms.apt.execute')
    def test_get_pms_version_failure(self, mock_execute):
        mock_execute.return_value = (1, '', 'error')
        result = self.apt._get_pms_version()
        self.assertEqual(result, (2, 0))

    @patch('migasfree_client.pms.apt.execute')
    def test_get_pms_version_invalid_format(self, mock_execute):
        mock_execute.return_value = (0, 'invalid', '')
        result = self.apt._get_pms_version()
        self.assertEqual(result, (2, 0))

    @patch('migasfree_client.pms.apt.execute')
    def test_get_pms_version_two_parts(self, mock_execute):
        mock_execute.return_value = (0, '2.4', '')
        result = self.apt._get_pms_version()
        self.assertEqual(result, (2, 4))


if __name__ == '__main__':
    unittest.main()
