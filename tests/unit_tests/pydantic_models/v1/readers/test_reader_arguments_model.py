# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Test Order-based procflow ReaderArgumentsModel."""

import copy

import pytest

# GeoIPS Libraries
from geoips.deprecation import GeoipsDeprecationWarning
from geoips.pydantic_models.v1.readers import ReaderArgumentsModel


def test_reader_arguments_model_chans_deprecation(
    caplog, valid_reader_arguments_model_data
):
    """Tests ReaderArgumentsModel with deprecated inputs."""
    invalid_test_data = copy.deepcopy(valid_reader_arguments_model_data)
    with pytest.warns(
        GeoipsDeprecationWarning,
        match="https://github.com/NRLMMD-GEOIPS/geoips/issues/953",
    ):
        invalid_test_data["chans"] = invalid_test_data.pop("variables")
        model = ReaderArgumentsModel(**invalid_test_data)

    # Assert model still created
    assert model
