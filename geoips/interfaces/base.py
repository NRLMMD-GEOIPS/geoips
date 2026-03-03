# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Base classes for interfaces, plugins, and plugin validation machinery."""

import abc
import inspect
import logging
from os.path import basename
from glob import glob

from importlib.resources import files
from jsonschema.exceptions import ValidationError

from geoips.errors import PluginError
from geoips.filenames.base_paths import PATHS

LOG = logging.getLogger(__name__)


class BaseYamlPlugin(dict):
    """Base class for GeoIPS plugins."""

    def __init__(self, *args, **kwargs):
        """Class BaseYamlPlugin init method."""
        super().__init__(*args, **kwargs)

    def __repr__(self):
        """Class BaseYamlPlugin repr method."""
        val = super().__repr__()
        return f"{self.__class__.__name__}({val})"


#     @property
#     def id(self):
#         """Return the id of the plugin.
#
#         Typically this is just the name of the plugin, but some plugin classes
#         override this field. For example, the ProductPlugin class overrides
#         this to a tuple containing 'source_name' and 'name'."""
#         return self.name


class BaseModulePlugin:
    """Base class for GeoIPS plugins."""

    pass


class BaseInterface(abc.ABC):
    """Base class for GeoIPS interfaces.

    This class should not be instantiated directly. Instead, interfaces should be
    accessed by importing them from ``geoips.interfaces``. For example:
    ```
    from geoips.interfaces import algorithms
    ```
    will retrieve an instance of ``AlgorithmsInterface`` which will provide access to
    the GeoIPS algorithm plugins.
    """

    import geoips.plugin_registry as plugin_registry_module

    name = "BaseInterface"
    interface_type = None  # This is set by child classes
    rebuild_registries = PATHS["GEOIPS_REBUILD_REGISTRIES"]
    # Setting this attribute at the top level so it can be used by all methods.
    # This can be overridden by setting them in child interface classes
    apiVersion = "geoips/v1"

    def __new__(cls):
        """Plugin interface new method."""
        if not hasattr(cls, "name") or not cls.name:
            raise AttributeError(
                f"Error creating {cls.name} class. SubClasses of ``BaseInterface`` "
                "must have the class attribute 'name'."
            )
        cls.__doc__ = f"GeoIPS interface for {cls.name} plugins."
        # cls.__doc__ += interface_attrs_doc causes duplication warnings

        return super(BaseInterface, cls).__new__(cls)

    @property
    def namespace(self):
        """Default namespace used for the plugin registry associated with this class.

        By default, we use 'geoips.plugin_packages' as the namespace for interface
        classes. However, if a user has developed interfaces in a separate namespace
        from geoips, they can override this in their own classes by setting the
        namespace to search in.
        """
        if not hasattr(self, "_namespace"):
            # By default all GeoIPS interfaces will have self.apiVersion = 'geoips/v1'
            # If that attribute is not already set.
            self._namespace = f"{self.apiVersion.split('/')[0]}.plugin_packages"
        return self._namespace

    @property
    def plugin_registry(self):
        """The plugin registry associated with this interface.

        By default, the plugin registry used comes from the namespace
        'geoips.plugin_packages'. However, if a user has developed interfaces in a
        separate namespace from geoips, they can override this in their own classes by
        setting the namespace to search in.
        """
        if not hasattr(self, "_plugin_registry"):
            self._plugin_registry = self.plugin_registry_module.PluginRegistry(
                self.namespace
            )
        return self._plugin_registry

    @abc.abstractmethod
    def get_plugin(self, name, rebuild_registries=rebuild_registries):
        """Abstract function for retrieving a plugin under a certain interface.

        Parameters
        ----------
        name: str or tuple(str)
            - The name of the yaml-based plugin. Either a single string or a tuple of
              strings for product plugins.
        rebuild_registries: bool (default=True)
            - Whether or not to rebuild the registries if get_plugin fails. If set to
              true and get_plugin fails, rebuild the plugin registry, call then call
              get_plugin once more with rebuild_registries toggled off, so it only gets
              rebuilt once.
            - By default, the value of rebuild_registries is set in
              geoips.filenames.base_paths with a value of True. Users and
              developers can change this if desired.
        """
        pass

    @abc.abstractmethod
    def get_plugins(self):
        """Abstract function for retrieving all plugins under a certain interface."""
        pass

    def get_plugin_metadata(self, name):
        """Retrieve a plugin's metadata.

        Where the metadata of the plugin matches the plugin's corresponding entry in the
        plugin registry.

        Parameters
        ----------
        name: str or tuple(str)
            - The name of the plugin whose metadata we want.

        Returns
        -------
        metadata: dict
            - A dictionary of metadata for the requested plugin.
        """
        return self.plugin_registry.get_plugin_metadata(self, name)


