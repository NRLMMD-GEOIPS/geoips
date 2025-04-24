# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Test Order-based procflow workflow building classes."""

# Python Standard Libraries
import copy

# Third-Party Libraries
from pydantic import ValidationError
import pytest

# GeoIPS Libraries
from geoips.pydantic import workflows


def test_good_workflow_step_model_valid_initialization(valid_step_data):
    """Tests WorkflowStepModel with valid inputs."""
    test_data = copy.deepcopy(valid_step_data)
    required_test_data = {"reader": test_data}
    # print("\n\n\nupdated test data", required_test_data)

    model = workflows.WorkflowStepModel(**required_test_data)
    assert model.definition.kind == "reader"


def test_bad_workflow_step_model_empty_initialization():
    """Tests WorkflowStepModel with empty input."""
    with pytest.raises(ValidationError) as exec_info:
        workflows.WorkflowStepModel()

    error_info = exec_info.value.errors()

    # since there is only one field
    assert len(error_info) == 1
    assert error_info[0]["loc"] == ()
    # message from custom validator
    assert error_info[0]["msg"] == "Value error, Empty : Step data cannot be empty."


def test_good_workflow_step_model_validator_valid_input(
    valid_step_data, valid_plugin_types
):
    """Tests WorkflowStepModel's custom validator."""
    test_data = copy.deepcopy(valid_step_data)
    required_test_data = {"reader": test_data}
    print("required test data \t", required_test_data)

    model = workflows.WorkflowStepModel(**required_test_data)

    validated_data = model._plugin_name_validator(required_test_data)
    assert validated_data == {
        "definition": {
            "kind": "reader",
            "name": "abi_netcdf",
            "arguments": {
                "area_def": "None",
                "variables": ["None"],
                "metadata_only": False,
                "self_register": ["None"],
            },
        }
    }
    assert model.definition.kind in valid_plugin_types


def test_bad_workflow_step_model_validator_invalid_plugin_type(
    valid_step_data, valid_plugin_types
):
    """Tests WorkflowStepModel's custom validator against invalid plugin type."""
    test_data = copy.deepcopy(valid_step_data)
    required_test_data = {"reader": test_data}
    required_test_data["invalid_plugin_type"] = required_test_data.pop("reader")

    with pytest.raises(ValidationError) as exec_info:
        workflows.WorkflowStepModel(**required_test_data)

    error_info = str(exec_info.value)
    assert "invalid_plugin_type" in error_info
