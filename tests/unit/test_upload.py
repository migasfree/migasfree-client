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

"""
Tests for package upload functionality using MigasFreeUpload class.
"""

import unittest
from unittest.mock import MagicMock, patch

from migasfree_client.upload import MigasFreeUpload


class TestMigasFreeUpload(unittest.TestCase):
    """Tests for MigasFreeUpload class"""

    @patch('migasfree_client.utils.is_root_user', return_value=True)
    @patch('migasfree_client.utils.get_config', return_value={})
    @patch('migasfree_client.command.logging.config.dictConfig')
    def setUp(self, mock_log_config, mock_config, mock_root):
        with patch('migasfree_client.utils.get_mfc_project', return_value='test-project'), patch(
            'migasfree_client.utils.get_mfc_computer_name', return_value='test-computer'
        ):
            self.upload = MigasFreeUpload()
            self.upload._url_request = MagicMock()
            self.upload._init_url_request = MagicMock()
            self.upload._init_mtls = MagicMock()

    @patch('builtins.input', side_effect=['user', 'project', 'store'])
    @patch('getpass.getpass', return_value='password')
    def test_left_parameters(self, mock_getpass, mock_input):
        """Test prompted parameters when not provided"""
        self.upload.packager_user = None
        self.upload.packager_pwd = None
        self.upload.packager_project = None
        self.upload.packager_store = None

        self.upload._left_parameters()

        self.assertEqual(self.upload.packager_user, 'user')
        self.assertEqual(self.upload.packager_pwd, 'password')
        self.assertEqual(self.upload.packager_project, 'project')
        self.assertEqual(self.upload.packager_store, 'store')

    @patch('os.path.isfile', return_value=True)
    @patch('migasfree_client.upload.build_magic')
    @patch('migasfree_client.upload.MigasFreeUpload._check_sign_keys')
    @patch('migasfree_client.upload.MigasFreeUpload._create_repository', return_value=True)
    def test_upload_file_success(self, mock_create, mock_keys, mock_magic, mock_exists):
        """Test successful file upload"""
        self.upload._file = 'test.pkg'
        self.upload.packager_project = 'test-proj'
        self.upload.packager_store = 'test-store'
        self.upload._url_request.run.return_value = {'status': 'ok'}

        result = self.upload._upload_file()

        self.assertTrue(result)
        self.upload._url_request.run.assert_called_once()
        _args, kwargs = self.upload._url_request.run.call_args
        self.assertEqual(kwargs['data']['project'], 'test-proj')
        self.assertIn('test.pkg', kwargs['upload_files'][0])

    @patch('os.path.isdir', return_value=True)
    @patch('os.walk')
    @patch('os.path.isfile', return_value=True)
    @patch('migasfree_client.upload.MigasFreeUpload._check_sign_keys')
    @patch('migasfree_client.upload.MigasFreeUpload._create_repository', return_value=True)
    def test_upload_set_success(self, mock_create, mock_keys, mock_isfile, mock_walk, mock_isdir):
        """Test successful directory (set) upload"""
        self.upload._directory = '/tmp/test_dir'
        mock_walk.return_value = [('/tmp/test_dir', ['subdir'], ['pkg1.pkg', 'pkg2.pkg'])]
        self.upload._url_request.run.return_value = {'status': 'ok'}

        result = self.upload._upload_set()

        self.assertTrue(result)
        # Should call run twice (one for each file)
        self.assertEqual(self.upload._url_request.run.call_count, 2)

    def test_create_repository_success(self):
        """Test successful repository creation API call"""
        self.upload._file = 'test.pkg'
        self.upload.packager_project = 'test-proj'
        self.upload._url_request.run.return_value = {'status': 'ok'}

        result = self.upload._create_repository()

        self.assertTrue(result)
        self.upload._url_request.run.assert_called_once()
        _args, kwargs = self.upload._url_request.run.call_args
        self.assertEqual(kwargs['url'], self.upload.api_endpoint(self.upload.URLS['create_repository']))


if __name__ == '__main__':
    unittest.main()
