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

''' Interface Under Development.  Please provide feedback to geoips@nrlmry.navy.mil

    Wrapper functions for geoips METOCTIFF interfacing.

    Once all related wrapper functions are finalized,
    this module will be moved to the geoips/stable sub-package.
'''

import logging
import collections
from warnings import warn
from importlib import import_module
LOG = logging.getLogger(__name__)

from geoips.utils.decorators import deprecated, developmental
from geoips.geoips_utils import find_entry_point, list_entry_points


### Algorithm functions ###
@developmental
def is_valid(func_name):
    ''' Interface Under Development, please provide feedback to geoips@nrlmry.navy.mil

    Check that the requested algorithm function has the correct call signature.
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
    func = get(func_name)
    # If this is __init__ (no __code__ attr), skip it
    if not hasattr(func, '__code__'):
        return False
    required_args = {'single_channel': ['arrays'],
                     'channel_combination': ['arrays'],
                     'list_numpy_to_numpy': ['arrays'],
                     'xarray_to_numpy': ['xobj'],
                     'rgb': ['arrays'],
                     'xarray_dict_to_xarray': ['xarray_dict'],
                     'xarray_dict_dict_to_xarray': ['xarray_dict_dict'],
                     'xarray_dict_to_xarray_dict': ['xarray_dict'],
                     'xarray_dict_area_def_to_numpy': ['xarray_dict', 'area_def'],
                     }
    required_kwargs = {'single_channel': [],
                       'channel_combination': [],
                       'xarray_to_numpy': [],
                       'list_numpy_to_numpy': [],
                       'rgb': [],
                       'xarray_dict_to_xarray': [],
                       'xarray_dict_dict_to_xarray': [],
                       'xarray_dict_to_xarray_dict': [],
                       'xarray_dict_area_def_to_numpy': [],
                       }

    family = get_family(func_name)

    if family not in required_args:
        raise ValueError(f'\nfunc "{func_name}" of unsupported type "{family}"\n'
                         f'family must be one of: {required_kwargs.keys()}\n'
                         f'Either add "{family}" to list of supported types in\n'
                         f'alg.is_valid.required_args\n'
                         f'or update "{func.__module__}" to a supported type')

    if family not in required_kwargs:
        raise ValueError(f'\nfunc "{func_name}" of unsupported type "{family}"\n'
                         f'family must be one of: {required_kwargs.keys()}\n'
                         f'Either add "{family}" to list of supported types in\n'
                         f'geoips.dev.alg.is_valid.required_kwargs\n'
                         f'or update "{func.__module__}" to a supported type')

    num_args = len(required_args[family])
    num_kwargs = len(required_kwargs[family])

    func_vars = func.__code__.co_varnames
    func_args = func_vars[0:num_args]
    func_kwargs = func_vars[num_args:num_args+num_kwargs]

    # Check for required call signature arguments
    if not set(required_args[family]).issubset(set(func_args)):
        LOG.error("INVALID ALG FUNC '%s': '%s' alg func type must have required arguments: '%s'",
                  func_name, family, func_args[family])
        return False

    # Check for optional call signature keyword arguments
    if not set(required_kwargs[family]).issubset(set(func_kwargs)):
        LOG.error("INVALID ALG FUNC '%s': '%s' func type must have kwargs: '%s'",
                  func_name, family, required_kwargs[family])
        return False

    return True


@deprecated(is_valid)
def is_valid_alg(alg_func_name):
    return is_valid(alg_func_name)


@developmental
def get(func_name):
    ''' Interface Under Development, please provide feedback to geoips@nrlmry.navy.mil

    Retrieve the requested algorithm function

    See: geoips.dev.alg.is_valid for full list of supported algorithm function call signatures and return values

    Args:
        func_name (str) : Desired algorithm function (ie, 'visir.IR_BD', 'pmw_tb.pmw_89pct', 'pmw_tb.color89', etc)

    Returns:
        (<alg function>) : Algorithm function
    '''
    return find_entry_point('algorithms', func_name)


@deprecated(get)
def get_alg(alg_func_name):
    return get(alg_func_name)


@developmental
def get_family(func_name):
    ''' Interface Under Development, please provide feedback to geoips@nrlmry.navy.mil

    Retrieve type of the requested algorithm function.
    Type specifies the required call signature and return values

    Args:
        func_name (str) : Desired algorithm function (ie, 'visir.IR_BD', 'pmw_tb.pmw_89pct', 'pmw_tb.color89', etc)

    Returns:
        (str) : Algorithm function type
    '''
    func = find_entry_point('algorithms', func_name)
    try:
        return getattr(import_module(func.__module__), 'family')
    except AttributeError:
        msg = f'Algorithm attribute "alg_func_type", used in {func_name}, is deprecated and will be'
        msg += ' removed in a future release. Please replace all occurrences with "family".'

        warn(msg, DeprecationWarning, stacklevel=1)
        return getattr(import_module(func.__module__), 'alg_func_type')


@deprecated(get_family)
def get_alg_type(alg_func_name):
    return get_family(alg_func_name)


def get_list(by_family=True):
    ''' Interface Under Development, please provide feedback to geoips@nrlmry.navy.mil

    List all available algorithm functions within the current GeoIPS instantiation, sorted by alg_family

    Algorithm function "type" determines exact required call signatures and return values

    See geoips.dev.alg.is_valid? for a list of available algorithm function types and associated call signatures / return values.
    See geoips.dev.alg.get(func_name) to retrieve the requested algorithm function
    See geoips.dev.alg.get_family(func_name) to retrieve the requested algorithm function type

    Returns:
        (dict) : Dictionary with all algorithm function types as keys, and associated algorithm function names (str) as values.
    '''
    if by_family:
        all_funcs = collections.defaultdict(list)
        for currfunc in list_entry_points('algorithms'):
            family = get_family(currfunc)
            if currfunc not in all_funcs[family]:
                all_funcs[family].append(currfunc)
        return all_funcs
    else:
        return [(func, get_family(func), get_description(func)) for func in sorted(list_entry_points('algorithms'))]


@deprecated(get_list)
def list_algs_by_type():
    return get_list(by_family=True)


def get_description(func_name):
    ''' Interface Under Development, please provide feedback to geoips@nrlmry.navy.mil
        
    Retrieve description of the requested algorithm function.
    Type specifies the required call signature and return values
                                                                                                                                                                                                             
    Args:
        func_name (str) : Desired algorithm function (ie, 'visir.IR_BD', 'pmw_tb.pmw_89pct', 'pmw_tb.color89', etc)
        
    Returns:
        (str) : Algorithm description
    ''' 
    func = find_entry_point('algorithms', func_name)
    return getattr(import_module(func.__module__), 'description', '')


def test_interface():
    ''' Finds and opens every alg func available within the current geoips instantiation

    See geoips.dev.alg.is_valid? for a list of available alg func types and associated call signatures / return values.
    See geoips.dev.alg.get(func_name) to retrieve the requested alg func

    Returns:
        (list) : List of all successfully opened geoips alg funcs
    '''
    curr_names = get_list(by_family=True)
    out_dict = {'by_family': curr_names, 'validity_check': {}, 'family': {}, 'func': {}}
    for curr_family in curr_names:
        for curr_name in curr_names[curr_family]:
            out_dict['validity_check'][curr_name] = is_valid(curr_name)
            out_dict['func'][curr_name] = get(curr_name)
            out_dict['family'][curr_name] = get_family(curr_name)
    return out_dict 


@deprecated(test_interface)
def test_alg_interface():
    return test_interface()