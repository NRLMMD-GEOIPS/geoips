# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Testing module for Pydantic FeatureAnnotatorPluginModel."""

from copy import deepcopy

import pytest

from geoips.pydantic_models.v1.feature_annotators import FeatureAnnotatorPluginModel
from tests.unit_tests.pydantic_models.v1.utils import (
    PathDict,
    load_test_cases,
    load_geoips_yaml_plugin,
    validate_bad_plugin,
    validate_base_plugin,
)

interface = "feature_annotators"

test_cases_bad = load_test_cases(interface, "bad")
good_yaml = load_geoips_yaml_plugin(interface, "default_oldlace")


@pytest.fixture
def good_feature_annotator():
    """Return a consistent dictionary that is a valid GeoIPS feature annotator."""
    # Make the loading code only occur once, return a copy every time
    return PathDict(deepcopy(good_yaml))


@pytest.mark.parametrize(
    "good_feature_annotator",
    [pytest.param("good_feature_annotator", id="good_feature_annotator")],
    indirect=True,
)
def test_good_feature_annotator(good_feature_annotator):
    """Assert that a well formatted feature annotator plugin is valid.

    Parameters
    ----------
    good_feature_annotator: dict
        - A dictionary representing a valid feature annotator plugin.
    """
    validate_base_plugin(good_feature_annotator, FeatureAnnotatorPluginModel)


@pytest.mark.parametrize(
    "test_tup", test_cases_bad.values(), ids=list(test_cases_bad.keys())
)
def test_bad_feature_annotator_plugins(good_feature_annotator, test_tup):
    """Perform validation on feature_annotator plugins, including failing cases.

    Parameters
    ----------
    good_feature_annotator: dict
        - A dictionary representing a feature_annotator plugin that is valid.
    test_tup:
        - A tuple formatted (key, value, class, err_str), formatted (str, any, str, str)
          used to run and validate tests.
    """
    validate_bad_plugin(good_feature_annotator, test_tup, FeatureAnnotatorPluginModel)
