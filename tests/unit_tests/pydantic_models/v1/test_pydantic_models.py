# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Testing module for Pydantic PluginModels."""

# Python Standard Libraries
from copy import deepcopy

# Third-Party Libraries
import pytest

# GeoIPS imports
from geoips.pydantic_models.v1.output_checkers import OutputCheckersArgumentsModel
from tests.unit_tests.pydantic_models.v1.utils import (
    PathDict,
    load_geoips_yaml_plugin,
    load_test_cases,
    retrieve_model,
    validate_bad_plugin,
    validate_base_plugin,
    validate_neutral_plugin,
)

# A mapping of interfaces implemented in pydantic and a plugin to validate against.
models_available = {
    "feature_annotators": {
        "good_source": ("yaml", "default_oldlace"),
        "model": None,
    },
    "gridline_annotators": {
        "good_source": ("yaml", "default_palegreen"),
        "model": None,
    },
    "sectors": {
        "good_source": ("yaml", "korea"),
        "model": None,
    },
    "output_checkers": {
        "good_source": ("fixture", "valid_output_checker_arguments"),
        "model": OutputCheckersArgumentsModel,
    },
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
    for interface, cfg in models_available.items():
        source_type, plugin = cfg["good_source"]
        if source_type == "yaml":
            good_plugins[interface] = load_geoips_yaml_plugin(interface, plugin)
    return good_plugins


good_plugins = load_good_plugins(models_available)


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
            cases.append(pytest.param((interface, key, value), id=f"{interface}_{key}"))
    return cases


def get_good_plugin(interface, request):
    """
    Return a "known-good" plugin instance or config for the given interface.

    Source of the good plugin is defined in `models_available[interface]["good_source"]`
    as a tuple: (source_type, source_value), where:

    - source_type == "yaml": return `good_plugins[interface]`
    - source_type == "fixture" return `request.getfixturevalue(source_value)`

    Parameters
    ----------
    interface : str
        GeoIPS interface name such as readers.
    request : pytest.FixtureRequest
        Pytest request object used to resolve fixture-based sources.

    Returns
    -------
    Any
        The good plugin object or config for the given interface.

    """
    cfg = models_available.get(interface)
    if cfg is None:
        raise KeyError(
            f"Unknown interface '{interface}' provided."
            f" Available: {sorted(models_available)}"
        )

    try:
        source_type, source_value = cfg["good_source"]
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"Invalid good_source for interface '{interface}'"
            f"(source_type, source_value), got {cfg.get('good_source')!r}"
        ) from exc

    if source_type == "yaml":
        try:
            return good_plugins[interface]
        except KeyError as exc:
            raise KeyError(
                f"Missing good_plugins entry for interface '{interface}'"
            ) from exc

    if source_type == "fixture":
        if not source_value:
            raise ValueError(
                f"Fixture for the interface '{interface}' is empty or None:"
                f"{source_value!r}"
            )
        return request.getfixturevalue(source_value)

    raise ValueError(
        f"unknown good_source type: {source_type} for interface '{interface}': "
        f"{source_type!r}. should be 'yaml' or 'fixture'"
    )


def get_model(interface, plugin):
    """Return the Pydantic model used to validate a plugin for a given interface."""
    cfg = models_available[interface]
    if cfg["model"] is not None:
        return cfg["model"]
    return retrieve_model(plugin)


@pytest.mark.parametrize("interface", list(models_available.keys()))
def test_good_plugin(interface, request):
    """Assert that a well formatted GeoIPS plugin is valid.

    Parameters
    ----------
    good_plugin: dict
        - A dictionary representing a valid GeoIPS plugin.
    """
    good_plugin = get_good_plugin(interface, request)
    model = get_model(interface, good_plugin)
    validate_base_plugin(good_plugin, model)


@pytest.mark.parametrize("test_case", generate_test_cases("bad"))
def test_bad_plugins(test_case, request):
    """Perform validation on GeoIPS plugins, including failing cases.

    Parameters
    ----------
    test_tup:
        - A tuple formatted (interface_name, (key, value, class, err_str)), Formatted:
          (str, (str, any, str, str)) used to run and validate tests.
    """
    interface, _key, case_value = test_case

    good_plugin = get_good_plugin(interface, request)
    plugin = PathDict(deepcopy(good_plugin))
    model = get_model(interface, plugin)

    validate_bad_plugin(plugin, case_value, model)


@pytest.mark.parametrize("test_case", generate_test_cases("neutral"))
def test_neutral_plugins(test_case, request):
    """Perform validation on GeoIPS plugins, including neutral cases.

    Parameters
    ----------
    test_tup:
        - A tuple formatted (interface_name, (key, value, class, err_str)), Formatted:
          (str, (str, any, str, str)) used to run and validate tests.
    """
    interface, _key, case_value = test_case

    good_plugin = get_good_plugin(interface, request)
    plugin = PathDict(deepcopy(good_plugin))
    model = get_model(interface, plugin)

    validate_neutral_plugin(plugin, case_value, model)
