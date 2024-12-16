# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Test Order-based procflow ReaderArgumentsModel."""

# Python Standard Libraries
import copy
import pytest

from pydantic import ValidationError

from geoips.pydantic import products


def test_good_valid_reader_arguments_model(valid_reader_arguments_model_data):
    """Tests ReaderArgumentsModel with valid inputs."""
    model = products.ReaderArgumentsModel(**valid_reader_arguments_model_data)

    assert model.area_def == "None"
    assert model.chans == ["None"]
    assert model.metadata_only is True
    assert model.self_register is True


def test_bad_reader_arguments_model_field_defaults():
    """Tests if the default value for a given field is valid or not."""
    model = products.ReaderArgumentsModel()

    expected_defaults = {
        "area_def": None,
        "chans": None,
        "metadata_only": False,
        "self_register": False,
    }

    for field, expected_value in expected_defaults.items():
        assert (
            getattr(model, field) == expected_value
        ), f"Default value for '{field}' is incorrect"


def test_bad_reader_arguments_model_invalid_field_type():
    """Tests ReaderArgumentsModel for invalid field type instantiation."""
    invalid_test_data = {
        "area_def": 123,
        "chans": "channel_1",
        "metadata_only": "invalid",
        "self_register": "invalid",
    }

    with pytest.raises(ValidationError) as exec_info:
        products.ReaderArgumentsModel(**invalid_test_data)

    error_info = exec_info.value.errors()

    test_data_errors = {
        "area_def": "string_type",
        "chans": "list_type",
        "metadata_only": "bool_parsing",
    }
    for field, error_type in test_data_errors.items():
        assert any(
            err["loc"] == (field,) and err["type"] == error_type for err in error_info
        ), f"Expected error for the field '{field}' with the type '{error_type}'."


def test_bad_reader_arguments_model_additional_field(valid_reader_arguments_model_data):
    """Tests ReaderArgumentsModel with additonal field."""
    invalid_data = copy.deepcopy(valid_reader_arguments_model_data)
    invalid_data["unexpected_field"] = "unexpected_value"

    with pytest.raises(ValidationError) as exec_info:
        products.ReaderArgumentsModel(**invalid_data)

    error_info = exec_info.value.errors()
    assert any(
        err["type"] == "extra_forbidden" for err in error_info
    ), "expected 'extra_frobidden' error type"
    assert "unexpected_field" in str(
        exec_info.value
    ), "Unexpected field should be rejected by ReaderArgumentsModel"


def test_bad_reader_arguments_model_empty_list_for_chans(
    valid_reader_arguments_model_data,
):
    """Tests ReaderArgumentsModel with empty list input for chans field."""
    valid_reader_arguments_model_data["chans"] = []

    model = products.ReaderArgumentsModel(**valid_reader_arguments_model_data)

    assert model.chans == []
