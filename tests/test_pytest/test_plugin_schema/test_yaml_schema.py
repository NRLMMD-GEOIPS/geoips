import pytest

import re
import yaml
from jsonschema.exceptions import ValidationError  # noqa
from pathlib import Path

from geoips.schema.plugin_validator import PluginValidator


test_path = Path(__file__).parent
validator = PluginValidator()


def get_error(name):
    try:
        exc = getattr(__builtins__, name)
    except AttributeError:
        try:
            exc = globals()[name]
        except KeyError:
            raise ValueError(f"{name} is not a known exception")
    if not issubclass(exc, Exception):
        raise ValueError(f"{name} is not a valid exception")
    return exc


def path_to_id(fname):
    fpath = Path(fname).relative_to(test_path)
    parts = list(fpath.parent.parts[1:])
    parts.append(fpath.stem)
    id = ".".join(parts)
    return id


def yield_bad_plugins():
    bad_files = {path_to_id(fname): fname for fname in test_path.rglob("bad/**/*.yaml")}
    for validator_name, bad_file in bad_files.items():
        plugins = yaml.safe_load_all(open(bad_file, "r"))
        for plugin in plugins:
            yield validator_name, plugin


def yield_good_plugins():
    good_files = {
        path_to_id(fname): fname for fname in test_path.rglob("good/**/*.yaml")
    }
    for validator_name, good_file in good_files.items():
        plugins = yaml.safe_load_all(open(good_file, "r"))
        for plugin in plugins:
            yield validator_name, plugin


# plugins_to_test = [
#     "feature_annotators",
#     "gridline_annotators",
#     "product_defaults",
# ]
# good_yaml_plugins = []
# for plg in plugins_to_test:
#     good_yaml_plugins.extend(Path(f"{package_path}/plugins/{plg}").rglob("*.yaml"))


@pytest.mark.parametrize("validator_name, plugin", yield_good_plugins())
def test_is_plugin_valid(validator_name, plugin):
    """Test whether a plugin validates against its interface's schema."""
    validator.validate(plugin, validator_id=validator_name)


@pytest.mark.parametrize("validator_name, plugin", yield_bad_plugins())
def test_is_plugin_invalid(validator_name, plugin):
    """Test that a plugin fails to validate against its interface's schema."""
    try:
        error_pattern = plugin.pop("error_pattern", None)
    except (AttributeError, TypeError):
        error_pattern = None
    try:
        error_name = plugin.pop("error", "ValidationError")
    except (AttributeError, TypeError):
        error_name = "ValidationError"
    error = get_error(error_name)

    with pytest.raises(error) as excinfo:
        validator.validate(plugin, validator_id=validator_name)
    if error_pattern is not None:
        assert re.match(error_pattern, str(excinfo.value))
