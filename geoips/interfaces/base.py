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

"""Base classes for BaseInterface and BasePlugin."""

import inspect
import logging

from jsonschema.exceptions import ValidationError

from geoips.errors import EntryPointError, PluginError
from geoips.geoips_utils import (
    find_entry_point,
    get_all_entry_points,
    load_all_yaml_plugins,
)
from geoips.schema import PluginValidator

LOG = logging.getLogger(__name__)

YAML_VALIDATOR = PluginValidator()
YAML_PLUGINS = load_all_yaml_plugins()


def plugin_repr(obj):
    """Repr plugin string."""
    return f'{obj.__class__}(name="{obj.name}", module="{obj.module}")'


def plugin_yaml_to_obj(yaml, obj_attrs={}):
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
    - The plugin must have the following top-level attributes and the must not be empty.
      - interface: The name of the interface that the plugin belongs to.
      - family: The family of plugins that the plugin belongs to within the interface.
      - name: The name of the plugin which must be unique within the interface.
      - docstring: A string to be used as the object's docstring.
    """
    obj_attrs["yaml"] = yaml

    missing = []
    for attr in [
        "package",
        "relpath",
        "abspath",
        "interface",
        "family",
        "name",
        "docstring",
    ]:
        try:
            obj_attrs[attr] = yaml[attr]
        except KeyError:
            missing.append(attr)

    if missing:
        raise PluginError(
            f"Plugin '{yaml['name']}' is missing the following required top-level "
            f"properties: {missing}"
        )

    obj_attrs["__doc__"] = obj_attrs["docstring"]

    plugin_interface_name = obj_attrs["interface"].title().replace("_", "")
    plugin_type = f"{plugin_interface_name}Plugin"

    return type(plugin_type, (BaseYamlPlugin,), obj_attrs)(yaml)


def plugin_module_to_obj(module, obj_attrs={}):
    """Convert a module plugin to an object.

    Convert the passed module plugin into an object and return it. The returned
    object will be derrived from a class named ``<interface>Plugin`` where
    interface is the interface specified by the plugin. This class is derrived
    from ``BasePlugin``.

    This function is used instead of predefined classes to allow setting ``__doc__`` and
    ``__call__`` on a plugin-by-plugin basis. This allows collecting ``__doc__`` and
    ``__call__`` from the plugin modules and using them in the objects.

    For a module to be converted into an object it must meet the following requirements:

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
    An object of type ``<interface>InterfacePlugin`` where ``<interface>`` is the name
    of the interface that the desired plugin belongs to.
    """
    obj_attrs["module"] = module

    missing = []
    for attr in ["interface", "family", "name"]:
        try:
            obj_attrs[attr] = getattr(module, attr)
        except AttributeError:
            missing.append(attr)

    if missing:
        raise PluginError(
            f"Plugin {module.__name__} is missing the following required global "
            f"attributes: {missing}."
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
            f"Plugin modules must contain a callable name 'call'. This is missing in "
            f"plugin module '{module.__name__}'"
        ) from err

    plugin_interface_name = obj_attrs["interface"].title().replace("_", "")
    plugin_type = f"{plugin_interface_name}Plugin"

    # Create an object of type ``plugin_type`` with attributes from ``obj_attrs``
    return type(plugin_type, (BaseModulePlugin,), obj_attrs)()


class BaseYamlPlugin(dict):
    """Base class for GeoIPS plugins."""

    def __init__(self, *args, **kwargs):
        """Class BaseYamlPlugin init method."""
        super().__init__(*args, **kwargs)

    def __repr__(self):
        """Class BaseYamlPlugin repr method."""
        val = super().__repr__()
        return f"{self.__class__.__name__}({val})"


class BaseModulePlugin:
    """Base class for GeoIPS plugins."""

    pass


class BaseInterface:
    """Base class for GeoIPS interfaces.

    This class should not be instantiated directly. Instead, interfaces should be
    accessed by importing them from ``geoips.interfaces``. For example:
    ```
    from geoips.interfaces import algorithms
    ```
    will retrieve an instance of ``AlgorithmsInterface`` which will provide access to
    the GeoIPS algorithm plugins.
    """

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

    def __new__(cls):
        """YAML plugin interface new method."""
        cls = super(BaseInterface, cls).__new__(cls)

        cls.validator = YAML_VALIDATOR
        cls._unvalidated_plugins = {plg["name"]: plg for plg in YAML_PLUGINS[cls.name]}

        return cls

    def __repr__(self):
        """Plugin interface repr method."""
        return f"{self.__class__.__name__}()"

    def get_plugin(self, name):
        """Get plugin method."""
        try:
            validated = self.validator.validate(self._unvalidated_plugins[name])
        except KeyError:
            raise PluginError(f"Plugin '{name}' not found for '{self.name}' interface.")
        return plugin_yaml_to_obj(validated)

    def get_plugins(self):
        """Get plugins method."""
        plugins = []
        for name in self._unvalidated_plugins.keys():
            plugins.append(self.get_plugin(name))
        return plugins

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
        """Test interface method."""
        plugins = self.get_plugins()
        all_valid = self.plugins_all_valid()
        family_list = []
        plugin_names = {}
        for plugin in plugins:
            if plugin.family not in family_list:
                family_list.append(plugin.family)
                plugin_names[plugin.family] = []
            plugin_names[plugin.family].append(plugin.name)

        output = {
            "all_valid": all_valid,
            "by_family": plugin_names,
            "validity_check": {},
            "family": {},
            "func": {},
            "docstring": {},
        }
        for curr_family in plugin_names:
            for curr_name in plugin_names[curr_family]:
                output["validity_check"][curr_name] = self.plugin_is_valid(curr_name)
                output["func"][curr_name] = self.get_plugin(curr_name)
                output["family"][curr_name] = curr_family
                output["docstring"][curr_name] = output["func"][curr_name].docstring
        return output


class BaseModuleInterface(BaseInterface):
    """Base Class for GeoIPS Interfaces.

    This class should not be instantiated directly. Instead, interfaces should be
    accessed by importing them from ``geoips.interfaces``. For example:
    ```
    from geoips.interfaces import algorithms
    ```
    will retrieve an instance of ``AlgorithmsInterface`` which will provide access to
    the GeoIPS algorithm plugins.
    """

    def __repr__(self):
        """Plugin interface repr method."""
        return f"{self.__class__.__name__}()"

    def _plugin_module_to_obj(self, module, module_call_func="call", obj_attrs={}):
        """Convert a plugin module into an object.

        Convert the passed module into an object of type.
        """
        obj = plugin_module_to_obj(
            module=module, module_call_func=module_call_func, obj_attrs=obj_attrs
        )
        if obj.interface != self.name:
            raise PluginError(
                f"Plugin 'interface' attribute on {obj.name} plugin does not match the "
                f"name of its interface as specified by entry_points."
            )
        return obj

    def get_plugin(self, name):
        """Retrieve a plugin from this interface by name.

        Parameters
        ----------
        name : str
          The name the desired plugin.

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
        try:
            module = find_entry_point(self.name, name)
        except EntryPointError:
            raise PluginError(f"Plugin '{name}' not found for '{self.name}' interface.")
        # Convert the module into an object
        return plugin_module_to_obj(module)

    def get_plugins(self):
        """Get a list of plugins for this interface."""
        plugins = []
        for ep in get_all_entry_points(self.name):
            plugins.append(plugin_module_to_obj(ep))
        return plugins

    def plugin_is_valid(self, name):
        """Check that an interface is valid.

        Check that the requested interface function has the correct call signature.
        Return values should be as specified below, but are not programmatically
        verified.

        Parameters
        ----------
        name : str
          Name of the interface to be validated

        Returns
        -------
        bool
          True if valid, False if invalid
        """
        plugin = self.get_plugin(name)
        if plugin.family not in self.required_args:
            raise PluginError(
                f"'{plugin.family}' must be added to required args list"
                f" for '{self.name}' interface,"
                f" found in '{plugin.name}' plugin,"
                f" in '{plugin.module.__name__}' module"
            )
        if plugin.family not in self.required_kwargs:
            raise PluginError(
                f"'{plugin.family}' must be added to required kwargs list"
                f" for '{self.name}' interface,"
                f" found in '{plugin.name}' plugin,"
                f" in '{plugin.module.__name__}' module"
            )
        expected_args = self.required_args[plugin.family]
        expected_kwargs = self.required_kwargs[plugin.family]

        sig = inspect.signature(plugin.__call__)
        arg_list = []
        kwarg_list = []
        kwarg_defaults_list = []
        for param in sig.parameters.values():
            # kwargs are identified by a default value - parameter will include "="
            if "=" in str(param):
                kwarg, default_value = str(param).split("=")
                kwarg_list += [kwarg]
                kwarg_defaults_list += [default_value]
            # If there is no "=", then it is a positional parameter
            else:
                arg_list += [str(param)]

        for expected_arg in expected_args:
            if expected_arg not in arg_list:
                LOG.error("MISSING expected arg %s", expected_arg)
                return False
        for expected_kwarg in expected_kwargs:
            # If expected_kwarg is a tuple, first item is kwarg, second default value
            if isinstance(expected_kwarg, tuple):
                if expected_kwarg[0] not in kwarg_list:
                    LOG.error("MISSING expected kwarg %s", expected_kwarg)
                    return False
            elif expected_kwarg not in kwarg_list:
                LOG.error("MISSING expected kwarg %s", expected_kwarg)
                return False

        return True

    def plugins_all_valid(self):
        """Test the current interface by validating every Plugin.

        Returns
        -------
            True if all plugins are valid, False if any plugin is invalid.
        """
        plugins = self.get_plugins()
        for plugin in plugins:
            if not self.plugin_is_valid(plugin.name):
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
            - 'family' contains a dict whose keys are plugin names and whose vlaues
              are the contents of the 'family' attribute for each Plugin.
        """
        # plugin_names = self.get_plugins(sort_by="family")
        plugins = self.get_plugins()
        all_valid = self.plugins_all_valid()
        family_list = []
        plugin_names = {}
        for plugin in plugins:
            if plugin.family not in family_list:
                family_list.append(plugin.family)
                plugin_names[plugin.family] = []
            plugin_names[plugin.family].append(plugin.name)

        output = {
            "all_valid": all_valid,
            "by_family": plugin_names,
            "validity_check": {},
            "family": {},
            "func": {},
            "docstring": {},
        }
        for curr_family in plugin_names:
            for curr_name in plugin_names[curr_family]:
                output["validity_check"][curr_name] = self.plugin_is_valid(curr_name)
                output["func"][curr_name] = self.get_plugin(curr_name)
                output["family"][curr_name] = curr_family
                output["docstring"][curr_name] = output["func"][curr_name].docstring
        return output
