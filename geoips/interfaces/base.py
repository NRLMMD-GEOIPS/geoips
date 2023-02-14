# # # Distribution Statement A. Approved for public release. Distribution unlimited.
# # #
# # # Author:
# # # Naval Research Laboratory, Marine Meteorology Division
# # #
# # # This program is free software:
# # # you can redistribute it and/or modify it under the terms
# # # of the NRLMMD License included with this program.
# # #
# # # If you did not receive the license, see
# # # https://github.com/U-S-NRL-Marine-Meteorology-Division/
# # # for more information.
# # #
# # # This program is distributed WITHOUT ANY WARRANTY;
# # # without even the implied warranty of MERCHANTABILITY
# # # or FITNESS FOR A PARTICULAR PURPOSE.
# # # See the included license for more details.

"""Base classes for BaseInterface and BasePlugin.
"""

import logging
from importlib import import_module
from typing import Callable
from warnings import warn

from geoips import __version__ as geoips_version
from geoips.errors import EntryPointError, PluginError
from geoips.geoips_utils import find_entry_point, get_all_entry_points

LOG = logging.getLogger(__name__)

plugin_deprecations = True
if geoips_version >= "2.0.0":
    plugin_deprecations = False


def plugin_repr(obj):
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
      plugin class as well as the description for the plugin when requested on the
      command line.
    - The following global attributes must be defined in the module:
      - name: The name of the plugin (must be unique for the interface)
      - family: The family of plugins within the interface that the plugin belongs to
      - description: A short description of the plugin. This will be used frequently on
        the command line and should be limited to something small.
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
        if plugin_deprecations:
            warn(
                f"Plugin module '{module.__name__}' does not have a docstring. "
                "Please add a module-level docstring",
                DeprecationWarning,
                stacklevel=1,
            )
        else:
            raise PluginError(
                f"Required '__doc__' attribute not found in '{module.__name__}'"
            )

    try:
        obj_attrs["name"] = module.name
    except AttributeError:
        if plugin_deprecations:
            warn(
                f"Variable 'name' not found in plugin module '{module.__name__}'."
                f"Assuming module name is "
                f"`{'.'.join(module.__name__.split('.')[-2:])}`. "
                "Please update to add 'name' variable."
            )
            obj_attrs["name"] = module.__name__.split(".")[-1]
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

    try:
        obj_attrs["description"] = module.description
    except AttributeError:
        if plugin_deprecations:
            warn(
                f"Plugin module '{module.__name__}' does not implement a 'description' "
                "attribute. In future releases this will result in a PluginError.",
                DeprecationWarning,
                stacklevel=1,
            )
            obj_attrs["description"] = None
        else:
            raise PluginError(
                f"Required 'description' attribute not found in '{module.__name__}'"
            )

    if module_call_func != "call":
        warn(
            f"Callable for plugin '{module.__name__}' is not named 'call'. "
            "This behavior is deprecated. The callable should be renamed to "
            "'call'. In the future this will result in a PluginError.",
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
        The name of the group in entry_points to use when looking for Plugins of this type. If not set, "name" will be used.
    deprecated_family_attr : string
        If this attribute exists in a plugin module but "family" does not, use the contents of this attribute in place
        of "family" and raise a `DeprecationWarning`. If neither exist, a `PluginError` will be raised.
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
        cls.__doc__ += interface_attrs_doc

        return super(BaseInterface, cls).__new__(cls)

    def __repr__(self):
        return f"{self.__class__.__name__}()"

    def _plugin_module_to_obj(self, module, module_call_func="call", obj_attrs={}):
        """Convert a plugin module into an object.

        Convert the passed module into an object of type"""
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
            # Below line doesn't seem to deal with entry points inside directories.
            # i.e. searches for "pmw_37pct", but can't find it because it is defined
            #   as "pmw_tb.pmw_37pct"
            #module = find_entry_point(self.entry_point_group, name)
            eps = get_all_entry_points(self.entry_point_group)
            eps_names = [ep.__name__ for ep in eps]
            ep_index = eps_names.index(name)
            module = import_module(eps[ep_index].__module__)
        except EntryPointError as err:
            raise PluginError(f"Plugin {name} not found for {self.name} interface")
        # This assumes that the module's callable is named "callable"
        if isinstance(module, Callable):
            return plugin_module_to_obj(self, module)
        # If "module" is not callable, treat this as a deprecated entry point
        # whose callable is specified in setup.py directly
        else:
            #func = module
            #module = import_module(func.__module__)
            # Below line can probably be replaced with above two lines if
            # commented out line in try block above is fixed.
            func = eps[ep_index]
            warn(
                f"Entry point for plugin '{module.__name__}' point to the callable "
                "rather than the module. This behavior is deprecated. Please update "
                "the entry point to point to the plugin module. In the future this "
                "will raise a PluginError.",
                DeprecationWarning,
                stacklevel=1,
            )
            return plugin_module_to_obj(self, module, module_call_func=func.__name__)

    def get_plugins(self):
        """Get a list of plugins for this interface."""
        # This is more complicated than needed. To simplify, we will need to remove the
        # function name from entry points.
        plugins = []
        for ep in get_all_entry_points(self.entry_point_group):
            module = import_module(ep.__module__)
            if hasattr(module, "call"):
                plugins.append(plugin_module_to_obj(module))
            else:
                plugins.append(
                    plugin_module_to_obj(self, module, module_call_func=ep.__name__)
                    #self._plugin_module_to_obj(module, module_call_func=ep.__name__)
                )

        # plugins = [
        #     self.create_plugin(import_module(ep.__module__),
        #     module_call_func=ep.__name__)
        #     for ep in get_all_entry_points(self.entry_point_group)
        # ]
        return plugins

    def is_valid(self, name):
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
        '''
        """
        plugin = self.get_plugin(name)
        expected_args = self.required_args[plugin.family]

        import inspect
        sig = inspect.signature(plugin.__call__)
        arg_list = [s.strip().split('=')[0] for s in str(sig).strip('()').split(',')]

        for expected_arg in expected_args:
            if expected_arg not in arg_list:
                return False
        return True

    def test_interface_plugins(self):
        """Test the current interface by validating every Plugin.

        Test this interface by opening every Plugin available to the interface. Then validate each plugin by calling
        `is_valid` for each.

        Returns:
            A dictionary containing three keys: 'by_family', 'validity_check', 'func', and 'family'. The value for each
            of these keys is a dictionary whose keys are the names of the Plugins.

            - 'by_family' contains a dictionary of plugin names sorted by family.
            - 'validity_check' contains a dict whose keys are plugin names and whose values are bools where `True`
              indicates that the Plugin's function is valid according to `is_valid`.
            - 'func' contains a dict whose keys are plugin names and whose values are the function for each Plugin.
            - 'family' contains a dict whose keys are plugin names and whose vlaues are the contents of the 'family'
              attribute for each Plugin.
        """
        #plugin_names = self.get_plugins(sort_by="family")
        plugins = self.get_plugins()
        family_list = []
        plugin_names = {}
        for plugin in plugins:
            if plugin.family not in family_list:
                family_list.append(plugin.family)
                plugin_names[plugin.family] = []
            plugin_names[plugin.family].append(plugin.__call__.__name__)

        output = {
            "by_family": plugin_names,
            "validity_check": {},
            "family": {},
            "func": {},
        }
        for curr_family in plugin_names:
            for curr_name in plugin_names[curr_family]:
                output["validity_check"][curr_name] = self.is_valid(curr_name)
                output["func"][curr_name] = self.get_plugin(curr_name)
                #output["family"][curr_name] = self.get_family(curr_name)
                output["family"][curr_name] = curr_family
        return output
