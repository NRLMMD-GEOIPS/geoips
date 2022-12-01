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

    Wrapper functions for geoips generalized output format interfaces.

    Once all related wrapper functions are finalized,
    this module will be moved to the geoips/stable sub-package.
'''
from geoips.geoips_utils import find_entry_point, list_entry_points
import collections
from importlib import import_module
import logging
LOG = logging.getLogger(__name__)


### Output Format Functions ###
def is_valid_outputter(output_func_name):
    ''' Interface Under Development, please provide feedback to geoips@nrlmry.navy.mil

    Check that the requested output function has the correct call signature.
        Return values should be as specified below, but return values are not verified with this format check.

        Output functions currently defined in:
            <geoips_package>.output_formats.<output_func_name>.<output_func_name>
        and currently requested via commandline with:
            --output_module_name <output_func_name>

        Output type currently found in:
            <geoips_package>.output_formats.<output_func_name>.output_type

        Output type one of:
               'image'
               'unprojected'
               'image_overlay'
               'image_multi'
               'xarray_dict_to_image'
               'xarray_dict_data'
               'standard_metadata'
               'xarray_data'

    Args:
        output_func_name (str) : Name of requested output product function
                                (ie, 'imagery_annotated', 'unprojected_image', etc)

    Returns:
        (bool) : True if 'output_func_name' function has the appropriate call signature
                 False if output function:
                        does not contain all required arguments
                        does not contain all required keyword arguments
    '''
    required_args = {'image': ['area_def', 'xarray_obj', 'product_name', 'output_fnames'],
                     'unprojected': ['xarray_obj', 'product_name', 'output_fnames'],
                     'image_overlay': ['area_def', 'xarray_obj', 'product_name', 'output_fnames'],
                     'image_multi': ['area_def', 'xarray_obj', 'product_names', 'output_fnames', 'mpl_colors_info'],
                     'xarray_dict_to_image': ['xarray_datasets', 'area_def', 'varlist'],
                     'xarray_dict_data': ['xarray_objs', 'product_names', 'output_fnames'],
                     'xarray_data': ['xarray_obj', 'product_names', 'output_fnames'],
                     'standard_metadata': ['area_def', 'xarray_obj', 'metadata_yaml_filename', 'product_filename'],
                     }

    required_kwargs = {'image': ['product_name_title', 'mpl_colors_info', 'existing_image'],
                       'unprojected': ['product_name_title', 'mpl_colors_info'],
                       'image_overlay': ['product_name_title', 'clean_fname',
                                         'mpl_colors_info', 'clean_fname',
                                         'boundaries_info', 'gridlines_info', 'clean_fname',
                                         'product_datatype_title', 'clean_fname',
                                         'bg_data', 'bg_mpl_colors_info', 'clean_fname',
                                         'bg_xarray', 'bg_product_name_title', 'bg_datatype_title', 'clean_fname',
                                         'remove_duplicate_minrange'],
                       'image_multi': ['product_name_titles'],
                       'xarray_dict_data': ['append', 'overwrite'],
                       'xarray_dict_to_image': [],
                       'xarray_data': [],
                       'standard_metadata': ['metadata_dir', 'basedir', 'output_dict'],
                       }

    try:
        output_type = get_outputter_type(output_func_name)
    except ImportError as resp:
        LOG.warning(f'Module {output_func_name} in output package not a valid output module: If this is intended to be a valid output module, ensure "output_type" is defined: Exception: "{resp}"')
        return False
    try:
        output_func = get_outputter(output_func_name)
    except ImportError as resp:
        raise ImportError(
            f'INVALID OUTPUT {output_func_name}: Must specify function "{output_func_name}" within module "{output_func_name}": Exception: "{resp}"')

    if output_type not in required_args:
        raise TypeError(f"INVALID OUTPUT FUNC {output_func_name}:\n"
                        f"      Unknown output type '{output_type}', allowed types: {required_args.keys()}\n"
                        f"      Either add '{output_type}' to list of supported types in\n"
                        f"      output.is_valid_output.required_args\n"
                        f"      or update '{output_func.__module__}' to a supported type")
    if output_type not in required_kwargs:
        raise TypeError(f"INVALID OUTPUT FUNC {output_func_name}:\n"
                        f"      Unknown output type '{output_type}', allowed types: {required_kwargs.keys()}\n"
                        f"      Either add '{output_type}' to list of supported types in\n"
                        f"      output.is_valid_output.required_kwargs\n"
                        f"      or update '{output_func.__module__}' to a supported type")

    num_args = len(required_args[output_type])
    num_kwargs = len(required_kwargs[output_type])

    # If this is __init__ (no __code__ attr), skip it
    if not hasattr(output_func, '__code__'):
        return False
    output_vars = output_func.__code__.co_varnames
    output_args = output_vars[0:num_args]
    output_kwargs = output_vars[num_args:num_args + num_kwargs]

    # Check for required call signature arguments
    if not set(required_args[output_type]).issubset(set(output_args)):
        LOG.error("INVALID OUTPUT FUNCTION '%s': '%s' output type must have required arguments: '%s'",
                  output_func_name, output_type, required_args[output_type])
        return False

    # Check for call signature keyword arguments
    if not set(required_kwargs[output_type]).issubset(set(output_kwargs)):
        LOG.error("INVALID OUTPUT FUNCTION '%s': '%s' output type must have optional kwargs: '%s'",
                  output_func_name, output_type, required_kwargs[output_type])
        return False

    return True


def get_outputter(output_func_name):
    ''' Interface Under Development, please provide feedback to geoips@nrlmry.navy.mil

    Retrieve the requested output product function

    See: geoips.dev.output.is_valid_outputter for full list of supported output function call signatures and return values

    Args:
        output_func_name (str) : Name of requested output product function
                                (ie, 'create_standard_imagery', 'create_standard_metoctiff', 'create_standard_windbarbs', etc)

    Returns:
        (<output function>) : Function for generating output products of the specified format.
    '''
    return find_entry_point('output_formats', output_func_name)


def get_outputter_type(output_func_name):
    ''' Interface Under Development, please provide feedback to geoips@nrlmry.navy.mil

    Retrieve type of the requested output product function.
    Type specifies the required call signature and return values

    See: geoips.dev.output.is_valid_outputter for full list of supported output function call signatures and return values

    Args:
        output_func_name (str) : Name of requested output product function
                                (ie, 'create_standard_imagery', 'create_standard_metoctiff', 'create_standard_windbarbs', etc)

    Returns:
        (str) : Type of requested output function
    '''
    curr_func = find_entry_point('output_formats', output_func_name)
    return getattr(import_module(curr_func.__module__), 'output_type')


def list_outputters_by_type():
    ''' Interface Under Development, please provide feedback to geoips@nrlmry.navy.mil

    List all available output format functions within the current GeoIPS instantiation, sorted by output_type

    Output "type" determines exact required call signatures and return values

    See geoips.dev.output.is_valid_outputter? for a list of available output format types and associated call signatures / return values.
    See geoips.dev.output.get_outputter(output_name) to retrieve the requested output format function

    Returns:
        (dict) : Dictionary with all output types as keys, and associated output format function names (str) as values.
    '''
    all_funcs = collections.defaultdict(list)
    for currfunc in list_entry_points('output_formats'):
        func_type = get_outputter_type(currfunc)
        if currfunc not in all_funcs[func_type]:
            all_funcs[func_type].append(currfunc)
    return all_funcs


def test_output_interface():
    ''' Finds and opens every output func available within the current geoips instantiation

    See geoips.dev.output.is_valid_outputter? for a list of available output func types and associated call signatures / return values.
    See geoips.dev.output.get_outputter(output_func_name) to retrieve the requested output func

    Returns:
        (list) : List of all successfully opened geoips output funcs
    '''

    curr_names = list_outputters_by_type()
    out_dict = {'by_type': curr_names, 'validity_check': {}, 'func_type': {}, 'func': {}}
    for curr_type in curr_names:
        for curr_name in curr_names[curr_type]:
            out_dict['validity_check'][curr_name] = is_valid_outputter(curr_name)
            out_dict['func'][curr_name] = get_outputter(curr_name)
            out_dict['func_type'][curr_name] = get_outputter_type(curr_name)
    return out_dict
