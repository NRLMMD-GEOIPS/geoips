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

''' Interface Under Development.  Please provide feedback to geoips@nrlmry.navy.mil

    Wrapper functions for geoips title format interfacing.

    Once all related wrapper functions are finalized,
    this module will be moved to the geoips/stable sub-package.
'''

import collections
from importlib import import_module
import logging

from geoips.geoips_utils import find_entry_point, list_entry_points

LOG = logging.getLogger(__name__)


def is_valid_title(title_func_name):
    ''' Interface Under Development, please provide feedback to geoips@nrlmry.navy.mil

    Check that the requested title function has the correct call signature.
        Return values should be as specified below, but return values are not verified with this format check.

    Args:
        title_func_name (str) : Name of requested title function

    Returns:
        (bool) : True if 'title_func_name' function has the appropriate call signature
                 False if title function:
                        does not contain all required arguments
                        does not contain all required keyword arguments
    '''
    required_args = {'standard': []}

    required_kwargs = {'standard': []}

    try:
        title_type = get_title_type(title_func_name)
    except ImportError as resp:
        LOG.warning('Module %s in title package not a valid title module: '
                    'If this is intended to be a valid title module, ensure "title_type" '
                    'is defined: Exception: "%s"',
                    title_func_name, str(resp))
        return False
    try:
        title_func = get_title(title_func_name)
    except ImportError as resp:
        raise ImportError(f'INVALID TITLE {title_func_name}: '
                          f'Must specify function "{title_func_name}" within module "{title_func_name}": '
                          f'Exception: "{resp}"')

    if title_type not in required_args:
        raise TypeError(f"INVALID TITLE FUNC {title_func_name}: "
                        f"Unknown title func type {title_type}, allowed types: {required_args.keys()}")

    if title_type not in required_kwargs:
        raise TypeError(f"INVALID TITLE FUNC {title_func_name}: "
                        f"Unknown title func type {title_type}, allowed types: {required_kwargs.keys()}")

    num_args = len(required_args[title_type])
    num_kwargs = len(required_kwargs[title_type])

    # If this is __init__ (no __code__ attr), skip it
    if not hasattr(title_func, '__code__'):
        return False
    title_vars = title_func.__code__.co_varnames
    title_args = title_vars[0:num_args]
    title_kwargs = title_vars[num_args:num_args+num_kwargs]

    # Check for required call signature arguments
    if not set(required_args[title_type]).issubset(set(title_args)):
        LOG.error("INVALID TITLE FUNCTION '%s': '%s' title type must have required arguments: '%s'",
                  title_func_name, title_type, required_args[title_type])
        return False

    # Check for call signature keyword arguments
    if not set(required_kwargs[title_type]).issubset(set(title_kwargs)):
        LOG.error("INVALID TITLE FUNCTION '%s': '%s' title type must have optional kwargs: '%s'",
                  title_func_name, title_type, required_kwargs[title_type])
        return False

    return True


def get_remove_duplicates_func(title_func_name):
    ''' Interface Under Development, please provide feedback to geoips@nrlmry.navy.mil

    Retrieve the requested function to remove duplicate output files

    See: geoips.dev.title.is_valid_title for full list of supported title function call signatures and return values

    Args:
        title_func_name (str) : Name of requested title function
                                   (ie, 'geoips_fname', 'tc_fname', 'metoctiff_fname', etc)

    Returns:
        (<title function>) : Function for generating titles of the specified format.
    '''
    curr_func = find_entry_point('title_formats', title_func_name)
    return getattr(import_module(curr_func.__module__), title_func_name+'_remove_duplicates')


def get_title(title_func_name):
    ''' Interface Under Development, please provide feedback to geoips@nrlmry.navy.mil

    Retrieve the requested output title function

    See: geoips.dev.title.is_valid_title for full list of supported title function call signatures and return values

    Args:
        title_func_name (str) : Name of requested title function
                                   (ie, 'geoips_fname', 'tc_fname', 'metoctiff_fname', etc)

    Returns:
        (<title function>) : Function for generating titles of the specified format.
    '''
    return find_entry_point('title_formats', title_func_name)


def get_title_type(func_name):
    ''' Interface Under Development, please provide feedback to geoips@nrlmry.navy.mil

    Retrieve type of the requested output title function.
    Type specifies the required call signature and return values

    See: geoips.dev.title.is_valid_title for full list of supported title function call signatures and return values

    Args:
        title_func_name (str) : Name of requested title function
                                   (ie, 'geoips_fname', 'tc_fname', 'metoctiff_fname', etc)

    Returns:
        (str) : Type of requested title function
    '''
    curr_func = find_entry_point('title_formats', func_name)
    return getattr(import_module(curr_func.__module__), 'title_type')


def list_titles_by_type():
    ''' Interface Under Development, please provide feedback to geoips@nrlmry.navy.mil

    List all available title format functions within the current GeoIPS instantiation, sorted by title_type

    title function "type" determines exact required call signatures and return values

    See geoips.dev.title.is_valid_title? for a list of available title format types and
            associated call signatures / return values.
    See geoips.dev.title.get_title(title_func_name) to retrieve the requested title format function

    Returns:
        (dict) : Dictionary with all title format types as keys,
                 and associated title format function names (str) as values.
    '''
    all_funcs = collections.defaultdict(list)
    for currfunc in list_entry_points('title_formats'):
        func_type = get_title_type(currfunc)
        if currfunc not in all_funcs[func_type]:
            all_funcs[func_type].append(currfunc)
    return all_funcs


def test_title_interface():
    ''' Finds and opens every title func available within the current geoips instantiation

    See geoips.dev.title.is_valid_title? for a list of available title func types and associated
            call signatures / return values.
    See geoips.dev.title.get_title(title_func_name) to retrieve the requested title func

    Returns:
        (list) : List of all successfully opened geoips title funcs
    '''
    curr_names = list_titles_by_type()
    out_dict = {'by_type': curr_names, 'validity_check': {}, 'func_type': {}, 'func': {}}
    for curr_type in curr_names:
        for curr_name in curr_names[curr_type]:
            out_dict['validity_check'][curr_name] = is_valid_title(curr_name)
            out_dict['func'][curr_name] = get_title(curr_name)
            out_dict['func_type'][curr_name] = get_title_type(curr_name)
    return out_dict
