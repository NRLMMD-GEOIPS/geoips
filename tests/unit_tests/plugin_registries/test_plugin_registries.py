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
"""Test PluginRegistry Class."""

from geoips.plugin_registry import PluginRegistry
import logging
from glob import glob
import pytest
from os.path import basename, splitext
import yaml

LOG = logging.getLogger(__name__)


class TestPluginRegistry:
    """Subclass of PluginRegistry which adds functionality for unit testing."""

    fpaths = glob(
        str(__file__).replace("test_plugin_registries.py", "files/**/*.yaml"),
        recursive=True,
    )

    plugin_registry = PluginRegistry(fpaths)

    def generate_id(fpath):
        """Generate pytest id for current test."""
        return f"{splitext(basename(fpath))[0]}"

    @pytest.mark.parametrize("fpath", plugin_registry.registry_files, ids=generate_id)
    def test_all_registries(self, fpath):
        """Test all available yaml registries."""
        current_registry = yaml.safe_load(open(fpath, "r"))
        self.plugin_registry.validate_registry(current_registry, fpath)

    def test_registered_plugin_property(self):
        """Ensure registered_plugins is valid in its nature."""
        print(self.plugin_registry.registered_plugins)
        assert isinstance(self.plugin_registry.registered_plugins, dict)
        assert "yaml_based" in self.plugin_registry.registered_plugins
        assert "module_based" in self.plugin_registry.registered_plugins
        assert "text_based" in self.plugin_registry.registered_plugins

    def test_interface_mapping_property(self):
        """Ensure interface_mapping is valid in its nature."""
        print(self.plugin_registry.interface_mapping)
        assert isinstance(self.plugin_registry.interface_mapping, dict)
        assert "yaml_based" in self.plugin_registry.interface_mapping
        assert "module_based" in self.plugin_registry.interface_mapping
        assert "text_based" in self.plugin_registry.interface_mapping
        assert isinstance(self.plugin_registry.interface_mapping["yaml_based"], list)
        assert isinstance(self.plugin_registry.interface_mapping["module_based"], list)
        assert isinstance(self.plugin_registry.interface_mapping["text_based"], list)
