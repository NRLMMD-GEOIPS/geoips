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

from importlib import util, metadata, resources
from inspect import isclass
import logging
import os

import json
import pydantic
import yaml

from geoips.create_plugin_registries import create_plugin_registries
from geoips.errors import PluginError, PluginRegistryError


LOG = logging.getLogger(__name__)


class PluginRegistry:
    """Plugin Registry class definition.

    Represents all of the plugins found in all of the available GeoIPS packages.
    This class will load a plugin when requested, rather than loading all plugins when
    GeoIPS is instantiated.
    """

    def __init__(self, namespace, _test_registry_files=[]):
        """Initialize the plugin registry for the namespace provided.

        Where namespace is the group of plugin packages used to create the plugin
        registry.
        """
        self.namespace = namespace
        # Use this for unit testing
        if _test_registry_files:
            self.registry_files = _test_registry_files
            self._is_test = True
        # Use this for normal operation and collect the registry files
        else:
            self._is_test = False
            self.registry_files = []  # Collect the paths to the registry files here
            for pkg in metadata.entry_points(group=self.namespace):
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

    @property
    def registered_yaml_based_plugins(self):
        """Plugin Registry yaml_based dictionary attribute."""
        if not hasattr(self, "_registered_plugins"):
            self._set_class_properties()
        return self._registered_plugins["yaml_based"]

    @property
    def registered_module_based_plugins(self):
        """Plugin Registry module_based dictionary attribute."""
        if not hasattr(self, "_registered_plugins"):
            self._set_class_properties()
        return self._registered_plugins["module_based"]

    def _set_class_properties(self, force_reset=False):
        """Find all plugins in registered plugin packages.

        Search the ``registered_plugins.yaml`` of each registered plugin package and add
        them to the _registered_plugins dictionary

        Parameters
        ----------
        force_reset: bool
            - Whether or not we want to force the plugin registry to recreate its
              'registered_plugins' attribute. This essentially forces a re-read of all
              of the registered_plugins.json files and recomputes the master dictionary.
            - Useful when we have rebuilt the registry files during runtime.
        """
        # Load the registries here and return them as a dictionary
        if not hasattr(self, "_registered_plugins") or force_reset:
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
                    with open(reg_path, "r") as fo:
                        pkg_plugins = yaml.safe_load(fo)
                else:
                    with open(reg_path, "r") as fo:
                        pkg_plugins = json.load(fo)
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

    def get_plugin_metadata(self, interface_obj, plugin_name):
        """Retrieve a plugin's metadata.

        Where the metadata of the plugin matches the plugin's corresponding entry in the
        plugin registry.

        Parameters
        ----------
        interface_obj: GeoIPS Interface Object
            - The object representing the interface class requesting plugin metadata.
        plugin_name: str or tuple(str)
            - The name of the plugin whose metadata we want.

        Returns
        -------
        metadata: dict
            - A dictionary of metadata for the requested plugin.
        """
        interface_registry = self.registered_plugins.get(
            interface_obj.interface_type, {}
        ).get(interface_obj.name)

        if interface_registry is None:
            raise KeyError(
                "Error: There is no interface in the plugin registry of type '"
                f"{self.interface_type}' called '{self.name}'."
            )

        if isinstance(plugin_name, tuple):
            # This occurs for product plugins: i.e. ('abi', 'Infrared')
            metadata = interface_registry.get(plugin_name[0], {}).get(plugin_name[1])
        elif isinstance(plugin_name, str):
            metadata = interface_registry.get(plugin_name)
        else:
            raise KeyError(
                f"Error: cannot search the plugin registry with the provided name = "
                f"{plugin_name}. Please provide either a string or a tuple of strings."
            )

        if metadata is None:
            raise PluginRegistryError(
                f"Error: There is no associated plugin under interface "
                f"'{interface_obj.name}' called '{plugin_name}'. If you're sure this "
                "plugin exists, please run 'create_plugin_registries'."
            )

        return metadata

    def get_yaml_plugin(self, interface_obj, name, rebuild_registries=None):
        """Get a plugin by its name.

        This default method can be overridden to provide different search
        functionality for an interface. An example of this is in the
        ProductsInterface which uses a tuple containing 'source_name' and
        'name'.

        Parameters
        ----------
        interface_obj: GeoIPS Interface Object
            - The object representing the interface class requesting plugin metadata.
        name: str or tuple(str)
            - The name of the yaml-based plugin. Either a single string or a tuple of
              strings for product plugins.
        rebuild_registries: bool (default=None)
            - Whether or not to rebuild the registries if get_plugin fails. If set to
              None, default to what we have set in geoips.filenames.base_paths, which
              defaults to True. If specified, use the input value of rebuild_registries,
              which should be a boolean value. If rebuild registries is true and
              get_plugin fails, rebuild the plugin registry, call then call
              get_plugin once more with rebuild_registries toggled off, so it only gets
              rebuilt once.
        """
        from importlib.resources import files

        registered_yaml_plugins = self.registered_plugins["yaml_based"]

        if rebuild_registries is None:
            rebuild_registries = interface_obj.rbr
        elif not isinstance(rebuild_registries, bool):
            raise ValueError(
                "Error: Argument 'rebuild_registries' was specified but isn't a boolean"
                f" value. Encountered this '{rebuild_registries}' instead."
            )

        # This is used for finding products whose plugin names are tuples
        # of the form ('source_name', 'name')
        if isinstance(name, tuple):
            # These are stored in the yaml as str(name),
            # ie "('viirs', 'Infrared')"
            try:
                relpath = registered_yaml_plugins[interface_obj.name][name[0]][name[1]][
                    "relpath"
                ]
                package = registered_yaml_plugins[interface_obj.name][name[0]][name[1]][
                    "package"
                ]
            except KeyError:
                err_str = (
                    f"Plugin [{name[1]}] doesn't exist under source name [{name[0]}]"
                )
                return self.retry_get_plugin(name, rebuild_registries, err_str)
            abspath = str(files(package) / relpath)
            # If abspath doesn't exist the registry is out of date with the actual
            # contents of all, or a certain plugin package.
            if not os.path.exists(abspath):
                err_str = (
                    f"Products plugin source: '{name[0]}', plugin: '{name[1]} exists in"
                    f" the registry but its corresponding file at '{abspath}' cannot be"
                    " found. Reinstall your package and re-run "
                    "'create_plugin_registries'."
                )
                # This error should never occur, but we're adding error handling here
                # just in case. The reason it will never occur is that, if the path
                # to such plugin does not exist, when create_plugin_registries is re-run
                # that syncs up the path to the associated plugin. It cannot reach this
                # point if the plugin name is invalid, so this point couldn't be hit
                # twice
                return self.retry_get_plugin(
                    interface_obj,
                    name,
                    rebuild_registries,
                    err_str,
                    PluginRegistryError,
                )
            with open(abspath, "r") as fo:
                plugin = yaml.safe_load(fo)
            plugin_found = False
            for product in plugin["spec"]["products"]:
                if product["name"] == name[1] and name[0] in product["source_names"]:
                    plugin_found = True
                    plugin = product
                    break
            if not plugin_found:
                err_str = "There is no plugin that has " + name[1] + " included in it."
                return self.retry_get_plugin(
                    interface_obj, name, rebuild_registries, err_str
                )
            plugin["interface"] = "products"
            plugin["package"] = package
            plugin["abspath"] = abspath
            plugin["relpath"] = relpath
        # This is used for finding all non-product plugins
        else:
            try:
                relpath = registered_yaml_plugins[interface_obj.name][name]["relpath"]
                package = registered_yaml_plugins[interface_obj.name][name]["package"]
            except KeyError:
                err_str = (
                    f"Plugin [{name}] doesn't exist under interface "
                    f"[{interface_obj.name}]"
                )
                return self.retry_get_plugin(
                    interface_obj, name, rebuild_registries, err_str
                )
            abspath = str(files(package) / relpath)
            # If abspath doesn't exist the registry is out of date with the actual
            # contents of all, or a certain plugin package.
            if not os.path.exists(abspath):
                err_str = (
                    f"Plugin '{name}' exists in the registry but its corresponding file"
                    f" at '{abspath}' cannot be found. Reinstall your package and "
                    "re-run 'create_plugin_registries'."
                )
                # This error should never occur, but we're adding error handling here
                # just in case. The reason it will never occur is that, if the path
                # to such plugin does not exist, when create_plugin_registries is re-run
                # that syncs up the path to the associated plugin. It cannot reach this
                # point if the plugin name is invalid, so this point couldn't be hit
                # twice
                return self.retry_get_plugin(
                    interface_obj,
                    name,
                    rebuild_registries,
                    err_str,
                    PluginRegistryError,
                )

            doc_iter = yaml.load_all(open(abspath, "r"), Loader=yaml.SafeLoader)
            doc_length = sum(1 for _ in doc_iter)
            if doc_length > 1 or interface_obj.name == "workflows":
                plugin_found = False
                for plugin in yaml.load_all(open(abspath, "r"), Loader=yaml.SafeLoader):
                    if plugin["name"] == name:
                        plugin_found = True
                        plugin["package"] = package
                        plugin["abspath"] = abspath
                        plugin["relpath"] = relpath
                        break
                if not plugin_found:
                    raise PluginRegistryError(
                        f"Error: YAML plugin under name '{name}' could not be found. "
                        "Please ensure this plugin exists, and if it does, run "
                        "'create_plugin_registries'."
                    )
                # NOTE: Haven't created a validator for this yet so we are just going to
                # convert this to an object without validating for the time being.
                return interface_obj._plugin_yaml_to_obj(name, plugin)
            else:
                plugin = yaml.safe_load(open(abspath, "r"))
                plugin["package"] = package
                plugin["abspath"] = abspath
                plugin["relpath"] = relpath
        if isclass(interface_obj.validator) and issubclass(
            pydantic.BaseModel, interface_obj.validator
        ):
            validated = interface_obj.validator(**plugin)
        else:
            validated = interface_obj.validator.validate(plugin)
        # Store "name" as the product's "id"
        # This is helpful when an interfaces uses something other than just "name" to
        # find its plugins as is the case with ProductsInterface
        return interface_obj._plugin_yaml_to_obj(name, validated)

    def get_module_plugin(self, interface_obj, name, rebuild_registries=None):
        """Retrieve a plugin from this interface by name.

        Parameters
        ----------
        interface_obj: GeoIPS Interface Object
            - The object representing the interface class requesting plugin metadata.
        name : str
            - The name the desired plugin.
        rebuild_registries: bool (default=None)
            - Whether or not to rebuild the registries if get_plugin fails. If set to
              None, default to what we have set in geoips.filenames.base_paths, which
              defaults to True. If specified, use the input value of rebuild_registries,
              which should be a boolean value. If rebuild registries is true and
              get_plugin fails, rebuild the plugin registry, call then call
              get_plugin once more with rebuild_registries toggled off, so it only gets
              rebuilt once.

        Returns
        -------
        An object of type ``<interface>Plugin`` where ``<interface>`` is the name of
        this interface.

        Raises
        ------
        PluginError
          If the specified plugin isn't found within the interface.
        """
        # Find the plugin module
        # Convert the module into an object
        registered_module_plugins = self.registered_plugins["module_based"]

        if rebuild_registries is None:
            rebuild_registries = interface_obj.rbr
        elif not isinstance(rebuild_registries, bool):
            raise ValueError(
                "Error: Argument 'rebuild_registries' was specified but isn't a boolean"
                f" value. Encountered this '{rebuild_registries}' instead."
            )

        if name not in registered_module_plugins[interface_obj.name]:
            err_str = (
                f"Plugin '{name}', "
                f"from interface '{interface_obj.name}' "
                f"appears to not exist."
                f"\nCreate plugin, then call create_plugin_registries."
            )
            return self.retry_get_plugin(
                interface_obj, name, rebuild_registries, err_str
            )

        package = registered_module_plugins[interface_obj.name][name]["package"]
        relpath = registered_module_plugins[interface_obj.name][name]["relpath"]
        module_path = os.path.splitext(relpath.replace("/", "."))[0]
        module_path = f"{package}.{module_path}"
        abspath = resources.files(package) / relpath
        # If abspath doesn't exist the registry is out of date with the actual contents
        # of all, or a certain plugin package.
        if not os.path.exists(abspath):
            err_str = (
                f"Plugin '{name}' exists in the registry but its corresponding file at "
                f"'{abspath}' cannot be found. Reinstall your package and re-run "
                "'create_plugin_registries'."
            )
            # This error should never occur, but we're adding error handling here
            # just in case. The reason it will never occur is that, if the path
            # to such plugin does not exist, when create_plugin_registries is re-run
            # that syncs up the path to the associated plugin. It cannot reach this
            # point if the plugin name is invalid, so this point couldn't be hit
            # twice
            return self.retry_get_plugin(
                interface_obj, name, rebuild_registries, err_str, PluginRegistryError
            )
        spec = util.spec_from_file_location(module_path, abspath)
        module = util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return interface_obj._plugin_module_to_obj(name, module)

    def retry_get_plugin(
        self, interface_obj, name, rebuild_registries, err_str, err_type=PluginError
    ):
        """Re-run self.get_plugin, but call 'create_plugin_registries' beforehand.

        By running 'create_plugin_registries', we automate the registration of plugins
        in GeoIPS. If the plugin persists not to be found, then we'll raise an
        appropriate PluginError as denoted by 'err_str'.

        Parameters
        ----------
        name: str or tuple(str)
            - The name of the yaml plugin. Either a single string or a tuple of strings
              for product plugins.
        rebuild_registries: bool
            - Whether or not to rebuild the registries if get_plugin fails. If set to
              true and get_plugin fails, rebuild the plugin registry, call then call
              get_plugin once more with rebuild_registries toggled off, so it only gets
              rebuilt once.
        err_str: string
            - The error to be reported.
        err_type: Exception-based Class
            - The class of exception to be raised.
        """
        if rebuild_registries:
            LOG.interactive(
                "Running 'create_plugin_registries' due to a missing plugin located "
                f"under interface: '{interface_obj.name}', plugin_name: '{name}'."
            )
            self.create_registries()
            # Force a rebuild of the master 'registered_plugins' dictionary.
            self._set_class_properties(force_reset=True)
            # This is done as some interface classes override 'get_plugin' with
            # additional parameters it it's call signature. We only want to call
            # BaseYamlInterface or BaseModuleInterface 'get_plugin', then return such
            # information to the child class which overrode 'get_plugin'. Implementing
            # it this way ensures that will happen.
            base_interface_class = interface_obj.__class__.__base__()
            base_interface_class.name = interface_obj.name
            return base_interface_class.get_plugin(
                interface_obj, name, rebuild_registries=False
            )
        else:
            raise err_type(err_str)

    def create_registries(self, packages=None, save_type="json") -> None:
        """Create one or more plugin registry files.

        By default, this command will create all plugin registry files for all
        installed geoips packages (geoips.plugin_packages entrypoint). If packages is
        provided via the argument above, create registry files associated with each
        of those packages.

        Parameters
        ----------
        packages: list[str], default=None
            - A list of names corresponding to geoips.plugin_packges whose registries
              we want to create.
        save_type: str, default="json"
            - Format to write registries to. This will also be the file extension. Valid
              options are either 'json' or 'yaml'.

        Raises
        ------
        ValueError:
            - Raised if 'save_type' is provided but is not one of ['json', 'yaml']
        TypeError:
            - Raised if packages is provided and is not a list of strings.
        PluginRegistryError:
            - Raised if one or more of the packages provided is not a valid
              geoips.plugin_package, or if the associated namespace provided is not
              a valid namespace.
        """
        if save_type not in ["json", "yaml"]:
            raise ValueError(
                "Error: 'save_type' kwarg was provided but is not one of "
                "['json', 'yaml']."
            )
        plugin_packages = metadata.entry_points(group=self.namespace)
        if packages:
            self._validate_packages_input(packages)
            filtered_packages = []
            for pkg in plugin_packages:
                if pkg.value in packages:
                    filtered_packages.append(pkg)
            plugin_packages = filtered_packages

        LOG.debug(plugin_packages)
        create_plugin_registries(plugin_packages, save_type, self.namespace)

    def delete_registries(self, packages=None) -> None:
        """Delete one or more plugin registry files.

        By default, this command will delete all plugin registry files found in all
        installed geoips packages (geoips.plugin_packages entrypoint). If packages is
        provided via the argument above, delete the registry file(s) associated with
        each of those packages.

        Parameters
        ----------
        packages: list[str], default=None
            - A list of names corresponding to geoips.plugin_packges whose registries
              we want to delete.

        Raises
        ------
        TypeError:
            - Raised if packages is provided and is not a list of strings.
        FileNotFoundError:
            - Raised if a registry file could not be found in one or more
              geoips.plugin_packages.
        PluginRegistryError:
            - Raised if one or more of the packages provided is not a valid
              geoips.plugin_package, or if the associated namespace provided is not
              a valid namespace.
        """
        if packages:
            self._validate_packages_input(packages)

        for pkg in metadata.entry_points(group=self.namespace):
            # If packages is provided and the current package is in that list, or if
            # we're using the default value for that argument, delete the associated
            # registry
            if (packages and pkg.value in packages) or packages is None:
                yaml_plug_path = str(
                    resources.files(pkg.value) / "registered_plugins.yaml"
                )
                json_plug_path = str(
                    resources.files(pkg.value) / "registered_plugins.json"
                )
                # If the .json registry is missing, raise a FileNotFoundError.
                if os.path.exists(json_plug_path):
                    os.remove(json_plug_path)
                else:
                    raise FileNotFoundError(
                        f"Error: deletion of '{pkg.value}'s registry was requested "
                        f" but {json_plug_path} couldn't be found. Run "
                        "'create_plugin_registries' to fix this issue."
                    )
                # Don't have the code above in a for loop as we don't require the
                # .yaml registry file. Just raise a warning if it's missing.
                if os.path.exists(yaml_plug_path):
                    os.remove(yaml_plug_path)
                else:
                    LOG.warning(
                        f"Warning: deletion was requested for '{pkg.value}'s plugin "
                        f"registry files but {yaml_plug_path} couldn't be found. "
                        "Run 'create_plugin_registries -s yaml' to fix this issue."
                    )

    def _validate_packages_input(self, packages):
        """Validate that packages is a list of strings.

        If not, then raise a TypeError indicating what was formatted incorrectly.

        Parameters
        ----------
        packages: list[str], default=None
            - A list of names corresponding to geoips.plugin_packges whose registries
              we want to delete.

        Raises
        ------
        TypeError:
            - Raised if packages is provided and is not a list of strings.
        PluginRegistryError:
            - Raised if one or more of the packages provided is not a valid
              geoips.plugin_package, or if the associated namespace provided is not
              a valid namespace.
        """
        if not isinstance(packages, list):
            raise TypeError(
                "Error: 'packages' kwarg was provided but it is not a list object."
            )
        elif any([not isinstance(pkg, str) for pkg in packages]):
            raise TypeError(
                "Error: 'packages' kwarg was provided but one or more of it's "
                "items were not a string."
            )
        # If any package name in 'packages' could not be associated with an entry point
        # found in pypi's package registry associated with 'self.namespace', raise a
        # plugin registry error.
        found_packages = [
            pkg.value for pkg in metadata.entry_points(group=self.namespace)
        ]
        if any([pkg_name not in found_packages for pkg_name in packages]):
            raise PluginRegistryError(
                "Error: either the namespace provided was invalid or one or more of "
                "the packages whose registry you requested to delete does not exist."
            )


plugin_registry = PluginRegistry("geoips.plugin_packages")