class BaseYamlInterface(BaseInterface):
    """Base class for GeoIPS yaml-based plugin interfaces.

    This class should not be instantiated directly. Instead, interfaces should be
    accessed by importing them from ``geoips.interfaces``. For example:
    ```
    from geoips.interfaces import products
    ```
    will retrieve an instance of ``ProductsInterface`` which will provide access to
    the GeoIPS products plugins.
    """

    interface_type = "yaml_based"
    name = "BaseYamlInterface"
    use_pydantic = False

    def __new__(cls):
        """YAML plugin interface new method."""
        cls = super(BaseInterface, cls).__new__(cls)

        return cls

    def __init__(self):
        """YAML plugin interface init method."""
        self.supported_families = [
            basename(fname).split(".")[0]
            for fname in sorted(
                glob(str(files("geoips") / f"schema/{self.name}/*.yaml"))
            )
        ]

    def _create_registered_plugin_names(self, yaml_plugin):
        """Create a plugin name for plugin registry.

        Some interfaces need to override this (e.g. products) because they
        need a more complex name for retrieval.
        """
        return [yaml_plugin["name"]]

    @classmethod
    def _plugin_yaml_to_obj(cls, name, yaml_plugin, obj_attrs={}):
        """Convert a yaml plugin to an object.

        Convert the passed YAML plugin into an object and return it. The returned
        object will be derived from a class named ``<interface>Plugin`` where
        interface is the interface specified by the plugin. This class is derived
        from ``BasePlugin``.

        This function is used instead of predefined classes to allow setting ``__doc__``
        on a plugin-by-plugin basis. This allows collecting ``__doc__`` and
        from the plugin and using them in the objects.

        For a yaml plugin to be converted into an object it must meet the following
        requirements:

        - Must match the jsonschema spec provided for its interface.
        - The plugin must have the following non-empty top-level attributes.
          - interface: The name of the interface that the plugin belongs to.
          - family: The family of plugins this plugin belongs to within the interface.
          - name: The name of the plugin which must be unique within the interface.
          - docstring: A string to be used as the object's docstring.
        """
        obj_attrs["id"] = name
        obj_attrs["yaml"] = yaml_plugin

        missing = []

        for attr in [
            "package",
            "relpath",
            "interface",
            "family",
            "name",
            "docstring",
        ]:
            try:
                obj_attrs[attr] = yaml_plugin[attr]
            # This should be removed once we fully switch to pydantic models
            except TypeError:
                yaml_plugin = yaml_plugin.model_dump()
                obj_attrs[attr] = yaml_plugin[attr]
            except KeyError:
                missing.append(attr)
        if missing:
            raise PluginError(
                f"Plugin '{yaml_plugin['name']}' is missing the following required "
                f"top-level properties: '{missing}'"
            )

        obj_attrs["__doc__"] = obj_attrs["docstring"]

        plugin_interface_name = obj_attrs["interface"].title().replace("_", "")
        plugin_type = f"{plugin_interface_name}Plugin"

        plugin_base_class = BaseYamlPlugin
        if hasattr(cls, "plugin_class") and cls.plugin_class:
            plugin_base_class = cls.plugin_class
        return type(plugin_type, (plugin_base_class,), obj_attrs)(yaml_plugin)

    def __repr__(self):
        """Plugin interface repr method."""
        return f"{self.__class__.__name__}()"

    def get_plugin(self, name, rebuild_registries=None):
        """Get a plugin by its name.

        This default method can be overridden to provide different search
        functionality for an interface. An example of this is in the
        ProductsInterface which uses a tuple containing 'source_name' and
        'name'.

        Parameters
        ----------
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
        return self.plugin_registry.get_yaml_plugin(self, name, rebuild_registries)

    def get_plugins(self):
        """Retrieve all yaml plugin objects."""
        return self.plugin_registry.get_yaml_plugins(self)

    def plugin_is_valid(self, name):
        """Plugin is valid method."""
        try:
            self.get_plugin(name)
            return True
        except ValidationError:
            return False

    def plugins_all_valid(self):
        """Plugins all valid method."""
        try:
            self.get_plugins()
            return True
        except ValidationError:
            return False

    def test_interface(self):
        """Test interface method.

        Note this is currently only called via the
        tests/utils/test_interfaces.py script (which is
        not a valid pytest script, but called directly
        via the command line.
        """
        plugins = self.get_plugins()
        all_valid = self.plugins_all_valid()
        family_list = []
        plugin_ids = {}
        for plugin in plugins:
            # TODO: Refactor to remove this `if` block after full migration from JSON
            # to Pydantic schemas.
            if hasattr(plugin, "model_dump"):
                pdata = plugin.model_dump()
            else:
                pdata = plugin if isinstance(plugin, dict) else plugin.__dict__

            plugin_family = pdata.get("family")
            plugin_name = pdata.get("name")

            if not plugin_family or not plugin_name:
                raise ValueError(
                    f"Missing required plugin fields. "
                    f" Expected 'family' and 'name' got: family={plugin_family}, "
                    f"name={plugin_name}. Full plugin data: {pdata}"
                )
            if plugin_family not in family_list:
                family_list.append(plugin_family)
                plugin_ids[plugin_family] = []
            plugin_ids[plugin_family].append(plugin_name)

        output = {
            "all_valid": all_valid,
            "by_family": plugin_ids,
            "validity_check": {},
            "family": {},
            "func": {},
            "docstring": {},
        }
        for curr_family in plugin_ids:
            for curr_id in plugin_ids[curr_family]:
                output["validity_check"][curr_id] = self.plugin_is_valid(curr_id)
                output["func"][curr_id] = self.get_plugin(curr_id)
                output["family"][curr_id] = curr_family
                output["docstring"][curr_id] = output["func"][curr_id].docstring
        return output


class BaseClassInterface(BaseInterface):
    """Base Class for GeoIPS Interfaces.

    This class should not be instantiated directly. Instead, interfaces should be
    accessed by importing them from ``geoips.interfaces``. For example:
    ```
    from geoips.interfaces import algorithms
    ```
    will retrieve an instance of ``AlgorithmsInterface`` which will provide access to
    the GeoIPS algorithm plugins.
    """

    interface_type = "class_based"
    name = "BaseClassInterface"
    required_args = {}

    def __repr__(self):
        """Plugin interface repr method."""
        return f"{self.__class__.__name__}()"

    # def _plugin_module_to_obj(self, module, module_call_func="call", obj_attrs={}):
    #     """Convert a plugin module into an object.

    #     Convert the passed module into an object of type.
    #     """
    #     obj = plugin_module_to_obj(
    #         module=module, module_call_func=module_call_func, obj_attrs=obj_attrs
    #     )
    #     if obj.interface != self.name:
    #         raise PluginError(
    #             f"Plugin 'interface' attribute on '{obj.name}' plugin does not "
    #             f"match the name of its interface as specified by entry_points."
    #         )
    #     return obj

    def __init__(self):
        """Initialize module plugin interface."""
        self.supported_families = list(self.required_args.keys())

    @classmethod
    def _plugin_module_to_obj(cls, name, module, obj_attrs={}):
        """Convert a module plugin to an object.

        Convert the passed module plugin into an object and return it. The returned
        object will be derrived from a class named ``<interface>Plugin`` where
        interface is the interface specified by the plugin. This class is derrived
        from ``BasePlugin``.

        This function is used instead of predefined classes to allow setting ``__doc__``
        and ``__call__`` on a plugin-by-plugin basis. This allows collecting ``__doc__``
        and ``__call__`` from the plugin modules and using them in the objects.

        For a module to be converted into an object it must meet the following
        requirements:

        - The module must define a docstring. This will be used as the docstring for the
          plugin class as well as the docstring for the plugin when requested on the
          command line.  The first line will be used as a "short" description, and the
          full docstring will be used as a more detailed discussion of the plugin.
        - The following global attributes must be defined in the module:
        - interface: The name of the interface that the plugin belongs to.
        - family: The family of plugins that the plugin belongs to within the interface.
        - name: The name of the plugin which must be unique within the interface.
        - A callable named `call` that will be called when the plugin is used.

        Parameters
        ----------
        module : module
        The imported plugin module.
        obj_attrs : dict, optional
        Additional attributes to be assigned to the plugin object.

        Returns
        -------
        An object of type ``<interface>InterfacePlugin`` where ``<interface>`` is the
        name of the interface that the desired plugin belongs to.
        """
        obj_attrs["id"] = name
        obj_attrs["module"] = module

        missing = []
        for attr in ["interface", "family", "name"]:
            try:
                obj_attrs[attr] = getattr(module, attr)
            except AttributeError:
                missing.append(attr)

        if missing:
            raise PluginError(
                f"Plugin '{module.__name__}' from '{module.__file__}' is missing the "
                f"following required global attributes: '{missing}'."
            )

        if module.__doc__:
            obj_attrs["__doc__"] = module.__doc__
        else:
            raise PluginError(
                f"Plugin modules must have a docstring. "
                f"No docstring found in '{module.__name__}'."
            )
        obj_attrs["docstring"] = module.__doc__

        # Collect the callable and assign to __call__
        try:
            obj_attrs["__call__"] = staticmethod(getattr(module, "call"))
        except AttributeError as err:
            raise PluginError(
                f"Plugin modules must contain a callable name 'call'. This is missing "
                f"in plugin module '{module.__name__}'"
            ) from err

        plugin_interface_name = obj_attrs["interface"].title().replace("_", "")
        plugin_type = f"{plugin_interface_name}Plugin"

        plugin_base_class = BaseModulePlugin
        if hasattr(cls, "plugin_class") and cls.plugin_class:
            plugin_base_class = cls.plugin_class

        # Create an object of type ``plugin_type`` with attributes from ``obj_attrs``
        return type(plugin_type, (plugin_base_class,), obj_attrs)()

    def get_plugin(self, name, rebuild_registries=None):
        """Retrieve a plugin from this interface by name.

        Parameters
        ----------
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
        return self.plugin_registry.get_class_plugin(self, name, rebuild_registries)

    def get_plugins(self):
        """Retrieve all module plugins for this interface."""
        return self.plugin_registry.get_class_plugins(self)

    def plugin_is_valid(self, plugin):
        """Check that an interface is valid.

        Check that the requested interface function has the correct call signature.
        Return values should be as specified below, but are not programmatically
        verified.

        Note this is currently only called via the
        tests/utils/test_interfaces.py script (which is
        not a valid pytest script, but called directly
        via the command line), via the test_interface
        method within this base interface.

        Parameters
        ----------
        plugin : PluginObject
          A plugin object coming from _plugin_module_to_obj that needs to be validated.

        Returns
        -------
        bool
          True if valid, False if invalid
        """
        if plugin.family not in self.required_args:
            raise PluginError(
                f"'{plugin.family}' must be added to required args list"
                f"\nfor '{self.name}' interface,"
                f"\nfound in '{plugin.name}' plugin,"
                f"\nin '{plugin.module.__name__}' module"
                f"\nat '{plugin.module.__file__}'\n"
            )
        if plugin.family not in self.required_kwargs:
            raise PluginError(
                f"'{plugin.family}' must be added to required kwargs list"
                f"\nfor '{self.name}' interface,"
                f"\nfound in '{plugin.name}' plugin,"
                f"\nin '{plugin.module.__name__}' module"
                f"\nat '{plugin.module.__file__}'\n"
            )
        expected_args = self.required_args[plugin.family]
        expected_kwargs = self.required_kwargs[plugin.family]

        sig = inspect.signature(plugin.__call__)
        arg_list = []
        kwarg_list = []
        kwarg_defaults_list = []
        for param_key, param_value in sig.parameters.items():
            # kwargs are identified by a default value - parameter will include "="
            if "=" in str(param_value):
                # This is kwarg = default, splitting on = and taking the second
                # value only.
                default_value = str(param_value).split("=")[-1]
                kwarg_list += [str(param_key)]
                kwarg_defaults_list += [default_value]
            # If there is no "=", then it is a positional parameter
            else:
                arg_list += [str(param_key)]

        for expected_arg in expected_args:
            if expected_arg not in arg_list:
                raise PluginError(
                    f"MISSING expected arg '{expected_arg}' in '{plugin.name}'"
                    f"\nfor '{self.name}' interface,"
                    f"\nfound in '{plugin.name}' plugin,"
                    f"\nin '{plugin.module.__name__}' module"
                    f"\nat '{plugin.module.__file__}'\n"
                )
        for expected_kwarg in expected_kwargs:
            # If expected_kwarg is a tuple, first item is kwarg, second default value
            if isinstance(expected_kwarg, tuple):
                if expected_kwarg[0] not in kwarg_list:
                    raise PluginError(
                        f"MISSING expected kwarg '{expected_kwarg}' in '{plugin.name}'"
                        f"\nfor '{self.name}' interface,"
                        f"\nfound in '{plugin.name}' plugin,"
                        f"\nin '{plugin.module.__name__}' module"
                        f"\nat '{plugin.module.__file__}'\n"
                    )
            elif expected_kwarg not in kwarg_list:
                raise PluginError(
                    f"MISSING expected kwarg '{expected_kwarg}' in '{plugin.name}'"
                    f"\nfor '{self.name}' interface,"
                    f"\nfound in '{plugin.name}' plugin,"
                    f"\nin '{plugin.module.__name__}' module"
                    f"\nat '{plugin.module.__file__}'\n"
                )

        return True

    def plugins_all_valid(self):
        """Test the current interface by validating every Plugin.

        Returns
        -------
            True if all plugins are valid, False if any plugin is invalid.
        """
        plugins = self.get_plugins()
        for plugin in plugins:
            if not self.plugin_is_valid(plugin):
                return False
        return True

    def test_interface(self):
        """Test the current interface by validating each Plugin and testing each method.

        Test this interface by opening every Plugin available to the interface,
        and validating each plugin by calling `plugin_is_valid` for each.
        Additionally, ensure all methods of this interface work as expected:

        * get_plugins
        * get_plugin
        * plugin_is_valid
        * plugins_all_valid

        Returns
        -------
            A dictionary containing three keys:
            'by_family', 'validity_check', 'func', and 'family'. The value for each
            of these keys is a dictionary whose keys are the names of the Plugins.

            - 'by_family' contains a dictionary of plugin names sorted by family.
            - 'validity_check' contains a dict whose keys are plugin names and whose
              values are bools where `True` indicates that the Plugin's function is
              valid according to `plugin_is_valid`.
            - 'func' contains a dict whose keys are plugin names and whose values are
              the function for each Plugin.
            - 'family' contains a dict whose keys are plugin names and whose values
              are the contents of the 'family' attribute for each Plugin.
        """
        # plugin_names = self.get_plugins(sort_by="family")
        plugins = self.get_plugins()
        all_valid = self.plugins_all_valid()
        family_list = []
        plugin_ids = {}
        for plugin in plugins:
            if plugin.family not in family_list:
                family_list.append(plugin.family)
                plugin_ids[plugin.family] = []
            plugin_ids[plugin.family].append(plugin.id)

        output = {
            "all_valid": all_valid,
            "by_family": plugin_ids,
            "validity_check": {},
            "family": {},
            "func": {},
            "docstring": {},
        }
        for curr_family in plugin_ids:
            for curr_id in plugin_ids[curr_family]:
                plugin = self.get_plugin(curr_id)
                output["validity_check"][curr_id] = self.plugin_is_valid(plugin)
                output["func"][curr_id] = plugin
                output["family"][curr_id] = curr_family
                output["docstring"][curr_id] = output["func"][curr_id].docstring
        return output
