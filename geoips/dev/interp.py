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

"""Interpolation interface will be deprecated v2.0.

Wrapper functions for geoips interpolation functionality.

This functionality will be replaced with a class-based implementation v2.0,
and deprecated at that time.
"""
import collections
from importlib import import_module
import logging

LOG = logging.getLogger(__name__)

from geoips.geoips_utils import find_entry_point, list_entry_points


###########################
# Interpolation Functions #
def is_valid_interp(interp_func_name):
    """Interface will be deprecated v2.0.

    Check that the requested interpolation function has the correct call
    signature.

    Return values should be as specified below, but are not programmatically
    verified.

    Parameters
    ----------
    interp_func_name : str
        Desired interp function (ie, 'interp_nearest', 'interp_gauss', etc)

    Returns
    -------
    is_valid : bool

        * True if 'interp_func_name' has the appropriate call signature
        * False if interp function:

            * does not contain all required arguments
            * does not contain all required keyword arguments

    Notes
    -----
    Interpolation function type currently found in
    ``<geoips_package>.interpolation.*.<interp_func_name>.interp_type``

    Interpolation functions currently defined in
    ``<geoips_package>.interpolation.*.<interp_func_name>.<interp_func_name>``
    and requested within the product parameters dictionary
    See geoips.dev.product.check_product_params

    interp_func types currently one of::

        '2d' :
          call signature
            <interp_func_name>(area_def, xarray_obj, varlist, array_num=None, **kwargs)
          return value:
            mpl_colors_info dict
        'grid' :
          call signature
            <interp_func_name>(area_def, xarray_obj, varlist, array_num=None, **kwargs)
          return value:
            mpl_colors_info dict

    Return list of arrays (same length and order as "varlist" argument)

    See Also
    --------
    For package based interpolation functions:

    * See geoips.dev.interp.get_interp
    * See geoips.dev.interp.get_interp_type
    * See geoips.dev.interp.list_interps_by_type

    For product based interpolation functions:

    * See geoips.dev.interp.get_interp
    * See geoips.dev.interp.get_interp_name
    * See geoips.dev.interp.get_interp_args
    """
    required_args = {
        "2d": ["area_def", "input_xarray", "output_xarray", "varlist"],
        "grid": ["area_def", "input_xarray", "output_xarray", "varlist"],
    }
    required_kwargs = {"2d": ["array_num"], "grid": ["array_num"]}

    try:
        interp_func_type = get_interp_type(interp_func_name)
    except ImportError as resp:
        LOG.warning(
            f'INVALID INTERP {interp_func_name} not a valid interp module: If this is intended to be valid, ensure "interp_type" is defined: Exception: "{resp}"'
        )
        return False
    try:
        interp_func = get_interp(interp_func_name)
    except ImportError as resp:
        raise ImportError(
            f'INVALID INTERP {interp_func_name}: Must specify function "{interp_func_name}" within module "{interp_func_name}": Exception: "{resp}"'
        )

    # If this is __init__ (no __code__ attr), skip it
    if not hasattr(interp_func, "__code__"):
        return False

    num_args = len(required_args[interp_func_type])
    num_kwargs = len(required_kwargs[interp_func_type])

    interp_func_vars = interp_func.__code__.co_varnames
    interp_func_args = interp_func_vars[0:num_args]
    interp_func_kwargs = interp_func_vars[num_args : num_args + num_kwargs]

    # Check for required call signature arguments
    if not set(required_args[interp_func_type]).issubset(set(interp_func_args)):
        LOG.error(
            "INVALID INTERP FUNC '%s': '%s' interp func type must have required arguments: '%s'",
            interp_func_name,
            interp_func_type,
            required_args[interp_func_type],
        )
        return False

    # Check for optional call signature keyword arguments
    if not set(required_kwargs[interp_func_type]).issubset(set(interp_func_kwargs)):
        LOG.error(
            "INVALID INTERP FUNC '%s': '%s' interp_func type must have kwargs: '%s'",
            interp_func_name,
            interp_func_type,
            required_kwargs[interp_func_type],
        )
        return False

    return True


