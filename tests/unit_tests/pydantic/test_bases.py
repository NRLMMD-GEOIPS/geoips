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


@pytest.fixture
def valid_plugin_data():
    """Fixture providing valid sample data for Plugin model."""
    return {
        "interface": "geoips_interface",
        "family": "geoips_family",
        "name": "geoips_name",
        "docstring": "This is a valid numpy docstring.",
        "package": "geoips_package",
        "relpath": "geoips/tests/unit_tests/pydantic",
        "abspath": "/home/kumar/geoips/geoips/tests/unit_tests/pydantic"
    }


def test_good_pretty_base_model_str():
    """Test if the PrettyBaseModel returns JSON data with two-sapce indentation."""
    mock_model = MockModel(plugin_type="Reader", plugin_name="abi_netcdf")

    string_representation_of_model = str(mock_model)
    expected_json_format = json.dumps({
        "plugin_type": "Reader",
        "plugin_name": "abi_netcdf"
    }, indent=2)

    assert string_representation_of_model == expected_json_format


def test_bad_pretty_base_model_missing_required_field():
    """Test PrettyBaseModel for missing required fields."""
    with pytest.raises(ValidationError) as exec_info:
        MockModel(plugin_type="Reader")

    error_info = exec_info.value.errors()
    assert len(error_info) == 1
    assert error_info[0]['loc'] == ('plugin_name',)
    assert error_info[0]['type'] == 'missing'


def test_bad_pretty_base_model_invalid_field_type():
    """Test PrettyBaseModel for missing required fields."""
    with pytest.raises(ValidationError) as exec_info:
        MockModel(plugin_type="Reader", plugin_name=123)

    error_info = exec_info.value.errors()
    assert len(error_info) == 1
    assert error_info[0]['loc'] == ('plugin_name',)
    assert error_info[0]['type'] == 'string_type'


def test_good_plugin_valid_instance(valid_plugin_data):
    """Test PluginModel with valid inputs."""
    plugin = bases.PluginModel(**valid_plugin_data)

    assert plugin.interface == valid_plugin_data["interface"]
    assert plugin.family == valid_plugin_data["family"]
    assert plugin.name == valid_plugin_data["name"]
    assert plugin.docstring == valid_plugin_data["docstring"]
    assert plugin.package == valid_plugin_data["package"]
    assert plugin.relpath == valid_plugin_data["relpath"]
    assert plugin.abspath == valid_plugin_data["abspath"]

