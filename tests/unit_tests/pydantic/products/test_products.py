# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Test Order-based procflow product building classes."""

# Python Standard Libraries
import copy

# Third-Party Libraries
from pydantic import ValidationError
import pytest

# GeoIPS Libraries
from geoips.pydantic import products


# The following tests would be added in the later stage of OBP
# Dependent on further steps development


# def  test_product_spec_model_initialization():
"""Test to validate sequence of multiple steps definition."""

# def test_product_plugin_model_valid_product():
"""Test to validate a product definition."""


def test_bad_get_plugin_types_missing_types(valid_plugin_types):
    """Test get_plugin_types call to check there are no missing plugin types."""
    assert not (
        set(valid_plugin_types) - set(products.get_plugin_types())
    ), "Missing plugin type(s)"


def test_bad_get_plugin_types_unexpected_or_new_plugin_type(valid_plugin_types):
    """Tests get_plugin_types call to check for no unexpected plugin is reported."""
    assert not (set(products.get_plugin_types()) - set(valid_plugin_types)), (
        "Unexpected New plugin type(s) -" " update test or check function:\n\n"
    )


def test_good_product_step_model_valid_initialization(valid_step_data):
    """Tests ProductStepModel with valid inputs."""
    test_data = copy.deepcopy(valid_step_data)
    test_data.pop("type")
    # print("\n\n\nupdated test data", test_data)
    required_test_data = {"reader": test_data}
    # print("\n\n\nupdated test data", required_test_data)

    model = products.ProductStepModel(**required_test_data)
    assert model.definition.type == "reader"


def test_bad_product_step_model_empty_initialization():
    """Tests ProductStepModel with empty input."""
    with pytest.raises(ValidationError) as exec_info:
        products.ProductStepModel()

    error_info = exec_info.value.errors()

    # since there is only one field
    assert len(error_info) == 1
    assert error_info[0]["loc"] == ()
    # message from custom validator
    assert error_info[0]["msg"] == "Value error, Empty : Step data cannot be empty."


def test_good_product_step_model_validator_valid_input(valid_step_data, valid_plugin_types):
    """Tests ProductStepModel's custom validator."""
    test_data = copy.deepcopy(valid_step_data)
    test_data.pop("type")
    required_test_data = {"reader": test_data}

    model = products.ProductStepModel(**required_test_data)

    validated_data = model._plugin_name_validator(required_test_data)
    assert validated_data == {
        "definition": {
            "type": "reader",
            "name": "abi_netcdf",
            "arguments": {
                "area_def": "None",
                "chans": ["None"],
                "metadata_only": False,
                "self_register": False,
            },
        }
    }
    assert model.definition.type in valid_plugin_types


def test_bad_product_step_model_validator_invalid_plugin_type(
    valid_step_data, valid_plugin_types
):
    """Tests ProductStepModel's custom validator."""
    test_data = copy.deepcopy(valid_step_data)
    test_data.pop("type")
    required_test_data = {"reader": test_data}
    required_test_data["invalid_plugin_type"] = required_test_data.pop("reader")

    with pytest.raises(ValidationError) as exec_info:
        products.ProductStepModel(**required_test_data)

    error_info = str(exec_info.value)

    assert "invalid_plugin_type" in error_info

