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
from importlib import import_module
from typing import Callable
from warnings import warn

from geoips.version import __version__ as geoips_version
from geoips.errors import EntryPointError, PluginError
from geoips.geoips_utils import find_entry_point, get_all_entry_points

LOG = logging.getLogger(__name__)

plugin_deprecations = True
if geoips_version >= "1.10.0":
    plugin_deprecations = False


def get_deprecated_name(module_name):
    """Get deprecated name."""
    # module_name == module.__name__
    # module.__name__ is ie geoips.plugins.modules.algorithms.pmw_tb.pmw_89pct
    # First split on interface name (algorithms), then drop the leading '.'
    path = module_name.split("plugins.modules")[-1]
    deprecated_name = path.split(".", 2)[2]
    warn(
        f"Variable 'name' not found in plugin module '{module_name}'."
        f"Assuming module name is "
        f"'{deprecated_name}'. "
        "Please update to add 'name' variable."
    )
    return deprecated_name


def plugin_repr(obj):
    """Repr plugin string."""
    return f'{obj.__class__}(name="{obj.name}", module="{obj.module}")'


def plugin_module_to_obj(interface, module, module_call_func="call", obj_attrs={}):
    """Convert a plugin module to an object.

    Convert the passed plugin module into an object and return it. The returned object
    will be derrived from a class specific to the passed interface whose name is
    ``<interface>Plugin``. This class is derrived from the ``BasePlugin``
    class.

    This function is used instead of predefined classes to allow setting ``__doc__`` and
    ``__call__`` on a plugin-by-plugin basis. This allows collecting ``__doc__`` and
    ``__call__`` from the plugin modules and using them in the objects.

    For a module to be converted into an object it must meet the following requirements:

    - The module must define a docstring. This will be used as the docstring for the
      plugin class as well as the docstring for the plugin when requested on the
      command line.  The first line will be used as a "short" description, and the
      full docstring will be used as a more detailed discussion of the plugin.
    - The following global attributes must be defined in the module:

      - name: The name of the plugin (must be unique for the interface)
      - family: The family of plugins within the interface that the plugin belongs to
    - A callable named `call` that will be called when the plugin is used.

    Parameters
    ----------
    interface : str
      Name of the interface that the desired plugin belongs to.
    plugin : str
      Name of the desired plugin.
    module_call_func : str, optional
      Use of this parameter is deprecated. Name of the callable within the plugin
      (defaults to "call").
    obj_attrs : dict, optional
      Additional attributes to be assigned to the plugin object.

    Returns
    -------
    An object of type ``<interface>InterfacePlugin`` where ``<interface>`` is the name
    of the interface that the desired plugin belongs to.
    """
    obj_attrs["interface"] = interface
    obj_attrs["module"] = module

    try:
        obj_attrs["__doc__"] = module.__doc__
    except AttributeError:
        raise PluginError(
            f"Required '__doc__' attribute not found in '{module.__name__}'"
        )
    # Don't know if we want to add this explicit "docstring" attribute - if we do,
    # module-based plugins will have EXACTLY the same attributes as yaml-based plugins.
    obj_attrs["docstring"] = module.__doc__

    try:
        obj_attrs["name"] = module.name
    except AttributeError:
        if plugin_deprecations:
            obj_attrs["name"] = get_deprecated_name(module.__name__)
        else:
            raise PluginError(
                f"Required 'name' attribute not found in '{module.__name__}'"
            )

    try:
        obj_attrs["family"] = module.family
    except AttributeError:
        if plugin_deprecations:
            warn(
                f"Use of the '{interface.deprecated_family_attr}' attribute is "
                "deprecated. All uses should be replaced with an attribute named "
                "'family'. In the future this will result in a PluginError.",
                DeprecationWarning,
                stacklevel=1,
            )
        else:
            raise PluginError(
                f"Required 'family' attribute not found in '{module.__name__}'"
            )
        try:
            obj_attrs["family"] = getattr(module, interface.deprecated_family_attr)
        except AttributeError:
            raise PluginError(
                f"Required 'family' attribute not found in '{module.__name__}'"
            )

    if module_call_func != "call":
        warn(
            f"Callable for plugin '{module.__name__}' is not named 'call'. "
            "This behavior is deprecated. The callable should be renamed to "
            "'call', and setup.py updated to point to the module vs function. "
            "In the future this will result in a PluginError.",
            DeprecationWarning,
            stacklevel=1,
        )
    # Collect the callable and assign to __call__
    try:
        obj_attrs["__call__"] = staticmethod(getattr(module, module_call_func))
    except AttributeError as err:
        raise PluginError(
            f"Plugin module '{module.__name__}' does not implement a function named "
            f"'{module_call_func}'."
        ) from err

    plugin_type = f"{interface.name.title()}Plugin"

    # Create an object of type ``plugin_type`` with attributes from ``obj_attrs``
    return type(plugin_type, (BasePlugin,), obj_attrs)()


