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
        # Use this for normal operation and collect the registry files
        else:
            from geoips.geoips_utils import get_entry_point_group

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
            import pickle

            self._registered_plugins = {}
            self._interface_mapping = {}
            for reg_path in self.registry_files:
                if not os.path.exists(reg_path):
                    raise PluginRegistryError(
                        f"Plugin registry {reg_path} did not exist, "
                        "please run 'create_plugin_registries'"
                    )
                # This will include all plugins, including schemas, yaml_based,
                # and module_based plugins.
                pkg_plugins = pickle.load(open(reg_path, "rb"))
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

    # def load_yaml_plugin(self, interface, name, just_info=False):
    #     """Load a YAML plugin and return it."""
    #     if isinstance(name, tuple):
    #         try:
    #             relpath = self._registered_plugins["yaml_based"]["products"][name[0]][
    #                 name[1]
    #             ]["relpath"]
    #             package = self._registered_plugins["yaml_based"]["products"][name[0]][
    #                 name[1]
    #             ]["package"]
    #         except KeyError:
    #             raise PluginError(
    #                 f"Plugin [{name[1]}] doesn't exist under source name [{name[0]}]"
    #             )
    #         abspath = str(resources.files(package) / relpath)
    #         plugin = yaml.safe_load(open(abspath, "r"))
    #         plugin_found = False
    #         for product in plugin["spec"]["products"]:
    #             if product["name"] == name[1] and name[0] in product["source_names"]:
    #                 plugin_found = True
    #                 plugin = product
    #                 break
    #         if not plugin_found:
    #             raise PluginError(
    #                 "There is no plugin that has " + name[1] + " included in it."
    #             )
    #         plugin["interface"] = "products"
    #         plugin["package"] = package
    #         plugin["abspath"] = abspath
    #         plugin["relpath"] = relpath
    #     else:
    #         try:
    #             relpath = self._registered_plugins["yaml_based"][interface][name][
    #                 "relpath"
    #             ]
    #             package = self._registered_plugins["yaml_based"][interface][name][
    #                 "package"
    #             ]
    #         except KeyError:
    #             raise PluginError(
    #                 f"Plugin [{name}] doesn't exist under interface [{interface}]"
    #             )
    #         abspath = str(resources.files(package) / relpath)
    #         plugin = yaml.safe_load(open(abspath, "r"))
    #         plugin["package"] = package
    #         plugin["abspath"] = abspath
    #         plugin["relpath"] = relpath
    #     if just_info:
    #         info_dict = {
    #             "interface": interface,
    #             "package": package,
    #             "abspath": abspath,
    #             "relpath": relpath,
    #             "name": plugin["name"],
    #         }
    #         if interface == "products":
    #             info_dict["source_names"] = plugin["source_names"]
    #             info_dict["product_defaults"] = plugin["product_defaults"]
    #         return info_dict
    #     else:
    #         interface_module = getattr(geoips.interfaces, "products")
    #         validated = interface_module.validator.validate(plugin)
    #         return interface_module._plugin_yaml_to_obj(name, validated)

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
