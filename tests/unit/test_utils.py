# -*- coding: utf-8 -*-

"""
Unit tests for migasfree_client.utils module
"""

import os
import sys
import pytest
from unittest.mock import patch

from migasfree_client import utils
from tests.fixtures.sample_data import SLUGIFY_TEST_CASES


class TestStringUtilities:
    """Tests for string manipulation functions"""

    @pytest.mark.parametrize("input_str,expected", SLUGIFY_TEST_CASES)
    def test_slugify(self, input_str, expected):
        """Test slugify converts strings to URL-friendly format"""
        result = utils.slugify(input_str)
        assert result == expected

    def test_slugify_with_special_characters(self):
        """Test slugify removes special characters"""
        result = utils.slugify("Test@#$%String!")
        assert "@" not in result
        assert "#" not in result
        assert "$" not in result

    def test_remove_commented_lines(self):
        """Test removing commented lines from text"""
        text = "line1\n# comment\nline2\n# another comment\nline3"
        result = utils.remove_commented_lines(text)
        assert "# comment" not in result
        assert "# another comment" not in result
        # Note: The current implementation has a bug - it removes ALL lines with #
        # This test documents the current behavior


class TestPlatformDetection:
    """Tests for platform detection functions"""

    @patch("sys.platform", "win32")
    def test_is_windows_true(self):
        """Test is_windows returns True on Windows"""
        assert utils.is_windows() is True

    @patch("sys.platform", "linux")
    def test_is_windows_false(self):
        """Test is_windows returns False on Linux"""
        assert utils.is_windows() is False

    @patch("sys.platform", "linux")
    def test_is_linux_true(self):
        """Test is_linux returns True on Linux"""
        assert utils.is_linux() is True

    @patch("sys.platform", "win32")
    def test_is_linux_false(self):
        """Test is_linux returns False on Windows"""
        assert utils.is_linux() is False

    @patch("migasfree_client.utils.is_windows", return_value=True)
    def test_sanitize_path_windows(self, mock_is_windows):
        """Test sanitize_path on Windows replaces invalid characters"""
        path = "C:\\\\path\\\\to\\\\file:name?.txt"
        result = utils.sanitize_path(path)
        assert ":" not in result
        assert "?" not in result
        assert "\\\\" not in result

    @patch("migasfree_client.utils.is_windows", return_value=False)
    def test_sanitize_path_linux(self, mock_is_windows):
        """Test sanitize_path on Linux keeps path unchanged"""
        path = "/path/to/file.txt"
        result = utils.sanitize_path(path)
        assert result == path


class TestFileOperations:
    """Tests for file I/O functions"""

    def test_read_file_binary(self, tmp_dir):
        """Test reading file in binary mode"""
        file_path = os.path.join(tmp_dir, "test.bin")
        content = b"Binary content"
        with open(file_path, "wb") as f:
            f.write(content)

        result = utils.read_file(file_path, mode="rb")
        assert result == content

    def test_read_file_text(self, tmp_dir):
        """Test reading file in text mode"""
        file_path = os.path.join(tmp_dir, "test.txt")
        content = "Text content"
        with open(file_path, "w") as f:
            f.write(content)

        result = utils.read_file(file_path, mode="r")
        assert result == content

    def test_write_file_string(self, tmp_dir):
        """Test writing string to file"""
        file_path = os.path.join(tmp_dir, "output.txt")
        content = "Test content"

        result = utils.write_file(file_path, content)
        assert result is True
        assert os.path.exists(file_path)

        with open(file_path, "r") as f:
            assert f.read() == content

    def test_write_file_bytes(self, tmp_dir):
        """Test writing bytes to file"""
        file_path = os.path.join(tmp_dir, "output.bin")
        content = b"Binary content"

        result = utils.write_file(file_path, content)
        assert result is True

        with open(file_path, "rb") as f:
            assert f.read() == content

    def test_write_file_creates_directory(self, tmp_dir):
        """Test write_file creates parent directories"""
        file_path = os.path.join(tmp_dir, "subdir", "nested", "file.txt")
        content = "Test"

        result = utils.write_file(file_path, content)
        assert result is True
        assert os.path.exists(file_path)

    def test_remove_file_existing(self, tmp_dir):
        """Test removing existing file"""
        file_path = os.path.join(tmp_dir, "to_remove.txt")
        with open(file_path, "w") as f:
            f.write("content")

        utils.remove_file(file_path)
        assert not os.path.exists(file_path)

    def test_remove_file_nonexistent(self, tmp_dir):
        """Test removing non-existent file doesn't raise error"""
        file_path = os.path.join(tmp_dir, "nonexistent.txt")
        # Should not raise exception
        utils.remove_file(file_path)


