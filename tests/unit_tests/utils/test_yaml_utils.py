# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Unit tests for geoips.utils.yaml_utils."""

import pytest
from geoips.errors import DuplicateKeyError
from geoips.utils.yaml_utils import safe_load

FLAT_UNIQUE = "key1: 1\nkey2: 2"

NESTED_UNIQUE = (
    "key1:\n"
    "  subkey1: 1\n"
    "  subkey2: 2\n"
    "key2:\n"
    "  subkey1: 1\n"
    "  subkey2: 2\n"
)

FLAT_DUPLICATE = "key1: 1\nkey1: 2"

NESTED_DUPLICATE = "key1:\n  subkey1: 1\n  subkey1: 2"


def test_safe_load_flat_unique_keys():
    """safe_load succeeds on flat YAML with no duplicate keys."""
    assert safe_load(FLAT_UNIQUE) == {"key1": 1, "key2": 2}


def test_safe_load_nested_unique_keys():
    """safe_load succeeds when same subkey names appear under different parent keys."""
    result = safe_load(NESTED_UNIQUE)
    assert result == {
        "key1": {"subkey1": 1, "subkey2": 2},
        "key2": {"subkey1": 1, "subkey2": 2},
    }


def test_safe_load_flat_duplicate_key_raises():
    """safe_load raises DuplicateKeyError on a top-level duplicate key."""
    with pytest.raises(DuplicateKeyError):
        safe_load(FLAT_DUPLICATE)


def test_safe_load_nested_duplicate_key_raises():
    """safe_load raises DuplicateKeyError on a duplicate key within a nested mapping."""
    with pytest.raises(DuplicateKeyError):
        safe_load(NESTED_DUPLICATE)
