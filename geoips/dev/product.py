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

Wrapper functions for geoips product specifications.

This functionality will be replaced with a class-based implementation v2.0,
and deprecated at that time.
"""
import logging

LOG = logging.getLogger(__name__)

from geoips.geoips_utils import find_entry_point, find_config


### Product parameter dictionaries ###
def is_valid_product(product_name, source_name, output_dict=None):
    """Interface will be deprecated v2.0.

        Check that requested product parameter dictionary is properly formatted.

        The dictionary of product parameters fully determines the algorithms,
        interpolation schemes,
        colormaps (if appropriate), etc that are applied to a given data array
        in order to generate
        the requested product.

        Dictionary of product parameters currently specified by:
            algorithms.<algorithm_name>.products[product_name]
        and requested via commandline with:
            --productname <product_name>

    Parameters
    ----------
    product_name : str
        Name of requested product
        (ie, '89H', 'IR-BD', 'color89Nearest', 'Infrared', etc)

    Returns
    -------
    is_valid : bool
        * True if 'product_name' is a properly formatted dictionary of
          product parameters.
        * False if product dictionary:
            * does not contain supported 'product_type',
            * does not contain all 'required' fields,
            * contains non-supported 'optional' fields

    Notes
    -----
    Product types currently one of::

        'interp_alg_cmap' : data first interpolated,
                        then algorithm applied,
                        then colormap applied,
                        as appropriate (None for cmap or interp
                        indicate no interpolation or colormap required)
               dictionary fields: {'product_type': 'interp_alg_cmap',
                                   'interp_func': <str>,
                                   'interp_args': <dict>,
                                   'alg_func': <str>,
                                   'alg_args': <str>,
                                   'cmap_func': <str: optional>,
                                   'cmap_args': <dict: optional>,
                                   'display_name': <str: optional>}
    """
    # product_name and source_input keys are added in the "get_product" interface func
    # valid product types:
    required_keys = {
        "interp_alg_cmap": [
            "product_type",  # Set in product_params
            "product_name",
            "source_input",
            "variables",  # Set in product_inputs
            "alg_func",
            "alg_args",  # Set in product_params
            "interp_func",
            "interp_args",  # Set in product_params
            "cmap_func",
            "cmap_args",
        ],  # Set in product_params
        "alg_interp_cmap": [
            "product_type",  # Set in product_params
            "product_name",
            "source_input",
            "variables",  # Set in product_inputs
            "alg_func",
            "alg_args",  # Set in product_params
            "interp_func",
            "interp_args",  # Set in product_params
            "cmap_func",
            "cmap_args",
        ],  # Set in product_params
        "interp": [
            "product_type",  # Set in product_params
            "product_name",
            "source_input",
            "variables",  # Set in product_inputs
            "interp_func",
            "interp_args",
        ],  # Set in product_params
        "interp_alg": [
            "product_type",  # Set in product_params
            "product_name",
            "source_input",
            "variables",  # Set in product_inputs
            "alg_func",
            "alg_args",  # Set in product_params
            "interp_func",
            "interp_args",
        ],  # Set in product_params
        "alg": [
            "product_type",  # Set in product_params
            "product_name",
            "source_input",
            "variables",  # Set in product_inputs
            "alg_func",
            "alg_args",
        ],  # Set in product_params
        "alg_cmap": [
            "product_type",
            "product_name",
            "source_input",
            "variables",  # Set in product_inputs
            "alg_func",
            "alg_args",
            "cmap_func",
            "cmap_args",
        ],
        "cmap": [
            "product_type",
            "product_name",
            "source_input",
            "variables",  # Set in product_inputs
            "cmap_func",
            "cmap_args",
        ],
        "sectored_xarray_dict_to_output_format": [
            "product_type",
            "product_name",
            "source_input",
            "variables",
        ],
        "unsectored_xarray_dict_to_output_format": [
            "product_type",
            "product_name",
            "source_input",
            "variables",
        ],
        "unsectored_xarray_dict_area_to_output_format": [
            "product_type",
            "product_name",
            "source_input",
            "variables",
        ],
        "xarray_dict_to_output_format": [
            "product_type",
            "product_name",
            "source_input",
            "variables",
        ],
    }

    optional_keys = {
        "interp_alg_cmap": ["display_name", "mtif_type", "covg_func", "covg_args"],
        "alg_interp_cmap": ["display_name", "mtif_type", "covg_func", "covg_args"],
        "interp": ["display_name", "covg_func", "covg_args"],
        "interp_alg": ["display_name", "covg_func", "covg_args"],
        "alg": ["display_name", "covg_func", "covg_args"],
        "cmap": ["display_name", "covg_func", "covg_args"],
        "sectored_xarray_dict_to_output_format": [
            "display_name",
            "covg_func",
            "covg_args",
        ],
        "unsectored_xarray_dict_to_output_format": [
            "display_name",
            "covg_func",
            "covg_args",
        ],
        "unsectored_xarray_dict_area_to_output_format": [
            "display_name",
            "covg_func",
            "covg_args",
        ],
        "alg_cmap": ["display_name", "mtif_type", "covg_func", "covg_args"],
    }

    product_dict = get_product(product_name, source_name, output_dict=output_dict)
    # if product_dict is None:
    #     LOG.error("INVALID PRODUCT '%s': product parameter dictionary did not exist",
    #               product_name)
    #     return False

    if "product_type" not in product_dict:
        LOG.error(
            "INVALID PRODUCT '%s': 'product_type' must be defined within product parameter dictionary",
            product_name,
        )
        return False
    if product_dict["product_type"] not in required_keys.keys():
        LOG.error(
            "INVALID PRODUCT '%s': 'product_type' in product parameter dictionary must be one of '%s'",
            product_name,
            list(required_keys.keys()),
        )
        return False

    product_type = get_product_type(product_name, source_name)

    # If we don't have all of the required keys, return False
    if not set(required_keys[product_type]).issubset(set(product_dict)):
        LOG.error(
            "INVALID PRODUCT '%s': '%s' product parameter dictionary must contain the following fields: '%s'",
            product_name,
            product_type,
            list(required_keys[product_type]),
        )
        return False

    # If we have non-allowed keys, return False
    if not set(product_dict).issubset(
        required_keys[product_type] + optional_keys[product_type]
    ):
        LOG.error(
            "INVALID PRODUCT '%s': Unknown fields in '%s' product parameter dictionary: '%s'",
            product_name,
            product_type,
            set(product_dict).difference(
                required_keys[product_type] + optional_keys[product_type]
            ),
        )
        return False

    # If we get here, then the product parameter dictionary format is valid.
    return True


def get_product(product_name, source_name, output_dict=None):
    """Interface will be deprecated v2.0.

    Get dictionary of product parameters for requested
    product/source combination.

    See: geoips.dev.product.is_valid_product for full list of supported
        product dictionary formats

    Parameters
    ----------
    product_name : str
        Name of requested product
        (ie, '89H', 'IR-BD', 'color89Nearest', 'Infrared', etc)

    Returns
    -------
    dict
        Dictionary of desired product specifications
    """
    all_products = {}

    source_dict = get_source_inputs(source_name)

    # Allow specifying product_template within product_inputs - allows fully
    # specifying product within product_inputs
    if "product_template" in source_dict[source_name][product_name]:
        product_template = source_dict[source_name][product_name]["product_template"]
    else:
        product_template = product_name

    product_dict = get_product_specs(product_template)

    product_dict[product_name] = product_dict[product_template]

    # Allow specifying product template within product_params YAMLs also -
    # only add fields that don't already exist
    if "product_template" in product_dict[product_name]:
        product_template = product_dict[product_name]["product_template"]
        product_template_dict = get_product_specs(product_template)
        for key in product_template_dict[product_template]:
            if key not in product_dict[product_name]:
                LOG.info(
                    "    Adding '%s'='%s' from template",
                    key,
                    product_template_dict[product_template][key],
                )
                product_dict[product_name][key] = product_template_dict[
                    product_template
                ][key]

    product_dict[product_name]["product_template"] = product_template

    if product_name not in product_dict:
        raise KeyError(
            f"INVALID PRODUCT/SOURCE {product_name}/{source_name}: product name {product_name} "
            f"must be top level of yaml file {product_dict['yaml_files']}"
        )

    if source_name not in source_dict:
        raise KeyError(
            f"INVALID PRODUCT/SOURCE {product_name}/{source_name}: source name {source_name} "
            f"must be top level of yaml file {source_dict['yaml_files']}"
        )

    if product_name not in source_dict[source_name]:
        raise KeyError(
            f"INVALID PRODUCT/SOURCE {product_name}/{source_name}: product name '{product_name}' "
            f"must be contained in source dict '{source_name}' in {source_dict['yaml_files']}"
        )

    for key in source_dict[source_name][product_name]:
        # If it is an empty dictionary, assume we are requesting no values explicitly
        if (
            key in product_dict[product_name]
            and isinstance(product_dict[product_name][key], dict)
            and not source_dict[source_name][product_name][key]
        ):
            LOG.debug(
                "Replacing key '%s' in %s product_dict with source specification",
                key,
                product_name,
            )
            product_dict[product_name][key] = source_dict[source_name][product_name][
                key
            ]
        # For non-empty dictionaries, replace each individual field rather than
        # entire dictionary
        elif key in product_dict[product_name] and isinstance(
            product_dict[product_name][key], dict
        ):
            for subkey in source_dict[source_name][product_name][key]:
                LOG.debug(
                    "Replacing key '%s/%s' in %s product_dict with source specification",
                    key,
                    subkey,
                    product_name,
                )
                product_dict[product_name][key][subkey] = source_dict[source_name][
                    product_name
                ][key][subkey]
        # If it is NOT a dictionary, replace the entire field
        elif key in product_dict[product_name] and not isinstance(
            product_dict[product_name][key], dict
        ):
            LOG.debug(
                "Replacing key '%s' in %s product_dict with source specification",
                key,
                product_name,
            )
            product_dict[product_name][key] = source_dict[source_name][product_name][
                key
            ]
        # If it is not included, just add it
        else:
            LOG.debug(
                "Adding key '%s' to %s product_dict from source specification",
                key,
                product_name,
            )
            product_dict[product_name][key] = source_dict[source_name][product_name][
                key
            ]
    product_dict[product_name]["source_input"] = source_name
    product_dict[product_name]["product_name"] = product_name

    if (
        output_dict is not None
        and "product_params_override" in output_dict
        and (
            product_name in output_dict["product_params_override"]
            or "all" in output_dict["product_params_override"]
        )
    ):
        keyname = "all"
        if product_name in output_dict["product_params_override"]:
            keyname = product_name
        for key, val in output_dict["product_params_override"][keyname].items():
            product_dict[product_name][key] = val
    return product_dict[product_name]


def get_product_type(product_name, source_name):
    """Interface will be deprecated v2.0.

    Retrieve product_type of the requested product, found in:
           geoips.dev.product.get_product(product_name)['product_type']

    See: geoips.dev.product.is_valid_product for full list of supported
    product types.

    Parameters
    ----------
    product_name : str
        Name of requested product
        (ie, '89H', 'IR-BD', 'color89Nearest', 'Infrared', etc)

    Returns
    -------
    str
        Product type,
        found in geoips.dev.product.get_product(product_name)['product_type']
    """
    product_dict = get_product(product_name, source_name)
    return product_dict["product_type"]


def list_products_by_type():
    """Interface will be deprecated v2.0.

    List all available products within the current GeoIPS instantiation,
    on a per-product_type basis.

    Product "type" determines exact required format of the product
    parameter dictionary.

    See geoips.dev.product.is_valid_product? for a list of available product
        types and associated dictionary formats.
    See geoips.dev.product.get_product(product_name) to retrieve the
        product parameter dictionary
        for a given product

    Returns
    -------
    dict
        Dictionary with all product types as keys, and lists of
        associated product names (str) as values.
    """
    return list_products()["by_type"]


def list_products_by_source():
    """Interface will be deprecated v2.0.

    List all available products within the current GeoIPS instantiation,
    on a per-source_name basis.

    See geoips.dev.product.is_valid_product? for a list of available
        product types and associated dictionary formats.
    See geoips.dev.product.get_product(product_name)
        to retrieve the product parameter dictionary
        for a given product

    Returns
    -------
    dict
        Dictionary with all sources as keys, and lists of associated product
        names (str) as values.
    """
    return list_products()["by_source"]


def list_products_by_product():
    """Interface will be deprecated v2.0.

    List all available products within the current GeoIPS instantiation,
    with all sources available for each product.

    See geoips.dev.product.is_valid_product? for a list of available
        product types and associated dictionary formats.
    See geoips.dev.product.get_product(product_name)
        to retrieve the product parameter dictionary
        for a given product

    Returns
    -------
    dict
        Dictionary with all products as keys, and lists of
        associated source names (str) as values.

    """
    return list_products()["by_product"]


def list_products():
    """Interface will be deprecated v2.0.

    List all available products within the current GeoIPS instantiation,
    on a per-product_type and per-source_name basis.

    Product "type" determines exact required format of the product
    parameter dictionary.

    See geoips.dev.product.is_valid_product? for a list of available
        product types and associated dictionary formats.
    See geoips.dev.product.get_product(product_name)
        to retrieve the product parameter dictionary
        for a given product

    Returns
    -------
    dict
        Dictionary with all product types as keys, and lists of
        associated product names (str) as values.
    """
    from os.path import basename, splitext
    from geoips.geoips_utils import (
        list_product_specs_dict_yamls,
        list_product_source_dict_yamls,
    )

    LOG.info("Listing products by type")
    all_product_files = list_product_specs_dict_yamls()
    all_source_files = list_product_source_dict_yamls()
    all_products = {"by_type": {}, "by_source": {}, "by_product": {}}
    product_names = []
    source_names = []
    for source_fname in all_source_files:
        for product_fname in all_product_files:
            product_names += [splitext(basename(product_fname))[0]]
            source_names += [splitext(basename(source_fname))[0]]

    product_names = sorted(list(set(product_names)))
    source_names = sorted(list(set(source_names)))
    for source_name in source_names:
        # LOG.info('Adding source %s', source_name)
        for product_name in product_names:
            # LOG.info('    Adding product %s', product_name)
            try:
                product = get_product(product_name, source_name)
            except KeyError:
                continue
            if not is_valid_product(product_name, source_name):
                LOG.error(
                    "    POORLY FORMATTED FILE %s %s", product_fname, source_fname
                )
                continue

            if product["product_type"] not in all_products["by_type"]:
                all_products["by_type"][product["product_type"]] = [product_name]
            else:
                if product_name not in all_products["by_type"][product["product_type"]]:
                    all_products["by_type"][product["product_type"]] += [product_name]

            if source_name not in all_products["by_source"]:
                all_products["by_source"][source_name] = [product_name]
            else:
                if product_name not in all_products["by_source"][source_name]:
                    all_products["by_source"][source_name] += [product_name]

            if product_name not in all_products["by_product"]:
                all_products["by_product"][product_name] = [source_name]
            else:
                if source_name not in all_products["by_product"][product_name]:
                    all_products["by_product"][product_name] += [source_name]

    return all_products


def get_source_inputs(source_name):
    """Interface will be deprecated v2.0."""
    source_dict = {}
    import yaml
    from os.path import basename, splitext
    from geoips.geoips_utils import list_product_source_dict_yamls

    all_source_files = list_product_source_dict_yamls()
    for source_fname in all_source_files:
        curr_source_name = splitext(basename(source_fname))[0]
        if curr_source_name == source_name:
            with open(source_fname, "r") as f:
                curr_source_dict = yaml.safe_load(f)
            if source_name not in source_dict:
                source_dict = curr_source_dict
                source_dict["yaml_files"] = []
            if source_name not in curr_source_dict:
                raise KeyError(
                    f"INVALID SOURCE {source_name}: source name {source_name} "
                    f"must be top level of yaml file {source_fname}"
                )
            source_dict[source_name].update(curr_source_dict[source_name])
            source_dict["yaml_files"] += [source_fname]

    if not source_dict:
        raise ValueError(f"INVALID SOURCE {source_name}: YAML config not found")

    return source_dict


def get_product_specs(product_name):
    """Interface will be deprecated v2.0."""
    product_yaml = None
    import yaml
    from os.path import basename, splitext
    from geoips.geoips_utils import list_product_specs_dict_yamls

    all_product_files = list_product_specs_dict_yamls()
    for product_fname in all_product_files:
        curr_product_name = splitext(basename(product_fname))[0]
        if product_name == curr_product_name:
            product_yaml = product_fname

    if not product_yaml:
        raise ValueError(f"INVALID PRODUCT {product_name}: YAML config not found")

    with open(product_yaml, "r") as f:
        product_dict = yaml.safe_load(f)
    product_dict["yaml_files"] = [product_fname]

    return product_dict


def test_product_interface():
    """Interface will be deprecated v2.0.

    Finds and opens every product params dict available within the
    current geoips instantiation

    See geoips.dev.product.is_valid_product? for a list of available
        product params dict types and associated call signatures / return values.
    See geoips.dev.product.get_product(product_params_dict_name)
        to retrieve the requested product params dict

    Returns
    -------
    list
        List of all successfully opened geoips product params dicts
    """
    product_params_dicts = {
        "validity_check": {},
        # 'get_source_inputs': {},  # Tested by get_product
        # 'get_product_specs': {},  # Tested by get_product
        # 'get_product': {},        # Tested by is_valid_product
        # 'get_product_type': {},   # Tested by is_valid_product
        "get_interp_name": {},
        "get_interp_args": {},
        "get_cmap_from_product": {},
        "get_cmap_name": {},
        "get_cmap_args": {},
        "get_alg_name": {},
        "get_alg_args": {},
        "get_required_variables": {},
        "get_data_range": {},
    }
    product_params_dicts["list_products"] = list_products()
    for source_name in product_params_dicts["list_products"]["by_source"]:
        # LOG.info('Checking source %s', source_name)
        product_params_dicts["validity_check"][source_name] = {}
        # product_params_dicts['get_source_inputs'][source_name] = {}
        # product_params_dicts['get_product_specs'][source_name] = {}
        # product_params_dicts['get_product'][source_name] = {}
        # product_params_dicts['get_product_type'][source_name] = {}
        product_params_dicts["get_alg_name"][source_name] = {}
        product_params_dicts["get_alg_args"][source_name] = {}
        product_params_dicts["get_interp_name"][source_name] = {}
        product_params_dicts["get_interp_args"][source_name] = {}
        product_params_dicts["get_cmap_from_product"][source_name] = {}
        product_params_dicts["get_cmap_name"][source_name] = {}
        product_params_dicts["get_cmap_args"][source_name] = {}
        product_params_dicts["get_required_variables"][source_name] = {}
        product_params_dicts["get_data_range"][source_name] = {}
        for product_name in product_params_dicts["list_products"]["by_source"][
            source_name
        ]:
            # LOG.info('    Checking product %s', product_name)
            product_params_dicts["validity_check"][source_name][
                product_name
            ] = is_valid_product(product_name, source_name)

            product_params_dicts["get_alg_name"][source_name][
                product_name
            ] = get_alg_name(product_name, source_name)
            if product_params_dicts["get_alg_name"][source_name][product_name]:
                product_params_dicts["get_alg_args"][source_name][
                    product_name
                ] = get_alg_args(product_name, source_name)
                try:
                    product_params_dicts["get_data_range"][source_name][
                        product_name
                    ] = get_data_range(product_name, source_name)
                except TypeError as resp:
                    LOG.error(
                        "SKIPPING %s %s: %s", product_name, source_name, str(resp)
                    )
            else:
                LOG.error(
                    "SKIPPING %s %s get_alg funcs: get_alg_name was None",
                    product_name,
                    source_name,
                )

            product_params_dicts["get_cmap_name"][source_name][
                product_name
            ] = get_cmap_name(product_name, source_name)
            if product_params_dicts["get_cmap_name"][source_name][product_name]:
                product_params_dicts["get_cmap_from_product"][source_name][
                    product_name
                ] = get_cmap_from_product(product_name, source_name)
                product_params_dicts["get_cmap_args"][source_name][
                    product_name
                ] = get_cmap_args(product_name, source_name)
            else:
                LOG.error(
                    "SKIPPING %s %s get_cmap funcs: get_cmap_name was None",
                    product_name,
                    source_name,
                )

            product_params_dicts["get_interp_name"][source_name][
                product_name
            ] = get_interp_name(product_name, source_name)
            if product_params_dicts["get_interp_name"][source_name][product_name]:
                product_params_dicts["get_interp_args"][source_name][
                    product_name
                ] = get_interp_args(product_name, source_name)
            else:
                LOG.error(
                    "SKIPPING %s %s get_interp_args: get_interp_name was None",
                    product_name,
                    source_name,
                )

            product_params_dicts["get_required_variables"][source_name][
                product_name
            ] = get_required_variables(product_name, source_name)

    return product_params_dicts


def get_alg_name(product_name, source_name, output_dict=None):
    """Interface will be deprecated v2.0.

    Retrieve the algorithm required for a given product_name

    Parameters
    ----------
    product_name : str
        Desired product_name ('IR-BD', 'Infrared', '89H', '89HNearest', etc)

    Returns
    -------
    alg_name : str
        Algorithm name, relative to algorithms subpackage,
        (ie, visir.IR_BD, pmw_tb.pmw_89H)

    Notes
    -----
    algorithm_name currently specified in:
        ``algorithms.<algorithm_name>.products[product_name]['alg_func']``
    Loop through all possible product dictionaries, which are currently in one of:
        * ``$GEOIPS_PACKAGES_DIR/*/algorithms/visir/*.py``
        * ``$GEOIPS_PACKAGES_DIR/*/algorithms/pmw_tb/pmw_*.py``
        * ``$GEOIPS_PACKAGES_DIR/*/*/algorithms/visir/*.py``
        * ``$GEOIPS_PACKAGES_DIR/*/*/algorithms/pmw_tb/pmw_*.py``
    """
    product_params = get_product(product_name, source_name, output_dict=output_dict)

    if not product_params:
        raise ValueError(
            f"UNSUPPORTED product_name {product_name} not supported for source {source_name}"
        )

    if "alg_func" not in product_params:
        return None
    func_name = product_params["alg_func"]
    if func_name is None:
        return None

    return product_params["alg_func"]


def get_alg_args(product_name, source_name, output_dict=None):
    """Interface will be deprecated v2.0.

    Retrieve required algorithm parameters for requested product

    Parameters
    ----------
    product_name : str
        Name of requested product (ie, 'IR-BD', '89H', 'color89Nearest', etc)

    Returns
    -------
    alg_args : dict
        List of float specifying min and max value for the output product
        <geoips_package>.algorithms.<algorithm_name>.alg_params['output_data_range']
    """
    product_params = get_product(product_name, source_name, output_dict=output_dict)
    return product_params["alg_args"]


def get_required_variables(product_name, source_name, output_dict=None):
    """Interface will be deprecated v2.0.

    Retrieve required variables, based on requested product and source

    Parameters
    ----------
    product_name : str
        Name of requested product (ie, 'IR-BD', '89H', 'color89Nearest', etc)
    source_name : str
        Name of requested source (ie, 'ahi', 'modis', etc)

    Returns
    -------
    required_variables : list or dict
        * If list: List of strings specifying required variables.
        * If dict: Dictionary of variable types of lists of variable names

            * {'<variable_type>': ['var1', 'var2', ... , 'varn']}
    """
    # This can either be a list or dictionary, dependent on YAML config specification
    variables = get_product(product_name, source_name, output_dict=output_dict)[
        "variables"
    ]
    # Support categorizing variables in a dictionary - var_dict[var_type] =
    # ['var1', 'var2', 'varn']
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


def get_requested_datasets_for_variables(product_name, source_name, output_dict=None):
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
    variables = get_product(product_name, source_name, output_dict=output_dict)[
        "variables"
    ]
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


def get_data_range(product_name, source_name, output_dict=None):
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
    alg_args = get_alg_args(product_name, source_name)
    if "output_data_range" not in alg_args:
        alg_func_name = get_alg_name(product_name, source_name)
        from geoips.dev.alg import get_alg_type

        alg_type = get_alg_type(alg_func_name)
        raise TypeError(
            f'Can not call get_data_range on "{alg_type}" algs, '
            f'"output_data_range" not defined (alg "{alg_func_name}" / prod "{product_name}"'
        )
    return alg_args["output_data_range"]


def get_interp_name(product_name, source_name, output_dict=None):
    """Interface will be deprecated v2.0.

    Retrieve interp function name, based on requested product and source

    Parameters
    ----------
    product_name : str
        Name of requested product (ie, 'IR-BD', '89H', 'color89Nearest', etc)
    source_name : str
        Name of requested source (ie, 'ahi', 'modis', etc)

    Returns
    -------
    interp_func_name : str
        Return name of interp function required for given product/source

    See Also
    --------
    ``geoips.check_interp_func``
        additional information on interp types, arguments, and return values
    """
    products = get_product(product_name, source_name, output_dict=output_dict)

    if not products:
        raise ValueError(
            "UNSUPPORTED product_name %s not supported for source %s".format(
                product_name, source_name
            )
        )
    if "interp_func" not in products:
        return None

    return products["interp_func"]


def get_interp_args(product_name, source_name, output_dict=None):
    """Interface will be deprecated v2.0.

    Retrieve interp function arguments, based on requested product and source

    Parameters
    ----------
    product_name : str
        Name of requested product (ie, 'IR-BD', '89H', 'color89Nearest', etc)
    source_name : str
        Name of requested source (ie, 'ahi', 'modis', etc)

    Returns
    -------
    interp_args : dict
        Return arguments for interp function

    See Also
    --------
    ``geoips.check_interp_func``
        additional information on interp types, arguments, and return values
    """
    products = get_product(product_name, source_name, output_dict=output_dict)

    if not products:
        raise ValueError(
            "UNSUPPORTED product_name %s not supported for source %s".format(
                product_name, source_name
            )
        )

    interp_args = products["interp_args"]
    if interp_args is None:
        return None

    return interp_args


def get_product_display_name(product_name, source_name, output_dict=None):
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
        additional information on colormap types, arguments, and return values
    """
    products = get_product(product_name, source_name, output_dict=output_dict)

    if not products:
        raise ValueError(
            "UNSUPPORTED product_name %s not supported for source %s".format(
                product_name, source_name
            )
        )

    if "display_name" not in products or products["display_name"] is None:
        return product_name

    return products["display_name"]


