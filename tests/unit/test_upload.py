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

import errno
import unittest
from unittest.mock import MagicMock, patch

from migasfree_client.upload import MigasFreeUpload


class TestMigasFreeUpload(unittest.TestCase):
    @patch('migasfree_client.utils.is_root_user', return_value=True)
    @patch('migasfree_client.utils.get_config', return_value={})
    @patch('migasfree_client.command.logging.config.dictConfig')
    def setUp(self, mock_log_config, mock_config, mock_root):
        with patch('migasfree_client.upload.MigasFreeUpload._ssl_cert'), patch(
            'migasfree_client.upload.MigasFreeUpload._init_url_request'
        ):
            self.upload = MigasFreeUpload()
            self.upload.console = MagicMock()
            self.upload.packager_project = 'test-proj'
            self.upload.packager_store = 'test-store'
            self.upload.packager_user = 'test-user'
            self.upload.packager_pwd = 'test-pass'
            self.upload._private_key = 'priv'
            self.upload._public_key = 'pub'

    @patch('os.path.isfile', return_value=True)
    @patch('migasfree_client.upload.build_magic')
    @patch('migasfree_client.upload.MigasFreeUpload._check_sign_keys')
    def test_upload_file_success(self, mock_check, mock_magic, mock_isfile):
        """Test successful single file upload"""
        self.upload._file = 'archive.pkg'
        mock_magic.return_value.file.return_value = 'application/x-debian-package'
        self.upload.pms = MagicMock()
        self.upload.pms._mimetype = ['application/x-debian-package']
        self.upload._url_request = MagicMock()
        self.upload._url_request.run.return_value = {'id': 1}

        with patch.object(self.upload, '_create_repository', return_value=True):
            result = self.upload._upload_file()
            self.assertTrue(result)
            self.upload._url_request.run.assert_called_once()

    @patch('os.path.isfile', return_value=False)
    def test_upload_file_not_found(self, mock_isfile):
        """Test upload fails if file does not exist"""
        self.upload._file = 'missing.pkg'
        with self.assertRaises(SystemExit) as cm:
            self.upload._upload_file()
        self.assertEqual(cm.exception.code, errno.ENOENT)

    @patch('os.path.isdir', return_value=True)
    @patch('os.walk', return_value=[('/dir', [], ['file1.pkg'])])
    @patch('os.path.isfile', return_value=True)
    @patch('migasfree_client.upload.MigasFreeUpload._check_sign_keys')
    def test_upload_set_success(self, mock_check, mock_isfile, mock_walk, mock_isdir):
        """Test successful directory (package set) upload"""
        self.upload._directory = '/dir'
        self.upload._url_request = MagicMock()
        self.upload._url_request.run.return_value = {'id': 1}
        with patch.object(self.upload, '_create_repository', return_value=True):
            result = self.upload._upload_set()
            self.assertTrue(result)
            self.upload._url_request.run.assert_called()

    def test_create_repository_success(self):
        """Test triggering repository creation on server"""
        self.upload._file = 'file.pkg'
        self.upload._url_request = MagicMock()
        self.upload._url_request.run.return_value = {'status': 'ok'}
        result = self.upload._create_repository()
        self.assertTrue(result)
        self.upload._url_request.run.assert_called_once()

    @patch('builtins.input', side_effect=['user', 'proj', 'store'])
    @patch('getpass.getpass', return_value='pass')
    def test_left_parameters(self, mock_getpass, mock_input):
        """Test interactive parameter collection"""
        self.upload.packager_user = None
        self.upload.packager_pwd = None
        self.upload.packager_project = None
        self.upload.packager_store = None
        self.upload._left_parameters()
        self.assertEqual(self.upload.packager_user, 'user')
        self.assertEqual(self.upload.packager_pwd, 'pass')

    @patch('sys.exit')
    @patch('migasfree_client.upload.lock_file_context')
    def test_run_file_upload(self, mock_lock, mock_exit):
        """Test CLI run dispatch for file upload"""
        args = MagicMock()
        args.file = 'test.pkg'
        args.dir = None
        args.user = 'u'
        args.pwd = 'p'
        args.project = 'pr'
        args.store = 'st'

        with patch.object(self.upload, '_upload_file') as mock_up:
            self.upload.run(args)
            mock_up.assert_called_once()
            self.assertEqual(self.upload.packager_user, 'u')


if __name__ == '__main__':
    unittest.main()