class PluginMetaclass:
    """Metaclass for GeoIPS plugins.

    This metaclass accepts a module
    """


class BasePlugin:
    """Base class for GeoIPS plugins."""

    pass


interface_attrs_doc = """

    Attributes
    ----------
    name : string
        The name of the interface.
    entry_point_group : string
        The name of the group in entry_points to use when looking for Plugins
        of this type. If not set, "name" will be used.
    deprecated_family_attr : string
        If this attribute exists in a plugin module but "family" does not,
        use the contents of this attribute in place
        of "family" and raise a `DeprecationWarning`.
        If neither exist, a `PluginError` will be raised.
    """


class BaseInterface:
    """Base Class for GeoIPS Interfaces.

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

        # Default to using the name of the interface as its entrypoint
        if hasattr(cls, "entry_point_group") and cls.entry_point_group:
            warn(
                "Use of 'entry_point_group' to specify the entry point group of an "
                "interface is deprecated. The interface name should match the name of "
                "the entry point group.",
                DeprecationWarning,
                stacklevel=1,
            )
        else:
            cls.entry_point_group = cls.name

        cls.__doc__ = f"GeoIPS interface for {cls.name} plugins."
        # cls.__doc__ += interface_attrs_doc causes duplication warnings

        return super(BaseInterface, cls).__new__(cls)

    def __repr__(self):
        """Plugin interface repr method."""
        return f"{self.__class__.__name__}()"

    def _plugin_module_to_obj(self, module, module_call_func="call", obj_attrs={}):
        """Convert a plugin module into an object.

        Convert the passed module into an object of type.
        """
        return plugin_module_to_obj(
            self, module=module, module_call_func=module_call_func, obj_attrs=obj_attrs
        )

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
            Nothing
        """
        try:
            module = find_entry_point(self.entry_point_group, name)
        except EntryPointError:
            raise PluginError(
                f"Plugin '{name}' not found for '{self.name}' interface."
                " Note for deprecated plugins, function name MUST match"
                " name used within entry point.  Please check that"
                " module name, function name, and entry point name"
                " in setup.py all match if using deprecated interface."
                " Note you must reinstall after updating setup.py."
            )
        # This assumes that the module's Callable is named "call", so the module
        # itself is NOT a Callable instance.
        # Note this implies setup.py has been updated to point to the
        # MODULE vs the FUNCTION for fully updated plugins.
        # Since we know the function will always be named "call", we can just specify
        # the module in setup.py.
        if not isinstance(module, Callable):
            return plugin_module_to_obj(self, module)
        # If "module" is callable, treat this as a deprecated entry point
        # whose callable is specified in setup.py directly.
        else:
            func = module
            module = import_module(func.__module__)
            warn(
                f"Entry point for plugin '{module.__name__}' points to the Callable "
                "rather than the module. This behavior is deprecated. Please update "
                "the entry point to point to the plugin module. In the future this "
                "will raise a PluginError.",
                DeprecationWarning,
                stacklevel=1,
            )
            return plugin_module_to_obj(self, module, module_call_func=func.__name__)

    def get_plugins(self):
        """Get a list of plugins for this interface."""
        plugins = []
        for ep in get_all_entry_points(self.entry_point_group):
            # If this is pointing to the full module, and NOT the Callable function
            # instance, that means it is a "new" style plugin.
            # Just call plugin_module_to_obj on it directly.
            if not isinstance(ep, Callable):
                plugins.append(plugin_module_to_obj(self, ep))
            else:
                # If the entry point points to the Callable function, that means
                # it is an old style plugin.  We need to get the name of the function
                # from ep.__name__ and pass it to plugin_module_to_obj so it knows
                # what function it is looking for.
                module = import_module(ep.__module__)
                plugins.append(
                    plugin_module_to_obj(self, module, module_call_func=ep.__name__)
                )
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
