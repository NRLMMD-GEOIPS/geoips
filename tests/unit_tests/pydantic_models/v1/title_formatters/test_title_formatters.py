# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Testing module for Pydantic TitleFormatterArgumentsModel."""

# Third-Party Libraries
import pytest

# GeoIPS Libraries
from geoips.pydantic_models.v1.title_formatters import TitleFormatterArgumentsModel
from tests.unit_tests.pydantic_models.v1.utils import (
    load_test_cases,
    validate_bad_plugin,
    validate_base_plugin,
)

interface = "title_formatters"

test_cases_bad = load_test_cases(interface, "bad")


def test_good_title_formatter(valid_title_formatter_arguments):
    """Validate a known-good TitleFormatterArgumentsModel configuration.

    Parameters
    ----------
    valid_title_formatter_arguments: dict
        - A dictionary representing a valid title formatter plugin.
    """
    validate_base_plugin(valid_title_formatter_arguments, TitleFormatterArgumentsModel)


@pytest.mark.parametrize(
    "test_tup", test_cases_bad.values(), ids=list(test_cases_bad.keys())
)
def test_bad_title_formatter_plugins(valid_title_formatter_arguments, test_tup):
    """Validate that invalid TitleFormatterArgumentsModel configs fail as expected.

    Parameters
    ----------
    valid_title_formatter_arguments: dict
        - A dictionary representing a valid title formatter plugin.
    test_tup:
        - A tuple formatted (description, key, value, class, err_str), formatted (str,
          any, str, str) used to run and validate tests.
    """
    validate_bad_plugin(
        valid_title_formatter_arguments, test_tup, TitleFormatterArgumentsModel
    )
