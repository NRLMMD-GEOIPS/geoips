# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Test Order-based procflow product building classes."""

import pytest

from geoips.pydantic import products


VALID_PLUGIN_TYPES = [
    "algorithm",
    "procflow",
    "sector_adjuster",
    "output_checker",
    "output_formatter",
    "reader",
    "gridline_annotator",
    "product_default",
    "sector_metadata_generator",
    "product",
    "sector_spec_generator",
    "title_formatter",
    "coverage_checker",
    "feature_annotator",
    "colormapper",
    "sector",
    "interpolator",
    "filename_formatter"
]


def test_get_plugin_types_missing_types():
    """Test get_plugin_types call to check there are no missing plugin types."""
    assert not (set(VALID_PLUGIN_TYPES) - set(products.get_plugin_types())), (
        "Missing plugin type(s)"
    )


def test_get_plugin_types_unexpected_or_new_plugin_type():
    """Tests get_plugin_types call to check for no unexpected plugin is reported."""
    assert not (set(products.get_plugin_types()) - set(VALID_PLUGIN_TYPES)), (
        "Unexpected New plugin type(s) -" " update test or check function:\n\n"
    )
