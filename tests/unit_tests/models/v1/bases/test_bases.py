# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Test Pydantic base models for Order-Based Procflow."""

# Python Standard Libraries
import copy
import json

# Third-Party Libraries
import pytest
from pydantic import Field, ValidationError

# GeoIPS Libraries
from geoips.models.v1 import bases


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
    assert bases.python_identifier(valid_identifier) == valid_identifier


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
        bases.python_identifier(invalid_identifier)

    assert isinstance(exec_info.value, ValueError), "Exception raised is not ValueError"
    error_message = str(exec_info.value)
    assert (
        expected_error in error_message
    ), f"{error_message} does not match {expected_error}"


# Test PrettyBaseModel
class MockPrettyBaseModel(bases.PrettyBaseModel):
    """Test PrettyBaseModel to test __str__method of PrettyBaseModel."""

    plugin_type: str = Field(description="name of the plugin type")
    plugin_name: str = Field(description="name of the plugin")


def test_good_pretty_base_model_str():
    """Test if the PrettyBaseModel returns JSON data with two-space indentation."""
    test_model = MockPrettyBaseModel(plugin_type="Reader", plugin_name="abi_netcdf")

    string_representation_of_model = str(test_model)
    expected_json_format = json.dumps(
        {"plugin_type": "Reader", "plugin_name": "abi_netcdf"}, indent=2
    )

    assert string_representation_of_model == expected_json_format


def test_bad_pretty_base_model_missing_required_field():
    """Test PrettyBaseModel for missing required fields."""
    with pytest.raises(ValidationError) as exec_info:
        MockPrettyBaseModel(plugin_type="Reader")

    error_info = exec_info.value.errors()
    assert len(error_info) == 1
    assert error_info[0]["loc"] == ("plugin_name",)
    assert error_info[0]["type"] == "missing"


def test_bad_pretty_base_model_invalid_field_type():
    """Test PrettyBaseModel for missing required fields."""
    with pytest.raises(ValidationError) as exec_info:
        MockPrettyBaseModel(plugin_type="Reader", plugin_name=123)

    error_info = exec_info.value.errors()
    assert len(error_info) == 1
    assert error_info[0]["loc"] == ("plugin_name",)
    assert error_info[0]["type"] == "string_type"


# Test PluginModel


def test_good_plugin_valid_instance(valid_plugin_data):
    """Test PluginModel with valid inputs."""
    plugin = bases.PluginModel(**valid_plugin_data)

    assert plugin.interface == valid_plugin_data["interface"]
    assert plugin.family == valid_plugin_data["family"]
    assert plugin.name == valid_plugin_data["name"]
    assert plugin.docstring == valid_plugin_data["docstring"]
    assert plugin.description == valid_plugin_data["description"]
    assert plugin.package == valid_plugin_data["package"]
    assert plugin.relpath == valid_plugin_data["relpath"]
    assert plugin.abspath == valid_plugin_data["abspath"]


def test_bad_plugin_invalid_instance_additional_field(valid_plugin_data):
    """Test PluginModel with additional field."""
    invalid_data = valid_plugin_data.copy()
    # adding an extra field
    invalid_data["unexpected_field"] = "unexpected_value"

    with pytest.raises(ValidationError) as exec_info:
        bases.PluginModel(**invalid_data)

    error_info = exec_info.value.errors()
    assert any(
        err["type"] == "extra_forbidden" for err in error_info
    ), "expected 'extra_forbidden' error type"
    assert "unexpected_field" in str(
        exec_info.value
    ), "Unexpected field should be mentioned in the error"


def test_good_plugin_model_valid_interfaces(valid_plugin_data, valid_interfaces):
    """Test PluginModel's valid_interface() method with valid interfaces."""
    model = bases.PluginModel(**valid_plugin_data)
    assert model.interface in valid_interfaces


