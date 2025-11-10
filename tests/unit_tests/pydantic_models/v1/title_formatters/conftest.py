# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Fixtures for testing the Order-based procflow TitleFormatterArguments pydantic model."""

# Third-Party Libraries
import pytest


@pytest.fixture
def valid_title_formatter_arguments():
    """Fixture to provide sample valid plugin data for testing TitleFormatterArgumentsModel."""
    return {
        "area_def": "test_string",
        "product_name_title": "tc_copyright",
        "product_datatype_title": "test_string",
        "bg_product_name_title": "test_string",
        "bg_datatype_title": "test_string",
        "title_copyright": "Data copyright 2021 EUMETSAT, Imagery NRL-MRY",
    }
