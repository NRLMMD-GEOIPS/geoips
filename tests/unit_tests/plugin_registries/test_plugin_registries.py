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
from geoips.errors import PluginRegistryError
import logging
from glob import glob
import pytest

LOG = logging.getLogger(__name__)


class CheckPluginRegistry(PluginRegistry):
    """Subclass of PluginRegistry which adds functionality for unit testing."""

    def __init__(self):
        """Initialize Test Plugin Registry."""
        fpaths = glob(str(__file__).replace(
            "test_plugin_registries.py",
            "files/**/*.yaml"), recursive=True)
        super().__init__(fpaths)

    def check_registries(self, ):
        """Test all plugins found in registered plugins for their validity."""
        try:
            self.check_registry_interfaces()
        except PluginRegistryError as e:
            pytest.xfail(str(e))
            # print(e)
        for plugin_type in self.registered_plugins:
            for interface in self.registered_plugins[plugin_type]:
                for plugin in self.registered_plugins[plugin_type][interface]:
                    try:
                        if interface == "products":
                            for subplg in self.registered_plugins[plugin_type][
                                interface
                            ][plugin]:
                                self.check_plugin_attrs(
                                    plugin_type,
                                    interface,
                                    (plugin, subplg),
                                    self.registered_plugins[plugin_type][interface][
                                        plugin
                                    ][subplg],
                                )
                        else:
                            self.check_plugin_attrs(
                                plugin_type,
                                interface,
                                plugin,
                                self.registered_plugins[plugin_type][interface][plugin],
                            )
                    except PluginRegistryError as e:
                        pytest.xfail(str(e))
                        # print(e)

    def check_plugin_attrs(self, plugin_type, interface, name, plugin):
        """Test non-product plugin for all required attributes."""
        missing = []
        if plugin_type == "yaml_based" and interface != "products":
            attrs = [
                "docstring",
                "family",
                "interface",
                "package",
                "plugin_type",
                "relpath",
            ]
        elif plugin_type == "yaml_based":
            attrs = [
                "docstring",
                "family",
                "interface",
                "package",
                "plugin_type",
                "product_defaults",
                "source_names",
                "relpath",
            ]
        else:
            attrs = [
                "docstring",
                "family",
                "interface",
                "package",
                "plugin_type",
                "signature",
                "relpath",
            ]
        for attr in attrs:
            try:
                plugin[attr]
            except KeyError:
                missing.append(attr)
        if missing:
            raise PluginRegistryError(
                f"Plugin '{name}' is missing the following required "
                f"top-level properties: '{missing}'"
            )

    def check_registry_interfaces(self):
        """Test Plugin Registry interfaces validity."""
        yaml_interfaces = [
            "feature_annotators",
            "gridline_annotators",
            "product_defaults",
            "products",
            "sectors",
        ]
        module_interfaces = [
            "algorithms",
            "colormappers",
            "coverage_checkers",
            "filename_formatters",
            "interpolators",
            "output_checkers",
            "output_formatters",
            "procflows",
            "readers",
            "sector_adjusters",
            "sector_metadata_generators",
            "sector_spec_generators",
            "title_formatters",
        ]
        bad_interfaces = []
        for plugin_type in ["module_based", "yaml_based"]:
            for interface in self.registered_plugins[plugin_type]:
                if (
                    interface not in module_interfaces
                    and interface not in yaml_interfaces
                ):
                    error_str = f"Plugin type '{plugin_type}' does not allow interface "
                    error_str += f"'{interface}'. Here is a list of valid interfaces: "
                    if plugin_type == "module_based":
                        interface_list = module_interfaces
                    else:
                        interface_list = yaml_interfaces
                    error_str += f"\n{interface_list}\n"
                    bad_interfaces.append(error_str)
        if bad_interfaces:
            error_str = "\nThe following interfaces were not valid:\n"
            for error in bad_interfaces:
                error_str += error
            raise PluginRegistryError(error_str)


@pytest.mark.parametrize("test_reg", [CheckPluginRegistry()])
def test_all_registries(test_reg):
    """Test all available yaml registries."""
    test_reg.check_registries()
