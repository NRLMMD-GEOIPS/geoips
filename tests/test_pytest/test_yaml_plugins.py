import pytest

import jsonschema
from pathlib import Path
from importlib import resources

from geoips.schema import validate


test_path = Path(__file__).parent
package_path = Path(resources.files("geoips"))

# yaml_plugins = Path(f"{package_path}/interface_modules/").rglob("*.yaml")
plugins_to_test = [
    "boundaries",
    "gridlines",
    "dynamic_sectors",
    "static_sectors",
]
yaml_plugins = []
for plg in plugins_to_test:
    yaml_plugins.extend(Path(f"{package_path}/interface_modules/{plg}").rglob("*.yaml"))
bad_yaml_plugins = Path(f"{test_path}/bad_plugins").rglob("*.yaml")


@pytest.mark.parametrize("plugin_file", yaml_plugins)
def test_is_plugin_valid(plugin_file):
    """Test whether a plugin validates against its interface's schema."""
    validate(plugin_file)


@pytest.mark.parametrize("plugin_file", bad_yaml_plugins)
def test_is_plugin_invalid(plugin_file):
    """Test that a plugin fails to validate against its interface's schema."""
    with pytest.raises(jsonschema.exceptions.ValidationError):
        validate(plugin_file)
