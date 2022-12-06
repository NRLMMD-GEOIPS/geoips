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

'''
Interface Under Development.  Please provide feedback to geoips@nrlmry.navy.mil
'''

import logging
from importlib import import_module
from typing import Callable
from warnings import warn

from geoips.geoips_utils import find_entry_point, get_all_entry_points

LOG = logging.getLogger(__name__)


def import_interface(name):
    try:
        return import_module(f'geoips.stable.{name}')
    except ModuleNotFoundError:
        try:
            return import_module(f'geoips.dev.{name}')
        except ModuleNotFoundError:
            raise ModuleNotFoundError(f'Module "{name}" not found in either stable or developmental interface sets')


def plugin_repr(obj):
    return f'{obj.__class__}(name="{obj.name}", module="{obj.module}")'


def plugin_module_to_obj(interface, module, module_call_func='callable', obj_attrs={}):
    obj_attrs['interface'] = interface
    obj_attrs['module'] = module

    try:
        obj_attrs['__doc__'] = module.__doc__
    except AttributeError:
        warn(
            f'Plugin module "{module.__name__}" does not have a docstring. Please add a module-level docstring',
            DeprecationWarning,
            stacklevel=1
        )

    try:
        obj_attrs['name'] = module.name
    except AttributeError:
        warn(
            f'Variable "name" not found in plugin module "{module.__name__}".'
            'Assuming module name is `\',\'.join(module.__name__.split(\'.\')[-2:])`.'
            'Please update to add "name" variable.'
        )
        obj_attrs['name'] = ','.join(module.__name__.split('.')[-2:])

    try:
        obj_attrs['family'] = module.family
    except AttributeError:
        try:
            obj_attrs['family'] = getattr(module, interface.deprecated_family_attr)
            warn(f'Use of the "{interface.deprecated_family_attr}" attribute is deprecated. '
                 'All uses should be replaced with an attribute named "family. '
                 'In the future this iwll result in a TypeError.',
                 DeprecationWarning,
                 stacklevel=1)
        except AttributeError:
            raise AttributeError(
                f'Attribute not found `{module.__name__}.family`. Plugins must carry the "family" attribute.'
            )

    try:
        obj_attrs['description'] = module.description
    except AttributeError:
        warn(f'Plugin module "{module.__name__}" does not implement a "description" attribute. '
             'In future releases this will result in a TypeError.',
             DeprecationWarning,
             stacklevel=1
             )
        obj_attrs['description'] = None

    if module_call_func != 'callable':
        warn(f'Callable for plugin "{module.__name__}" is not named "callable". '
             'This behavior is deprecated. The callable should be renamed to "callable". '
             'In the future this will result in a TypeError.',
             DeprecationWarning,
             stacklevel=1
             )
    # Collect the callable and assign to __call__
    try:
        obj_attrs['__call__'] = staticmethod(getattr(module, module_call_func))
    except AttributeError:
        raise TypeError(
            f'Plugin module "{module.__name__}" does not implement a function named "{module_call_func}".')

    plugin_type = f'{interface.__class__.__name__}Plugin'
    return type(plugin_type, (BaseInterfacePlugin,), obj_attrs)()


class BaseInterfacePlugin:
    pass


