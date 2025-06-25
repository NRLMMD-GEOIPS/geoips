# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Test Order-based procflow ReaderArgumentsModel."""

from copy import deepcopy
import yaml
from importlib.resources import files

# Third-Party Libraries
import pytest

# GeoIPS Libraries
from geoips.pydantic import workflows
from tests.unit_tests.pydantic.utils import (
    PathDict,
    load_test_cases,
    validate_bad_plugin,
    validate_base_plugin,
    validate_neutral_plugin,
)


test_cases_bad = load_test_cases("workflows", "bad")
test_cases_neutral = load_test_cases("workflows", "neutral")

good_yaml = yaml.safe_load(
    open(str(files("geoips") / "plugins/yaml/workflows/read_test.yaml"), mode="r")
)

base_yaml["abspath"] = str(files("geoips") / "plugins/yaml/workflows/read_test.yaml")
base_yaml["relpath"] = "plugins/yaml/workflows/read_test.yaml"
base_yaml["package"] = "geoips"


@pytest.fixture
def good_reader_arguments_instance():
    """Return a consistent dictionary that is a valid GeoIPS sector plugin."""
    # Make the loading code only occur once, return a copy every time
    return PathDict(deepcopy(base_yaml))


@pytest.mark.parametrize(
    "good_reader_arguments_instance",
    [pytest.param("good_reader_arguments_instance", id="valid_ReaderArgumentsModel")],
    indirect=True,
)
def test_good_reader_arguments_model_instance(good_reader_arguments_instance):
    """Assert that a well formatted ReaderArgumentsModel is valid.

    Parameters
    ----------
    good_sector: dict
        - A dictionary representing a valid sector plugin.
    """
    validate_base_plugin(good_reader_arguments_instance, workflows.ReaderArgumentsModel)


@pytest.mark.parametrize(
    "test_tup", test_cases_bad.values(), ids=list(test_cases_bad.keys())
)
def test_bad_reader_arguments_instance(good_reader_arguments_instance, test_tup):
    """Perform validation on reader plugins with known failing cases.

    Parameters
    ----------
    good_reader: dict
        - A dictionary representing a reader plugin that is valid.
    test_tup:
        - A tuple formatted (key, value, class, err_str), formatted (str, any, str, str)
          used to run and validate tests.
    """
    validate_bad_plugin(
        good_reader_arguments_instance, test_tup, workflows.ReaderArgumentsModel
    )


@pytest.mark.parametrize("test_tup", test_cases_neutral.values(), ids=list(test_cases_neutral.keys()))
def test_neutral_reader_arguments_instance(good_reader_arguments_instance, test_tup):
    """Perform validation on reader plugins with known failing cases.

    Parameters
    ----------
    good_reader: dict
        - A dictionary representing a reader plugin that is valid.
    test_tup:
        - A tuple formatted (key, value, class, err_str), formatted (str, any, str, str)
          used to run and validate tests.
    """
    validate_neutral_plugin(
        good_reader_arguments_instance, test_tup, workflows.ReaderArgumentsModel
    )
