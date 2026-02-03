# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""PluginRegistry class to interface with the JSON plugin registries.

The "geoips config create-registries" utility generates a JSON file at the top
level of every geoips plugin package with a complete list of all plugins with
the associated metadata (everything except the actual contents of the plugin
itself).

Once all of the registered_plugins.json files have been generated via
geoips config create-registries, this class uses those registries to quickly
identify and open plugins as required.  Previously the individual
interface classes would open all plugins every time one was required,
so moving this process into a single PluginRegistry object allows us to
more effectively cache plugins across all interfaces, and avoid reading
in all plugins multiple times.
"""

from importlib import import_module, util, metadata, resources
import json
import logging
import os
from pathlib import Path
from types import SimpleNamespace

from pydantic import BaseModel
import yaml

from geoips.create_plugin_registries import create_plugin_registries
from geoips.errors import PluginError, PluginRegistryError
from geoips.filenames.base_paths import PATHS
from geoips.geoips_utils import merge_nested_dicts
from geoips.utils.types.partial_lexeme import Lexeme

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
            self.registry_files = self._find_registry_files(self.namespace)

    @property
    def registered_plugins(self):
        """Dictionary of every plugin's metadata found within self.namespace.

        self.namespace usually should correspond to 'geoips.plugin_packages' unless
        you're creating registries for plugins that exist outside this namespace.
        """
        if not hasattr(self, "_registered_plugins"):
            self._set_class_properties()
        return self._registered_plugins

    @registered_plugins.setter
    def registered_plugins(self, new_value):
        """Set the registered_plugins class attribute.

        See the registered_plugins property for more information.
        """
        self._registered_plugins = new_value

    @property
    def interface_mapping(self):
        """Dictionary of interface types and interfaces of that type.

        GeoIPS has three types of interfaces, though only two are commonly used
        (yaml_based, module_based). This dictionary has top level keys of all interface
        types, with their values being the list of unique interfaces that inherit that
        type.
        """
        if not hasattr(self, "_interface_mapping"):
            self._set_class_properties()
        return self._interface_mapping

    @interface_mapping.setter
    def interface_mapping(self, new_value):
        """Set the interface_mapping class attribute.

        See the interface_mapping property for more information.
        """
        self._registered_plugins = new_value

    @property
    def registered_yaml_based_plugins(self):
        """A dictionary of registered YAML-based plugins."""
        if not hasattr(self, "_registered_plugins"):
            self._set_class_properties()
        return self._registered_plugins["yaml_based"]

    @property
    def registered_module_based_plugins(self):
        """A dictionary of registered module-based plugins."""
        if not hasattr(self, "_registered_plugins"):
            self._set_class_properties()
        return self._registered_plugins["module_based"]

    def _set_class_properties(self, force_reset=False):
        """Find all plugins in registered plugin packages.

        Traverse the ``registered_plugins.json`` of each registered plugin package under
        self.namespace and add their entries to the _registered_plugins dictionary
        attribute.

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
                try:
                    registry = self._load_registry(reg_path)
                except FileNotFoundError as e:
                    if PATHS["GEOIPS_REBUILD_REGISTRIES"] == True:
                        # This will be hit if we have this environment variable set to
                        # True
                        LOG.warning(
                            f"Plugin registry {reg_path} does not exist, "
                            "please run 'geoips config create-registries'"
                        )
                        # We attempt to create plugin registries under self.namespace
                        # if one or more plugin packages' registry file is missing and
                        # the GEOIPS_REBUILD_REGISTRIES environment is set to true. This
                        # should not be hit twice.

                        # Create plugin registries
                        self.create_registries()
                        registry = self._load_registry(reg_path)
                    else:
                        raise FileNotFoundError(
                            f"Plugin registry {reg_path} does not exist and "
                            "GEOIPS_REBUILD_REGISTRIES isn't set to True. To manually "
                            "create these files, run 'geoips config create-registries'."
                        ) from e
                return_tuple = self._parse_registry(
                    self.interface_mapping, self.registered_plugins, registry
                )
                self.interface_mapping = return_tuple.interface_mapping
                self.registered_plugins = return_tuple.registered_plugins
            # Let's test this separately, not at runtime (see validate_all_registries).
            # Assume it was tested up front, and no longer needs testing at
            # runtime, so we don't fail catastrophically for a single bad
            # plugin that may not even be used.
            # if not self._is_test:
            #     self.validate_registry(
            #         self._registered_plugins,
            #         "all_registered_plugins",
            #     )

    @staticmethod
    def _find_registry_files(namespace):
        """Locate all plugin registry files found under 'namespace'.

        Parameters
        ----------
        namespace: str
            - The namespace in which plugin packages are registered to. Usually, this
              will be the 'geoips.plugin_package' namespace, however this can be changed
              by providing a different top-level namespace to the PluginRegistry class.

        Returns
        -------
        registry_files: list[str]
            - A list of filepaths corresponding to expected registered_plugins.json
              files for all plugin packages found under namespace.

        Raises
        ------
        PluginRegistryError:
            - Occurs if a package is potentially missing an __init__.py file.
        """
        registry_files = []  # Collect the paths to the registry files here
        for pkg in metadata.entry_points(group=namespace):
            try:
                registry_files.append(
                    str(resources.files(pkg.value) / "registered_plugins.json")
                )
            except TypeError as e:
                raise PluginRegistryError(
                    f"resources.files('{pkg.value}') failed\n"
                    f"pkg {pkg}\n"
                    "Potentially missing __init__.py file? Try:\n"
                    f"    touch {pkg.value}/__init__.py\n"
                    "and try again.\n"
                    "Note you will need to add a docstring to "
                    f"{pkg.value}/__init__.py in order for all tests to pass"
                ) from e
        return registry_files

    @staticmethod
    def _load_registry(reg_path):
        """Load the plugin registry found at 'reg_path'.

        All files provided to this function share the same namespace. Usually, this
        will be the 'geoips.plugin_package' namespace, however this can be changed by
        providing a different top-level namespace to the PluginRegistry class.

        Parameters
        ----------
        reg_path: str
            - The absolute path to the plugin registry file for a certain plugin
              package.

        Returns
        -------
        registry: dict
            - A dictionary representing the contents of a plugin registry file. Can
              include top-level keys such as 'yaml_based' or 'module_based' each of
              which is another dictionary containing interfaces of that type, which
              are also dictionaries containing plugins that correspond to that
              interface.

        Raises
        ------
        FileNotFoundError:
            - Raised if 'reg_path' doesn't exist.
        """
        # if this is a yaml file, this is used for testing
        if Path(reg_path).suffix == ".yaml":
            with open(reg_path, "r") as fo:
                registry = yaml.safe_load(fo)
        else:
            with open(reg_path, "r") as fo:
                registry = json.load(fo)

        return registry

    @staticmethod
    def _parse_registry(interface_mapping, registered_plugins, registry):
        """Parse all plugins found under a package's plugin registry.

        Parameters
        ----------
        interface_mapping: dict
            - Dictionary of interface types and interfaces of that type.
              GeoIPS has three types of interfaces, though only two are commonly used
              (yaml_based, module_based). This dictionary has top level keys of all
              interface types, with their values being the list of unique interfaces
              that inherit that type.
        registered_plugins: dict
            - A dictionary of every plugin's metadata found within the plugin_registry's
              namespace.
        registry: dict
            - A dictionary representing the contents of a plugin registry file. Can
              include top-level keys such as 'yaml_based' or 'module_based' each of
              which is another dictionary containing interfaces of that type, which
              are also dictionaries containing plugins that correspond to that
              interface.

        Returns
        -------
        return_tuple: SimpleNamespace
            - A SimpleNamespace object containing updated values of the variables
              ['interface_mapping', 'registered_plugins'] which are dictionaries. See
              comments about those two variables in the parameters section above.
        """
        for plugin_type in registry:
            if plugin_type not in registered_plugins:
                registered_plugins[plugin_type] = {}
                interface_mapping[plugin_type] = []

            for interface in registry[plugin_type]:
                interface_dict = registry[plugin_type][interface]

                if interface not in registered_plugins[plugin_type]:
                    registered_plugins[plugin_type][interface] = interface_dict
                    interface_mapping[plugin_type].append(interface)
                else:
                    merge_nested_dicts(
                        registered_plugins[plugin_type][interface],
                        interface_dict,
                    )

        return_tuple = SimpleNamespace(
            interface_mapping=interface_mapping, registered_plugins=registered_plugins
        )
        return return_tuple

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
                f"{interface_obj.interface_type}' called '{interface_obj.name}'."
            )

        if isinstance(plugin_name, tuple):
            # This occurs for product plugins: i.e. ('abi', 'Infrared')
            metadata = interface_registry.get(plugin_name[0], {}).get(plugin_name[1])
        elif isinstance(plugin_name, str):
            metadata = interface_registry.get(plugin_name)
        else:
            raise TypeError(
                f"Error: cannot search the plugin registry with the provided name = "
                f"{plugin_name}. Please provide either a string or a tuple of strings."
            )

        if metadata is None:
            raise PluginRegistryError(
                f"Error: There is no associated plugin under interface "
                f"'{interface_obj.name}' called '{plugin_name}'. If you're sure this "
                "plugin exists, please run 'geoips config create-registries'."
            )

        return metadata

    def load_plugin(self, data: dict) -> BaseModel:
        """
        Dynamically load and validate pydantic models based on apiVersion and interface.

        This method parses the `apiVersion` field from the input dictionary to
        determine the package and pydantic model version to use. It then dynamically
        imports the corresponding Pydantic model classes based on the `interface` field
        to validate the input data.

        Parameters
        ----------
        data : dict
            Dictionary representing a plugin definition. Must include the `interface`
            field. May optionally include `apiVersion`. If not present, "geoips/v1" is
            assumed.

        Returns
        -------
        BaseModel
            A validated Pydantic model instance.

        Raises
        ------
        ValueError
            If `apiVersion` is improperly formatted or if `interface` field is missing.
        ImportError
            If the specified module for the given model version cannot be imported.
        """
        api_version = data.get("apiVersion", "geoips/v1")

        # Split "package_name/model_version"
        # Use package_name to select the appropriate package to search for the api.
        # This way, we could access the api from geoips_real_time by using
        # geoips_real_time/v1.
        try:
            package_name, model_version = api_version.split("/")
        except ValueError as e:
            raise ValueError(
                f"Invalid apiVersion format: {api_version}. "
                f"Expected format: 'package_name/version'"
            ) from e

        interface = data.get("interface")
        if not interface:
            raise ValueError("Missing 'interface' field for plugin dispatch")

        # Construct module path and import
        try:
            module = import_module(
                f"{package_name}.pydantic_models.{model_version}.{interface}"
            )
        except ImportError as e:
            raise ImportError(
                f"Could not import models from '{api_version}': {e}"
            ) from e

        interface_base = str(Lexeme(interface).singular)
        model_name = f"{interface_base.title().replace('_', '')}PluginModel"

        try:
            model_class = getattr(module, model_name)
        except AttributeError as e:
            raise ValueError(
                f"Model '{model_name}' not found in '{api_version}'"
            ) from e

        return model_class.model_validate(data)

    def get_yaml_plugin(self, interface_obj, name, rebuild_registries=None):
        """Get a YAML plugin by its name.

        Parameters
        ----------
        interface_obj: GeoIPS Interface Object
            - The object representing the interface class requesting this yaml plugin.
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
        try:
            registered_yaml_plugins = self.registered_plugins["yaml_based"]
        except KeyError:
            # Very likely could occur if registries haven't been built yet
            err_str = (
                "No YAML-based plugins found. There likely have been no plugin "
                "registries built yet. If automatic registry creation has been disabled"
                ", please run 'geoips config create-registries'."
            )
            self.retry_get_plugin(interface_obj, name, rebuild_registries, err_str)

        if rebuild_registries is None:
            rebuild_registries = interface_obj.rebuild_registries
        elif not isinstance(rebuild_registries, bool):
            raise TypeError(
                "Error: Argument 'rebuild_registries' was specified but isn't a boolean"
                f" value. Encountered this '{rebuild_registries}' instead."
            )

        interface_entry = registered_yaml_plugins[interface_obj.name]
        # This occurs for product plugins
        if isinstance(name, tuple):
            source_name = name[0]
            plg_name = name[1]
            extra_info = f"under source_name '{source_name}', "
        # This occurs for every other YAML plugin
        else:
            source_name = None
            plg_name = name
            extra_info = ""

        if plg_name not in interface_entry.get(source_name, interface_entry):
            err_str = (
                f"Plugin '{plg_name}', {extra_info}"
                f"from interface '{interface_obj.name}' "
                f"appears to not exist."
                f"\nCreate plugin, then call geoips config create-registries."
            )
            return self.retry_get_plugin(
                interface_obj, name, rebuild_registries, err_str
            )

        relpath = interface_entry.get(source_name, interface_entry)[plg_name]["relpath"]
        package = interface_entry.get(source_name, interface_entry)[plg_name]["package"]
        abspath = str(resources.files(package) / relpath)

        # If abspath doesn't exist the registry is out of date with the actual
        # contents of all, or a certain plugin package.
        if not os.path.exists(abspath):
            err_str = (
                f"Products plugin source: '{source_name}', plugin: '{plg_name} "
                f"exists in the registry but its corresponding file at '{abspath}' "
                "cannot be found. Reinstall your package and re-run "
                "'geoips config create-registries'."
            )
            # This error should never occur, but we're adding error handling here
            # just in case. The reason it will never occur is that, if the path
            # to such plugin does not exist, when geoips config create-registries is
            # re-run that syncs up the path to the associated plugin. It cannot
            # reach this point if the plugin name is invalid, so this point couldn't
            # be hit twice
            return self.retry_get_plugin(
                interface_obj,
                name,
                rebuild_registries,
                err_str,
                PluginRegistryError,
            )
        with open(abspath, "r") as file:
            documents = yaml.safe_load_all(file)
            plugin_found = False
            for plugin in documents:
                # This occurs for product plugins
                if source_name:
                    for product in plugin["spec"]["products"]:
                        if (
                            product["name"] == plg_name
                            and source_name in product["source_names"]
                        ):
                            plugin_found = True
                            plugin = product
                            break
                # Every other type of YAML plugin
                else:
                    if plugin["name"] == plg_name:
                        plugin_found = True

                if plugin_found:
                    break

        if not plugin_found:
            err_str = (
                f"Error: {interface_obj.name} YAML plugin under name '{name}' could"
                " not be found. Please ensure this plugin exists, and if it does, "
                "run 'geoips config create-registries'."
            )
            return self.retry_get_plugin(
                interface_obj, name, rebuild_registries, err_str
            )
        plugin["interface"] = interface_obj.name
        plugin["package"] = package
        plugin["abspath"] = abspath
        plugin["relpath"] = relpath

        if getattr(interface_obj, "use_pydantic", False):
            plugin_json_formatted = self.load_plugin(plugin)
            plugin_dict_formatted = plugin_json_formatted.model_dump()
            validated = interface_obj.validator.validate(plugin_dict_formatted)
            return interface_obj._plugin_yaml_to_obj(name, validated)
        else:
            validated = interface_obj.validator.validate(plugin)
            return interface_obj._plugin_yaml_to_obj(name, validated)

    def get_yaml_plugins(self, interface_obj):
        """Retrieve all yaml plugin objects for this interface.

        Parameters
        ----------
        interface_obj: GeoIPS Interface Object
            - The object representing the interface class requesting all plugins.
        """
        plugins = []
        registered_yaml_plugins = self.registered_yaml_based_plugins
        if interface_obj.name not in registered_yaml_plugins:
            LOG.debug("No plugins found for '%s' interface.", interface_obj.name)
            return plugins
        for name in registered_yaml_plugins[interface_obj.name].keys():
            plugins.append(self.get_yaml_plugin(interface_obj, name))
        return plugins

    def get_module_plugin(self, interface_obj, name, rebuild_registries=None):
        """Retrieve a plugin from this interface by name.

        Parameters
        ----------
        interface_obj: GeoIPS Interface Object
            - The object representing the interface class requesting this module plugin.
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
        try:
            registered_module_plugins = self.registered_plugins["module_based"]
        except KeyError:
            # Very likely could occur if registries haven't been built yet
            err_str = f"No plugins found for '{interface_obj.name}' interface."
            self.retry_get_plugin(interface_obj, name, rebuild_registries, err_str)

        if rebuild_registries is None:
            rebuild_registries = interface_obj.rebuild_registries
        elif not isinstance(rebuild_registries, bool):
            raise TypeError(
                "Error: Argument 'rebuild_registries' was specified but isn't a boolean"
                f" value. Encountered this '{rebuild_registries}' instead."
            )

        if name not in registered_module_plugins[interface_obj.name]:
            err_str = (
                f"Plugin '{name}', "
                f"from interface '{interface_obj.name}' "
                f"appears to not exist."
                f"\nCreate plugin, then call geoips config create-registries."
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
                "'geoips config create-registries'."
            )
            # This error should never occur, but we're adding error handling here
            # just in case. The reason it will never occur is that, if the path
            # to such plugin does not exist, when geoips config create-registries is
            # re-run that syncs up the path to the associated plugin. It cannot reach
            # this point if the plugin name is invalid, so this point couldn't be hit
            # twice
            return self.retry_get_plugin(
                interface_obj, name, rebuild_registries, err_str, PluginRegistryError
            )
        spec = util.spec_from_file_location(module_path, abspath)
        module = util.module_from_spec(spec)
        spec.loader.exec_module(module)
        plugin = interface_obj._plugin_module_to_obj(name, module)
        # This function might raise a PluginError with pertinent information on why
        # the plugin is invalid. Don't catch that, we want the error to be raised.
        interface_obj.plugin_is_valid(plugin)
        return plugin

    def get_module_plugins(self, interface_obj):
        """Retrieve all module plugins for this interface.

        Parameters
        ----------
        interface_obj: GeoIPS Interface Object
            - The object representing the interface class requesting all plugins.
        """
        plugins = []
        # All plugin interfaces are explicitly imported in
        # geoips/interfaces/__init__.py
        # self.name comes explicitly from one of the interfaces that are
        # found by default on geoips.interfaces.
        # If there is a defined interface with no plugins available in the current
        # geoips installation (in any currently installed plugin package),
        # then there will NOT be an entry within registered plugins
        # for that interface, and a KeyError will be raised in the for loop
        # below.
        # Check if the current interface (self.name) is found in the
        # registered_plugins dictionary - if it is not, that means there
        # are no plugins for that interface, so return an empty list.
        registered_module_plugins = self.registered_module_based_plugins
        if interface_obj.name not in registered_module_plugins:
            LOG.debug("No plugins found for '%s' interface.", interface_obj.name)
            return plugins

        for plugin_name in registered_module_plugins[interface_obj.name]:
            try:
                plugins.append(self.get_module_plugin(interface_obj, plugin_name))
            except AttributeError as resp:
                raise PluginError(
                    f"Plugin '{plugin_name}' is missing the 'name' attribute, "
                    f"\nfrom package '{plugin_name['package']},' "
                    f"'{plugin_name['relpath']}' module,"
                ) from resp
        return plugins

    def retry_get_plugin(
        self, interface_obj, name, rebuild_registries, err_str, err_type=PluginError
    ):
        """Rerun self.get_plugin, but call 'geoips config create-registries' beforehand.

        By running 'geoips config create-registries', we automate the registration of
        plugins in GeoIPS. If the plugin persists not to be found, then we'll raise an
        appropriate PluginError as denoted by 'err_str'.

        Parameters
        ----------
        interface_obj: GeoIPS Interface Object
            - The object representing the interface class requesting this plugin.
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
                "Running 'geoips config create-registries' due to a missing plugin "
                f"located under interface: '{interface_obj.name}', plugin_name: "
                f"'{name}'."
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
            return base_interface_class.get_plugin(name, rebuild_registries=False)
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
        if len(plugin_packages) == 0:
            raise PluginRegistryError(
                f"Error: namespace '{self.namespace}' does not exist or has no plugin "
                "packages associated with it. Please resolve this before continuing."
            )
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
        else:
            packages = [ep.value for ep in metadata.entry_points(group=self.namespace)]
            if len(packages) == 0:
                raise PluginRegistryError(
                    f"Error: namespace '{self.namespace}' does not exist or has no "
                    "plugin packages associated with it. Please resolve this before "
                    "continuing."
                )

        for pkg in packages:
            # If packages is provided and the current package is in that list, or if
            # we're using the default value for that argument, delete the associated
            # registry
            if (packages and pkg in packages) or packages is None:
                yaml_plug_path = str(resources.files(pkg) / "registered_plugins.yaml")
                json_plug_path = str(resources.files(pkg) / "registered_plugins.json")
                for path in [json_plug_path, yaml_plug_path]:
                    # Attempt to remove the files, pass silently if they don't exist.
                    try:
                        os.remove(path)
                        print(f"Removed registry file @ {path} from package '{pkg}'.")
                    except FileNotFoundError:
                        print(
                            f"Unable to remove registry file @ {path} from package "
                            f"'{pkg}'."
                        )
                        continue

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