def test_bad_plugin_model_valid_interfaces(valid_plugin_data, valid_interfaces):
    """Test PluginModel's  valid_interface() method with invalid interfaces."""
    invalid_interface = "invalid_interface_name"

    assert (
        invalid_interface not in valid_interfaces
    ), f"'{invalid_interface}' should not be a valid interface."

    invalid_data = valid_plugin_data.copy()
    invalid_data["interface"] = invalid_interface

    with pytest.raises(ValidationError, match="Invalid interface"):
        bases.PluginModel(**invalid_data)


# Parameterized test input for a valid description test
@pytest.mark.parametrize(
    "docstring",
    ["This is a valid docstring."],
)
def test_good_plugin_model_docstring(valid_plugin_data, docstring):
    """Test PluginModel with a good docstring."""
    data = copy.deepcopy(valid_plugin_data)
    data["docstring"] = docstring
    model = bases.PluginModel(**data)
    assert model.docstring == docstring


# Parameterized test input for multiple invalid descriptions
@pytest.mark.parametrize(
    "invalid_docstring",
    [
        (
            "This is a \n a multiline docstring.",
            "The description must be one line only.",
        ),
        ("Docstring with missing period", "The docstring must end with a period"),
        (
            "docstring starting with lower case and ending with no period",
            "The Docstring should start with a capital letter and end with a period",
        ),
    ],
    ids=[
        "Multiline docstring",
        "Missing period docstring",
        "Start with Capital & end in period",
    ],
)
def test_bad_plugin_model_description(valid_plugin_data, invalid_docstring):
    """Test PluginModel with invalid docstring use cases."""
    data = copy.deepcopy(valid_plugin_data)
    data["description"] = invalid_docstring

    with pytest.raises(ValueError) as exec_info:
        bases.PluginModel(**data)

    error_info = exec_info.value.errors()
    assert any(error["loc"] == ("description",) for error in error_info)
    assert any("valid string" in error["msg"] for error in error_info)


@pytest.mark.parametrize(
    "docstring_input, expected_description",
    [
        (
            {"docstring": "First line. \n Second line.", "description": None},
            "First line.",
        ),
    ],
    ids=[
        "Description is None",
    ],
)
def test_bad_plugin_model_set_description(
    valid_plugin_data, docstring_input, expected_description
):
    """Test PluginModel's set_description() method when description is set to None."""
    data = copy.deepcopy(valid_plugin_data)
    data.update(docstring_input)
    model = bases.PluginModel(**data)

    assert model.description == expected_description, (
        f"Expected description: {expected_description},"
        f"but got this: {model.docstring}"
    )


@pytest.mark.parametrize(
    "docstring_input, expected_description",
    [
        (
            {
                "docstring": "First line. \n Second line.",
            },
            "First line.",
        ),
    ],
    ids=[
        "Description not provided",
    ],
)
def test_bad_plugin_model_set_description_without_input_field(
    valid_plugin_data, docstring_input, expected_description
):
    """Test PluginModel's set_description() method when description field is missing."""
    data = copy.deepcopy(valid_plugin_data)
    data.pop("description", None)
    data.update(docstring_input)
    model = bases.PluginModel(**data)
    assert model.description == expected_description, (
        f"Expected description: {expected_description},"
        f"but got this: {model.docstring}"
    )


def test_bad_plugin_model_validate_one_line_description_length(valid_plugin_data):
    """Test PluginModel's description validator against more than 72 characters."""
    data = copy.deepcopy(valid_plugin_data)
    data["description"] = (
        "This description is intentionally crafted to exceed seventy-two characters."
    )

    with pytest.warns(
        FutureWarning, match="Description cannot be more than 72 characters."
    ):
        model = bases.PluginModel(**data)

    assert model.description


def test_bad_plugin_model_validate_one_line_description_multi_line(valid_plugin_data):
    """Test PluginModel's description validator against multi line input."""
    data = copy.deepcopy(valid_plugin_data)
    data["description"] = "This description is a \n multi line one."

    with pytest.warns(FutureWarning, match="Description must be a single line."):
        model = bases.PluginModel(**data)

    assert model.description
