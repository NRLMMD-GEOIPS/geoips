# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Test Order-based procflow ReaderArgumentsModel."""

import copy

# Third-Party Libraries
import pytest
from pydantic import ValidationError

# GeoIPS Libraries
from geoips.pydantic_models.v1 import workflows


def test_good_valid_reader_arguments_model(valid_reader_arguments_model_data):
    """Tests ReaderArgumentsModel with valid inputs."""
    model = workflows.ReaderArgumentsModel(**valid_reader_arguments_model_data)

    assert model.area_def == "None"
    assert model.variables == ["None"]
    assert model.metadata_only is True
    assert model.self_register == ["None"]
    assert model.fnames == ["None"]


def test_bad_reader_arguments_model_field_defaults():
    """Tests if the default value for a given field is valid or not."""
    model = workflows.ReaderArgumentsModel()

    expected_defaults = {
        "area_def": None,
        "variables": None,
        "metadata_only": False,
        "self_register": None,
        "fnames": None,
    }

    for field, expected_value in expected_defaults.items():
        assert (
            getattr(model, field) == expected_value
        ), f"Default value for '{field}' is incorrect"


def test_bad_reader_arguments_model_invalid_field_type():
    """Tests ReaderArgumentsModel for invalid field type instantiation."""
    invalid_test_data = {
        "area_def": 123,
        "variables": "hello",
        "metadata_only": "invalid",
        "self_register": "invalid",
        "fnames": "invalid",
    }

    with pytest.raises(ValidationError) as exec_info:
        workflows.ReaderArgumentsModel(**invalid_test_data)

    error_info = exec_info.value.errors()

    print("error_info \n\n\n", error_info)
    test_data_errors = {
        "area_def": "string_type",
        "variables": "list_type",
        "metadata_only": "bool_parsing",
    }
    for field, error_type in test_data_errors.items():
        assert any(
            err["loc"] == (field,) and err["type"] == error_type for err in error_info
        ), f"Expected error for the field '{field}' with the type '{error_type}'."


def test_bad_reader_arguments_model_empty_list_for_variable(
    valid_reader_arguments_model_data,
):
    """Tests ReaderArgumentsModel with empty list input for variable field."""
    valid_reader_arguments_model_data["variables"] = []

    model = workflows.ReaderArgumentsModel(**valid_reader_arguments_model_data)

    assert model.variables == []


def test_bad_reader_arguments_model_chans_deprecation(
    caplog, valid_reader_arguments_model_data
):
    """Tests ReaderArgumentsModel with valid inputs."""
    invalid_test_data = copy.deepcopy(valid_reader_arguments_model_data)
    invalid_test_data["chans"] = invalid_test_data.pop("variables")

    with caplog.at_level("WARNING"):
        model = workflows.ReaderArgumentsModel(**invalid_test_data)

    # Assert model still created
    assert model

    # Check that a warning was logged
    assert any("'chans' is deprecated" in msg for msg in caplog.messages)