def get_cmap_name(product_name, source_name, output_dict=None):
    """Interface will be deprecated v2.0.

    Retrieve colormap function name, based on requested product and source

    Parameters
    ----------
    product_name : str
        Name of requested product (ie, 'IR-BD', '89H', 'color89Nearest', etc)
    source_name : str
        Name of requested source (ie, 'ahi', 'modis', etc)

    Returns
    -------
    cmap_func_name : str
        Return name of colormap function required for given product/source

    See Also
    --------
    ``geoips.dev.check_cmap_func``
        additional information on colormap types, arguments, and return values
    """
    products = get_product(product_name, source_name, output_dict=output_dict)

    if not products:
        raise ValueError(
            "UNSUPPORTED product_name %s not supported for source %s".format(
                product_name, source_name
            )
        )

    if "cmap_func" not in products:
        return None
    func_name = products["cmap_func"]
    if func_name is None:
        return None

    return products["cmap_func"]


def get_cmap_args(product_name, source_name, output_dict=None):
    """Interface will be deprecated v2.0.

    Retrieve colormap function arguments, based on requested product and source

    Parameters
    ----------
    product_name : str
        Name of requested product (ie, 'IR-BD', '89H', 'color89Nearest', etc)
    source_name : str
        Name of requested source (ie, 'ahi', 'modis', etc)

    Returns
    -------
    cmap_args : dict
        Return arguments for colormap function

    See Also
    --------
    ``geoips.dev.check_cmap_func``
        additional information on colormap types, arguments, and return values
    """
    products = get_product(product_name, source_name, output_dict=output_dict)

    if not products:
        raise ValueError(
            "UNSUPPORTED product_name %s not supported for source %s".format(
                product_name, source_name
            )
        )

    args = products["cmap_args"]
    if args is None:
        return None

    return products["cmap_args"]


