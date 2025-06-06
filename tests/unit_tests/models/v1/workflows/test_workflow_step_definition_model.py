# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Test Order-based procflow WorkflowStepDefinition Model."""


# Python Standard Libraries
import copy

# Third-Party Libraries
from pydantic import ValidationError
import pytest

# GeoIPS Libraries
from geoips.models.v1 import workflows


# def test_bad_workflow_step_definition_model_
#
def test_bad_workflow_step_definition_model_empty_value_kind():
    """Test WorkflowStepDefinitionModel with empty 'kind'."""
    with pytest.raises(ValidationError) as exec_info:
        workflows.WorkflowStepDefinitionModel(
            kind="", name="abi_netcdf", arguments={"variables": ["B14BT"]}
        )

    error_info = exec_info.value.errors()
    assert any(
        "Invalid input: 'kind' cannot be empty." in err["msg"] for err in error_info
    )


# This test is retained as it would be used for any PluginArgumentsModel
# where one or more attributes are required.
# ReaderArgumentsModel has all fields as optional or some default value

# def test_bad_workflow_step_definition_model_empty_arguments(valid_step_data):
#     """Tests _validate_plugin_arguments() model validator."""
#     invalid_step_data = copy.deepcopy(valid_step_data)
#     invalid_step_data["arguments"] = {}
#     print("invalid step data \t", invalid_step_data)
#     with pytest.raises(ValidationError) as exec_info:
#         workflows.WorkflowStepDefinitionModel(**invalid_step_data)

#     error_info = exec_info.value.errors()
#     assert any("argument model" in err["msg"] for err in error_info)


def test_good_workflow_step_definition_model_valid_step(valid_step_data):
    """Tests WorkflowStepDefinitionModel with valid data."""
    # creating an instance of PSDModel
    model = workflows.WorkflowStepDefinitionModel(**valid_step_data)

    assert model.kind == "reader"
    assert model.name == "abi_netcdf"
    assert model.arguments == {
        "area_def": "None",
        "variables": ["None"],
        "metadata_only": False,
        "self_register": ["None"],
    }


def test_bad_workflow_step_definition_model_validator_empty_input():
    """Tests WorkflowStepDefinitionModel with empty input."""
    with pytest.raises(ValidationError) as exec_info:
        workflows.WorkflowStepDefinitionModel()

    error_info = exec_info.value.errors()

    # Pydantic reports both kind and name as missing fields since they are
    # required. len(err_info) is set to 2 for this reason.
    assert len(error_info) == 2
    # , after element makes it a tuple otherwise it's a string
    expected_missing_fields = {("kind",), ("name",)}
    actual_missing_fields = {tuple(err["loc"]) for err in error_info}
    assert expected_missing_fields.issubset(actual_missing_fields)


def test_bad_workflow_step_definition_model_validator_invalid_plugin_name(
    valid_step_data,
):
    """Tests WorkflowStepDefinitionModel validator against invalid plugin name."""
    invalid_data = copy.deepcopy(valid_step_data)
    invalid_data["name"] = ""
    with pytest.raises(ValidationError) as exec_info:
        workflows.WorkflowStepDefinitionModel(**invalid_data)

    error_info = exec_info.value.errors()

    assert error_info[0]["loc"] == ()
    assert error_info[0]["msg"].startswith("Value error, ")
    assert "Must be one of " in error_info[0]["msg"]


def test_bad_workflow_step_definition_model_validate_kind(
    valid_step_data,
):
    """Tests WorkflowStepDefinitionModel validator against invalid plugin kind."""
    invalid_data = copy.deepcopy(valid_step_data)
    invalid_data["kind"] = "invalid_plugin_kind"

    with pytest.raises(ValidationError) as exec_info:
        workflows.WorkflowStepDefinitionModel(**invalid_data)

    error_info = exec_info.value.errors()
    assert "Invalid plugin kind" in error_info[0]["msg"]


def test_bad_workflow_step_definition_model_additional_field(valid_step_data):
    """Tests ReaderArgumentsModel with additional field."""
    invalid_data = copy.deepcopy(valid_step_data)
    invalid_data["unexpected_field"] = "unexpected_value"

    with pytest.raises(ValidationError) as exec_info:
        workflows.WorkflowStepDefinitionModel(**invalid_data)

    error_info = exec_info.value.errors()
    assert any(
        err["type"] == "extra_forbidden" for err in error_info
    ), "expected 'extra_forbidden' error type"
    assert "unexpected_field" in str(
        exec_info.value
    ), "Unexpected field should be rejected by the WorkflowStepDefinitionModel"


def test_bad_workflow_step_definition_model_invalid_field_type(
    mocker, valid_reader_arguments_model_data, valid_step_data
):
    """Tests WorkflowStepDefinitionModel for invalid field type instantiation."""

    def mock_init(self, **kwargs):
        self.__dict__.update(kwargs)

    mocker.patch.object(workflows.WorkflowStepDefinitionModel, "__init__", mock_init)

    invalid_test_data_PSDModel = {
        "type": 123,
        "name": 123,
        "arguments": valid_reader_arguments_model_data,
    }
    model = workflows.WorkflowStepDefinitionModel(**invalid_test_data_PSDModel)

    assert model.type == 123, "Expected 'type' to retain the invalid value"
    assert model.name == 123, "Expected 'name' to retain the invalid value"
