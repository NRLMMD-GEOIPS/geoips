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

from geoips.geoips_utils import find_entry_point, list_entry_points
import collections
from importlib import import_module
import logging
LOG = logging.getLogger(__name__)


### Filename Functions ###
def is_valid_filenamer(filename_func_name):
    ''' Interface Under Development, please provide feedback to geoips@nrlmry.navy.mil

    Check that the requested filename function has the correct call signature.
        Return values should be as specified below, but return values are not verified with this format check.

        Filename functions currently defined in:
            <geoips_package>.filenames.<filename_func_name>.<filename_func_name>
        and currently requested via commandline with:
            --filename_module_names <filename_func1_name> <filename_func2_name>

        Output type currently found in:
            <geoips_package>.filenames.<filename_func_name>.filename_type

        Output type one of:

               'standard' : call signature: <filename_func_name>(area_def,
                                                                 xarray_obj,
                                                                 product_name,
                                                                 coverage=None,
                                                                 output_type=None,
                                                                 output_type_dir=None,
                                                                 product_dir=None,
                                                                 product_subdir=None,
                                                                 source_dir=None,
                                                                 basedir=None)
                                 return value:   str full path to filename
               'data' : call signature: <filename_func_name>(area_def,
                                                             xarray_obj,
                                                             product_names,  # List of all product names contained in data file
                                                             coverage=None,
                                                             output_type=None,
                                                             output_type_dir=None,
                                                             product_dir=None,
                                                             product_subdir=None,
                                                             source_dir=None,
                                                             basedir=None)
                                 return value:   str full path to filename

    Args:
        filename_func_name (str) : Name of requested filename function
                                   (ie, 'geoips_fname', 'tc_fname', 'metoctiff_fname', etc)

    Returns:
        (bool) : True if 'filename_func_name' function has the appropriate call signature
                 False if filename function:
                        does not contain all required arguments
                        does not contain all required keyword arguments
    '''
    required_args = {'standard': ['area_def', 'xarray_obj', 'product_name'],
                     'xarray_metadata_to_filename': ['xarray_obj'],
                     'data': ['area_def', 'xarray_obj', 'product_names'],
                     'standard_metadata': ['area_def', 'xarray_obj', 'product_filename'],
                     }

    required_kwargs = {'standard': ['coverage',
                                    'output_type',
                                    'output_type_dir',
                                    'product_dir',
                                    'product_subdir',
                                    'source_dir',
                                    'basedir'],
                       'xarray_metadata_to_filename': ['extension',
                                                       'basedir'],
                       'data': ['coverage',
                                'output_type',
                                'output_type_dir',
                                'product_dir',
                                'product_subdir',
                                'source_dir',
                                'basedir'],
                       'standard_metadata': ['metadata_dir', 'metadata_type', 'basedir'],
                       }

    try:
        filename_type = get_filenamer_type(filename_func_name)
    except ImportError as resp:
        LOG.warning('Module %s in filename package not a valid filename module: '
                    'If this is intended to be a valid filename module, ensure "filename_type" is defined: '
                    'Exception: "%s"', filename_func_name, resp)
        return False
    try:
        filename_func = get_filenamer(filename_func_name)
    except ImportError as resp:
        raise ImportError(
            f'INVALID FILENAME {filename_func_name}: Must specify function "{filename_func_name}" within module "{filename_func_name}": Exception: "{resp}"')

    if filename_type not in required_args:
        raise TypeError(
            f"INVALID FILENAME FUNC {filename_func_name}: Unknown filename func type {filename_type}, allowed types: {required_args.keys()}")

    if filename_type not in required_kwargs:
        raise TypeError(
            f"INVALID FILENAME FUNC {filename_func_name}: Unknown filename func type {filename_type}, allowed types: {required_kwargs.keys()}")

    num_args = len(required_args[filename_type])
    num_kwargs = len(required_kwargs[filename_type])

    # If this is __init__ (no __code__ attr), skip it
    if not hasattr(filename_func, '__code__'):
        return False
    filename_vars = filename_func.__code__.co_varnames
    filename_args = filename_vars[0:num_args]
    filename_kwargs = filename_vars[num_args:num_args + num_kwargs]

    # Check for required call signature arguments
    if not set(required_args[filename_type]).issubset(set(filename_args)):
        LOG.error("INVALID FILENAME FUNCTION '%s': '%s' filename type must have required arguments: '%s'",
                  filename_func_name, filename_type, required_args[filename_type])
        return False

    # Check for call signature keyword arguments
    if not set(required_kwargs[filename_type]).issubset(set(filename_kwargs)):
        LOG.error("INVALID FILENAME FUNCTION '%s': '%s' filename type must have optional kwargs: '%s'",
                  filename_func_name, filename_type, required_kwargs[filename_type])
        return False

    return True


