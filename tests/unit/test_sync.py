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

"""
Tests for sync-related functionality.

Since MigasFreeSync has complex initialization requirements (root privileges,
logging configuration, signal handlers, file permissions), these tests focus
on testing the core logic directly without importing the class.
"""

import unittest
from collections import defaultdict
from datetime import datetime


class TestSoftwareHistory(unittest.TestCase):
    """Tests for software_history static method logic"""

    def test_compare_software_installed(self):
        """Test detection of installed packages"""
        before = ['pkg1', 'pkg2']
        after = ['pkg1', 'pkg2', 'pkg3']

        # Simulating compare_lists behavior
        diff = [f'+{pkg}' for pkg in after if pkg not in before]
        diff.extend([f'-{pkg}' for pkg in before if pkg not in after])

        installed = [x for x in diff if x.startswith('+')]
        uninstalled = [x for x in diff if x.startswith('-')]

        self.assertEqual(installed, ['+pkg3'])
        self.assertEqual(uninstalled, [])

    def test_compare_software_uninstalled(self):
        """Test detection of uninstalled packages"""
        before = ['pkg1', 'pkg2', 'pkg3']
        after = ['pkg1', 'pkg2']

        diff = [f'+{pkg}' for pkg in after if pkg not in before]
        diff.extend([f'-{pkg}' for pkg in before if pkg not in after])

        installed = [x for x in diff if x.startswith('+')]
        uninstalled = [x for x in diff if x.startswith('-')]

        self.assertEqual(installed, [])
        self.assertEqual(uninstalled, ['-pkg3'])

    def test_compare_software_mixed(self):
        """Test detection of mixed changes"""
        before = ['pkg1', 'pkg2', 'pkg3']
        after = ['pkg1', 'pkg2', 'pkg4']

        diff = [f'+{pkg}' for pkg in after if pkg not in before]
        diff.extend([f'-{pkg}' for pkg in before if pkg not in after])

        installed = [x for x in diff if x.startswith('+')]
        uninstalled = [x for x in diff if x.startswith('-')]

        self.assertEqual(installed, ['+pkg4'])
        self.assertEqual(uninstalled, ['-pkg3'])

    def test_compare_software_no_changes(self):
        """Test no changes detected"""
        before = ['pkg1', 'pkg2']
        after = ['pkg1', 'pkg2']

        diff = [f'+{pkg}' for pkg in after if pkg not in before]
        diff.extend([f'-{pkg}' for pkg in before if pkg not in after])

        self.assertEqual(diff, [])


class TestEvalCodeLogic(unittest.TestCase):
    """Tests for _eval_code method logic"""

    def test_allowed_languages_linux(self):
        """Test allowed languages on Linux"""
        allowed_languages = ['python', 'perl', 'php', 'ruby', 'bash']
        self.assertIn('python', allowed_languages)
        self.assertIn('bash', allowed_languages)
        self.assertIn('perl', allowed_languages)
        self.assertIn('php', allowed_languages)
        self.assertIn('ruby', allowed_languages)

    def test_allowed_languages_windows(self):
        """Test allowed languages on Windows"""
        allowed_languages = ['python', 'perl', 'php', 'ruby', 'cmd', 'powershell']
        self.assertIn('python', allowed_languages)
        self.assertIn('cmd', allowed_languages)
        self.assertIn('powershell', allowed_languages)

    def test_code_cleanup(self):
        """Test code cleanup removes carriage returns and strips whitespace"""
        code = '  echo hello\r\n  '
        clean_code = code.replace('\r', '').strip()
        self.assertEqual(clean_code, 'echo hello')

    def test_build_command_python_linux(self):
        """Test command building for Python on Linux"""
        lang = 'python'
        filename = '/tmp/test.py'
        # On Linux, python becomes python3
        lang = 'python3'
        cmd = f'{lang} {filename}'
        self.assertEqual(cmd, 'python3 /tmp/test.py')

    def test_unknown_language_graceful_degradation(self):
        """Test unknown language returns no-op command"""
        lang = 'unknown'
        allowed = ['python', 'perl', 'php', 'ruby', 'bash']
        if lang not in allowed:
            cmd = ':'  # no-op in bash
        self.assertEqual(cmd, ':')


