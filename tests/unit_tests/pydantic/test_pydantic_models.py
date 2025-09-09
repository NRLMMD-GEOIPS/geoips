"""Testing module for Pydantic PluginModels."""

from copy import deepcopy

import pytest

from tests.unit_tests.pydantic.utils import (
    PathDict,
    load_test_cases,
    load_geoips_yaml_plugin,
    retrieve_model,
    validate_bad_plugin,
    validate_base_plugin,
    validate_neutral_plugin,
)


# A mapping of interfaces implemented in pydantic and a plugin to validate against.
models_available = {
    "feature_annotators": "default_oldlace",
    "gridline_annotators": "default_palegreen",
    "products": ("abi", "Infrared"),
    "product_defaults": "windbarbs",
    "sectors": "korea",
}


def load_good_plugins(models_available):
    """Generate a dictionary of valid GeoIPS plugins.

    Parameters
    ----------
    models_available: dict
        - A dictionary of interfaces and plugin names. Formatted:
          {interface_name: plugin_name}

    Returns
    -------
    good_plugins: dict
        - A dictionary of interfaces and their corresponding valid plugin. Formatted:
          {interface_name: plugin[dict]}
    """
    good_plugins = {}
    for interface, plugin in models_available.items():
        good_plugins[interface] = load_geoips_yaml_plugin(interface, plugin)

    return good_plugins


# Generate separate test cases for each interface
def generate_test_cases(test_type):
    """Generate test cases used for pydantic validation.

    Where each case is a pytest parameter set, Formatted:
    param(argval=(interface_name, test_case[dict]), id={interface_name}_{test_id})

    Parameters
    ----------
    test_type: str
        - The type of test being ran. Must be one of ["bad", "neutral"].

    Returns
    -------
    cases: list[pytest.param]
        - A list of pytest parameters representing cases to test.

    Raises
    ------
    ValueError:
        - Raised if test_type isn't one of 'bad' or 'neutral'. (Raised via
          load_test_cases).
    """
    cases = []
    for interface in models_available.keys():
        test_cases = load_test_cases(interface, test_type)
        for key, value in test_cases.items():
            print(interface, key)
            cases.append(pytest.param((interface, value), id=f"{interface}_{key}"))
    return cases


good_plugins = load_good_plugins(models_available)


@pytest.mark.parametrize(
    "good_plugin",
    good_plugins.values(),
    ids=list(models_available.keys()),
)
def test_good_plugin(good_plugin):
    """Assert that a well formatted GeoIPS plugin is valid.

    Parameters
    ----------
    good_plugin: dict
        - A dictionary representing a valid GeoIPS plugin.
    """
    model = retrieve_model(good_plugin)
    validate_base_plugin(good_plugin, model)


@pytest.mark.parametrize("test_tup", generate_test_cases("bad"))
def test_bad_plugins(test_tup):
    """Perform validation on GeoIPS plugins, including failing cases.

    Parameters
    ----------
    test_tup:
        - A tuple formatted (interface_name, (key, value, class, err_str)), Formatted:
          (str, (str, any, str, str)) used to run and validate tests.
    """
    plugin = PathDict(deepcopy(good_plugins[test_tup[0]]))
    model = retrieve_model(plugin)
    validate_bad_plugin(plugin, test_tup[1], model)


@pytest.mark.parametrize("test_tup", generate_test_cases("neutral"))
def test_neutral_plugins(test_tup):
    """Perform validation on GeoIPS plugins, including neutral cases.

    Parameters
    ----------
    test_tup:
        - A tuple formatted (interface_name, (key, value, class, err_str)), Formatted:
          (str, (str, any, str, str)) used to run and validate tests.
    """
    plugin = PathDict(deepcopy(good_plugins[test_tup[0]]))
    model = retrieve_model(plugin)
    validate_neutral_plugin(plugin, test_tup[1], model)
