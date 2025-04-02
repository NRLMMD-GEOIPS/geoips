# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Test Pydantic base models for Order-Based Procflow."""

from copy import deepcopy
from importlib.resources import files

import pytest
import yaml

from geoips.pydantic.bases import PluginModel
from tests.unit_tests.pydantic.utils import (
    PathDict,
    load_test_cases,
    validate_bad_plugin,
    validate_good_plugin,
)


test_cases = load_test_cases("./test_pydantic_base_cases.yaml")
good_yaml = yaml.safe_load(
    open(str(files("geoips") / "plugins/yaml/workflows/read_test.yaml"), mode="r")
)

good_yaml["abspath"] = str(files("geoips") / "plugins/yaml/workflows/read_test.yaml")
good_yaml["relpath"] = "plugins/yaml/workflows/read_test.yaml"
good_yaml["package"] = "geoips"


@pytest.fixture
def good_plugin():
    """Return a consistent dictionary that is a valid GeoIPS base plugin."""
    # Make the loading code only occur once, return a copy every time
    return PathDict(deepcopy(good_yaml))


@pytest.mark.parametrize(
    "good_plugin",
    [pytest.param("good_plugin", id="good_plugin")],
    indirect=True,
)
def test_good_plugin(good_plugin):
    """Assert that a well formatted base plugin is valid.

    Parameters
    ----------
    good_sector: dict
        - A dictionary representing a valid sector plugin.
    """
    validate_good_plugin(good_plugin, PluginModel)


@pytest.mark.parametrize("test_tup", test_cases.values(), ids=list(test_cases.keys()))
def test_bad_plugins(good_plugin, test_tup):
    """Perform validation on base plugin, including failing cases.

    Parameters
    ----------
    good_sector: dict
        - A dictionary representing a pydantic base plugin that is valid.
    test_tup:
        - A tuple formatted (key, value, class, err_str), formatted (str, any, str, str)
          used to run and validate tests.
    """
    validate_bad_plugin(good_plugin, test_tup, PluginModel)