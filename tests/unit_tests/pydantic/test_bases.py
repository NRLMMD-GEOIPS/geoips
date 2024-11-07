# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Test Pydantic base models for Order-Based Procflow."""
import json
import pytest

from pydantic import Field


from geoips.pydantic import bases


class MockModel(bases.PrettyBaseModel):
    """MockModel to test __str__method of PrettyBasemodel."""

    plugin_type: str = Field(description="name of the plugin type")
    plugin_name: str = Field(description="name of the plugin")


def test_prettybase_model_str():
    """Test if the PrettyBaseModel returns JSON data with two-sapce indentation."""
    mock_model = MockModel(plugin_type="Reader", plugin_name="abi_netcdf")

    string_representation_of_model = str(mock_model)
    expected_json_format = json.dumps({
        "plugin_type": "Reader",
        "plugin_name": "abi_netcdf"
    }, indent=2)

    assert string_representation_of_model == expected_json_format