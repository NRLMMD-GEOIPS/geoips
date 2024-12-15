# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Test Order-based procflow product building classes."""
import copy
import pytest

from pydantic import ValidationError

from geoips.pydantic import products

# Tests for ReaderArgumentsModel


@pytest.fixture
def valid_reader_arguments_model_data():
    """Fixture to provide sample valid Reader arguments for testing."""
    return {
        "area_def": "None",
        "chans": ["None"],
        "metadata_only": False,
        "self_register": False,
    }


def test_good_valid_reader_arguments_model(valid_reader_arguments_model_data):
    """Tests ReaderArgumentsModel with valid inputs."""
    model = products.ReaderArgumentsModel(**valid_reader_arguments_model_data)

    assert model.area_def == "None"
    assert model.chans == ["None"]
    assert model.metadata_only is False
    assert model.self_register is False


def test_bad_reader_arguments_model_field_default(valid_reader_arguments_model_data):
    """Tests if the default value for a given field is valid or not."""
    test_data = copy.deepcopy(valid_reader_arguments_model_data)
    test_data.pop("chans", None)
    model = products.ReaderArgumentsModel(**test_data)

    assert model.chans is None


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

    assert any(
        err["loc"] == ("area_def",) and err["type"] == "string_type"
        for err in error_info
    )
    assert any(
        err["loc"] == ("chans",) and err["type"] == "list_type" for err in error_info
    )
    assert any(
        err["loc"] == ("metadata_only",) and err["type"] == "bool_parsing"
        for err in error_info
    )


def test_bad_reader_arguments_model_additional_field(valid_reader_arguments_model_data):
    """Tests ReaderArgumentsModel with additonal field."""
    invalid_data = copy.deepcopy(valid_reader_arguments_model_data)
    # adding an extra field
    invalid_data["unexpected_field"] = "unexpected_value"

    with pytest.raises(ValidationError) as exec_info:
        products.ReaderArgumentsModel(**invalid_data)

    error_info = exec_info.value.errors()
    assert any(
        err["type"] == "extra_forbidden" for err in error_info
    ), "expected 'extra_frobidden' error type"
    assert "unexpected_field" in str(
        exec_info.value
    ), "Unexpected field should be mentioned in the error"


def test_bad_reader_arguments_model_empty_list_for_chans(
    valid_reader_arguments_model_data,
):
    """Tests ReaderArgumentsModel with empty list input for chans field."""
    valid_reader_arguments_model_data["chans"] = []

    model = products.ReaderArgumentsModel(**valid_reader_arguments_model_data)

    assert model.chans == []