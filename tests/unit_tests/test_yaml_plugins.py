import pytest

import jsonschema
from pathlib import Path

from geoips.schema import validate


test_path = Path(__file__).parent
yaml_plugins = Path("./geoips/interface_modules/").rglob("*.yaml")
bad_yaml_plugins = Path(f"{test_path}/bad_plugins").rglob("*.yaml")


@pytest.mark.parametrize("plugin_file", yaml_plugins)
def test_is_plugin_valid(plugin_file):
    validate(plugin_file)


@pytest.mark.parametrize("plugin_file", bad_yaml_plugins)
def test_is_plugin_invalid(plugin_file):
    with pytest.raises(jsonschema.exceptions.ValidationError):
        validate(plugin_file)
