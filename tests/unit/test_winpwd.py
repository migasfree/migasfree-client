import os

# Mock the windows specific modules before importing winpwd
import sys
import unittest
from unittest.mock import MagicMock, patch


class Win32NetError(Exception):
    pass


win32net_mock = MagicMock()
win32net_mock.error = Win32NetError
sys.modules['win32api'] = MagicMock()
sys.modules['win32net'] = win32net_mock
sys.modules['win32security'] = MagicMock()

from migasfree_client.winpwd import getpwall, getpwnam, getpwuid, struct_passwd  # noqa: E402


class TestWinPwd(unittest.TestCase):
    def test_struct_passwd_iteration(self):
        passwd = struct_passwd('user', 'pass', 'uid', 'gid', 'gecos', 'dir', 'shell')
        items = list(passwd)
        self.assertEqual(items, ['user', 'pass', 'uid', 'gid', 'gecos', 'dir', 'shell'])
        self.assertEqual(passwd[0], 'user')
        self.assertEqual(passwd.pw_name, 'user')

    @patch('win32security.LookupAccountName')
    @patch('win32security.ConvertSidToStringSid')
    def test_get_user_sid(self, mock_convert, mock_lookup):
        from migasfree_client.winpwd import _get_user_sid

        mock_convert.return_value = 'S-1-5-21-XXX'
        mock_lookup.return_value = ('sid_obj', 'domain', 'type')

        result = _get_user_sid('testuser')
        self.assertEqual(result, 'S-1-5-21-XXX')

    @patch('win32security.ConvertStringSidToSid')
    @patch('win32security.LookupAccountSid')
    def test_get_username_from_sid(self, mock_lookup, mock_convert):
        from migasfree_client.winpwd import _get_username_from_sid

        mock_lookup.return_value = ('testuser', 'domain', 'type')

        result = _get_username_from_sid('S-1-5-21-XXX')
        self.assertEqual(result, 'testuser')

    def test_get_user_home(self):
        from migasfree_client.winpwd import _get_user_home

        with patch.dict(os.environ, {'USERNAME': 'testuser', 'USERPROFILE': 'C:\\Users\\testuser'}):
            self.assertEqual(_get_user_home('testuser'), 'C:\\Users\\testuser')
            # On Linux, os.path.dirname('C:\\Users') is '' because \ is not a separator
            # So os.path.join('', 'other') is 'other'
            import platform

            if platform.system() != 'Windows':
                self.assertEqual(_get_user_home('other'), 'other')
            else:
                self.assertEqual(_get_user_home('other'), 'C:\\Users\\other')

    @patch('migasfree_client.winpwd._get_username_from_sid', return_value='testuser')
    @patch('migasfree_client.winpwd.getpwnam')
    def test_getpwuid_sid_string(self, mock_getpwnam, mock_get_username):
        getpwuid('S-1-5-21-XXX')
        mock_getpwnam.assert_called_with('testuser')

    @patch('win32api.GetUserName', return_value='current')
    @patch('migasfree_client.winpwd.getpwnam')
    def test_getpwuid_int(self, mock_getpwnam, mock_get_username):
        getpwuid(1000)
        mock_getpwnam.assert_called_with('current')

    @patch('win32net.NetUserGetInfo')
    @patch('migasfree_client.winpwd._get_user_sid', return_value='S-1-2-3')
    def test_getpwnam_success(self, mock_sid, mock_getinfo):
        mock_getinfo.return_value = {'name': 'testuser', 'full_name': 'Test User'}
        res = getpwnam('testuser')
        self.assertEqual(res.pw_name, 'testuser')
        self.assertEqual(res.pw_gecos, 'Test User')

    @patch('win32net.NetUserGetInfo')
    @patch('migasfree_client.winpwd._get_user_sid', return_value=None)
    def test_getpwnam_failure(self, mock_sid, mock_getinfo):
        from win32net import error

        mock_getinfo.side_effect = error('User not found')
        with self.assertRaises(KeyError):
            getpwnam('nonexistent')

    @patch('win32net.NetUserEnum')
    @patch('migasfree_client.winpwd.getpwnam')
    def test_getpwall(self, mock_getpwnam, mock_enum):
        mock_enum.return_value = ([{'name': 'u1'}, {'name': 'u2'}], 2, 0)
        mock_getpwnam.side_effect = lambda x: struct_passwd(x, 'x', 's', '', '', '', '')

        users = getpwall()
        self.assertEqual(len(users), 2)
        self.assertEqual(users[0].pw_name, 'u1')


if __name__ == '__main__':
    unittest.main()
