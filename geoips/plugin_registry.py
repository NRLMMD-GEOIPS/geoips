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

"""PluginRegistry class to interface with the JSON plugin registries.

The "create_plugin_registries" utility generates a JSON file at the top
level of every geoips plugin package with a complete list of all plugins with
the associated metadata (everything except the actual contents of the plugin
itself).

Once all of the registered_plugins.json files have been generated via
create_plugin_registries, this class uses those registries to quickly
identify and open plugins as required.  Previously the individual
interface classes would open all plugins every time one was required,
so moving this process into a single PluginRegistry object allows us to
more effectively cache plugins across all interfaces, and avoid reading
in all plugins multiple times.
"""

from importlib import resources, metadata, import_module
import sys
import os
import logging
from pprint import pformat
from geoips.errors import PluginRegistryError
import pytest
import yaml
import json

LOG = logging.getLogger(__name__)


def get_entry_point_group(group):
    """Get entry point group."""
    # NOTE: When there is a .egg-info directory in the plugin package top
    # level (ie, from setuptools pip install -e), it seems to return that
    # package twice in this list.  For now, just use the full list with
    # duplicates.
    if sys.version_info[:3] >= (3, 10, 0):
        eps = metadata.entry_points(group=group)
    else:
        eps = metadata.entry_points()[group]

    return eps