class BaseInterface():
    def __new__(cls):
        if not hasattr(cls, 'name') or not cls.name:
            raise AttributeError(f'Error creating {cls.name} class. SubClasses of "BaseInterface" must have the '
                                 'class attribute "name".')
        # Default to using the name of the interface as its entrypoint
        if hasattr(cls, 'entry_point_group') and cls.entry_point_group:
            warn('Use of "entry_point_group" to specify the entry point group of an interface is deprecated. '
                 'The interface name should match the name of the entry point group.',
                 DeprecationWarning,
                 stacklevel=1)
        else:
            cls.entry_point_group = cls.name

        return super(BaseInterface, cls).__new__(cls)

    def get(self, name):
        """Retrieve a plugin's function.

        Each plugin defines one callable function. Given the name of a function, returns that plugin's function.

        Args:
            name: The name of a plugin.

        Returns:
            A callable function for the named plugin.

        Raises:
            Nothing
        """
        module = find_entry_point(self.entry_point_group, name)
        # This assumes that the module's callable is named "callable"
        if not isinstance(module, Callable):
            return self.create_plugin(module)
        # If "module" is callable, treat this as a deprecated entry point
        # whose callable is specified in setup.py directly
        else:
            func = module
            module = import_module(func.__module__)
            warn(f'Entry point for plugin "{module.__name__}" point to the callable rather than the module. '
                 'This behavior is deprecated. Please update the entry point to point to the plugin module. '
                 'In the future this will raise a TypeError.',
                 DeprecationWarning,
                 stacklevel=1
                 )
            return self.create_plugin(module, module_call_func=func.__name__)

    def get_list(self):
        # This is more complicated than needed. To simplify, we will need to remove the function name from entry points.
        plugins = []
        for ep in get_all_entry_points(self.entry_point_group):
            module = import_module(ep.__module__)
            if hasattr(module, 'callable'):
                plugins.append(self.create_plugin(module))
            else:
                return self.create_plugin(module, module_call_func=ep.__name__)

        plugins = [self.create_plugin(import_module(ep.__module__), module_call_func=ep.__name__)
                   for ep in get_all_entry_points(self.entry_point_group)]
        return plugins

    def is_valid(self, name):
        """Check that an interface is valid.

        Check that the requested interface function has the correct call signature.
            Return values should be as specified below, but are not programmatically verified.

        Args:
            func_name (str) : Desired algorithm function (ie, 'visir.IR_BD', 'pmw_tb.pmw_89pct', 'pmw_tb.color89', etc)

        Returns:
            (bool) : True if 'func_name' has the appropriate call signature
                     False if algorithm function:
                            does not contain all required arguments
                            does not contain all required keyword arguments

        Algorithm func type currently found in
            <geoips_package>.algorithms.*.<func_name>.alg_params['alg_family']

        Algorithm functions currently defined in
            <geoips_package>.algorithms.*.<func_name>.<func_name>
        and requested within the product parameters dictionary
            See geoips.dev.product.check_product_params_dict

        func types currently one of:

               'list_numpy_to_numpy' : call signature <func_name>(arrays)
                                       return value: dstacked_array
               The following are subsets of the "list_numpy_to_numpy" type:
                   'single_channel' : call signature <func_name>(arrays)
                                      return value: array_2d
                   'channel_combination' : call signature <cmap_func_name>(arrays)
                                           return value: array_2d
                   'rgb' : call signature <cmap_func_name>(arrays)
                                return value: array_rgba

        Call signature array lists:
            Must be same length and in same order as required within function. Specified in product/sensor config.

        Return arrays:
            array_2d is a single 2d array of the processed dat
            array_rgba contains dstacked red, green, blue and (optional) alpha arrays.
            dstacked_array contains arbitrary output arrays dstacked into a single numpy array

        For package based algorithm functions:
            See geoips.dev.alg.get
            See geoips.dev.alg.list_algs_by_type

        For product based algorithm functions:
            See geoips.dev.alg.get
            See geoips.dev.alg.get_alg_name
            See geoips.dev.alg.get_alg_args
        '''
        """
        plugin = self.get(name)

    def create_plugin(self, module, module_call_func='callable', obj_attrs={}):
        return plugin_module_to_obj(self, module=module, module_call_func=module_call_func, obj_attrs=obj_attrs)

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
        plugin_names = self.get_list(sort_by='family')
        output = {'by_family': plugin_names, 'validity_check': {}, 'family': {}, 'func': {}}
        for curr_family in plugin_names:
            for curr_name in plugin_names[curr_family]:
                output['validity_check'][curr_name] = self.is_valid(curr_name)
                output['func'][curr_name] = self.get(curr_name)
                output['family'][curr_name] = self.get_family(curr_name)
        return output
