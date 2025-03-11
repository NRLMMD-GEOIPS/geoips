# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""TC product YAML metadata output format."""

import logging

from geoips.filenames.base_paths import PATHS as gpaths
from geoips.geoips_utils import replace_geoips_paths
from geoips.sector_utils.yaml_utils import write_yamldict
from geoips.interfaces import products

LOG = logging.getLogger(__name__)

interface = "output_formatters"
family = "standard_metadata"
name = "metadata_tc"


def call(
    area_def,
    xarray_obj,
    metadata_yaml_filename,
    product_filename,
    metadata_dir="metadata",
    basedir=gpaths["TCWWW"],
    output_dict=None,
    metadata_fname_dict=None,
    output_fname_dict=None,
):
    """Produce metadata yaml file of sector info associated with final_product.

    Parameters
    ----------
    area_def : AreaDefinition
        Pyresample AreaDefintion object
    final_product : str
        Product that is associated with the passed area_def
    metadata_dir : str, default="metadata"
        Subdirectory name for metadata (using non-default allows for
        non-operational outputs)

    Returns
    -------
    str
        Metadata yaml filename, if one was produced.
    """
    from geoips.sector_utils.utils import is_sector_type

    if not is_sector_type(area_def, "tc"):
        return None
    # os.path.join does not take a list, so "*" it
    # product_partial_path = product_filename.replace(gpaths['TCWWW'],
    #   'https://www.nrlmry.navy.mil/tcdat')
    product_partial_path = replace_geoips_paths(product_filename)
    # product_partial_path = pathjoin(
    #   *final_product.split('/')[-5:-1]+[basename(final_product)])
    return output_tc_metadata_yaml(
        metadata_yaml_filename,
        area_def,
        xarray_obj,
        product_partial_path,
        output_dict,
        metadata_fname_dict=metadata_fname_dict,
        output_fname_dict=output_fname_dict,
    )


def update_sector_info_with_data_times(sector_info, xarray_obj):
    """Update sector info with data times, for YAML metadata output."""
    start = xarray_obj.start_datetime
    end = xarray_obj.end_datetime
    mid = start + (end - start) / 2.0
    sector_info["data_times"] = {}
    sector_info["data_times"]["start"] = start
    sector_info["data_times"]["end"] = end
    sector_info["data_times"]["mid"] = mid
    return sector_info


def update_sector_info_with_coverage(
    sector_info, product_name, xarray_obj, area_def, output_dict
):
    """Update sector info with coverage, for YAML metadata output."""
    from geoips.dev.product import get_covg_from_product, get_covg_args_from_product

    covg_func_types = {
        "image_production": "image_production_coverage_checker",
        "fname": "filename_coverage_checker",
        "full": "full_coverage_checker",
    }

    covg_funcs = {}
    covg_args = {}
    covgs = {}

    prod_plugin = products.get_plugin(
        xarray_obj.source_name, product_name, output_dict.get("product_spec_override")
    )

    default_covg_plugin = get_covg_from_product(
        prod_plugin,
        covg_field="coverage_checker",
    )

    default_covg_args = get_covg_args_from_product(
        prod_plugin,
        covg_field="coverage_checker",
    )
    try:
        default_covgs = default_covg_plugin(
            xarray_obj, prod_plugin.name, area_def, **covg_args["default"]
        )
    except KeyError:
        LOG.warning(
            '"%s" covg_func not defined, not including in metadata_tc output', "default"
        )

    for covg_func_type, coverage_checker_plugin_name in covg_func_types.items():
        covg_funcs[covg_func_type] = get_covg_from_product(
            prod_plugin,
            covg_field=coverage_checker_plugin_name,
        )
        covg_args[covg_func_type] = get_covg_args_from_product(
            prod_plugin,
            covg_field=coverage_checker_plugin_name,
        )
        # Set variable_name to prod_plugin.name if not defined.
        # Always use variable_name if it is defined.
        # Remove from args so there is not a duplicate are when passing
        # (since we are passing covg_varname explicitly).
        # Note get_covg_args_from_product was updated to return a copy of
        # covg_args, so this does not impact future uses of the product.
        covg_varname = covg_args[covg_func_type].pop("variable_name", prod_plugin.name)
        # Note variables can be specified as DATASET:VARIABLE, since this is a
        # preprocessed alg_xarray, and not a dictionary of datasets, just use the
        # variable name (we expect the correct variable will exist in this final
        # processed array)
        if ":" in covg_varname:
            covg_varname = covg_varname.split(":")[1]
        try:
            covgs[covg_func_type] = covg_funcs[covg_func_type](
                xarray_obj, covg_varname, area_def, **covg_args[covg_func_type]
            )
        except KeyError:
            LOG.warning(
                '"%s" covg_func not defined, not including in metadata_tc output',
                covg_func_type,
            )

    if covgs:
        sector_info["covg_info"] = {}

    for covg_func_type in covgs.keys():
        sector_info["covg_info"][covg_func_type + "_covg_func"] = covg_funcs[
            covg_func_type
        ].name
        sector_info["covg_info"][covg_func_type + "_covg_args"] = covg_args[
            covg_func_type
        ]
        sector_info["covg_info"][covg_func_type + "_covg"] = covgs[covg_func_type]

    if covgs.keys() and not set(covg_func_types).issubset(set(covgs.keys())):
        sector_info["covg_info"]["default_covg_func"] = default_covgs.name
        sector_info["covg_info"]["default_covg_args"] = default_covg_args
        sector_info["covg_info"]["default_covg"] = default_covgs

    return sector_info


def output_tc_metadata_yaml(
    metadata_fname,
    area_def,
    xarray_obj,
    product_filename=None,
    output_dict=None,
    metadata_fname_dict=None,
    output_fname_dict=None,
):
    """Write out yaml file "metadata_fname" of sector info found in "area_def".

    Parameters
    ----------
    metadata_fname : str
        Path to output metadata_fname
    area_def : AreaDefinition
        Pyresample AreaDefinition of sector information
    xarray_obj : xarray.Dataset
        xarray Dataset object that was used to produce product
    productname : str
        Full path to full product filename that this YAML file refers to

    Returns
    -------
    str
        Path to metadata filename if successfully produced.
    """
    from geoips.plugins.modules.output_formatters.metadata_default import (
        update_sector_info_with_default_metadata,
    )

    sector_info = update_sector_info_with_default_metadata(
        area_def, xarray_obj, product_filename=product_filename
    )

    sector_info = update_sector_info_with_coverage(
        sector_info,
        metadata_fname_dict["product_name"],
        xarray_obj,
        area_def,
        output_dict,
    )

    sector_info = update_sector_info_with_data_times(
        sector_info,
        xarray_obj,
    )

    returns = write_yamldict(
        sector_info, metadata_fname, force=True, replace_geoips_paths=True
    )
    if returns:
        LOG.info("METADATASUCCESS Writing %s", metadata_fname)
    return returns