class PluginRegistry:
    """Plugin Registry class definition.

    Represents all of the plugins found in all of the available GeoIPS packages.
    This class will load a plugin when requested, rather than loading all plugins when
    GeoIPS is instantiated.
    """

    def __init__(self, _test_registry_files=[]):
        # Use this for unit testing
        if _test_registry_files:
            self.registry_files = _test_registry_files
            self._is_test = True
        # Use this for normal operation and collect the registry files
        else:
            self._is_test = False
            self.registry_files = []  # Collect the paths to the registry files here
            for pkg in get_entry_point_group("geoips.plugin_packages"):
                try:
                    self.registry_files.append(
                        str(resources.files(pkg.value) / "registered_plugins.json")
                    )
                except TypeError:
                    raise PluginRegistryError(
                        f"resources.files('{pkg.value}') failed\n"
                        f"pkg {pkg}\n"
                        "Potentially missing __init__.py file? Try:\n"
                        f"    touch {pkg.value}/__init__.py\n"
                        "and try again.\n"
                        "Note you will need to add a docstring to "
                        f"{pkg.value}/__init__.py in order for all tests to pass"
                    )

    @property
    def registered_plugins(self):
        """Plugin Registry registered_plugins attribute."""
        if not hasattr(self, "_registered_plugins"):
            self._set_class_properties()
        return self._registered_plugins

    @property
    def interface_mapping(self):
        """Plugin Registry interface_mapping attribute."""
        if not hasattr(self, "_interface_mapping"):
            self._set_class_properties()
        return self._interface_mapping

    def _set_class_properties(self):
        """Find all plugins in registered plugin packages.

        Search the ``registered_plugins.yaml`` of each registered plugin package and add
        them to the _registered_plugins dictionary
        """
        # Load the registries here and return them as a dictionary
        if not hasattr(self, "_registered_plugins"):
            from geoips.geoips_utils import merge_nested_dicts

            # Complete dictionary of all available plugins found in every geoips package
            self._registered_plugins = {}
            # A mapping of interfaces to plugin_types. Ie:
            # {
            # "yaml_based": [products, sectors, ...],
            # "module_based": [algorithms, readers, ...],
            # "text_based": [tpw_cimss, ...]
            # }
            self._interface_mapping = {}
            for reg_path in self.registry_files:
                if not os.path.exists(reg_path):
                    LOG.error(
                        f"Plugin registry {reg_path} did not exist, "
                        "please run 'create_plugin_registries'"
                    )
                    continue
                # This will include all plugins, including schemas, yaml_based,
                # and module_based plugins.
                if self._is_test:
                    pkg_plugins = yaml.safe_load(open(reg_path, "r"))
                else:
                    pkg_plugins = json.load(open(reg_path, "r"))
                    # Do not validate ALL plugins at runtime.
                    # self.validate_registry(pkg_plugins, reg_path)
                try:
                    for plugin_type in pkg_plugins:
                        if plugin_type not in self._registered_plugins:
                            self._registered_plugins[plugin_type] = {}
                            self._interface_mapping[plugin_type] = []
                        for interface in pkg_plugins[plugin_type]:
                            interface_dict = pkg_plugins[plugin_type][interface]
                            if interface not in self._registered_plugins[plugin_type]:
                                self._registered_plugins[plugin_type][
                                    interface
                                ] = interface_dict  # NOQA
                                self._interface_mapping[plugin_type].append(interface)
                            else:
                                merge_nested_dicts(
                                    self._registered_plugins[plugin_type][interface],
                                    interface_dict,
                                )
                except TypeError:
                    raise PluginRegistryError(f"Failed reading {reg_path}.")
            # Let's test this separately, not at runtime (see validate_all_registries).
            # Assume it was tested up front, and no longer needs testing at
            # runtime, so we don't fail catastrophically for a single bad
            # plugin that may not even be used.
            # if not self._is_test:
            #     self.validate_registry(
            #         self._registered_plugins,
            #         "all_registered_plugins",
            #     )
        return self._registered_plugins

    def get_plugin_info(self, interface, plugin_name):
        """Find a plugin in the registry and return its info.

        This should remove all plugin loading from the base interfaces and allow us
        to only load one plugin at a time
        """
        plugin_type = self.identify_plugin_type(interface)
        if isinstance(plugin_name, tuple):
            return self.registered_plugins[plugin_type][interface][plugin_name[0]][
                plugin_name[1]
            ]
        return self.registered_plugins[plugin_type][interface][plugin_name]

    def get_interface_plugin_info(self, interface):
        """Find an interface in the registry and return its corresponding info.

        This should remove all plugin loading from the base interfaces and allow us
        to only load one plugin at a time
        """
        plugin_type = self.identify_plugin_type(interface)
        return self.registered_plugins[plugin_type][interface]

    def get_interface_plugin_names(self, interface):
        """List all available plugins in the an interface of the registry.

        This should remove all plugin loading from the base interfaces and allow us
        to only load one plugin at a time
        """
        plugin_type = self.identify_plugin_type(interface)
        return list(self.registered_plugins[plugin_type][interface].keys())

    def list_plugins(self, interface):
        """List the plugins available for an interface ONLY based on the registries.

        This should not load any plugins, just return info from the registries.
        """
        plugin_type = self.identify_plugin_type(interface)
        return self.registered_plugins[plugin_type][interface]

    def identify_plugin_type(self, interface):
        """Identify the Plugin Type based on the provided interface."""
        plugin_type = None
        for p_type in self.interface_mapping:
            if interface in self.interface_mapping[p_type]:
                plugin_type = p_type
                break
        if plugin_type is None:
            raise PluginRegistryError(
                f"{interface} does not exist within any package registry."
            )
        return plugin_type

    def validate_plugin_types_exist(self, reg_dict, reg_path):
        """Test that all top level plugin types exist in each registry file."""
        expected_plugin_types = ["yaml_based", "module_based", "text_based"]
        for p_type in expected_plugin_types:
            if p_type not in reg_dict:
                error_str = f"Expected plugin type '{p_type}' to be in the registry but"
                error_str += f" wasn't. This was in file '{reg_path}'."
                raise PluginRegistryError(error_str)

    def validate_all_registries(self):
        """Validate all registries in the current installation.

        This should be run during testing, but not at runtime.
        Ensure we do not fail catastrophically for a single bad plugin
        at runtime, so test up front to test validity.
        """
        for reg_path in self.registry_files:
            pkg_plugins = json.load(open(reg_path, "r"))
            self.validate_registry(pkg_plugins, reg_path)

    def validate_registry(self, current_registry, fpath):
        """Test all plugins found in registered plugins for their validity."""
        try:
            self.validate_plugin_types_exist(current_registry, fpath)
        except PluginRegistryError as e:
            # xfail if this is a test, otherwise just raise PluginRegistryError
            if self._is_test:
                pytest.xfail(str(e))
            else:
                raise PluginRegistryError(e)
        try:
            self.validate_registry_interfaces(current_registry)
        except PluginRegistryError as e:
            # xfail if this is a test, otherwise just raise PluginRegistryError
            if self._is_test:
                pytest.xfail(str(e))
            else:
                raise PluginRegistryError(e)
        for plugin_type in current_registry:
            for interface in current_registry[plugin_type]:
                for plugin in current_registry[plugin_type][interface]:
                    try:
                        if interface == "products":
                            for subplg in current_registry[plugin_type][interface][
                                plugin
                            ]:
                                self.validate_plugin_attrs(
                                    plugin_type,
                                    interface,
                                    (plugin, subplg),
                                    current_registry[plugin_type][interface][plugin][
                                        subplg
                                    ],
                                )
                        elif plugin_type != "text_based":
                            self.validate_plugin_attrs(
                                plugin_type,
                                interface,
                                plugin,
                                current_registry[plugin_type][interface][plugin],
                            )
                    except PluginRegistryError as e:
                        # xfail if this is a test,
                        # otherwise just raise PluginRegistryError
                        if self._is_test:
                            pytest.xfail(str(e))
                        else:
                            raise PluginRegistryError(e)

    def validate_plugin_attrs(self, plugin_type, interface, name, plugin):
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

    def validate_registry_interfaces(self, current_registry):
        """Test Plugin Registry interfaces validity."""
        yaml_interfaces = []
        module_interfaces = []

        # NOTE: all <pkg>/interfaces/__init__.py files MUST
        # contain a "module_based_interfaces" list and a
        # "yaml_based_interfaces" list - this is how we
        # identify the valid interface names.
        # We must avoid actually importing the interfaces within
        # the geoips repo - or we will end up with a circular import
        # due to BaseInterface.
        for pkg in get_entry_point_group("geoips.plugin_packages"):
            try:
                mod = import_module(f"{pkg.value}.interfaces")
            except ModuleNotFoundError as resp:
                if f"No module named '{pkg.value}.interfaces'" in str(resp):
                    continue
                else:
                    raise ModuleNotFoundError(resp)
            module_interfaces += mod.module_based_interfaces
            yaml_interfaces += mod.yaml_based_interfaces

        bad_interfaces = []
        for plugin_type in ["module_based", "yaml_based"]:
            for interface in current_registry[plugin_type]:
                if (
                    interface not in module_interfaces
                    and interface not in yaml_interfaces
                ):
                    error_str = f"\nPlugin type '{plugin_type}' does not allow "
                    error_str += f"interface '{interface}'.\n"
                    error_str += "\nValid interfaces: "
                    if plugin_type == "module_based":
                        interface_list = module_interfaces
                    else:
                        interface_list = yaml_interfaces
                    error_str += f"\n{interface_list}\n"
                    error_str += "\nPlease update the following plugins "
                    error_str += "to use a valid interface:\n"
                    error_str += pformat(current_registry[plugin_type][interface])
                    bad_interfaces.append(error_str)
        if bad_interfaces:
            error_str = "The following interfaces were not valid:\n"
            for error in bad_interfaces:
                error_str += error
            raise PluginRegistryError(error_str)


plugin_registry = PluginRegistry()
