"""Testing module for Pydantic SectorPluginModel."""

from copy import deepcopy
from importlib.resources import files

import pytest
import yaml

from geoips.pydantic.sectors import SectorPluginModel
from tests.unit_tests.pydantic.utils import (
    PathDict,
    load_test_cases,
    validate_bad_plugin,
    validate_good_plugin,
    validate_neutral_plugin,
)

interface = "sectors"


test_cases_bad = load_test_cases(interface, "bad")
test_cases_neutral = load_test_cases(interface, "neutral")


with open(str(files("geoips") / "plugins/yaml/sectors/static/korea.yaml"), "r") as fo:
    good_yaml = yaml.safe_load(fo)

good_yaml["abspath"] = str(files("geoips") / "plugins/yaml/sectors/static/korea.yaml")
good_yaml["relpath"] = "plugins/yaml/sectors/static/korea.yaml"
good_yaml["package"] = "geoips"


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


@pytest.mark.parametrize("test_tup", test_cases_bad.values(), ids=list(test_cases_bad.keys()))
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


@pytest.mark.parametrize("test_tup", test_cases_neutral.values(), ids=list(test_cases_neutral.keys()))
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
    validate_neutral_plugin(good_sector, test_tup, SectorPluginModel)
