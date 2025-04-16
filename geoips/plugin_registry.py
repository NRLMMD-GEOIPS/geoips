# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

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

from importlib import metadata, resources
import os
import logging
from geoips.errors import PluginRegistryError
import yaml
import json


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
            self._is_test = False
            self.registry_files = []  # Collect the paths to the registry files here
            for pkg in metadata.entry_points(group="geoips.plugin_packages"):
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


plugin_registry = PluginRegistry()
