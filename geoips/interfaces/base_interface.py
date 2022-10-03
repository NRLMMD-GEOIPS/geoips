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
import collections
from warnings import warn
from importlib import import_module

LOG = logging.getLogger(__name__)

from geoips.utils.decorators import deprecated, developmental
from geoips.geoips_utils import find_entry_point, list_entry_points


def import_interface(name):
    try:
        return import_module(f'geoips.stable.{name}')
    except ModuleNotFoundError:
        try:
            return import_module(f'geoips.dev.{name}')
        except ModuleNotFoundError:
            raise ModuleNotFoundError(f'Module "{name}" not found in either stable or developmental interface sets')


class BaseInterface:
    def __new__(cls):
        if not hasattr(cls, 'name') or not cls.name:
            raise AttributeError(f'Error creating {cls.name} class. SubClasses of "BaseInterface" must have the class attribute "name".')
        # Default to using the name of the interface as its entrypoint
        if not hasattr(cls, 'entry_point') or not cls.entry_point:
            cls.entry_point = cls.name
        return super(BaseInterface, cls).__new__(cls)

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
            See geoips.dev.alg.get_family
            See geoips.dev.alg.list_algs_by_type

        For product based algorithm functions:
            See geoips.dev.alg.get
            See geoips.dev.alg.get_alg_name
            See geoips.dev.alg.get_alg_args
        '''
        """
        try:
            family = self.get_family(name)
        except AttributeError:
            func = self.get(name)
        family = self.get_family(name)

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
        self.is_valid(name)
        func = find_entry_point(self.entry_point, name)
        return func

    def get_plugin_attr(self, name, attr):
        """Retrieve the requested attribute from the named Plugin.
        
        Given the name of an existing GeoIPS Plugin, retrieve an attribte's value from that plugin by name. For example,
        if a plugin exists for the "algorithm" interface called "myalgorithm" and we want to retrieve it's "family"
        attribute, this would be called as:
            from interfaces import algorithms
            algorithms.get_plugin_attr('myplugin', 'family')
        
        Args:
            name: The name of a Plugin.
            attr: The name of an attribute of the named Plugin.
        
        Returns:
            The contents of the named attribute of the named Plugin.

        Raises:
            AttributeError if the plugin doesn't have the requested attribute
        """
        func = find_entry_point(self.entry_point, name)
        mod = import_module(func.__module__)
        return getattr(mod, attr)

    def get_family(self, name):
        """Retrieve the family of the requested plugin.
        
        Given the name of a plugin, return its family. This should be available in the plugin as `plugin.family`.

        Args:
            name: The name of a plugin.
        
        Returns:
            The family of the named plugin as a string.
       
        Raises:
            AttributeError if the plugin doesn't have a "family" attribute
        """
        try:
            # This tries mod's family attribute.
            # If that fails and "deprecated_family_attr" is set, tries that attribute on mod.
            return self.get_plugin_attr(name, 'family')
        except AttributeError as err:
            if hasattr(self, 'deprecated_family_attr'):
                try:
                    return self.get_plugin_attr(name, self.deprecated_family_attr)
                except AttributeError:
                    pass
            raise AttributeError(f'Attribute not found {mod.__name__}.{family_attr}. Plugins must carry the "family" attribute.')

    def get_description(self, name):
        """Retrieve the description of the requested plugin.
        
        Given the name of a plugin, return its description. This should be available in the plugin as
        `plugin.description`
        
        Args:
            name: The name of a plugin.
        
        Returns:
            The description of the named plugin as a string.
       
        Raises:
            AttributeError if the plugin doesn't have a "description" attribute
        """
        try:
            self.get_plugin_attr(name, 'description')
        except AttributeError:
            msg = f'Plugin {name} does not have a "description" attribute. In the future this will raise an AttributeError.'
            warn(msg, FutureWarning, stacklevel=1)
        
    def get_list(self, with_family=False, with_description=False, group_by_family=False):
        plugins = sorted(list_entry_points(self.entry_point))
        to_zip = [plugins]
        if with_family or group_by_family:
            families = [self.get_family(plugin) for plugin in plugins]
            
            to_zip.append(families)
        if with_description:
            descriptions = [self.get_description(plugin) for plugin in plugins]

        if group_by_family:
            grouped_plugins = collections.defaultdict(list)
            for currfunc in list_entry_points(self.entry_point):
                family = self.get_family(currfunc)
                if currfunc not in grouped_plugins[family]:
                    grouped_plugins[family].append(currfunc)
            return grouped_plugins
        return [(func, self.get_family(func), self.get_description(func)) for func in sorted(list_entry_points(self.entry_point))]
    
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