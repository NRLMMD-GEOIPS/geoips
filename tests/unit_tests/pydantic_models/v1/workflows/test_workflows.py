# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Test Order-based procflow product building classes."""

# Python Standard Libraries
# import copy

# Third-Party Libraries
# from pydantic import ValidationError
import pytest

# GeoIPS Libraries
from geoips.pydantic_models.v1 import workflows

# The following tests would be added in the later stage of OBP
# Dependent on further steps development


# def  test_product_spec_model_initialization():
"""Test to validate sequence of multiple steps definition."""

# def test_product_plugin_model_valid_product():
"""Test to validate a product definition."""


def test_bad_get_plugin_types_missing_types(valid_plugin_kinds):
    """Test get_plugin_kinds call to check there are no missing plugin kinds."""
    assert not (
        set(valid_plugin_kinds) - set(workflows.get_plugin_kinds())
    ), "Missing plugin kind(s)"


def test_good_get_plugin_names_valid_kind():
    """Test get_plugin_names call with a valid plugin kind."""
    plugin_names = workflows.get_plugin_names("reader")

    assert isinstance(plugin_names, list)
    for plugin in plugin_names:
        assert isinstance(plugin, str)
        # assert plugin


def test_bad_get_plugin_names_invalid_kind(caplog):
    """Test get_plugin_names call with an invalid plugin kind."""
    with caplog.at_level("CRITICAL"):
        with pytest.raises(AttributeError) as exec_info:
            workflows.get_plugin_names("invalid_plugin_kind")

        assert "is not a recognized plugin kind." in str(exec_info.value)

        # Check that critical log was made
        assert any(
            "is not a recognized plugin kind." in message for message in caplog.messages
        )
