# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Test Order-based procflow product building classes."""

# Python Standard Libraries
# import copy

# Third-Party Libraries
# from pydantic import ValidationError
import pytest

# GeoIPS Libraries
from geoips.pydantic import workflows


# The following tests would be added in the later stage of OBP
# Dependent on further steps development


# def  test_product_spec_model_initialization():
"""Test to validate sequence of multiple steps definition."""

# def test_product_plugin_model_valid_product():
"""Test to validate a product definition."""


# def test_bad_get_plugin_types_missing_types(valid_plugin_types):
#     """Test get_plugin_types call to check there are no missing plugin types."""
#     assert not (
#         set(valid_plugin_types) - set(workflows.get_plugin_names())
#     ), "Missing plugin type(s)"


# def test_bad_get_plugin_types_unexpected_or_new_plugin_type(valid_plugin_types):
#     """Tests get_plugin_types call to check for no unexpected plugin is reported."""
#     unexpected_types = set(workflows.get_plugin_names()) - set(valid_plugin_types)
#     assert not unexpected_types, (
#         f"Unexpected new plugin type(s): {unexpected_types}."
#         "Update the test or check the function implementation."
#     )


def test_good_get_plugin_names_valid_kind():
    """Test get_plugin_names call with a valid plugin kind."""
    plugin_names = workflows.get_plugin_names("reader")

    assert isinstance(plugin_names, list)
    for plugin in plugin_names:
        assert isinstance(plugin, str)
        # assert plugin


def test_bad_get_plugin_names_invalid_kind(caplog):
    """Test get_plugin_names call with an invalid plugin kind."""
    with caplog.at_level("CRITICAL"):  # capture logging at critical level
        with pytest.raises(AttributeError) as exc_info:
            workflows.get_plugin_names("invalid_plugin_kind")

        # Check that error message is raised
        assert "is not a recognized plugin kind." in str(exc_info.value)

        # Check that critical log was made
        assert any(
            "is not a recognized plugin kind." in message for message in caplog.messages
        )
