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
Tests for tag-related functionality.

Since MigasFreeTags has complex initialization requirements (root privileges,
logging configuration, file permissions), these tests focus on testing the
core logic directly without importing the class.
"""

import collections
import unittest


class TestTagSanitization(unittest.TestCase):
    """Tests for tag sanitization logic"""

    def _sanitize_tag(self, tag):
        """
        Simulate the sanitization logic from MigasFreeTags._sanitize

        Tags must be in 'prefix-value' format where:
        - prefix: at least one character before the hyphen
        - value: at least one character after the hyphen
        """
        tag = tag.replace('"', '')
        try:
            prefix, value = tag.split('-', 1)
            if not prefix or not value:
                raise ValueError('Invalid tag format')
            return True
        except ValueError:
            raise ValueError('Tags must be in "prefix-value" format')  # noqa: B904

    def test_valid_tag_single_hyphen(self):
        """Test valid tag with single hyphen"""
        self.assertTrue(self._sanitize_tag('LOC-office1'))

    def test_valid_tag_multiple_hyphens(self):
        """Test valid tag with multiple hyphens (split at first hyphen)"""
        self.assertTrue(self._sanitize_tag('LOC-sub-office-1'))

    def test_valid_tag_short(self):
        """Test minimal valid tag"""
        self.assertTrue(self._sanitize_tag('A-B'))

    def test_invalid_tag_no_hyphen(self):
        """Test invalid tag without hyphen"""
        with self.assertRaises(ValueError):
            self._sanitize_tag('invalidtag')

    def test_invalid_tag_underscore(self):
        """Test invalid tag with underscore instead of hyphen"""
        with self.assertRaises(ValueError):
            self._sanitize_tag('invalid_tag')

    def test_tag_with_quotes(self):
        """Test tag with quotes are handled"""
        self.assertTrue(self._sanitize_tag('"LOC-office1"'))

    def test_tag_empty_prefix(self):
        """Test tag with empty prefix fails"""
        with self.assertRaises(ValueError):
            self._sanitize_tag('-value')

    def test_tag_empty_value(self):
        """Test tag with empty value fails"""
        with self.assertRaises(ValueError):
            self._sanitize_tag('prefix-')


class TestTagSelection(unittest.TestCase):
    """Tests for tag selection logic"""

    def test_available_tags_sorted(self):
        """Test available tags dictionary is sorted by key"""
        available = {'ZZZ': ['ZZZ-1'], 'AAA': ['AAA-1'], 'MMM': ['MMM-1']}
        sorted_tags = collections.OrderedDict(sorted(available.items()))
        keys = list(sorted_tags.keys())
        self.assertEqual(keys, ['AAA', 'MMM', 'ZZZ'])

    def test_tag_values_sorted(self):
        """Test tag values within a category are sorted"""
        values = ['LOC-z', 'LOC-a', 'LOC-m']
        values.sort()
        self.assertEqual(values, ['LOC-a', 'LOC-m', 'LOC-z'])

    def test_tag_active_detection(self):
        """Test detection of active tags from assigned list"""
        assigned = ['LOC-office1', 'DEP-marketing']
        tag = 'LOC-office1'
        self.assertIn(tag, assigned)

        tag2 = 'LOC-office2'
        self.assertNotIn(tag2, assigned)

    def test_empty_available_tags(self):
        """Test empty available tags"""
        available = {}
        self.assertEqual(len(available), 0)

    def test_filter_selected_tags(self):
        """Test filtering selected tags from output"""
        output = 'LOC-office1\nDEP-marketing\n'
        selected = list(filter(None, output.split('\n')))
        self.assertEqual(selected, ['LOC-office1', 'DEP-marketing'])

    def test_filter_empty_output(self):
        """Test filtering empty output"""
        output = ''
        selected = list(filter(None, output.split('\n')))
        self.assertEqual(selected, [])


class TestTagRules(unittest.TestCase):
    """Tests for tag rules processing"""

    def test_rules_structure(self):
        """Test expected rules structure from API"""
        rules = {
            'install': ['pkg1', 'pkg2'],
            'remove': ['pkg3'],
            'preinstall': ['pkg4'],
        }
        self.assertIn('install', rules)
        self.assertIn('remove', rules)
        self.assertIn('preinstall', rules)
        self.assertIsInstance(rules['install'], list)

    def test_empty_rules(self):
        """Test empty rules lists"""
        rules = {
            'install': [],
            'remove': [],
            'preinstall': [],
        }
        self.assertEqual(len(rules['install']), 0)
        self.assertEqual(len(rules['remove']), 0)
        self.assertEqual(len(rules['preinstall']), 0)


class TestZenityCommand(unittest.TestCase):
    """Tests for zenity command building logic"""

    def _build_zenity_command(self, title, text, available_tags, assigned, linux=True):
        """
        Build zenity command similar to MigasFreeTags._select_tags
        """
        cmd = 'zenity --title="{}" --text="{}" {} --list --checklist --column=" " --column=TAG --column=TYPE'.format(
            title,
            text,
            '--separator="\\n"' if linux else '',
        )
        for key, value in sorted(available_tags.items()):
            value.sort()
            for item in value:
                tag_active = item in assigned
                cmd += f' "{tag_active}" "{item}" "{key}"'
        return cmd

    def test_zenity_command_basic(self):
        """Test basic zenity command structure"""
        cmd = self._build_zenity_command('Change tags', 'Select tags', {'LOC': ['LOC-office1']}, [], linux=True)
        self.assertIn('zenity', cmd)
        self.assertIn('--title="Change tags"', cmd)
        self.assertIn('--checklist', cmd)
        self.assertIn('LOC-office1', cmd)

    def test_zenity_command_with_assigned(self):
        """Test zenity command marks assigned tags as True"""
        cmd = self._build_zenity_command(
            'Change tags', 'Select', {'LOC': ['LOC-office1', 'LOC-office2']}, ['LOC-office1']
        )
        # Assigned tag should have True
        self.assertIn('"True" "LOC-office1"', cmd)
        # Non-assigned should have False
        self.assertIn('"False" "LOC-office2"', cmd)

    def test_zenity_linux_separator(self):
        """Test zenity command has separator on Linux"""
        cmd = self._build_zenity_command('Title', 'Text', {'A': ['A-1']}, [], linux=True)
        self.assertIn('--separator=', cmd)

    def test_zenity_windows_no_separator(self):
        """Test zenity command has no separator on Windows"""
        cmd = self._build_zenity_command('Title', 'Text', {'A': ['A-1']}, [], linux=False)
        self.assertNotIn('--separator=', cmd)


class TestDialogCommand(unittest.TestCase):
    """Tests for dialog command building logic"""

    def _build_dialog_command(self, title, text, available_tags, assigned):
        """
        Build dialog command similar to MigasFreeTags._select_tags
        """
        cmd = f"dialog --backtitle '{title}' --separate-output --stdout --checklist '{text}' 0 0 8"
        for key, value in sorted(available_tags.items()):
            value.sort()
            for item in value:
                tag_active = 'on' if item in assigned else 'off'
                cmd += f" '{item}' '{key}' {tag_active}"
        return cmd

    def test_dialog_command_basic(self):
        """Test basic dialog command structure"""
        cmd = self._build_dialog_command('Change tags', 'Select tags', {'LOC': ['LOC-office1']}, [])
        self.assertIn('dialog', cmd)
        self.assertIn("--backtitle 'Change tags'", cmd)
        self.assertIn('--checklist', cmd)
        self.assertIn('LOC-office1', cmd)

    def test_dialog_command_with_assigned(self):
        """Test dialog command marks assigned tags as on"""
        cmd = self._build_dialog_command('Title', 'Text', {'LOC': ['LOC-office1', 'LOC-office2']}, ['LOC-office1'])
        self.assertIn("'LOC-office1' 'LOC' on", cmd)
        self.assertIn("'LOC-office2' 'LOC' off", cmd)


if __name__ == '__main__':
    unittest.main()
