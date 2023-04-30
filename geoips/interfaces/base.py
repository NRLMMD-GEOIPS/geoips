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

from geoips.errors import EntryPointError, PluginError
from geoips.geoips_utils import find_entry_point, get_all_entry_points

LOG = logging.getLogger(__name__)


def plugin_repr(obj):
    """Repr plugin string."""
    return f'{obj.__class__}(name="{obj.name}", module="{obj.module}")'


def plugin_module_to_obj(module, obj_attrs={}):
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
      - interface: The name of the interface that the plugin belongs to.
      - family: The family of plugins that the plugin belongs to within the interface.
      - name: The name of the plugin which must be unique within the interface.
    - A callable named `call` that will be called when the plugin is used.

    Parameters
    ----------
    plugin : str
      Name of the desired plugin.
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

    plugin_type = f"{obj_attrs['interface'].title()}Plugin"

    # Create an object of type ``plugin_type`` with attributes from ``obj_attrs``
    return type(plugin_type, (BasePlugin,), obj_attrs)()


class BasePlugin:
    """Base class for GeoIPS plugins."""

    pass


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
            module=module, module_call_func=module_call_func, obj_attrs=obj_attrs
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
