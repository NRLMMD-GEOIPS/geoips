# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Interpolation interface will be deprecated v2.0.

Wrapper functions for geoips product specifications.

This functionality will be replaced with a class-based implementation v2.0,
and deprecated at that time.
"""

import logging
from geoips.interfaces import colormappers, coverage_checkers

LOG = logging.getLogger(__name__)


def get_required_variables(prod_plugin):
    """Interface will be deprecated v2.0.

    Return required variables names for the input product plugin. If variables are
    combined with their dataset name, the dataset name will be stripped and only the
    variable names will be returned.

    Parameters
    ----------
    prod_plugin : ProductPlugin
        An instance of the GeoIPS ProductPlugin class.

    Returns
    -------
    required_variables : list or dict
        * If list: List of strings specifying required variables.
        * If dict: Dictionary of variable types of lists of variable names

            * {'<variable_type>': ['var1', 'var2', ... , 'varn']}
    """
    # This can either be a list or dictionary, dependent on YAML config specification
    variables = prod_plugin["spec"].get("variables")
    if variables is None:
        return []

    # Support categorizing variables in a dictionary
    if isinstance(variables, dict):
        return_vars = {}
        for vartype in variables:
            return_vars[vartype] = []
            for varname in variables[vartype]:
                if ":" in varname:
                    return_vars[vartype] += [varname.split(":")[1]]
                else:
                    return_vars[vartype] += [varname]
    # Otherwise, just a single variable
    else:
        return_vars = []
        for varname in variables:
            if ":" in varname:
                return_vars += [varname.split(":")[1]]
            else:
                return_vars += [varname]
    return return_vars


def get_requested_datasets_for_variables(prod_plugin):
    """Interface will be deprecated v2.0.

    Retrieve required datasets if specified for product variables,
    based on requested product and source

    Within product_inputs YAML specifications, variables can be
    requested with ``<DATASET>:<VARNAME>`` if
    you need a particular variable from a specific dataset.

    If ``<DATASET>:`` is not specified, the first
    variable found when looping through the datasets is used.

    Parameters
    ----------
    product_name : str
        Name of requested product (ie, 'IR-BD', '89H', 'color89Nearest', etc)
    source_name : str
        Name of requested source (ie, 'ahi', 'modis', etc)

    Returns
    -------
    datasets_for_variable : dict
        * Dictionary of

            * ``{'<variable_name>': '<requested_dataset>'}`` OR
            * ``{'variable_type': {'<variable_name>': '<requested_dataset>'}``
    """
    variables = prod_plugin["spec"]["variables"]
    return_dict = {}
    # Support categorizing variables in a dictionary - var_dict[var_type] =
    # ['var1', 'var2', 'varn']
    if isinstance(variables, dict):
        return_dict = {}
        for vartype in variables:
            return_dict[vartype] = {}
            for varname in variables[vartype]:
                dataset, variable = varname.split(":")
                if varname not in return_dict:
                    return_dict[vartype][variable] = [dataset]
                else:
                    return_dict[vartype][variable] += [dataset]
    # Otherwise just a list
    else:
        for varname in variables:
            if ":" in varname:
                dataset, variable = varname.split(":")
                if varname not in return_dict:
                    return_dict[variable] = [dataset]
                else:
                    return_dict[variable] += [dataset]
    return return_dict


def get_data_range(prod_plugin, output_dict=None):
    """Interface will be deprecated v2.0.

    Retrieve required data range for requested product

    Parameters
    ----------
    product_name : str
        Name of requested product (ie, 'IR-BD', '89H', 'color89Nearest', etc)

    Returns
    -------
    data_range : list
        List of float specifying min and max value for the output product
        ``<geoips_package>.algorithms.<algorithm_name>.alg_params['output_data_range']``
    """
    alg_args = prod_plugin["spec"]["algorithm"]["plugin"]["arguments"]
    if "output_data_range" not in alg_args:
        raise TypeError(
            f"Product {prod_plugin.name} does not define 'output_data_range' for its "
            f"algorithm."
        )
    # Add .copy() so we aren't returning the ACTUAL list attached to the args
    return alg_args["output_data_range"].copy()


def get_cmap_data_range(prod_plugin, output_dict=None):
    """Interface will be deprecated v2.0.

    Retrieve required data range for requested product

    Parameters
    ----------
    product_name : str
        Name of requested product (ie, 'IR-BD', '89H', 'color89Nearest', etc)

    Returns
    -------
    data_range : list
        List of float specifying min and max value for the output product
        ``<geoips_package>.colormapper.<cmap_name>.arguments['data_range']``
    """
    cmap_args = prod_plugin["spec"]["colormapper"]["plugin"]["arguments"]
    if "data_range" not in cmap_args:
        raise TypeError(
            f"Product {prod_plugin.name} does not define 'output_data_range' for its "
            f"algorithm."
        )
    # Add .copy() so we aren't returning the ACTUAL list attached to the args
    return cmap_args["data_range"].copy()


def get_product_display_name(prod_plugin, output_dict=None):
    """Interface will be deprecated v2.0.

    Retrieve product display name. For titles, etc.

    Parameters
    ----------
    product_name : str
        Name of requested product (ie, 'IR-BD', '89H', 'color89Nearest', etc)
    source_name : str
        Name of requested source (ie, 'ahi', 'modis', etc)

    Returns
    -------
    product_display_name : str
        Return display name for given product

    See Also
    --------
    ``geoips.dev.check_cmap_func``
        additional information on colormapper types, arguments, and return values
    """
    try:
        return prod_plugin["spec"]["display_name"]
    except KeyError:
        return prod_plugin.name


def get_cmap_from_product(prod_plugin, output_dict=None):
    r"""Interface will be deprecated v2.0.

    Retrieve colormapper information, based on requested product and source

    Parameters
    ----------
    product_name : str
        Name of requested product (ie, 'IR-BD', '89H', 'color89Nearest', etc)
    source_name : str
        Name of requested source (ie, 'ahi', 'modis', etc)

    Returns
    -------
    cmap_func(\*\*cmap_args) : function
        Return actual colormapper information

    See Also
    --------
    ``geoips.dev.check_cmap_func``
        additional information on colormapper types, arguments, and return values
    """
    cmap_func = colormappers.get_plugin(
        prod_plugin["spec"]["colormapper"]["plugin"]["name"]
    )
    cmap_args = prod_plugin["spec"]["colormapper"]["plugin"]["arguments"]

    return cmap_func(**cmap_args)


def get_covg_from_product(prod_plugin, output_dict=None, covg_field=None):
    """Interface will be deprecated v2.0.

    Retrieve coverage check function name, based on requested product and source

    Parameters
    ----------
    product_name : str
        Name of requested product (ie, 'IR-BD', '89H', 'color89Nearest', etc)
    source_name : str
        Name of requested source (ie, 'ahi', 'modis', etc)

    Returns
    -------
    covg_func_name : str
        Return name of coverage function required for given product/source

    See Also
    --------
    ``geoips.dev.check_cmap_func``
        additional information on colormapper types, arguments, and return values
    """
    prod_spec = prod_plugin["spec"]
    if covg_field in prod_spec:
        return coverage_checkers.get_plugin(prod_spec[covg_field]["plugin"]["name"])
    elif "coverage_checker" in prod_spec:
        return coverage_checkers.get_plugin(
            prod_spec["coverage_checker"]["plugin"]["name"]
        )
    else:
        return coverage_checkers.get_plugin("masked_arrays")


def get_covg_args_from_product(prod_plugin, output_dict=None, covg_field=None):
    """Interface will be deprecated v2.0.

    Retrieve coverage check function args, based on requested product and source

    Parameters
    ----------
    product_name : str
        Name of requested product (ie, 'IR-BD', '89H', 'color89Nearest', etc)
    source_name : str
        Name of requested source (ie, 'ahi', 'modis', etc)

    Returns
    -------
    covg_func_name : str
        Return dictionary of coverage args required for given product/source

    See Also
    --------
    ``geoips.dev.check_cmap_func``
        additional information on colormapper types, arguments, and return values
    """
    prod_spec = prod_plugin["spec"]
    # Add .copy() to coverage args so we aren't passing the ACTUAL coverage
    # args attached to the product plugin.
    if covg_field in prod_spec:
        return prod_spec[covg_field]["plugin"]["arguments"].copy()
    elif "coverage_checker" in prod_spec:
        return prod_spec["coverage_checker"]["plugin"]["arguments"].copy()
    else:
        return {}
