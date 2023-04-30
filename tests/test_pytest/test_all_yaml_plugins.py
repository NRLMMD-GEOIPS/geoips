import pytest
import yaml
from importlib import resources

from geoips.schema import PluginValidator


validator = PluginValidator()


def yield_plugins():
    fpath = resources.files("geoips") / "plugins/yaml"
    plugin_files = fpath.rglob("*.yaml")
    for pf in plugin_files:
        yield yaml.safe_load(open(pf, "r"))


@pytest.mark.parametrize("plugin", yield_plugins())
def test_is_plugin_valid(plugin):
    validator.validate(plugin)
