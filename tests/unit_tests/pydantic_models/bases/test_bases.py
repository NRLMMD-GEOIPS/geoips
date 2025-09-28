# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Test Pydantic base models for Order-Based Procflow."""

# Python Standard Libraries
import copy
import json
from typing import ClassVar, Tuple

# Third-Party Libraries
import pytest
from pydantic import ConfigDict, Field, ValidationError

# GeoIPS Libraries
from geoips.pydantic_models import bases as bases_root

@pytest.mark.parametrize(
    "valid_identifier",
    [
        "variable",
        "_underscore_prefixed_variable",
        "variable_alpha_numeric123",
        "_",
        "valid_variable_with_underscore",
    ],
    ids=[
        "simple identifier",
        "underscore-prefixed",
        "alphanumeric",
        "single underscore",
        "contains underscore",
    ],
)
def test_good_valid_python_identifier(valid_identifier):
    """Tests python_identifier call against multiple valid Python identifiers."""
    assert bases_root.python_identifier(valid_identifier) == valid_identifier


@pytest.mark.parametrize(
    "invalid_identifier, expected_error",
    [
        ("123_starts_with_number", "is not a valid Python identifier"),
        ("invalid_$_symbol", "is not a valid Python identifier"),
        ("variable with_space", "is not a valid Python identifier"),
        ("", "is not a valid Python identifier"),
        ("class", "is a reserved Python keyword"),
    ],
    ids=[
        "starts with number",
        "contains invalid special character",
        "contains space",
        "empty variable name",
        "uses reserved keyword",
    ],
)
def test_bad_invalid_python_identifier(invalid_identifier, expected_error):
    """Tests python_identifier call against multiple invalid Python identifiers."""
    with pytest.raises(ValueError) as exec_info:
        bases_root.python_identifier(invalid_identifier)

    assert isinstance(exec_info.value, ValueError), "Exception raised is not ValueError"
    error_message = str(exec_info.value)
    assert (
        expected_error in error_message
    ), f"{error_message} does not match {expected_error}"


# Test CoreBaseModel
class MockCoreBaseModel(bases_root.CoreBaseModel):
    """Test CoreBaseModel to test __str__ method of CoreBaseModel."""

    plugin_type: str = Field(description="name of the plugin type")
    plugin_name: str = Field(description="name of the plugin", alias="pluginname")
    restricted_fields: ClassVar[Tuple[str, ...]] = (
        bases_root.CoreBaseModel.restricted_fields + ("restricted_field_1",)
    )
    model_config = ConfigDict(extra="allow")
    # @classmethod
    # def get_disallowed_fields(cls):
    #     """Return a list of fields restricted from user input."""
    #     # return super().get_disallowed_fields()
    #     return ["internal_field"]


def test_good_core_base_model_model_name():
    """Test if the CoreBaseModel model_name method returns valid class name."""
    test_model = MockCoreBaseModel(plugin_type="Reader", pluginname="abi_netcdf")
    assert test_model.model_name == "MockCoreBaseModel"


def test_good_core_base_model_whitespace():
    """Test if the CoreBaseModel trims space around input values."""
    test_model = MockCoreBaseModel(
        plugin_type="  Reader  ", plugin_name="  abi_netcdf  "
    )
    assert test_model.plugin_type == "Reader"
    assert test_model.plugin_name == "abi_netcdf"


def test_good_core_base_model_check_restricted_fields():
    """Test if CoreBaseModel rejects fields marked restricted."""
    with pytest.raises(ValidationError) as exec_info:
        MockCoreBaseModel(
            plugin_type="Reader",
            pluginname="abi_netcdf",
            restricted_field_1="restricted_field_value",
        )
    assert "restricted_field_1 can't be user-defined" in str(exec_info.value)


def test_good_core_base_model_alias():
    """Test if the CoreBasemodel allows population by alias name."""
    test_model = MockCoreBaseModel(plugin_type="Reader", pluginname="abi_netcdf")
    assert test_model.plugin_name == "abi_netcdf"


def test_good_core_base_model_str():
    """Test if the CoreBaseModel returns JSON data with two-space indentation."""
    test_model = MockCoreBaseModel(plugin_type="Reader", plugin_name="abi_netcdf")

    string_representation_of_model = str(test_model)
    expected_json_format = json.dumps(
        {"plugin_type": "Reader", "plugin_name": "abi_netcdf"}, indent=2
    )

    assert string_representation_of_model == expected_json_format


def test_good_core_base_model_has_key_nested():
    """Test CoreBaseModel internal fields presence at a nested level."""
    sample_data = [
        {"input1": "value1"},
        {"nested_input": {"internal_field": "internal_value"}},
    ]
    # Both assertions are included in this test because this is a boolean check
    # One assertion would be sufficient, but the second is added as a precautionary
    # measure. No need to parameterize and over-engineer
    assert MockCoreBaseModel._has_key_nested(sample_data, "internal_field") is True
    assert MockCoreBaseModel._has_key_nested(sample_data, "internal_field1") is False


def test_bad_core_base_model_missing_required_field():
    """Test CoreBaseModel for missing required fields."""
    with pytest.raises(ValidationError) as exec_info:
        MockCoreBaseModel(plugin_type="Reader")

    error_info = exec_info.value.errors()
    assert len(error_info) == 1
    assert error_info[0]["loc"] == ("plugin_name",)
    assert error_info[0]["type"] == "missing"


def test_bad_core_base_model_invalid_field_type():
    """Test CoreBaseModel for missing required fields."""
    with pytest.raises(ValidationError) as exec_info:
        MockCoreBaseModel(plugin_type="Reader", plugin_name=123)

    error_info = exec_info.value.errors()
    assert len(error_info) == 1
    assert error_info[0]["loc"] == ("plugin_name",)
    assert error_info[0]["type"] == "string_type"
