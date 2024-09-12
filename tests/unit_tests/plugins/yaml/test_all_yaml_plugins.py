# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Test all YAML plugins."""
import pytest
import yaml
from importlib import resources, metadata

from geoips.interfaces.base import YamlPluginValidator
from geoips.interfaces.yaml_based.products import ProductsPluginValidator

validator = YamlPluginValidator()
product_validator = ProductsPluginValidator()


def yield_plugins():
    """Yield plugins."""
    plugin_packages = metadata.entry_points(group="geoips.plugin_packages")
    for pkg in plugin_packages:
        fpath = resources.files(pkg.name) / "plugins/yaml"
        plugin_files = fpath.rglob("*.yaml")
        for pf in plugin_files:
            yield pf


def gen_label(val):
    """Generate the yaml name for pytest ids."""
    return val.name


@pytest.mark.parametrize("plugin", yield_plugins(), ids=gen_label)
def test_is_plugin_valid(plugin):
    """Test if plugin is valid."""
    rplugin = yaml.safe_load(open(plugin, "r"))
    if rplugin["interface"] == "products":
        product_validator.validate(rplugin)
    else:
        validator.validate(rplugin)
