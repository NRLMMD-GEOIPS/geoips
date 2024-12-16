# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Fixtures for testing the Order-based procflow pydantic models."""

import pytest


@pytest.fixture
def valid_step_data():
    """Fixture to provide sample valid plugin data for testing."""
    return {
        "type": "reader",
        "name": "abi_netcdf",
        "arguments": {
            "area_def": "None",
            "chans": ["None"],
            "metadata_only": False,
            "self_register": False,
        },
    }



@pytest.fixture
def valid_reader_arguments_model_data():
    """Fixture to provide sample valid Reader arguments for testing."""
    return {
        "area_def": "None",
        "chans": ["None"],
        "metadata_only": True,
        "self_register": True,
    }