def get_cmap_from_product(product_name, source_name, output_dict=None):
    r"""Interface will be deprecated v2.0.

    Retrieve colormap information, based on requested product and source

    Parameters
    ----------
    product_name : str
        Name of requested product (ie, 'IR-BD', '89H', 'color89Nearest', etc)
    source_name : str
        Name of requested source (ie, 'ahi', 'modis', etc)

    Returns
    -------
    cmap_func(\*\*cmap_args) : function
        Return actual colormap information

    See Also
    --------
    ``geoips.dev.check_cmap_func``
        additional information on colormap types, arguments, and return values
    """
    cmap_func_name = get_cmap_name(product_name, source_name, output_dict=output_dict)
    try:
        from geoips.dev.cmap import get_cmap

        cmap_func = get_cmap(cmap_func_name)
    except Exception as resp:
        raise ValueError(
            f"UNDEFINED CMAP FUNC '{cmap_func_name}'"
            f" in product '{product_name}'"
            f" source '{source_name}':"
            f" ORIGINAL EXCEPTION {type(resp).__name__}:"
            f" {resp.__doc__} >> {resp.args}"
        )

    cmap_args = get_cmap_args(product_name, source_name, output_dict=output_dict)

    return cmap_func(**cmap_args)


def get_covg_from_product(
    product_name, source_name, output_dict=None, covg_func_field_name=None
):
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
        additional information on colormap types, arguments, and return values
    """
    default_covg_func_field_name = "covg_func"
    if covg_func_field_name is None:
        covg_func_field_name = default_covg_func_field_name

    products = get_product(product_name, source_name, output_dict)

    if not products:
        raise ValueError(
            "UNSUPPORTED product_name %s not supported for source %s".format(
                product_name, source_name
            )
        )

    if covg_func_field_name in products:
        return find_entry_point("coverage_checks", products[covg_func_field_name])
    if default_covg_func_field_name in products:
        return find_entry_point(
            "coverage_checks", products[default_covg_func_field_name]
        )
    return find_entry_point("coverage_checks", "masked_arrays")


def get_covg_args_from_product(
    product_name, source_name, output_dict=None, covg_args_field_name=None
):
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
        additional information on colormap types, arguments, and return values
    """
    default_covg_args_field_name = "covg_args"

    if covg_args_field_name is None:
        covg_args_field_name = default_covg_args_field_name
    products = get_product(product_name, source_name, output_dict=output_dict)

    if not products:
        raise ValueError(
            "UNSUPPORTED product_name %s not supported for source %s".format(
                product_name, source_name
            )
        )

    if covg_args_field_name in products:
        return products[covg_args_field_name]
    if default_covg_args_field_name in products:
        return products[default_covg_args_field_name]
    return {}
