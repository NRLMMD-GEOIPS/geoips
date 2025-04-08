"""Testing module for Pydantic SectorPluginModel."""

from copy import deepcopy

import pytest

from geoips.pydantic.sectors import SectorPluginModel
from tests.unit_tests.pydantic.utils import (
    PathDict,
    load_test_cases,
    load_geoips_yaml_plugin,
    validate_bad_plugin,
    validate_good_plugin,
)

interface = "sectors"

test_cases = load_test_cases(interface)
good_yaml = load_geoips_yaml_plugin(interface, "korea")


@pytest.fixture
def good_sector():
    """Return a consistent dictionary that is a valid GeoIPS sector plugin."""
    # Make the loading code only occur once, return a copy every time
    return PathDict(deepcopy(good_yaml))


@pytest.mark.parametrize(
    "good_sector",
    [pytest.param("good_sector", id="good_sector")],
    indirect=True,
)
def test_good_sector(good_sector):
    """Assert that a well formatted sector plugin is valid.

    Parameters
    ----------
    good_sector: dict
        - A dictionary representing a valid sector plugin.
    """
    validate_good_plugin(good_sector, SectorPluginModel)


@pytest.mark.parametrize("test_tup", test_cases.values(), ids=list(test_cases.keys()))
def test_bad_sector_plugins(good_sector, test_tup):
    """Perform validation on static sector plugins, including failing cases.

    Parameters
    ----------
    good_sector: dict
        - A dictionary representing a sector plugin that is valid.
    test_tup:
        - A tuple formatted (key, value, class, err_str), formatted (str, any, str, str)
          used to run and validate tests.
    """
    validate_bad_plugin(good_sector, test_tup, SectorPluginModel)
