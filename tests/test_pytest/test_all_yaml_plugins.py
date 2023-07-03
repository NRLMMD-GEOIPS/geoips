# # # Distribution Statement A. Approved for public release. Distribution unlimited.
# # #
# # # Author:
# # # Naval Research Laboratory, Marine Meteorology Division
# # #
# # # This program is free software: you can redistribute it and/or modify it under
# # # the terms of the NRLMMD License included with this program. This program is
# # # distributed WITHOUT ANY WARRANTY; without even the implied warranty of
# # # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the included license
# # # for more details. If you did not receive the license, for more information see:
# # # https://github.com/U-S-NRL-Marine-Meteorology-Division/

"""Test all YAML plugins."""
import pytest
import yaml
from importlib import resources

from geoips.interfaces.base import YamlPluginValidator
from geoips.interfaces.yaml_based.products import ProductsPluginValidator
from geoips.geoips_utils import get_entry_point_group

validator = YamlPluginValidator()
product_validator = ProductsPluginValidator()


def yield_plugins():
    """Yield plugins."""
    plugin_packages = get_entry_point_group("geoips.plugin_packages")
    for pkg in plugin_packages:
        fpath = resources.files("geoips") / "plugins/yaml"
        plugin_files = fpath.rglob("*.yaml")
        for pf in plugin_files:
            yield yaml.safe_load(open(pf, "r"))


@pytest.mark.parametrize("plugin", yield_plugins())
def test_is_plugin_valid(plugin):
    """Test if plugin is valid."""
    if plugin["interface"] == "products":
        product_validator.validate(plugin)
    else:
        validator.validate(plugin)