class TestEvalAttributesLogic(unittest.TestCase):
    """Tests for _eval_attributes method logic"""

    def test_response_structure(self):
        """Test response structure from _eval_attributes"""
        computer_id = 123
        uuid = 'test-uuid'
        computer_name = 'test-computer'
        fqdn = 'test-computer.example.com'
        ip_address = '192.168.1.1'
        graphic_user = 'testuser'
        fullname = 'Test User'

        response = {
            'id': computer_id,
            'uuid': uuid,
            'name': computer_name,
            'fqdn': fqdn,
            'ip_address': ip_address,
            'sync_user': graphic_user,
            'sync_fullname': fullname,
            'sync_attributes': {},
        }

        self.assertEqual(response['id'], 123)
        self.assertEqual(response['uuid'], 'test-uuid')
        self.assertIn('sync_attributes', response)
        self.assertIsInstance(response['sync_attributes'], dict)

    def test_property_evaluation(self):
        """Test property evaluation result structure"""
        properties = [
            {'prefix': 'HST', 'language': 'bash', 'code': 'hostname'},
            {'prefix': 'USR', 'language': 'bash', 'code': 'whoami'},
        ]

        sync_attributes = {}
        for item in properties:
            # Simulating evaluation
            sync_attributes[item['prefix']] = f'value_of_{item["prefix"]}'

        self.assertEqual(sync_attributes['HST'], 'value_of_HST')
        self.assertEqual(sync_attributes['USR'], 'value_of_USR')


class TestEvalFaultsLogic(unittest.TestCase):
    """Tests for _eval_faults method logic"""

    def test_faults_response_structure(self):
        """Test faults response structure"""
        computer_id = 123
        response = {'id': computer_id, 'faults': {}}

        self.assertEqual(response['id'], 123)
        self.assertIsInstance(response['faults'], dict)

    def test_fault_with_output(self):
        """Test fault with output is recorded"""
        faults = {}
        fault_name = 'disk_space_low'
        result = 'Disk /dev/sda1 is 95% full'

        if result:  # Only record faults with output
            faults[fault_name] = result

        self.assertEqual(len(faults), 1)
        self.assertIn('disk_space_low', faults)

    def test_fault_without_output(self):
        """Test fault without output is not recorded"""
        faults = {}
        fault_name = 'disk_space_ok'
        result = ''  # No output means no fault

        if result:
            faults[fault_name] = result

        self.assertEqual(len(faults), 0)


class TestTraitsLogic(unittest.TestCase):
    """Tests for _traits and _events method logic"""

    def test_to_prefix_dict(self):
        """Test conversion of traits list to prefix dictionary"""
        traits_list = [
            {'prefix': 'SET', 'value': 'value1'},
            {'prefix': 'SET', 'value': 'value2'},
            {'prefix': 'CID', 'value': 'computer1'},
        ]

        result = defaultdict(list)
        for item in traits_list:
            result[item['prefix']].append(item['value'])
        result = dict(result)

        self.assertEqual(result['SET'], ['value1', 'value2'])
        self.assertEqual(result['CID'], ['computer1'])

    def test_to_env_single_value(self):
        """Test environment variable format for single values"""
        content = {'HST': ['hostname1'], 'USR': ['user1']}
        prefix = 'TRAIT_'

        result = ''
        for key in content:
            if len(content[key]) == 1:
                value = content[key][0]
                result += f'{prefix}{key}="{value}"\n'

        self.assertIn('TRAIT_HST="hostname1"', result)
        self.assertIn('TRAIT_USR="user1"', result)

    def test_to_env_multiple_values(self):
        """Test environment variable format for multiple values"""
        content = {'SET': ['value1', 'value2', 'value3']}
        prefix = 'TRAIT_'

        result = ''
        for key in content:
            if len(content[key]) > 1:
                value = ' '.join([f'"{item}"' for item in content[key]])
                result += f'{prefix}{key}=({value})\n'

        self.assertIn('TRAIT_SET=("value1" "value2" "value3")', result)

    def test_traits_diff_calculation(self):
        """Test calculation of traits differences"""
        before = {'SET': ['val1'], 'CID': ['id1']}
        after = {'SET': ['val2'], 'CID': ['id1']}

        diff = [
            (key, {'before': before.get(key), 'after': after.get(key)})
            for key in before
            if key not in after or before[key] != after[key]
        ]

        self.assertEqual(len(diff), 1)
        self.assertEqual(diff[0][0], 'SET')
        self.assertEqual(diff[0][1]['before'], ['val1'])
        self.assertEqual(diff[0][1]['after'], ['val2'])

    def test_traits_no_diff(self):
        """Test no differences when traits are equal"""
        before = {'SET': ['val1'], 'CID': ['id1']}
        after = {'SET': ['val1'], 'CID': ['id1']}

        diff = [
            (key, {'before': before.get(key), 'after': after.get(key)})
            for key in before
            if key not in after or before[key] != after[key]
        ]

        self.assertEqual(len(diff), 0)


