# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Test Pydantic base models for Order-Based Procflow."""
import json
import pytest

from pydantic import Field, ValidationError


from geoips.pydantic import bases


class MockModel(bases.PrettyBaseModel):
    """MockModel to test __str__method of PrettyBasemodel."""

    plugin_type: str = Field(description="name of the plugin type")
    plugin_name: str = Field(description="name of the plugin")


def test_good_prettybase_model_str():
    """Test if the PrettyBaseModel returns JSON data with two-sapce indentation."""
    mock_model = MockModel(plugin_type="Reader", plugin_name="abi_netcdf")

    string_representation_of_model = str(mock_model)
    expected_json_format = json.dumps({
        "plugin_type": "Reader",
        "plugin_name": "abi_netcdf"
    }, indent=2)

    assert string_representation_of_model == expected_json_format


def test_bad_invalid_prettybase_model_missing_required_field():
    """Test PrettyBaseModel for missing required fields."""
    with pytest.raises(ValidationError) as exec_info:
        MockModel(plugin_type="Reader")

    error_info = exec_info.value.errors()
    assert len(error_info) == 1
    assert error_info[0]['loc'] == ('plugin_name',)
    assert error_info[0]['type'] == 'missing'


def test_bad_prettybase_model_invalid_field_type():
    """Test PrettyBaseModel for missing required fields."""
    with pytest.raises(ValidationError) as exec_info:
        MockModel(plugin_type="Reader", plugin_name=123)

    error_info = exec_info.value.errors()
    assert len(error_info) == 1
    assert error_info[0]['loc'] == ('plugin_name',)
    assert error_info[0]['type'] == 'string_type'