def get_interp(interp_func_name):
    """Interface will be deprecated v2.0.

    Retrieve the requested interpolation function

    See: geoips.dev.interp.is_valid_interp for full list of supported
    interp function call signatures and return values

    Parameters
    ----------
    interp_func_name : str
        Desired interp function (ie, 'interp_nearest', 'interp_gauss', etc)

    Returns
    -------
    <interp function>
        Interpolation function
    """
    return find_entry_point("interpolation", interp_func_name)


def get_interp_type(interp_func_name):
    """Interface will be deprecated v2.0.

    Retrieve type of the requested interpolation function.
    Type specifies the required call signature and return values

    Parameters
    ----------
    interp_func_name : str
        Desired interp function (ie, 'interp_nearest', 'interp_gauss', etc)

    Returns
    -------
    str
        Interpolation function type
    """
    func = find_entry_point("interpolation", interp_func_name)
    return getattr(import_module(func.__module__), "interp_type")


def list_interps_by_type():
    """Interface will be deprecated v2.0.

    List all available interpolation functions within the current
    GeoIPS instantiation, sorted by interp_type

    Interpolation function "type" determines exact required call signatures
    and return values

    See geoips.dev.interp.is_valid_interp?
        for a list of available interpolation function types
        and associated call signatures / return values.
    See geoips.dev.interp.get_interp(interp_func_name)
        to retrieve the requested interpolation function
    See geoips.dev.interp.get_interp_type(interp_func_name)
        to retrieve the requested interpolation function type

    Returns
    -------
    dict
        Dictionary with all interpolation function types as keys,
        and associated interpolation function names (str) as values.
    """
    all_funcs = collections.defaultdict(list)
    for currfunc in list_entry_points("interpolation"):
        func_type = get_interp_type(currfunc)
        if currfunc not in all_funcs[func_type]:
            all_funcs[func_type].append(currfunc)
    return all_funcs


def test_interp_interface():
    """Interface will be deprecated v2.0.

    Finds and opens every interp func available within the current
    geoips instantiation

    See geoips.dev.interp.is_valid_interp?
        for a list of available interp
        func types and associated call signatures / return values.
    See geoips.dev.interp.get_interp(interp_func_name)
        to retrieve the requested interp func

    Returns
    -------
    list
        List of all successfully opened geoips interp funcs
    """
    curr_names = list_interps_by_type()
    out_dict = {
        "by_type": curr_names,
        "validity_check": {},
        "func_type": {},
        "func": {},
    }
    for curr_type in curr_names:
        for curr_name in curr_names[curr_type]:
            out_dict["validity_check"][curr_name] = is_valid_interp(curr_name)
            out_dict["func"][curr_name] = get_interp(curr_name)
            out_dict["func_type"][curr_name] = get_interp_type(curr_name)

    # from geoips.dev.product import list_products_by_source
    # product_params_dicts = list_products_by_source()
    # for source_name in product_params_dicts:
    #     for product_name in product_params_dicts[source_name]:
    #         if product_name not in return_dict['interp_func_names']:
    #             return_dict['interp_func_names'][product_name] = {}
    #             return_dict['interp_args'][product_name] = {}
    #         if source_name not in return_dict['interp_func_names'][product_name]:
    #             return_dict['interp_func_names'][product_name][source_name] = {}
    #             return_dict['interp_args'][product_name][source_name] = {}
    #         func_name = get_interp_name(product_name, source_name)
    #         return_dict['interp_func_names'][product_name][source_name][func_name] = func_name
    #         # This needs some more thought. The 2d interp routines always take area_def and xobj,
    #         # But that is not going to be generally true for all interpolation routines.
    #         # return_dict['interp'][func_name] = get_interp(product_name, source_name)
    #         return_dict['interp_args'][product_name][source_name][func_name] = get_interp_args(product_name, source_name)
    return out_dict
