# Copyright (c) Castor Sky (@castorsky) <csky57@gmail.com>
# License: GPL-3.0-or-later
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import pytest
from plugins.module_utils.opensearch import params_differ


class TestParamsDiffer:
    """Test cases for the params_differ function."""

    def test_identical_params(self) -> None:
        """Test that identical parameters return False."""
        local = {"key1": "value1", "key2": "value2"}
        remote = {"key1": "value1", "key2": "value2"}
        assert params_differ(local, remote) is False

    def test_different_values(self) -> None:
        """Test that different values return True."""
        local = {"key1": "value1", "key2": "value2"}
        remote = {"key1": "value1", "key2": "different_value"}
        assert params_differ(local, remote) is True

    def test_missing_remote_key(self) -> None:
        """Test that missing remote keys return True."""
        local = {"key1": "value1", "key2": "value2"}
        remote = {"key1": "value1"}
        assert params_differ(local, remote) is True

    def test_skip_keys(self) -> None:
        """Test that skip_keys are ignored in comparison."""
        local = {"key1": "value1", "key2": "value2", "key3": "value3"}
        remote = {"key1": "value1", "key2": "different_value", "key3": "value3"}
        assert params_differ(local, remote, skip_keys=["key2"]) is False

    def test_none_value_missing_remote(self) -> None:
        """Test that None local values with missing remote keys are skipped."""
        local = {"key1": "value1", "key2": None}
        remote = {"key1": "value1"}
        assert params_differ(local, remote) is False

    def test_none_value_present_remote(self) -> None:
        """Test that None local values with present remote keys are compared."""
        local = {"key1": "value1", "key2": None}
        remote = {"key1": "value1", "key2": "some_value"}
        assert params_differ(local, remote) is True

    def test_numeric_string_parsing(self) -> None:
        """Test parsing of OpenSearch numeric strings."""
        local = {"int_val": 100, "float_val": 3.14, "byte_val": 1024}
        remote = {"int_val": "100", "float_val": "3.14", "byte_val": "1024"}
        assert params_differ(local, remote) is False

    def test_numeric_string_differences(self) -> None:
        """Test that different numeric values are detected."""
        local = {"int_val": 100, "byte_val": 1024}
        remote = {"int_val": "200", "byte_val": "2048"}
        assert params_differ(local, remote) is True

    def test_complex_data_structures(self) -> None:
        """Test comparison of complex data structures with normalization."""
        local = {
            "dict_val": {"a": 1, "b": 2},
            "list_val": [1, 2, 3],
            "nested": {"x": {"y": [4, 5]}}
        }
        remote = {
            "dict_val": {"b": 2, "a": 1},  # Different order, same content
            "list_val": [3, 1, 2],  # Different order, same content
            "nested": {"x": {"y": [5, 4]}}  # Different order, same content
        }
        assert params_differ(local, remote) is False

    def test_complex_data_structure_differences(self) -> None:
        """Test that differences in complex structures are detected."""
        local = {
            "dict_val": {"a": 1, "b": 2},
            "list_val": [1, 2, 3]
        }
        remote = {
            "dict_val": {"a": 1, "b": 3},  # Different value
            "list_val": [1, 2, 4]  # Different value
        }
        assert params_differ(local, remote) is True

    def test_empty_local_params(self) -> None:
        """Test that empty local params always return False."""
        local = {}
        remote = {"key1": "value1", "key2": "value2"}
        assert params_differ(local, remote) is False

    def test_mixed_data_types(self) -> None:
        """Test comparison with mixed data types."""
        local = {
            "string": "test",
            "integer": 42,
            "boolean": True,
            "none_value": None,
            "list": [1, 2, 3],
            "dict": {"key": "value"}
        }
        remote = {
            "string": "test",
            "integer": 42,
            "boolean": True,
            "list": [3, 2, 1],  # Different order, same content
            "dict": {"key": "value"}
        }
        assert params_differ(local, remote) is False

    def test_invalid_numeric_strings(self) -> None:
        """Test handling of invalid numeric strings."""
        local = {"valid_num": 100, "invalid_num": "not_a_number"}
        remote = {"valid_num": "100", "invalid_num": "not_a_number"}
        assert params_differ(local, remote) is False

    def test_negative_numeric_strings(self) -> None:
        """Test parsing of negative numeric strings."""
        local = {"neg_int": -100, "neg_float": -3.14}
        remote = {"neg_int": "-100", "neg_float": "-3.14"}
        assert params_differ(local, remote) is False

    def test_deeply_nested_structures(self) -> None:
        """Test normalization of deeply nested structures."""
        local = {
            "level1": {
                "level2": {
                    "level3": {
                        "data": [1, 2, {"nested_key": "nested_value"}]
                    }
                }
            }
        }
        remote = {
            "level1": {
                "level2": {
                    "level3": {
                        "data": [{"nested_key": "nested_value"}, 2, 1]  # Different order
                    }
                }
            }
        }
        assert params_differ(local, remote) is False
