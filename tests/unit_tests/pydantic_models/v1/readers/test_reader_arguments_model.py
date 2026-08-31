# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Test Order-based procflow ReaderArgumentsModel."""

import copy

# GeoIPS Libraries
from geoips.pydantic_models.v1.readers import ReaderArgumentsModel


def test_reader_arguments_model_chans_deprecation(
    caplog, valid_reader_arguments_model_data
):
    """Tests ReaderArgumentsModel with valid inputs."""
    invalid_test_data = copy.deepcopy(valid_reader_arguments_model_data)
    invalid_test_data["chans"] = invalid_test_data.pop("variables")

    with caplog.at_level("WARNING"):
        model = ReaderArgumentsModel(**invalid_test_data)

    # Assert model still created
    assert model

    # Check that a warning was logged
    assert any(
        "'chans' is deprecated and will be removed in GeoIPS 2.0." in msg
        for msg in caplog.messages
    )
