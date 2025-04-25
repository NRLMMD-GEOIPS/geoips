# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Test Order-based procflow product building classes."""

# Python Standard Libraries
# import copy

# Third-Party Libraries
# from pydantic import ValidationError
# import pytest

# GeoIPS Libraries
# from geoips.pydantic import workflows


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