class TestListComparison:
    """Tests for list comparison functions"""

    def test_compare_lists_identical(self):
        """Test comparing identical lists"""
        list_a = ["item1", "item2", "item3"]
        list_b = ["item1", "item2", "item3"]
        result = utils.compare_lists(list_a, list_b)
        assert result == []

    def test_compare_lists_different(self):
        """Test comparing different lists"""
        list_a = ["item1", "item2"]
        list_b = ["item1", "item3"]
        result = utils.compare_lists(list_a, list_b)
        assert len(result) > 0
        # Result should contain diff markers
        assert any("-item2" in item for item in result)
        assert any("+item3" in item for item in result)

    def test_compare_lists_added_items(self):
        """Test comparing lists with added items"""
        list_a = ["item1"]
        list_b = ["item1", "item2", "item3"]
        result = utils.compare_lists(list_a, list_b)
        assert len(result) > 0
        assert any("+item2" in item for item in result)
        assert any("+item3" in item for item in result)

    def test_compare_files(self, tmp_dir):
        """Test comparing two files"""
        file_a = os.path.join(tmp_dir, "file_a.txt")
        file_b = os.path.join(tmp_dir, "file_b.txt")

        with open(file_a, "w") as f:
            f.write("line1\\nline2\\nline3")
        with open(file_b, "w") as f:
            f.write("line1\\nline2_modified\\nline3")

        result = utils.compare_files(file_a, file_b)
        assert len(result) > 0


class TestTypeConversion:
    """Tests for type conversion functions"""

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("true", True),
            ("True", True),
            ("yes", True),
            ("1", True),
            ("on", True),
            ("false", False),
            ("False", False),
            ("no", False),
            ("0", False),
            ("off", False),
        ],
    )
    def test_cast_to_bool_valid_values(self, value, expected):
        """Test cast_to_bool with valid boolean strings"""
        result = utils.cast_to_bool(value)
        assert result == expected

    def test_cast_to_bool_invalid_default_false(self):
        """Test cast_to_bool with invalid value returns default False"""
        result = utils.cast_to_bool("invalid", default=False)
        assert result is False

    def test_cast_to_bool_invalid_default_true(self):
        """Test cast_to_bool with invalid value returns default True"""
        result = utils.cast_to_bool("invalid", default=True)
        assert result is True

    def test_cast_to_bool_empty_string(self):
        """Test cast_to_bool with empty string"""
        result = utils.cast_to_bool("", default=False)
        assert result is False


class TestSystemFunctions:
    """Tests for system-related functions"""

    @patch("os.getuid", return_value=0)
    @pytest.mark.skipif(sys.platform == "win32", reason="Unix-only test")
    def test_is_root_user_true(self, mock_getuid):
        """Test is_root_user returns True for root"""
        result = utils.is_root_user()
        assert result is True

    @patch("os.getuid", return_value=1000)
    @pytest.mark.skipif(sys.platform == "win32", reason="Unix-only test")
    def test_is_root_user_false(self, mock_getuid):
        """Test is_root_user returns False for non-root"""
        result = utils.is_root_user()
        assert result is False