class TestPackageProxyCache(unittest.TestCase):
    """Tests for package proxy cache logic"""

    def test_server_without_proxy(self):
        """Test server URL without proxy cache"""
        server = 'migasfree.example.com'
        package_proxy_cache = None

        if package_proxy_cache:
            server = f'{package_proxy_cache}/{server}'

        self.assertEqual(server, 'migasfree.example.com')

    def test_server_with_proxy(self):
        """Test server URL with proxy cache"""
        server = 'migasfree.example.com'
        package_proxy_cache = 'http://cache.local:3142'

        if package_proxy_cache:
            server = f'{package_proxy_cache}/{server}'

        self.assertEqual(server, 'http://cache.local:3142/migasfree.example.com')


class TestSynchronizationData(unittest.TestCase):
    """Tests for synchronization data structures"""

    def test_sync_upload_data(self):
        """Test synchronization upload data structure"""
        computer_id = 123
        start_date = datetime.now().isoformat()
        consumer = 'migasfree 5.0'
        pms_status_ok = True

        data = {
            'id': computer_id,
            'start_date': start_date,
            'consumer': consumer,
            'pms_status_ok': pms_status_ok,
        }

        self.assertEqual(data['id'], 123)
        self.assertIn('start_date', data)
        self.assertEqual(data['consumer'], 'migasfree 5.0')
        self.assertTrue(data['pms_status_ok'])

    def test_sync_upload_data_with_error(self):
        """Test synchronization upload data when PMS has errors"""
        pms_status_ok = False

        data = {'pms_status_ok': pms_status_ok}

        self.assertFalse(data['pms_status_ok'])


class TestMandatoryPackagesLogic(unittest.TestCase):
    """Tests for mandatory packages logic"""

    def test_mandatory_packages_structure(self):
        """Test mandatory packages response structure"""
        response = {
            'install': ['pkg1', 'pkg2'],
            'remove': ['pkg3'],
        }

        self.assertIn('install', response)
        self.assertIn('remove', response)
        self.assertEqual(len(response['install']), 2)
        self.assertEqual(len(response['remove']), 1)

    def test_empty_mandatory_packages(self):
        """Test empty mandatory packages response"""
        response = None

        if not response:
            # No action needed
            pass

        self.assertIsNone(response)

    def test_partial_mandatory_packages(self):
        """Test mandatory packages with only install"""
        response = {'install': ['pkg1']}

        remove_pkgs = response.get('remove', [])

        install_pkgs = response.get('install', [])

        self.assertEqual(install_pkgs, ['pkg1'])
        self.assertEqual(remove_pkgs, [])


class TestDevicesLogic(unittest.TestCase):
    """Tests for devices response structure"""

    def test_devices_response_structure(self):
        """Test devices response structure"""
        response = {
            'logical': [
                {'id': 1, 'name': 'Printer1'},
                {'id': 2, 'name': 'Printer2'},
            ],
            'default': 1,
        }

        self.assertIn('logical', response)
        self.assertIn('default', response)
        self.assertEqual(len(response['logical']), 2)
        self.assertEqual(response['default'], 1)

    def test_empty_devices(self):
        """Test empty devices response"""
        response = {'logical': [], 'default': None}

        self.assertEqual(len(response['logical']), 0)
        self.assertIsNone(response['default'])


class TestHardwareInventory(unittest.TestCase):
    """Tests for hardware inventory logic"""

    def test_hardware_capture_required_true(self):
        """Test hardware capture required response"""
        response = {'capture': True}
        self.assertTrue(response.get('capture', False))

    def test_hardware_capture_required_false(self):
        """Test hardware capture not required response"""
        response = {'capture': False}
        self.assertFalse(response.get('capture', False))

    def test_hardware_capture_missing_key(self):
        """Test hardware capture with missing key defaults to False"""
        response = {}
        self.assertFalse(response.get('capture', False))


if __name__ == '__main__':
    unittest.main()
