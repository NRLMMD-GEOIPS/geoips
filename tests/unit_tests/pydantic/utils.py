# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Generic testing utilities used for pydantic unit testing."""

# from collections import UserDict
import logging
from importlib.resources import files
import os
import pytest
from copy import deepcopy
from pydantic import ValidationError
import yaml

from geoips import interfaces
from geoips import pydantic as geoips_pydantic


LOG = logging.getLogger(__name__)


class PathDict(dict):
    """Custom dictionary class used to access GeoIPS plugins using paths.

    Where a 'path' is a key which can include slashes ('/') for easy access to the
    values contained in nested dictionaries.

    I.e. some_dict["key1/key2/key3"] = some_val

    This is essentially the same thing as a dict object besides the __setitem__ method.
    Not inheriting from that class to avoid unexpected consequences.
    """

    def __setitem__(self, key, value):
        """Set an item under key with value 'value'.

        Custom implementation of dict's __setitem__, which makes use of paths to
        set an item which may be multiple levels deep.

        Parameters
        ----------
        key: str
            - The path to the attribute to set
        value: any
            - The value to set the attribute to.
        """
        keys = key.split("/")
        if len(keys) > 1:
            current = self
            for subkey in keys[:-1]:
                current = current.setdefault(subkey, {})
            dict.__setitem__(current, keys[-1], value)
        else:
            dict.__setitem__(self, key, value)


def load_test_cases(interface_name):
    """Load a set of test cases used to validate pydantic model(s).

    This can either be a top level model, such as SectorPluginModel, or a component
    of that model.

    Parameters
    ----------
    interface_name: str
        - The name of the interface that's going to be tested.

    Returns
    -------
    test_cases: dict
        - The dictionary of test cases used to validate your model.
    """
    fpath = f"{os.path.dirname(__file__)}/{interface_name}/test_cases.yaml"
    if not os.path.exists(fpath):
        raise FileNotFoundError(
            f"Error: No test cases file could be found. Expected {fpath} but it did not"
            " exist. Please create this file and rerun your tests."
        )
    with open(fpath, "r") as fo:
        test_cases = yaml.safe_load(fo)

    for id, val in test_cases.items():
        for key in list(val.keys()):
            if key not in ("key", "val", "cls", "err_str", "warn_match"):
                error = (
                    f"ERROR: test_case '{id}' has item with key '{key}' which is an "
                    "invalid test case key. We only support the full set of keys "
                    "[key, val, cls, err_str] at this moment."
                )
                raise RuntimeError(error)
    return test_cases


def load_geoips_yaml_plugin(interface_name, plugin_name):
    """Load a GeoIPS YAML plugin via yaml.safe_load, not interface.get_plugin.

    This will be used until we convert all of our schema to pydantic. If we load a
    plugin via <interface>.get_plugin, this sometimes will cause errors due to different
    validation protocols.

    Parameters
    ----------
    interface_name: str
        - The name of the GeoIPS plugin's interface.
    plugin_name: str
        - The name of the plugin of type 'interface_name'.

    Returns
    -------
    yam: dict
        - A dictionary object representing the yaml plugin requested.
    """
    yam_ints = interfaces.list_available_interfaces()["yaml_based"]
    if interface_name not in yam_ints:
        raise KeyError(
            f"'{interface_name}' is not a valid yaml interface. Please select an "
            f"interface out of any of the following {yam_ints}."
        )
    interface = getattr(interfaces, interface_name)
    registry = interface.plugin_registry.registered_plugins["yaml_based"][
        interface_name
    ]
    if isinstance(plugin_name, tuple):
        # Likely a product. Do a nested search for the plugin.
        entry = registry[plugin_name[0]][plugin_name[1]]
    else:
        entry = registry[plugin_name]

    relpath = entry["relpath"]
    abspath = str(files("geoips") / relpath)
    package = "geoips"

    with open(abspath, "r") as fo:
        yam = yaml.safe_load(fo)
    # Append these attributes to the plugin for further validation. 'get_plugin'
    # already does this, but since we're loading in a different manner, we do this
    # manually for the time being.
    yam["abspath"] = abspath
    yam["relpath"] = relpath
    yam["package"] = package

    return yam


def validate_good_plugin(good_plugin, plugin_model):
    """Assert that a well formatted plugin is valid.

    Parameters
    ----------
    good_plugin: dict
        - A dictionary representing a valid plugin.
    plugin_model: instance or child of geoips.pydantic.bases.PluginModel
        - The pydantic-based model used to validate this plugin.
    """
    plugin_model(**good_plugin)


