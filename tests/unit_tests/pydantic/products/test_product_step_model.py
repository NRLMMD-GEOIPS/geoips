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


def test_good_product_step_model_validator_valid_input(
    valid_step_data, valid_plugin_types
):
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
                "variables": ["None"],
                "metadata_only": False,
                "self_register": ["None"],
            },
        }
    }
    assert model.definition.type in valid_plugin_types


def test_bad_product_step_model_validator_invalid_plugin_type(
    valid_step_data, valid_plugin_types
):
    """Tests ProductStepModel's custom validator against invalid plugin type."""
    test_data = copy.deepcopy(valid_step_data)
    test_data.pop("type")
    required_test_data = {"reader": test_data}
    required_test_data["invalid_plugin_type"] = required_test_data.pop("reader")

    with pytest.raises(ValidationError) as exec_info:
        products.ProductStepModel(**required_test_data)

    error_info = str(exec_info.value)
    assert "invalid_plugin_type" in error_info


def test_bad_product_Step_model_validator_invalid_plugin_name(
    valid_step_data, valid_plugin_types
):
    """Tests ProductStepModel's custom validator against invalid plugin name."""
    invalid_test_data = {
        "reader": {
            "type": "reader1",
            "name": "abi_netcdf",
            "arguments": {
                "area_def": "None",
                "chans": ["None"],
                "metadata_only": False,
                "self_register": False,
            },
        }
    }

    with pytest.raises(ValidationError) as exec_info:
        products.ProductStepModel(**invalid_test_data)

    error_info = str(exec_info.value)
    assert (
        "step name : 'reader'"
        "and type : 'reader1' mismatch. "
        "Check your product definition" in error_info
    )
