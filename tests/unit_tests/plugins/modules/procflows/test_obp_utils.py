# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Unit tests for Order-Based Procflow specific utility functions."""

# GeoIPS imports
from geoips.plugins.modules.procflows.obp_utils import (
    remove_keys_with_default_value_plugin_provided,
)


def test_remove_plugin_provided_root_level_key(workflow_with_plugin_provided):
    """Ensure keys wtih value PLUGIN_PROVIDED are removed."""
    actual = remove_keys_with_default_value_plugin_provided(
        workflow_with_plugin_provided
    )

    reader_arguments = actual["spec"]["steps"]["reader"]["arguments"]

    assert "test" not in reader_arguments
    assert reader_arguments["variables"] == ["B14BT"]