def _validate_test_tup_keys(test_tup: dict) -> tuple:
    """Ensure test_tup contains either 'err_str' or 'warn_match', and extract values.

    Parameters
    ----------
    test_tup:
        - A dictionary containing the following keys:
            - 'key' (str): Path to the attribute being mutated.
            - 'val' (any): The value to set for the given key.
            - 'cls' (str): The name of the model expected to fail.
            - 'err_str' (str, optional): Expected error message fragment for the
                ValidationError.
            - 'warn_match' (str, optional): Expected warning message fragment if a
                warning is tested.

    Returns
    -------
    tuple
        (key, value, cls, err_str / warn_match)

    Raises
    ------
    ValueError
        If neither or both 'err_str' and 'warn_match' are provided.
    """
    key = test_tup["key"]
    val = test_tup["val"]
    failing_model = test_tup["cls"]
    err_str = test_tup.get("err_str")
    warn_match = test_tup.get("warn_match")

    if err_str is not None and warn_match is not None:
        raise ValueError("Only one of 'err_str' or 'warn_match' should be set.")
    elif err_str is None and warn_match is None:
        raise ValueError("At least one of 'err_str' or 'warn_match' must be provided.")

    return key, val, failing_model, err_str, warn_match


def _resolve_model_class(failing_model):
    """Resolve the actual Pydantic model class by name."""
    for mod in geoips_pydantic._modules:
        if failing_model in geoips_pydantic._classes[mod]:
            return getattr(geoips_pydantic._modules[mod], failing_model)
        if hasattr(geoips_pydantic._modules[mod], failing_model):
            # This behavior occurs for the 'ColorType' attribute, which is
            # a type instance but not actually a pydantic class.
            return None
    return None


def _attempt_to_associate_model_with_error(
    failing_model: str, errors: list[dict]
) -> dict:
    """Attempt to associate the correct error with the model that should be failing.

    This occurs when more than one error was raised for a given test. Assuming that
    two fields were not incorrect, only one, then this means that a field is one of a
    Union of models and/or other fields. Attempt to locate the correct error based on
    the model provided.

    Parameters
    ----------
    failing_model: str
        - The name (case sensitive) of the model that we expect to raise this error
    errors: pydantic.ValidationError.errors() -- list
        - A list of errors containing information on why a field failed to validate.

    """
    for error in reversed(errors):
        if failing_model in error.get("loc", ()):
            return error

    # If no errors could be associated with the failing model, just default
    # to the last error reported
    return errors[-1]


def validate_bad_plugin(good_plugin, test_tup, plugin_model):
    """Perform validation on any GeoIPS plugin, ensuring correct ValidationErrors occur.

    Current supported plugins include readers and sectors. More to come in the future,
    and this function might change because of that. This is a beta method for the time
    being.

    Parameters
    ----------
    good_plugin: dict
        - A dictionary representing a plugin that is valid.
    test_tup:
        - A tuple formatted (key, value, class, err_str), formatted (str, any, str, str)
          used to run and validate tests.
    plugin_model: instance or child of geoips.pydantic.bases.PluginModel
        - The pydantic-based model used to validate this plugin.
    """
    key, val, failing_model, err_str, warn_match = _validate_test_tup_keys(test_tup)

    bad_plugin = deepcopy(good_plugin)
    bad_plugin[key] = val

    # ValidationErrors won't occur for these fields at the moment.
    # Skip the testing until the validators are implemented.
    validation_to_be_implemented = ["abspath", "relpath", "package"]
    if key in validation_to_be_implemented:
        return

    if warn_match:
        with pytest.warns(FutureWarning, match=warn_match):
            plugin_model(**bad_plugin)
        return

    try:
        plugin_model(**bad_plugin)
    except ValidationError as e:
        # The code below assumes that your test only raised one error. That's how
        # we've structured testing for the time being. In the case that one or more
        # errors are reported, we default to the last error of the failing model
        # reported, or, if no failing model could be associated with this error, we
        # just default to the last error reported.
        errors = e.errors()
        if len(e.errors()) > 1:
            val_err = _attempt_to_associate_model_with_error(failing_model, errors)
        else:
            val_err = errors[0]
        # In Pydantic ValidationError, the last element of 'loc' tuple identifies
        # the failing attribute
        bad_field = val_err["loc"][-1]
        err_msg = val_err["msg"]

        model_class = _resolve_model_class(failing_model)

        if model_class:
            assert (
                bad_field in model_class.model_fields
            ), f"Field '{bad_field}' not found in model '{failing_model}'"
        if err_str:
            assert (
                err_str in err_msg or err_str == err_msg
            ), f"Expected error message to match: \n {err_str} \n Got:\n{err_msg}"
    else:
        assert False, f"Expected ValidationError for key '{key}', but none was raised."