def get_remove_duplicates_func(filename_func_name):
    ''' Interface Under Development, please provide feedback to geoips@nrlmry.navy.mil

    Retrieve the requested function to remove duplicate output files

    See: geoips.dev.filename.is_valid_filenamer for full list of supported filename function call signatures and return values

    Args:
        filename_func_name (str) : Name of requested filename function
                                   (ie, 'geoips_fname', 'tc_fname', 'metoctiff_fname', etc)

    Returns:
        (<filename function>) : Function for generating filenames of the specified format.
    '''
    curr_func = find_entry_point('filename_formats', filename_func_name)
    return getattr(import_module(curr_func.__module__), filename_func_name + '_remove_duplicates')


def get_filenamer(filename_func_name):
    ''' Interface Under Development, please provide feedback to geoips@nrlmry.navy.mil

    Retrieve the requested output filename function

    See: geoips.dev.filename.is_valid_filenamer for full list of supported filename function call signatures and return values

    Args:
        filename_func_name (str) : Name of requested filename function
                                   (ie, 'geoips_fname', 'tc_fname', 'metoctiff_fname', etc)

    Returns:
        (<filename function>) : Function for generating filenames of the specified format.
    '''
    return find_entry_point('filename_formats', filename_func_name)


def get_filenamer_type(func_name):
    ''' Interface Under Development, please provide feedback to geoips@nrlmry.navy.mil

    Retrieve type of the requested output filename function.
    Type specifies the required call signature and return values

    See: geoips.dev.filename.is_valid_filenamer for full list of supported filename function call signatures and return values

    Args:
        filename_func_name (str) : Name of requested filename function
                                   (ie, 'geoips_fname', 'tc_fname', 'metoctiff_fname', etc)

    Returns:
        (str) : Type of requested filename function
    '''
    curr_func = find_entry_point('filename_formats', func_name)
    return getattr(import_module(curr_func.__module__), 'filename_type')


def list_filenamers_by_type():
    ''' Interface Under Development, please provide feedback to geoips@nrlmry.navy.mil

    List all available filename format functions within the current GeoIPS instantiation, sorted by filename_type

    Filename function "type" determines exact required call signatures and return values

    See geoips.dev.filename.is_valid_filenamer? for a list of available filename format types and associated call signatures / return values.
    See geoips.dev.filename.get_filenamer(filename_func_name) to retrieve the requested filename format function

    Returns:
        (dict) : Dictionary with all filename format types as keys, and associated filename format function names (str) as values.
    '''
    all_funcs = collections.defaultdict(list)
    for currfunc in list_entry_points('filename_formats'):
        func_type = get_filenamer_type(currfunc)
        if currfunc not in all_funcs[func_type]:
            all_funcs[func_type].append(currfunc)
    return all_funcs


def test_filename_interface():
    ''' Finds and opens every filename func available within the current geoips instantiation

    See geoips.dev.filename.is_valid_filenamer? for a list of available filename func types and associated call signatures / return values.
    See geoips.dev.filename.get_filenamer(filename_func_name) to retrieve the requested filename func

    Returns:
        (list) : List of all successfully opened geoips filename funcs
    '''
    curr_names = list_filenamers_by_type()
    out_dict = {
        'by_type': curr_names,
        'validity_check': {},
        'func_type': {},
        'func': {},
        'cmaps': {},
        'cmap_args': {},
        'cmap_func_names': {}}
    for curr_type in curr_names:
        for curr_name in curr_names[curr_type]:
            out_dict['validity_check'][curr_name] = is_valid_filenamer(curr_name)
            out_dict['func'][curr_name] = get_filenamer(curr_name)
            out_dict['func_type'][curr_name] = get_filenamer_type(curr_name)
    return out_dict
