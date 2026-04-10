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
Tests for Pms base class and decorators.
"""

import unittest

from migasfree_client.pms.pms import Pms, invalidate_installed_cache


class TestPmsBase(unittest.TestCase):
    """Tests for Pms base class and registry logic"""

    def test_pms_registry(self):
        """Test PMS registration and factory pattern"""

        @Pms.register('mock-pms')
        class MockPms(Pms):
            pass

        self.assertEqual(Pms.factory('mock-pms'), MockPms)
        instance = Pms.factory('mock-pms')()
        self.assertIsInstance(instance, MockPms)

    def test_invalidate_installed_cache_decorator(self):
        """Test the cache invalidation decorator"""

        class MockPms(Pms):
            def __init__(self):
                super().__init__()
                self._installed_cache = ['pkg1', 'pkg2']

            @invalidate_installed_cache
            def successful_action(self):
                return True

            @invalidate_installed_cache
            def failed_action(self):
                return False

            @invalidate_installed_cache
            def successful_tuple(self):
                return (True, 'Success')

        pms = MockPms()

        # Failed action should NOT clear cache
        pms.failed_action()
        self.assertIsNotNone(pms._installed_cache)

        # Successful action should clear cache
        pms.successful_action()
        self.assertIsNone(pms._installed_cache)

        # Reset and test tuple
        pms._installed_cache = ['pkg1']
        pms.successful_tuple()
        self.assertIsNone(pms._installed_cache)

    def test_not_implemented_methods(self):
        """Test that base methods raise NotImplementedError"""
        pms = Pms()
        with self.assertRaises(NotImplementedError):
            pms.install('pkg')
        with self.assertRaises(NotImplementedError):
            pms.remove('pkg')
        with self.assertRaises(NotImplementedError):
            pms.search('pkg')
        with self.assertRaises(NotImplementedError):
            pms.update_silent()
        with self.assertRaises(NotImplementedError):
            pms.install_silent([])
        with self.assertRaises(NotImplementedError):
            pms.remove_silent([])
        with self.assertRaises(NotImplementedError):
            pms.is_installed('pkg')
        with self.assertRaises(NotImplementedError):
            pms.clean_all()
        with self.assertRaises(NotImplementedError):
            pms.query_all()
        with self.assertRaises(NotImplementedError):
            pms.create_repos('', '', [])
        with self.assertRaises(NotImplementedError):
            pms.import_server_key('')
        with self.assertRaises(NotImplementedError):
            pms.get_system_architecture()
        with self.assertRaises(NotImplementedError):
            pms.available_packages()


if __name__ == '__main__':
    unittest.main()
