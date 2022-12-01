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

    Wrapper functions for geoips procflow interface.

    Once all related wrapper functions are finalized,
    this module will be moved to the geoips/stable sub-package.
'''

from geoips.geoips_utils import find_entry_point, list_entry_points
import logging
import collections
from importlib import import_module
LOG = logging.getLogger(__name__)


### Driver functions ###
def is_valid_procflow(procflow_func_name):
    ''' Interface Under Development, please provide feedback to geoips@nrlmry.navy.mil

    Check that the requested procflow function has the correct call signature.
        Return values should be 0 for successful completion, non-zero otherwise - return values are not verified within this format check.

        Driver functions currently defined in
            <geoips_package>.procflows.<procflow_func_name>.<procflow_func_name>
        and requested via commandline with:
            --procflow <procflow_func_name>

    Args:
        procflow_func_name (str) : Desired procflow function (ie, 'single_source', 'pmw_tbs', 'stitched_procflow', etc)

    Returns:
        (bool) : True if 'procflow_func_name' has the appropriate call signature
                 False if procflow function:
                        does not contain all required arguments
                        does not contain all required keyword arguments

                 Driver types currently one of:

                        'standard' : call signature <procflow_func_name>(fnames, command_line_args=None)
                                     return value: 0 for successful completion, non-zero for failure.
                                                   This can be used for determining successful output comparisons for unit tests / CI/CD.

    '''
    required_args = {'standard': ['fnames']}
    required_kwargs = {'standard': ['command_line_args']}

    type_name = 'procflow_type'

    try:
        procflow_type = get_procflow_type(procflow_func_name)
    except ImportError as resp:
        if 'procflow_type' in str(resp):
            LOG.warning(f'Module {procflow_func_name} in procflow package not a valid procflow module: '
                        f'If this is intended to be a valid procflow module, ensure "{type_name}" is defined:'
                        f'Exception: "{resp}"')
        else:
            LOG.exception(f'ImportError in module {procflow_func_name} in procflow package. Exception: "{resp}"')
            raise
        return False
    try:
        procflow_func = get_procflow(procflow_func_name)
    except ImportError as resp:
        raise ImportError(
            f'INVALID OUTPUT {procflow_func_name}: Must specify function "{procflow_func_name}" within module "{procflow_func_name}": Exception: "{resp}"')

    if procflow_type not in required_args:
        raise TypeError(f"INVALID PROCFLOW FUNC {procflow_func_name}:\n"
                        f"Unknown output type {procflow_type}, allowed types: {required_args.keys()}\n"
                        f"Either add '{procflow_type}' to list of supported types\n"
                        f"in procflow.is_valid_procflow.required_args\n"
                        f"or update '{procflow_func.__module__}' to a supported type")
    if procflow_type not in required_kwargs:
        raise TypeError(f"INVALID PROCFLOW FUNC {procflow_func_name}:\n"
                        f"Unknown output type {procflow_type}, allowed types: {required_kwargs.keys()}\n"
                        f"Either add '{procflow_type}' to list of supported types\n"
                        f"in procflow.is_valid_procflow.required_kwargs\n"
                        f"or update '{procflow_func.__module__}' to a supported type")

    num_args = len(required_args[procflow_type])
    num_kwargs = len(required_kwargs[procflow_type])

    # If this is __init__ (no __code__ attr), skip it
    if not hasattr(procflow_func, '__code__'):
        return False
    procflow_vars = procflow_func.__code__.co_varnames
    procflow_args = procflow_vars[0:num_args]
    procflow_kwargs = procflow_vars[num_args:num_args + num_kwargs]

    # Check for required call signature arguments
    if not set(required_args[procflow_type]).issubset(set(procflow_args)):
        LOG.error("INVALID READER '%s': '%s' procflow type must have required arguments: '%s'",
                  procflow_func_name, procflow_type, required_args[procflow_type])
        return False

    # Check for call signature keyword arguments
    if not set(required_kwargs[procflow_type]).issubset(set(procflow_kwargs)):
        LOG.error("INVALID READER '%s': '%s' procflow type must have optional kwargs: '%s'",
                  procflow_func_name, procflow_type, required_kwargs[procflow_type])
        return False

    return True


def get_procflow(procflow_func_name):
    ''' Interface Under Development, please provide feedback to geoips@nrlmry.navy.mil

    Retrieve the requested procflow function

    See: geoips.dev.procflow.is_valid_procflow for full list of supported procflow function call signatures and return values

    Args:
        procflow_func_name (str) : Desired procflow function (ie, 'single_source', 'pmw_tbs', 'stitched_procflow', etc)

    Returns:
        (<procflow function>) : Driver function, currently specified in <geoips_package>.procflows.<procflow_func_name>.<procflow_func_name>
    '''
    return find_entry_point('procflows', procflow_func_name)


def get_procflow_type(procflow_func_name):
    ''' Interface Under Development, please provide feedback to geoips@nrlmry.navy.mil

    Retrieve type of the requested procflow
    Type specifies the required call signature and return values

    Args:
        procflow_func_name (str) : Desired procflow module (ie, 'single_source', 'stitched_procflow', etc)

    Returns:
        (str) : Driver type currently found in <geoips_package>.procflows.<procflow_func_name>.procflow_type
                        Type defaults to 'standard' if not specified. Driver types currently one of:
                        'standard' : call signature <procflow_func_name>(fnames, command_line_args=None)
    '''
    procflow_func = find_entry_point('procflows', procflow_func_name)
    return getattr(import_module(procflow_func.__module__), 'procflow_type')


def list_procflows_by_type():
    ''' Interface Under Development, please provide feedback to geoips@nrlmry.navy.mil

    List all available procflows within the current GeoIPS instantiation, sorted by procflow_type

    Driver "type" determines exact required call signatures and return values

    See geoips.dev.procflow.is_valid_procflow? for a list of available procflow types and associated call signatures / return values.
    Use geoips.dev.procflow.get_procflow(procflow_func_name) to retrieve the requested procflow

    Returns:
        (dict) : Dictionary with all procflow types as keys, and associated procflow names (str) as values.
    '''
    all_funcs = collections.defaultdict(list)
    for currfunc in list_entry_points('procflows'):
        func_type = get_procflow_type(currfunc)
        if currfunc not in all_funcs[func_type]:
            all_funcs[func_type].append(currfunc)
    return all_funcs


def test_procflow_interface():
    ''' Finds and opens every procflow func available within the current geoips instantiation

    See geoips.dev.procflow.is_valid_procflow? for a list of available procflow func types and associated call signatures / return values.
    See geoips.dev.procflow.get_procflow(procflow_func_name) to retrieve the requested procflow func

    Returns:
        (list) : List of all successfully opened geoips procflow funcs
    '''
    curr_names = list_procflows_by_type()
    out_dict = {'by_type': curr_names, 'validity_check': {}, 'func_type': {}, 'func': {}}
    for curr_type in curr_names:
        for curr_name in curr_names[curr_type]:
            out_dict['validity_check'][curr_name] = is_valid_procflow(curr_name)
            out_dict['func'][curr_name] = get_procflow(curr_name)
            out_dict['func_type'][curr_name] = get_procflow_type(curr_name)
    return out_dict
