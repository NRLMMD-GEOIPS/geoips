"""Generates all available plugins from all installed GeoIPS packages.

After all plugins have been generated, they are written to a registered_plugins.yaml
file which contains a dictionary of all the registered GeoIPS plugins.

To use this module, simply call 'python create_plugin_registry.py'.
The main function will do the rest!
"""

from importlib import resources
import os
import logging
from geoips.errors import PluginRegistryError
import pytest
import yaml
import pickle  # nosec

LOG = logging.getLogger(__name__)


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
            from geoips.geoips_utils import get_entry_point_group

            self._is_test = False
            self.registry_files = []  # Collect the paths to the registry files here
            for pkg in get_entry_point_group("geoips.plugin_packages"):
                self.registry_files.append(
                    str(resources.files(pkg.value) / "registered_plugins")
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
                    raise PluginRegistryError(
                        f"Plugin registry {reg_path} did not exist, "
                        "please run 'create_plugin_registries'"
                    )
                # This will include all plugins, including schemas, yaml_based,
                # and module_based plugins.
                if self._is_test:
                    pkg_plugins = yaml.safe_load(open(reg_path, "r"))
                else:
                    pkg_plugins = pickle.load(open(reg_path, "rb"))  # nosec
                    self.validate_registry(pkg_plugins, reg_path)
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
            if not self._is_test:
                self.validate_registry(
                    self._registered_plugins,
                    "all_registered_plugins",
                )
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

    def validate_registry(self, current_registry, fpath):
        """Test all plugins found in registered plugins for their validity."""
        try:
            self.validate_plugin_types_exist(current_registry, fpath)
        except PluginRegistryError as e:
            print(e)
            pytest.xfail(str(e))
        try:
            self.validate_registry_interfaces(current_registry)
        except PluginRegistryError as e:
            print(e)
            pytest.xfail(str(e))
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
                        print(e)
                        pytest.xfail(str(e))

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
        from geoips import interfaces
        import inspect

        yaml_interfaces = [
            str(info[0])
            for info in inspect.getmembers(interfaces.yaml_based, inspect.ismodule)
        ]
        module_interfaces = [
            str(info[0])
            for info in inspect.getmembers(interfaces.module_based, inspect.ismodule)
        ]
        bad_interfaces = []
        for plugin_type in ["module_based", "yaml_based"]:
            for interface in current_registry[plugin_type]:
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
            error_str = "The following interfaces were not valid:\n"
            for error in bad_interfaces:
                error_str += error
            raise PluginRegistryError(error_str)


plugin_registry = PluginRegistry()
