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

"""Processing workflow for config-based processing."""

import logging
from copy import deepcopy
from glob import glob
from os.path import exists

from geoips.filenames.base_paths import PATHS as gpaths
from geoips.geoips_utils import find_entry_point
from geoips.utils.memusg import print_mem_usage
from geoips.geoips_utils import output_process_times
from geoips.dev.product import (
    get_covg_from_product,
    get_covg_args_from_product,
    get_required_variables,
)
from geoips.xarray_utils.data import sector_xarrays
from geoips.filenames.duplicate_files import remove_duplicates
from geoips.geoips_utils import replace_geoips_paths

try:
    from geoips_db.utils.database_writes import (
        write_to_database,
        flag_product_as_deleted,
        write_stats_to_database,
    )
except ImportError:
    pass

# Old interfaces (YAML, will migrate to new soon)
from geoips.dev.output_config import (
    get_output_formatter_kwargs,
    get_output_formatter,
    get_minimum_coverage,
    produce_current_time,
)

# New interfaces
from geoips.interfaces import interpolators
from geoips.interfaces import output_formatters
from geoips.interfaces import readers
from geoips.interfaces import products
from geoips.interfaces import sector_adjusters

# Collect functions from single_source (should consolidate these somewhere)
from geoips.plugins.modules.procflows.single_source import (
    process_sectored_data_output,
    process_xarray_dict_to_output_format,
    pad_area_definition,
    add_filename_extra_field,
    get_area_defs_from_command_line_args,
    plot_data,
    combine_filename_extra_fields,
    get_alg_xarray,
    verify_area_def,
)

# Moved to top-level errors module, fixing issue #67
from geoips.errors import CoverageError

PMW_NUM_PIXELS_X = 1400
PMW_NUM_PIXELS_Y = 1400
PMW_PIXEL_SIZE_X = 1000
PMW_PIXEL_SIZE_Y = 1000

LOG = logging.getLogger(__name__)

interface = "procflows"
family = "standard"
name = "config_based"


def update_output_dict_from_command_line_args(output_dict, command_line_args=None):
    """Update output dict from command line args."""
    if command_line_args is None:
        LOG.info(
            "SKIPPING command_line_args not specified, returning original output_dict"
        )
        return output_dict

    final_output_dict = output_dict.copy()
    for cmdline_fld_name in [
        "filename_formatter_kwargs",
        "metadata_filename_formatter_kwargs",
    ]:
        # Skip fields that are NOT in command_line_args
        if (
            cmdline_fld_name not in command_line_args
            or command_line_args[cmdline_fld_name] is None
        ):
            LOG.info("SKIPPING %s argument not specified command line")
            continue

        # Convert filename_formatter_kwargs and metadata_filename_formatter_kwargs to
        # their plural counterparts
        # Ensure we copy the command_line_args so we do not inadvertently modify
        # the original command line arguments. This should likely be refactored.
        if cmdline_fld_name == "filename_formatter_kwargs":
            output_fld_name = "filename_formatters_kwargs"
            output_fld_val = {"all": deepcopy(command_line_args[cmdline_fld_name])}
        elif cmdline_fld_name == "metadata_filename_formatter_kwargs":
            output_fld_name = "metadata_filename_formatters_kwargs"
            output_fld_val = {"all": deepcopy(command_line_args[cmdline_fld_name])}
        else:
            output_fld_name = cmdline_fld_name
            output_fld_val = deepcopy(command_line_args[cmdline_fld_name])

        # If the current command line field is not in the output dict at all, just
        # add the whole thing.
        if output_fld_name not in output_dict:
            LOG.info(
                'ADDING output_dict "%s" from command_line_args: %s',
                cmdline_fld_name,
                output_fld_val,
            )
            final_output_dict[output_fld_name] = output_fld_val

        # If the special key 'all' is in the desired output_dict field,
        # and it is NOT currently in the
        # output_dict, then add the entire "all" field
        elif "all" in output_fld_val and "all" not in output_dict[output_fld_name]:
            LOG.warning(
                'REPLACING output_dict "%s" *all*with command_line_args: %s',
                output_fld_name,
                output_fld_val,
            )
            final_output_dict[output_fld_name]["all"] = output_fld_val["all"]

        # If the special key "all" is in the desired output_dict field,
        # but IS currently in the output_dict, then add the individual fields
        # within the command line dictionary
        elif "all" in output_fld_val:
            LOG.warning(
                'REPLACING output_dict "%s" *fields* with command_line_args: %s',
                output_fld_name,
                output_fld_val,
            )
            for kwarg_name in output_fld_val["all"]:
                final_output_dict[output_fld_name]["all"][kwarg_name] = output_fld_val[
                    "all"
                ][kwarg_name]

        # Otherwise this is a normal argument, just replace it.
        else:
            LOG.warning(
                'REPLACING entire output_dict "%s" with command_line_args: %s',
                output_fld_name,
                output_fld_val,
            )
            final_output_dict[cmdline_fld_name] = output_fld_val

    return final_output_dict


def get_required_outputs(config_dict, sector_type):
    """Get only the required outputs from the current sector_type."""
    return_dict = {}
    for output_type, output_dict in config_dict["outputs"].items():
        # If the current output type does not require the current sector_type, skip
        if output_dict["requested_sector_type"] != sector_type:
            continue
        return_dict[output_type] = output_dict

    return return_dict


def get_bg_xarray(
    sect_xarrays,
    area_def,
    prod_plugin,
    resampled_read=False,
    window_start_time=None,
    window_end_time=None,
):
    """Get background xarray.

    Parameters
    ----------
    sect_xarrays: dict of xarray.Dataset
        dictionary of xarray Datasets to pull appropriate background xarray from.
        This may include multiple products / variables.
    area_def: pyresample.AreaDefinition
        Spatial region required in the final xarray Datasets.
    prod_plugin: ProductPlugin
        GeoIPS Product Plugin obtained through interfaces.products.get_plugin("name").
    resampled_read: bool, default=False
        Specify whether a resampled read is required, needed for datatypes that
        will be read within "get_alg_xarray"
    window_start_time: datetime.datetime, default=None
        If specified, sector temporally between window_start_time and window_end_time.
        hours_before_sector_time and hours_after_sector_time are ignored if
        window start/end time are set!
    window_end_time: datetime.datetime, default=None
        If specified, sector temporally between window_start_time and window_end_time.
        hours_before_sector_time and hours_after_sector_time are ignored if
        window start/end time are set!

    Returns
    -------
    alg_xarray: xarray.Dataset
        xarray Dataset containing the data needed to produce the background for
        overlay imagery.
    """
    interp_plugin = None
    LOG.interactive(
        "Getting background xarray dataset for product '%s'", prod_plugin.name
    )
    if "interpolator" in prod_plugin["spec"]:
        interp_plugin = interpolators.get_plugin(
            prod_plugin["spec"]["interpolator"]["plugin"]["name"]
        )
        interp_args = prod_plugin["spec"]["interpolator"]["plugin"]["arguments"]

    alg_xarray = None

    # If this is a preprocessed data file with the final product in it,
    # just pull the final product. Must take out METADATA dataset!
    if (
        len(set(sect_xarrays.keys()).difference({"METADATA"})) == 1
        and prod_plugin.name in list(sect_xarrays.values())[0].variables
    ):
        sect_xarray = list(sect_xarrays.values())[0]

        # Efficiency hit with to_masked_array
        # LOG.info('Min/max %s %s / %s',
        #          product_name,
        #          sect_xarray[product_name].to_masked_array().min(),
        #          sect_xarray[product_name].to_masked_array().max())

        alg_xarray = interp_plugin(
            area_def, sect_xarray, alg_xarray, varlist=[prod_plugin.name], **interp_args
        )

        # Efficiency hit with to_masked_array
        # LOG.info('Min/max interp %s %s / %s',
        #          product_name,
        #          alg_xarray[product_name].min(),
        #          alg_xarray[product_name].max())

    # If this is a raw datafile, pull the required variables for applying the given
    # algorithm, and generate the product array.
    else:
        pad_area_def = pad_area_definition(area_def)
        # Ensure pre-processed and raw look the same - this requires applying algorithm
        # to padded sectored data, since that is what is written out to the
        # pre-processed netcdf file, then interpolating to the desired area definition.

        sect_xarray = get_alg_xarray(
            sect_xarrays,
            pad_area_def,
            prod_plugin,
            resampled_read=resampled_read,
            window_start_time=window_start_time,
            window_end_time=window_end_time,
        )
        alg_xarray = interp_plugin(
            area_def, sect_xarray, alg_xarray, varlist=[prod_plugin.name]
        )

    alg_xarray.attrs["registered_dataset"] = True
    alg_xarray.attrs["area_definition"] = area_def
    if prod_plugin.name in alg_xarray.variables:
        alg_xarray = add_filename_extra_field(
            alg_xarray, "background_data", f"bg{prod_plugin.name}"
        )

    return alg_xarray


def get_resampled_read(
    config_dict,
    area_defs,
    area_def_id,
    sector_type,
    reader_plugin,
    reader_kwargs,
    fnames,
    variables,
):
    """Return dictionary of xarray datasets for a given area def.

    Xarrays resampled to area_def
    """
    return get_sectored_read(
        config_dict,
        area_defs,
        area_def_id,
        sector_type,
        reader_plugin,
        reader_kwargs,
        fnames,
        variables,
    )


def get_sectored_read(
    config_dict,
    area_defs,
    area_def_id,
    sector_type,
    reader_plugin,
    reader_kwargs,
    fnames,
    variables,
):
    """Return dictionary of xarray datasets for a given area def.

    Xarrays sectored to area_def
    """
    area_def = area_defs[area_def_id][sector_type]["area_def"]

    if "primary_sector" in config_dict:
        primary_sector_type = area_defs[area_def_id][config_dict["primary_sector"]]
        pad_area_def = primary_sector_type["area_def"]
    else:
        pad_area_def = pad_area_definition(area_def)
    try:
        xobjs = reader_plugin(
            fnames,
            metadata_only=False,
            chans=variables,
            area_def=pad_area_def,
            **reader_kwargs,
        )
    # geostationary satellites fail with IndexError when the area_def does not intersect
    # the data.  Just skip those.  We need a better method for handling this generally,
    # but for now skip IndexErrors.
    except IndexError as resp:
        LOG.error("%s SKIPPING no coverage for %s", resp, area_def)
        return {}
    return xobjs


def get_area_def_list_from_dict(area_defs):
    """Get a list of actual area_defs from full dictionary.

    Dict returned from get_area_defs_from_available_sectors
    """
    list_area_defs = []
    for area_def_id in area_defs:
        for sector_type in area_defs[area_def_id]:
            for ad in area_defs[area_def_id][sector_type]:
                list_area_defs += [area_defs[area_def_id][sector_type]["area_def"]]
    return list_area_defs


def set_comparison_path(output_dict, product_name, output_type, command_line_args=None):
    """Replace variables specified by <varname> in compare_path.

    Parameters
    ----------
    config : dict
        Dictionary of output specifications, containing key "compare_path"
    product_name : str
        Current requested product name, all instances of
        <product> in compare_path replaced with product_name argument
    output_type : str
        Current requested output type, all instances of
        <output> in compare_path replaced with output argument

    Returns
    -------
    str
        Return a single string with the fully specified comparison path for
        current product
    """
    compare_path = None
    if command_line_args is not None and command_line_args["compare_path"] is not None:
        compare_path = command_line_args["compare_path"]

    # If this config has a compare_path specified, replace variables appropriately
    if "compare_path" in output_dict or compare_path is not None:
        if "compare_outputs_module" in output_dict:
            compare_outputs_module = output_dict["compare_outputs_module"]
        else:
            compare_outputs_module = "compare_outputs"

        if compare_path is None:
            compare_path = output_dict["compare_path"]

        cpath = (
            compare_path.replace("<product>", product_name)
            .replace("<procflow>", "config_based")
            .replace("<output>", output_type)
        )
    # If there is no comparison specified, identify as "no_comparison"
    else:
        cpath = "no_comparison"
        compare_outputs_module = "no_compare_outputs_module"

    return cpath, compare_outputs_module


def initialize_final_products(final_products, cpath, cmodule):
    """Initialize the final_products dictionary with cpath dict key if needed.

    Parameters
    ----------
    final_products : dict
        Dictionary of final products, with keys of final required "compare_path"
        Products with no compare_path specified are stored with the key
        "no_comparison"
    cpath : str
        Key to add to final_products dictionary

    Returns
    -------
    dict
        Return final_products dictionary, updated with current "cpath" key:
        final_products[cpath]['files'] = <list_of_files_in_given_cpath>
    """
    if cpath not in final_products:
        final_products[cpath] = {}
        # This is where we store all the files
        final_products[cpath]["files"] = []
        final_products[cpath]["database writes"] = []
        final_products[cpath]["compare_outputs_module"] = cmodule

    return final_products


def process_unsectored_data_outputs(
    final_products,
    available_outputs_dict,
    available_sectors_dict,
    xobjs,
    variables,
    command_line_args=None,
    write_to_product_db=False,
):
    """Process unsectored data output.

    Loop through all possible outputs, identifying output types that require
    unsectored data output. Produce all required unsectored data output,
    update final_products dictionary accordingly, and
    return final_products dictionary with the new unsectored outputs.

    Parameters
    ----------
    final_products : dict
        Dictionary of final products, with keys of final required "compare_path"
        Products with no compare_path specified are stored with the key
        "no_comparison"
    available_outputs_dict : dict
        Dictionary of all available output product specifications
    available_sectors_dict : dict
        Dictionary of available sector types - we are looking for available
        sectors that contain the "unsectored" keyword.
    xobjs : dict
        Dictionary of xarray datasets, for use in producing unsectored output
        formats
    variables : list
        List of strings of required variables in the given product.

    Returns
    -------
    dict
        Return final_products dictionary, updated with current "cpath" key:
        final_products[cpath]['files'] = <list_of_files_in_given_cpath>
    """
    # These are the different sectors, one for each method of reprojecting or
    # sectoring or resampling the data
    for sector_type in available_sectors_dict:
        # We are looking for a sector_type that has the keyword "unsectored" meaning we
        # want to process the dat before doing anything else to it
        if (
            "unsectored" in available_sectors_dict[sector_type]
            and available_sectors_dict[sector_type]["unsectored"]
        ):
            # Once we've found an "unsectored" data type, we will look for all the
            # output_types in "available_outputs_dict" that use that sector_type
            for output_type in available_outputs_dict:
                output_dict = available_outputs_dict[output_type]
                output_dict = update_output_dict_from_command_line_args(
                    output_dict, command_line_args
                )
                if output_dict["requested_sector_type"] == sector_type:
                    # Now we will produce all of the individual products for the given
                    # output_type/sector_type
                    for product_name in output_dict["product_names"]:
                        # This grabs the compare_path that was requested in the YAML
                        # config, and replaces all instances of <product> with
                        # product_name and all instances of <output> with output_type
                        cpath, cmodule = set_comparison_path(
                            output_dict, product_name, output_type, command_line_args
                        )
                        # This adds "cpath" to the final_products dictionary, if
                        # necessary
                        final_products = initialize_final_products(
                            final_products, cpath, cmodule
                        )
                        final_products[cpath]["compare_outputs_module"] = cmodule

                        # This actually produces all the required output files for the
                        # current produsct
                        prod_plugin = products.get_plugin(
                            xobjs["METADATA"].source_name,
                            product_name,
                            output_dict.get("product_spec_override"),
                        )
                        out = process_xarray_dict_to_output_format(
                            xobjs, variables, prod_plugin, output_dict
                        )

                        # Add them to the final_products dictionary - comparisons happen
                        # at the end.
                        final_products[cpath]["files"] += out
                        if write_to_product_db:
                            for fprod in out.keys():
                                product_added = write_to_database(
                                    fprod,
                                    product_name,
                                    xobjs,
                                    available_sectors_dict,
                                    output_dict,
                                )
                                final_products[cpath]["database writes"] += [
                                    product_added
                                ]
    return final_products


def requires_bg(available_outputs_dict, sector_type):
    """Check if current sector requires background imagery.

    Check if a given sector_type is requested for any product_types that also
    require background imagery.

    Parameters
    ----------
    available_outputs_dict : dict
        Dictionary of all requested output_types (specified in YAML config)
    sector_type : str
        sector_type to determine if any output_types that require background
        imagery also request the passed sector_type

    Returns
    -------
    bool
        * True if any output_types that require background imagery require
          the passed "sector_type"
        * False if no output_types require both background imagery and the
          passed "sector_type"
    """
    # Check each output_type in the full config_dict
    for output_type in available_outputs_dict:
        # If the current output_type has an entry for "background_products" that means
        # it requires background imagery If the current output_type also requested the
        # passed "sector_type", then return True.
        if (
            "background_products" in available_outputs_dict[output_type]
            and available_outputs_dict[output_type]["requested_sector_type"]
            == sector_type
        ):
            return True
    # If no output_types required both background_products and the passed
    # "sector_type" then return False
    return False


def is_required_sector_type(available_outputs_dict, sector_type):
    """Check if current sector is required for any outputs.

    Check if a given sector_type is required for any currently requested
    output_types

    Parameters
    ----------
    available_outputs_dict : dict
        Dictionary of all requested output_types (specified in YAML config)
    sector_type : str
        Determine if any output_types require the currently requested
        "sector_type"

    Returns
    -------
    bool
        * True if any output_types require the passed "sector_type"
        * False if no output_types require the passed "sector_type"
    """
    # Go through each output_type currently requested in the YAML config file
    for output_type in available_outputs_dict.keys():
        # If the passed sector_type is requested for any output_type in the YAML
        # config, return True
        if sector_type == available_outputs_dict[output_type]["requested_sector_type"]:
            return True
    # If the passed sector_type is not needed in the YAML config, return False
    return False


def get_config_dict(config_yaml_file):
    """Populate the full config dictionary from a given YAML config file.

    Includes both sector and output specifications.

    Parameters
    ----------
    config_yaml_file : str
        Full path to YAML config file, containing sector and output
        specifications. YAML config files support environment variables in
        entries flagged with !ENV

    Returns
    -------
    dict
        Return dictionary of both sector and output specifications,
        as found in config_yaml_file. The output dictionary references the
        "sector_types" found in the available_sectors dictionary,
        each output_type requests a specific "sector_type" to be used for
        processing.
    """
    # import yaml
    # with open(config_yaml_file, 'r') as f:
    #     config_dict = yaml.safe_load(f)
    # return config_dict
    # This allows environment variables specified by !ENV ${ENVVARNAME}
    from pyaml_env import parse_config

    return parse_config(config_yaml_file)


def get_variables_from_available_outputs_dict(
    available_outputs_dict, source_name, sector_types=None
):
    """Get required variables for all outputs for a given "source_name".

    Outputs specified within the YAML config.

    Parameters
    ----------
    available_outputs_dict : dict
        Dictionary of all requested output_types (specified in YAML config)
    source_name : str
        Find all required variables for the passed "source_name"
    sector_types : list, default=None
        if sector_types list of strings is passed, only include
        output_types that require one of the passed "sector_types"

    Returns
    -------
    list
        List of all required variables for all output products for the given
        source_name
    """
    variables = []
    # Loop through all possible output types
    for output_type in available_outputs_dict:
        # If we requested specific sector_types, only include output_types that
        # require that sector_type
        if (
            sector_types is None
            or available_outputs_dict[output_type]["requested_sector_type"]
            in sector_types
        ):
            # Loop through all products for the given output_type
            for product_name in available_outputs_dict[output_type]["product_names"]:
                # Add all required variables for the current product and source to the
                # list
                prod_plugin = products.get_plugin(
                    source_name,
                    product_name,
                    available_outputs_dict[output_type].get("product_spec_override"),
                )
                variables += get_required_variables(prod_plugin)
    # Return list of all required variables
    return list(set(variables))


def get_area_defs_from_available_sectors(
    available_sectors_dict, command_line_args, xobjs, variables
):
    """Get all required area_defs for the given set of parameters.

    YAML config parameters (config_dict), command_line_args,
    xobjs, and required variables. Command line args override config
    specifications.

    Parameters
    ----------
    available_sectors_dict : dict
        Dictionary of all requested sector_types (specified in YAML config)
    command_line_args : dict
        Dictionary of command line arguments - any command line argument that is
        also a key in available_sectors_dict[<sector_type>] will replace the
        value in the available_sectors_dict[<sector_type>]
    xobjs : dict
        Dictionary of xarray datasets, used in determining start/end time of
        data files for identifying dynamic sectors
    variables : list
        List of required variables, for determining center coverage for TCs

    Returns
    -------
    dict
        Dictionary of required area_defs, with area_def.name as the dictionary
        keys. Based on YAML config-specified available_sectors, and command
        line args

    Notes
    -----
    * Each area_def.name key has one or more "sector_types" associated with it.
    * Each sector_type dictionary contains the actual "requested_sector_dict"
      from the YAML config, and the actual AreaDefinition object that was
      returned.

        * ``area_defs[area_def.name][sector_type]['requested_sector_dict']``
        * ``area_defs[area_def.name][sector_type]['area_def']``
    """
    area_defs = {}

    # Loop through all available sector types
    for sector_type in available_sectors_dict:
        sector_dict = available_sectors_dict[sector_type].copy()

        # If the current sector_type is "unsectored" skip it, because it has no
        # associated sector information
        if "unsectored" in sector_dict and sector_dict["unsectored"]:
            continue

        # command_line_args take priority over config args - if someone passes something
        # in explicitly, it will be used rather than config "default"
        for argname in command_line_args.keys():
            if command_line_args[argname]:
                sector_dict[argname] = command_line_args[argname]

        # Double check if tcdb should be set to false
        if sector_dict.get("trackfiles"):
            sector_dict["tcdb"] = False

        # This is the standard "get_area_defs_from_command_line_args", YAML config
        # specified sector information matches the command line specified sector
        # information
        curr_area_defs = get_area_defs_from_command_line_args(
            sector_dict, xobjs, variables, filter_time=True
        )

        # Loop through the list of area_defs returned by
        # get_area_defs_from_command_line_args, we are going to organize them
        for area_def in curr_area_defs:
            # Use description or name so it includes synoptic time
            # We want each sectorname as a key in the dictionary, with one or more
            # sector_types attached to it. Ie, we may have different sizes/resolutions
            # for the same region, so we want a dictionary of sector_types
            # within the dictionary of area_defs
            if area_def.name not in area_defs:
                # Store the actual sector_dict and area_def in the dictionary
                area_defs[area_def.name] = {
                    sector_type: {
                        "requested_sector_dict": sector_dict,
                        "area_def": area_def,
                    }
                }
            else:
                area_defs[area_def.name][sector_type] = {
                    "requested_sector_dict": sector_dict,
                    "area_def": area_def,
                }
    return area_defs


def call(fnames, command_line_args=None):
    """Workflow for efficiently running all required outputs.

    Includes all sectors and products specified in a YAML output config file.
    Specified via a YAML config file

    Parameters
    ----------
    fnames : list
        List of strings specifying full paths to input file names to process
    command_line_args : dict
        dictionary of command line arguments

    Returns
    -------
    int
        0 for successful completion,
        non-zero for error (incorrect comparison, or failed run)
    """
    from datetime import datetime

    process_datetimes = {}
    process_datetimes["overall_start"] = datetime.utcnow()
    final_products = {}
    removed_products = []
    saved_products = []
    num_jobs = 0

    from geoips.commandline.args import check_command_line_args

    # These args should always be checked
    check_args = [
        "output_config",
        "reader_kwargs",
        "fuse_files",
        "fuse_reader",
        "fuse_reader_kwargs",
        "fuse_resampled_read",
        "fuse_product",
        "filename_formatter_kwargs",
        "metadata_filename_formatter_kwargs",
        "tcdb_sector_list",
        "window_start_time",
        "window_end_time",
        "product_db",
        "product_db_writer_override",
        "output_file_list_fname",
    ]

    check_command_line_args(check_args, command_line_args)
    config_dict = get_config_dict(command_line_args["output_config"])

    if not fnames and "filenames" in config_dict:
        fnames = glob(config_dict["filenames"])

    if not fnames:
        raise IOError(
            "No files found on disk. "
            "Please include valid files either at the command line, "
            "or within the YAML config"
        )
    for fname in fnames:
        if not exists(fname):
            raise IOError(
                f"File '{fname}' not found. "
                "Please include valid files either at the command line, "
                "or within the YAML config"
            )

    output_file_list_fname = command_line_args["output_file_list_fname"]
    reader_kwargs = None
    bg_files = None
    bg_product_name = None
    bg_reader_kwargs = None
    bg_resampled_read = False
    # bg_self_register_dataset = None
    # bg_self_register_source = None

    # 1. get reader_kwargs from command line if specified command line
    # 2. next get reader_kwargs from YAML config_dict if specified within YAML config
    # 3. Finally, if not specified elsewhere, default reader_kwargs to {}
    if command_line_args.get("reader_kwargs"):
        reader_kwargs = command_line_args["reader_kwargs"]
    elif "reader_kwargs" in config_dict:
        reader_kwargs = config_dict.get("reader_kwargs")
    if not reader_kwargs:
        reader_kwargs = {}
    if command_line_args.get("no_presectoring") is not None:
        presector_data = not command_line_args["no_presectoring"]
    else:
        presector_data = True

    # Allow pulling command line arguments from either command line or YAML config.
    # Command line arguments override YAML config

    window_start_time = None
    window_end_time = None
    if command_line_args.get("window_start_time") is not None:
        window_start_time = command_line_args["window_start_time"]
    elif "window_start_time" in config_dict:
        window_start_time = config_dict["window_start_time"]

    if command_line_args.get("window_end_time") is not None:
        window_end_time = command_line_args["window_end_time"]
    elif "window_end_time" in config_dict:
        window_end_time = config_dict["window_end_time"]

    if command_line_args.get("fuse_files") is not None:
        bg_files = command_line_args["fuse_files"][0]
    elif "fuse_files" in config_dict:
        bg_files = glob(config_dict["fuse_files"])

    if command_line_args.get("fuse_reader") is not None:
        bg_reader_plugin = readers.get_plugin(command_line_args["fuse_reader"][0])
    elif "fuse_reader" in config_dict:
        bg_reader_plugin = readers.get_plugin(config_dict["fuse_reader"])

    # 1. get bg_reader_kwargs from command line if specified command line
    # 2. next get bg_reader_kwargs from YAML config_dict if specified within YAML
    # 3. Finally, if not specified elsewhere, default bg_reader_kwargs to {}
    if command_line_args.get("fuse_reader_kwargs") is not None:
        bg_reader_kwargs = command_line_args["fuse_reader_kwargs"][0]
    elif "fuse_reader_kwargs" in config_dict:
        bg_reader_kwargs = config_dict["fuse_reader_kwargs"]
    if not bg_reader_kwargs:
        bg_reader_kwargs = {}

    if command_line_args.get("fuse_product") is not None:
        bg_product_name = command_line_args["fuse_product"][0]
    elif "fuse_product" in config_dict:
        bg_product_name = config_dict["fuse_product"]

    if command_line_args.get("fuse_resampled_read") is not None:
        bg_resampled_read = command_line_args["fuse_resampled_read"][0]
    elif "fuse_resampled_read" in config_dict:
        bg_resampled_read = config_dict["fuse_resampled_read"]

    # if command_line_args.get("fuse_self_register_dataset") is not None:
    #     bg_self_register_dataset = command_line_args["fuse_self_register_dataset"][0]
    # elif "fuse_self_register_dataset" in config_dict:
    #     bg_self_register_dataset = config_dict["fuse_self_register_dataset"]

    # if command_line_args.get("fuse_self_register_source") is not None:
    #     bg_self_register_source = command_line_args["fuse_self_register_source"][0]
    # elif "fuse_self_register_source" in config_dict:
    #     bg_self_register_source = config_dict["fuse_self_register_source"]

    if command_line_args.get("product_db"):
        product_db = command_line_args["product_db"]
    elif "product_db" in config_dict:
        product_db = config_dict["product_db"]

    else:
        product_db = False

    if command_line_args.get("product_db_writer_override"):
        for sector, database_writer in command_line_args[
            "product_db_writer_override"
        ].items():
            config_dict["available_sectors"][sector] = database_writer

    if bg_files is not None:
        LOG.interactive(
            "Reading background datasets using reader '%s'...", bg_reader_plugin.name
        )
        bg_xobjs = bg_reader_plugin(bg_files, metadata_only=True, **bg_reader_kwargs)
        prod_plugin = products.get_plugin(
            bg_xobjs["METADATA"].source_name,
            bg_product_name,
        )
        bg_variables = get_required_variables(prod_plugin)

    if product_db:
        from os import getenv

        if not getenv("GEOIPS_DB_USER") or not getenv("GEOIPS_DB_PASS"):
            raise ValueError("Need to set both $GEOIPS_DB_USER and $GEOIPS_DB_PASS")

    print_mem_usage("MEMUSG", verbose=False)
    reader_plugin = readers.get_plugin(config_dict["reader_name"])
    LOG.interactive(
        "Reading metadata from datasets using reader '%s'...", reader_plugin.name
    )
    xobjs = reader_plugin(fnames, metadata_only=True, **reader_kwargs)
    source_name = xobjs["METADATA"].source_name

    if not produce_current_time(config_dict, xobjs["METADATA"], output_dict_keys=None):
        LOG.interactive("SKIPPING ALL PROCESSING no products required for current time")
        return 0

    print_mem_usage("MEMUSG", verbose=False)
    variables = get_variables_from_available_outputs_dict(
        config_dict["outputs"], source_name
    )

    # If this config does not perform a sectored read, just read all the data now
    # Otherwise data will be read within the area_def loop
    sectored_read = False
    resampled_read = False
    if "sectored_read" in config_dict and config_dict["sectored_read"]:
        sectored_read = True
    if "resampled_read" in config_dict and config_dict["resampled_read"]:
        resampled_read = True

    if not resampled_read and not sectored_read:
        print_mem_usage("MEMUSG", verbose=False)
        LOG.interactive("Reading full dataset using reader '%s'...", reader_plugin.name)
        xobjs = reader_plugin(
            fnames, metadata_only=False, chans=variables, **reader_kwargs
        )

    print_mem_usage("MEMUSG", verbose=False)

    # command_line_args take priority over config args - if someone passes something in
    # explicitly, it will be used rather than config "default"
    area_defs = get_area_defs_from_available_sectors(
        config_dict["available_sectors"], command_line_args, xobjs, variables
    )

    # Check if we have any required unsectored outputs, if so produce here,
    # then continue
    LOG.interactive("\n\n\n\nNEXT Processing any unsectored data outputs...\n\n")
    final_products = process_unsectored_data_outputs(
        final_products,
        config_dict["outputs"],
        config_dict["available_sectors"],
        xobjs,
        variables,
        command_line_args,
        write_to_product_db=product_db,
    )
    print_mem_usage("MEMUSG", verbose=False)

    list_area_defs = get_area_def_list_from_dict(area_defs)

    LOG.interactive("\n\n\n\nNEXT Processing any sectored data outputs...\n\n")
    area_def_num = 0
    # Loop through each template - register the data once for each template/area_def
    for area_def_id in area_defs:
        area_def_num = area_def_num + 1

        LOG.interactive(
            "\n\n\n\nNEXT area def id: %s (%s of %s)\n\n",
            area_def_id,
            area_def_num,
            len(area_defs),
        )

        bg_alg_xarrays = {}
        # Loop through each sector_type - each sector_type is a different projection /
        # shape / resolution, so we only want to reproject once for each sector_type
        sector_type_num = 0
        for sector_type in area_defs[area_def_id]:
            sector_type_num = sector_type_num + 1

            curr_variables = get_variables_from_available_outputs_dict(
                config_dict["outputs"], source_name, sector_types=[sector_type]
            )

            if not curr_variables:
                LOG.info("No input variables for sector type: %s", sector_type)
                continue

            # If we read separately for each sector (geostationary), then must set
            # xobjs within area_def loop
            if sectored_read:
                print_mem_usage("MEMUSG", verbose=False)
                # This will return potentially multiple sectored datasets of different
                # shapes/resolutions. Note currently get_sectored_read and
                # get_resampled_read are identical, because we have no
                # sectored_read based readers.
                LOG.interactive(
                    "Performing sectored read with reader '%s'", reader_plugin.name
                )
                xobjs = get_sectored_read(
                    config_dict,
                    area_defs,
                    area_def_id,
                    sector_type,
                    reader_plugin,
                    reader_kwargs,
                    fnames,
                    curr_variables,
                )
                if not xobjs:
                    continue
            if resampled_read:
                print_mem_usage("MEMUSG", verbose=False)
                # This will return one resampled dataset
                # Note currently get_sectored_read and get_resampled_read are identical,
                # because we have no sectored_read based readers.
                LOG.interactive(
                    "Performing resampled read with reader '%s'", reader_plugin.name
                )
                xobjs = get_resampled_read(
                    config_dict,
                    area_defs,
                    area_def_id,
                    sector_type,
                    reader_plugin,
                    reader_kwargs,
                    fnames,
                    curr_variables,
                )
                if not xobjs:
                    continue

            print_mem_usage("MEMUSG", verbose=False)
            area_def = area_defs[area_def_id][sector_type]["area_def"]

            # Padded region to ensure we have enough data for recentering, etc.
            # Do NOT pad if we are using a reader_defined or self_register area_def -
            # that indicates we are going to use all of the data we have, so we
            # will not sector
            if area_def.sector_type not in ["reader_defined", "self_register"]:
                pad_area_def = pad_area_definition(
                    area_def, xobjs["METADATA"].source_name
                )
            else:
                pad_area_def = area_def

            print_mem_usage("MEMUSG", verbose=False)
            # See if this sector_type is used at all for product output, if not, skip
            # it.
            if not is_required_sector_type(config_dict["outputs"], sector_type):
                LOG.interactive(
                    "\n\n\nSKIPPING sector type: %s, not required for outputs %s",
                    sector_type,
                    config_dict["outputs"].keys(),
                )
                continue
            requested_sector_dict = area_defs[area_def_id][sector_type][
                "requested_sector_dict"
            ]

            LOG.interactive(
                "\n\n\n\nNEXT area def id: %s (%s of %s), "
                "sector_type: %s (%s of %s)\n\n",
                area_def_id,
                area_def_num,
                len(area_defs),
                sector_type,
                sector_type_num,
                len(area_defs[area_def_id]),
            )

            LOG.info("\n\n\n\narea definition: %s", area_def)
            LOG.info("\n\n\n\nrequested sector dict: %s\n\n\n\n", requested_sector_dict)

            # Reduce hours before and after sector time, so we don't get both overpasses
            # from a single. Sector to pad_area_def so we have enough data for
            # recentering.
            process_datetimes[area_def.area_id] = {}
            process_datetimes[area_def.area_id]["start"] = datetime.utcnow()

            # Make sure we grab some around the required data.
            # Do NOT sector if we are using a reader_defined or self_register area_def -
            # that indicates we are going to use all of the data we have, so we will not
            # sector
            if area_def.sector_type not in ["reader_defined", "self_register"]:
                if presector_data:
                    LOG.interactive("Sectoring xarrays, drop=True")
                    # window start/end time override hours before/after sector time.
                    pad_sect_xarrays = sector_xarrays(
                        xobjs,
                        pad_area_def,
                        varlist=curr_variables,
                        hours_before_sector_time=6,
                        hours_after_sector_time=9,
                        drop=True,
                        window_start_time=window_start_time,
                        window_end_time=window_end_time,
                    )
                else:
                    pad_sect_xarrays = xobjs
            else:
                pad_sect_xarrays = xobjs

            print_mem_usage("MEMUSG", verbose=False)

            # See what variables are left after sectoring (could lose some due to
            # day/night)
            all_vars = []
            for key, xobj in pad_sect_xarrays.items():
                # Double check the xarray object actually contains data
                for var in list(xobj.variables.keys()):
                    if xobj[var].count() > 0:
                        all_vars.append(var)

            # If we didn't get any data, continue to the next sector_type
            if len(pad_sect_xarrays) == 0:
                LOG.interactive(
                    "SKIPPING no pad_area_def pad_sect_xarrays returned for %s",
                    area_def.name,
                )
                continue

            # Now we check to see if the current area_def is the closest one to
            # the dynamic time, if appropriate. We could end up with multiple
            # area_defs for a single dynamic sector, and we can't truly test to see
            # how close each one is to the actual data until we sector it...
            # So, check now to see if any of the area_defs in list_area_defs is
            # closer than pad_area_def
            if not verify_area_def(
                list_area_defs,
                pad_area_def,
                pad_sect_xarrays["METADATA"].start_datetime,
                pad_sect_xarrays["METADATA"].end_datetime,
            ):
                LOG.interactive(
                    "SKIPPING duplicate area_def, out of time range, for %s",
                    area_def.name,
                )
                continue

            # Check the config dict to see if this sector_type requests background
            # products
            if bg_files and requires_bg(config_dict["outputs"], sector_type):
                # If we haven't created the bg_alg_xarray for the current sector_type
                # yet, process it and add to the dictionary
                if sector_type not in bg_alg_xarrays:
                    print_mem_usage("MEMUSG", verbose=False)
                    bg_pad_sect_xarrays = None
                    try:
                        LOG.interactive(
                            "Reading background data with reader '%s'",
                            bg_reader_plugin.name,
                        )
                        bg_xobjs = bg_reader_plugin(
                            bg_files,
                            metadata_only=False,
                            chans=bg_variables,
                            area_def=pad_area_def,
                        )
                        if presector_data:
                            LOG.interactive("Sectoring background data")
                            # window start/end time override hours before/after sector
                            # time.
                            bg_pad_sect_xarrays = sector_xarrays(
                                bg_xobjs,
                                pad_area_def,
                                varlist=bg_variables,
                                hours_before_sector_time=6,
                                hours_after_sector_time=9,
                                drop=True,
                                window_start_time=window_start_time,
                                window_end_time=window_end_time,
                            )
                        else:
                            bg_pad_sect_xarrays = bg_xobjs
                    except CoverageError as resp:
                        LOG.warning(
                            f"{resp} SKIPPING - NO COVERAGE FOR BACKGROUND DATA"
                        )
                    # Only attempt to get bg xarrays if they weren't sectored away to
                    # nothing.
                    bg_prod_plugin = products.get_plugin(
                        bg_xobjs["METADATA"].source_name, bg_product_name
                    )
                    if bg_pad_sect_xarrays:
                        bg_alg_xarrays[sector_type] = get_bg_xarray(
                            bg_pad_sect_xarrays,
                            area_def,
                            bg_prod_plugin,
                            resampled_read=bg_resampled_read,
                        )
            print_mem_usage("MEMUSG", verbose=False)

            # Must adjust the area definition AFTER sectoring xarray (to get valid
            # start/end time
            sector_adjuster = None
            if "sector_adjuster" in config_dict["available_sectors"][sector_type]:
                sector_adjuster = config_dict["available_sectors"][sector_type][
                    "sector_adjuster"
                ]

            adadj_fnames = []
            if sector_adjuster:
                LOG.info("\n\n\n\nAdjusting Area Definition: %s", sector_adjuster)
                LOG.info(
                    "\n\n\n\nBEFORE ADJUSTMENT area definition: %s\n\n\n\n", area_def
                )
                sect_adj_plugin = sector_adjusters.get_plugin(sector_adjuster)
                # Use normal size sectored xarray when running sector_adjuster, not
                # padded. Center time (mintime + (maxtime - mintime)/2) is very slightly
                # different for different size sectored arrays, so for consistency if we
                # change padding amounts, use the fully sectored array for adjusting the
                # area_def.
                if pad_sect_xarrays["METADATA"].source_name not in ["amsu-b", "mhs"]:
                    # The exact sectored arrays, without padding.
                    # Note this must be sectored both before AND after sector_adjuster -
                    # to ensure we both have an accurate center time for adjustments,
                    # and so we get all of the data.
                    if area_def.sector_type not in ["reader_defined", "self_register"]:
                        LOG.interactive(
                            "Sectoring xarrays for sector adjuster '%s'",
                            sector_adjuster,
                        )
                        if presector_data:
                            # window start/end time override hours before/after sector
                            # time.
                            sect_xarrays = sector_xarrays(
                                pad_sect_xarrays,
                                area_def,
                                varlist=curr_variables,
                                hours_before_sector_time=6,
                                hours_after_sector_time=9,
                                drop=True,
                                window_start_time=window_start_time,
                                window_end_time=window_end_time,
                            )
                        else:
                            sect_xarrays = pad_sect_xarrays
                    else:
                        sect_xarrays = pad_sect_xarrays
                    print_mem_usage("MEMUSG", verbose=False)
                    # If we didn't get any data, continue to the next sector_type
                    # Note we can have coverage for pad_sect_xarrays, but none for
                    # sect_xarrays - ensure we also skip no coverage for sect_xarrays
                    if len(sect_xarrays) == 0:
                        LOG.interactive(
                            "SKIPPING no area_def sect_xarrays returned for %s",
                            area_def.name,
                        )
                        continue
                    if (
                        sect_adj_plugin.family
                        == "list_xarray_list_variables_to_area_def_out_fnames"
                    ):
                        LOG.interactive("Adjusting sector with '%s'", sector_adjuster)
                        area_def, adadj_fnames = sect_adj_plugin(
                            list(sect_xarrays.values()),
                            area_def,
                            curr_variables,
                            config_dict["available_sectors"][sector_type][
                                "adjust_variables"
                            ],
                        )
                    else:
                        LOG.interactive("Adjusting sector with '%s'", sector_adjuster)
                        area_def = sect_adj_plugin(
                            list(sect_xarrays.values()),
                            area_def,
                            curr_variables,
                            config_dict["available_sectors"][sector_type][
                                "adjust_variables"
                            ],
                        )
                else:
                    # AMSU-b specifically needs full swath width... Need a way to
                    # generalize this.
                    if (
                        sect_adj_plugin.family
                        == "list_xarray_list_variables_to_area_def_out_fnames"
                    ):
                        LOG.interactive("Adjusting sector with '%s'", sector_adjuster)
                        area_def, adadj_fnames = sect_adj_plugin(
                            list(pad_sect_xarrays.values()),
                            area_def,
                            curr_variables,
                            config_dict["available_sectors"][sector_type][
                                "adjust_variables"
                            ],
                        )
                    else:
                        LOG.interactive("Adjusting sector with '%s'", sector_adjuster)
                        area_def = sect_adj_plugin(
                            list(pad_sect_xarrays.values()),
                            area_def,
                            curr_variables,
                            config_dict["available_sectors"][sector_type][
                                "adjust_variables"
                            ],
                        )

                cpath, cmodule = set_comparison_path(
                    config_dict["available_sectors"][sector_type],
                    product_name="archer",
                    output_type="archer",
                    command_line_args=command_line_args,
                )
                final_products = initialize_final_products(
                    final_products, cpath, cmodule
                )
                final_products[cpath]["compare_outputs_module"] = cmodule
                final_products[cpath]["files"] += adadj_fnames

                LOG.info(
                    "\n\n\n\nAFTER ADJUSTMENT area definition: %s\n\n\n\n", area_def
                )

            print_mem_usage("MEMUSG", verbose=False)
            # The exact sectored arrays, without padding.
            # Note this must be sectored AFTER sector_adjuster - to ensure we get all
            # the data. Do NOT sector if we are using a reader_defined or self_register
            # area_def - that indicates we are going to use all of the data we have, so
            # we will not sector
            if area_def.sector_type not in ["reader_defined", "self_register"]:
                LOG.interactive(
                    "Sectoring self register xarrays for area_def '%s'", area_def.name
                )
                if presector_data:
                    # window start/end time override hours before/after sector time.
                    sect_xarrays = sector_xarrays(
                        pad_sect_xarrays,
                        area_def,
                        varlist=curr_variables,
                        hours_before_sector_time=6,
                        hours_after_sector_time=9,
                        drop=True,
                        window_start_time=window_start_time,
                        window_end_time=window_end_time,
                    )
                else:
                    sect_xarrays = pad_sect_xarrays
            else:
                sect_xarrays = pad_sect_xarrays

            print_mem_usage("MEMUSG", verbose=False)
            # If we didn't get any data, continue to the next sector_type
            # Note we can have coverage for pad_sect_xarrays, but none for sect_xarrays
            # - ensure we also skip no coverage for sect_xarrays
            if len(sect_xarrays) == 0:
                LOG.interactive(
                    "SKIPPING no area_def sect_xarrays returned for %s", area_def.name
                )
                continue

            # Keep track of the applied algorithms in order to prevent redundant
            # algorithm application
            pad_alg_xarrays = {}
            alg_xarrays = {}
            output_num = 0
            required_outputs = get_required_outputs(config_dict, sector_type)
            for output_type, output_dict in required_outputs.items():
                if not produce_current_time(
                    config_dict, xobjs["METADATA"], output_dict_keys=[output_type]
                ):
                    LOG.interactive(
                        """SKIPPING PROCESSING no products required for output_type {0}
                        at current time""".format(
                            output_type,
                        )
                    )
                    continue
                output_dict = update_output_dict_from_command_line_args(
                    output_dict, command_line_args
                )

                output_num = output_num + 1

                LOG.interactive(
                    "\n\n\n\nNEXT area def id: %s (%s of %s), "
                    "sector_type: %s (%s of %s), "
                    "output_type: %s (%s of %s)\n\n",
                    area_def_id,
                    area_def_num,
                    len(area_defs),
                    sector_type,
                    sector_type_num,
                    len(area_defs[area_def_id]),
                    output_type,
                    output_num,
                    len(required_outputs.keys()),
                )

                LOG.info("\n\n\n\narea definition: %s", area_def)

                product_num = 0
                for product_name in output_dict["product_names"]:
                    product_num = product_num + 1
                    prod_plugin = products.get_plugin(
                        pad_sect_xarrays["METADATA"].source_name,
                        product_name,
                        output_dict.get("product_spec_override"),
                    )
                    LOG.info("\n\n\n\nAll area_def_ids: %s", area_defs.keys())
                    LOG.info(
                        "\n\n\n\nAll sector_types: %s", area_defs[area_def_id].keys()
                    )
                    LOG.info(
                        "\n\n\n\nAll output_types: %s", config_dict["outputs"].keys()
                    )
                    LOG.info(
                        "\n\n\n\nAll product_names: %s", output_dict["product_names"]
                    )
                    LOG.info("\n\n\n\nCurrent area definition: %s", area_def)

                    LOG.interactive(
                        "\n\n\n\nNEXT area def id: %s (%s of %s), "
                        "sector_type: %s (%s of %s), "
                        "output_type: %s (%s of %s), "
                        "product_name: %s (%s of %s)\n\n",
                        area_def_id,
                        area_def_num,
                        len(area_defs),
                        sector_type,
                        sector_type_num,
                        len(area_defs[area_def_id]),
                        output_type,
                        output_num,
                        len(required_outputs.keys()),
                        product_name,
                        product_num,
                        len(output_dict["product_names"]),
                    )

                    LOG.info(
                        """\n\n\n\nAll current output_types for sector_type {0}:
                        {1}\n\n\n\n""".format(
                            sector_type,
                            required_outputs.keys(),
                        )
                    )

                    product_variables = get_required_variables(prod_plugin)

                    # Make sure we still have all the required variables after sectoring
                    if not set(product_variables).issubset(all_vars):
                        LOG.interactive(
                            "SKIPPING product %s missing variables %s",
                            product_name,
                            set(product_variables).difference(all_vars),
                        )
                        continue
                    cpath, cmodule = set_comparison_path(
                        output_dict, product_name, output_type, command_line_args
                    )
                    final_products = initialize_final_products(
                        final_products, cpath, cmodule
                    )
                    final_products[cpath]["compare_outputs_module"] = cmodule

                    # Produce sectored data output
                    LOG.interactive(
                        "Processing sectored data products for product '%s'",
                        prod_plugin.name,
                    )
                    curr_output_products = process_sectored_data_output(
                        pad_sect_xarrays,
                        product_variables,
                        prod_plugin,
                        output_dict,
                        area_def=area_def,
                    )
                    # If the current product required sectored data processing, skip the
                    # rest of the loop
                    if curr_output_products:
                        final_products[cpath]["files"] += curr_output_products
                        if product_db:
                            for fprod in curr_output_products:
                                product_added = write_to_database(
                                    fprod,
                                    product_name,
                                    pad_sect_xarrays["METADATA"],
                                    config_dict["available_sectors"],
                                    output_dict,
                                    area_def=area_def,
                                )
                                if product_added is not None:
                                    final_products[cpath]["database writes"] += [
                                        product_added
                                    ]
                        continue

                    output_formatter = get_output_formatter(output_dict)
                    output_fmt_plugin = output_formatters.get_plugin(output_formatter)

                    if output_fmt_plugin.family == "xarray_data":
                        # If we're saving out intermediate data file, write out
                        # pad_area_def.
                        if product_name not in pad_alg_xarrays:
                            pad_alg_xarrays[product_name] = get_alg_xarray(
                                pad_sect_xarrays,
                                pad_area_def,
                                prod_plugin,
                                resampled_read=resampled_read,
                                variable_names=product_variables,
                                window_start_time=window_start_time,
                                window_end_time=window_end_time,
                            )
                        alg_xarray = pad_alg_xarrays[product_name]
                    elif area_def.sector_type in ["reader_defined", "self_register"]:
                        alg_xarray = get_alg_xarray(
                            pad_sect_xarrays,
                            pad_area_def,
                            prod_plugin,
                            resector=False,
                            resampled_read=resampled_read,
                            variable_names=product_variables,
                            window_start_time=window_start_time,
                            window_end_time=window_end_time,
                        )
                    else:
                        # If we're writing out an image, cut it down to the desired
                        # size.
                        if product_name not in alg_xarrays:
                            alg_xarrays[product_name] = get_alg_xarray(
                                sect_xarrays,
                                area_def,
                                prod_plugin,
                                resampled_read=resampled_read,
                                variable_names=product_variables,
                                window_start_time=window_start_time,
                                window_end_time=window_end_time,
                            )
                        alg_xarray = alg_xarrays[product_name]

                    covg_plugin = get_covg_from_product(
                        prod_plugin,
                        covg_field="image_production_coverage_checker",
                    )
                    covg_args = get_covg_args_from_product(
                        prod_plugin,
                        covg_field="image_production_coverage_checker",
                    )
                    covg = covg_plugin(
                        alg_xarray, prod_plugin.name, area_def, **covg_args
                    )

                    fname_covg_plugin = get_covg_from_product(
                        prod_plugin,
                        covg_field="filename_coverage_checker",
                    )
                    fname_covg_args = get_covg_args_from_product(
                        prod_plugin,
                        covg_field="filename_coverage_checker",
                    )
                    fname_covg = fname_covg_plugin(
                        alg_xarray, prod_plugin.name, area_def, **fname_covg_args
                    )

                    minimum_coverage = 10
                    config_minimum_coverage = get_minimum_coverage(
                        prod_plugin.name, output_dict
                    )
                    if hasattr(alg_xarray, "minimum_coverage"):
                        minimum_coverage = alg_xarray.minimum_coverage
                    if config_minimum_coverage is not None:
                        minimum_coverage = config_minimum_coverage
                    LOG.interactive(
                        "Required coverage %s for product %s, actual coverage %s",
                        minimum_coverage,
                        product_name,
                        covg,
                    )
                    if covg < minimum_coverage and fname_covg < minimum_coverage:
                        LOG.interactive(
                            "Insufficient coverage %s / %s for data products, SKIPPING",
                            covg,
                            fname_covg,
                        )
                        continue

                    plot_data_kwargs = get_output_formatter_kwargs(
                        output_dict,
                        alg_xarray,
                        area_def,
                        sector_type,
                        bg_files,
                        bg_alg_xarrays,
                        bg_product_name,
                    )

                    if (
                        bg_files
                        and "background_products" in output_dict
                        and sector_type in bg_alg_xarrays
                    ):
                        alg_xarray = combine_filename_extra_fields(
                            bg_alg_xarrays[sector_type], alg_xarray
                        )

                    curr_products = plot_data(
                        output_dict,
                        alg_xarray,
                        area_def,
                        prod_plugin,
                        plot_data_kwargs,
                    )

                    final_products[cpath]["files"] += list(curr_products.keys())

                    if product_db:
                        for fprod in curr_products.keys():
                            product_added = write_to_database(
                                fprod,
                                product_name,
                                alg_xarray,
                                config_dict["available_sectors"],
                                output_dict,
                                coverage=covg,
                                area_def=area_def,
                            )
                            if product_added is not None:
                                final_products[cpath]["database writes"] += [
                                    product_added
                                ]

                    if (
                        "remove_duplicates" in output_dict
                        and output_dict["remove_duplicates"] is not None
                    ):
                        curr_removed_products, curr_saved_products = remove_duplicates(
                            curr_products, remove_files=True
                        )
                        removed_products += curr_removed_products
                        saved_products += curr_saved_products

                    process_datetimes[area_def.area_id]["end"] = datetime.utcnow()
                    num_jobs += 1

    print_mem_usage("MEMUSG", verbose=False)
    process_datetimes["overall_end"] = datetime.utcnow()

    LOG.interactive("\n\n\nProcessing complete! Checking outputs...\n\n\n")

    retval = 0
    failed_compares = {}
    for cpath in final_products:
        if cpath != "no_comparison":
            curr_compare_outputs = find_entry_point(
                "output_comparisons", final_products[cpath]["compare_outputs_module"]
            )
            curr_retval = curr_compare_outputs(cpath, final_products[cpath]["files"])
            retval += curr_retval
            if curr_retval != 0:
                failed_compares[cpath] = curr_retval
        else:
            LOG.info("No comparison specified, not attempting to compare outputs")

    successful_comparison_dirs = 0
    failed_comparison_dirs = 0
    from os.path import basename

    LOG.interactive(
        "\n\n\nThe following products were produced from procflow %s\n\n",
        basename(__file__),
    )
    for cpath in final_products:
        if cpath in failed_compares:
            LOG.interactive(
                "%s FAILED COMPARISONS IN DIR: %s\n", failed_compares[cpath], cpath
            )
            failed_comparison_dirs = failed_comparison_dirs + 1
        elif cpath != "no_comparison":
            LOG.info("SUCCESSFUL COMPARISON DIR: %s\n", cpath)
            successful_comparison_dirs = successful_comparison_dirs + 1
        for filename in final_products[cpath]["files"]:
            LOG.interactive(
                "    \u001b[34mCONFIGSUCCESS\033[0m %s",
                replace_geoips_paths(filename, curly_braces=True),
            )
            if filename in final_products[cpath]["database writes"]:
                LOG.info("    DATABASESUCCESS %s", filename)
        LOG.info("\n")

    for removed_product in removed_products:
        LOG.interactive("    DELETEDPRODUCT %s", removed_product)
        if product_db:
            LOG.info("    FLAGGING as deleted in product database")
            flag_product_as_deleted(removed_product, area_defs)

    if output_file_list_fname:
        LOG.info("Writing successful outputs to %s", output_file_list_fname)
        with open(output_file_list_fname, "w", encoding="utf8") as fobj:
            for cpath in final_products:
                LOG.info("Trying %s", cpath)
                if len(final_products[cpath]["files"]) > 0:
                    LOG.info(
                        "  WRITING %s to output file list, %s products generated",
                        cpath,
                        len(final_products[cpath]["files"]),
                    )
                    fobj.writelines(
                        "\n".join(
                            [
                                fname.replace(
                                    gpaths["GEOIPS_OUTDIRS"], "$GEOIPS_OUTDIRS"
                                )
                                for fname in final_products[cpath]["files"]
                            ]
                        )
                    )
                    # If we don't write out the last newline, then wc won't return the
                    # appropriate number, and we won't get to the last file when
                    # attempting to loop through
                    fobj.writelines(["\n"])
                else:
                    LOG.info(
                        """  SKIPPING WRITING {0} to output file list, no products
                        generated""".format(
                            cpath,
                        )
                    )

    mem_usage_stats = print_mem_usage("MEMUSG", verbose=True)
    LOG.interactive("READER_NAME: %s", config_dict["reader_name"])
    num_products = sum(
        [len(final_products[cpath]["files"]) for cpath in final_products]
    )
    LOG.interactive("NUM_PRODUCTS: %s", num_products)
    if product_db:
        LOG.info(
            "NUM_DATABASE_WRITES: %s",
            sum(
                [
                    len(final_products[cpath]["database writes"])
                    for cpath in final_products
                ]
            ),
        )
    LOG.interactive("NUM_DELETED_PRODUCTS: %s", len(removed_products))
    LOG.interactive("NUM_SUCCESSFUL_COMPARISON_DIRS: %s", successful_comparison_dirs)
    LOG.interactive("NUM_FAILED_COMPARISON_DIRS: %s", failed_comparison_dirs)
    output_process_times(process_datetimes, num_jobs)
    if product_db:
        all_sectors_use_tcdb = all(
            [
                config_dict["available_sectors"][x].get("tcdb")
                for x in config_dict["available_sectors"].keys()
            ]
        )
        if (
            command_line_args.get("tcdb")
            or command_line_args.get("trackfiles")
            or all_sectors_use_tcdb
        ):
            sector_type = "dynamic_tc"
        else:
            sector_type = "static"
        write_stats_to_database(
            procflow_name="config_based",
            platform=xobjs["METADATA"].platform_name.lower(),
            source=xobjs["METADATA"].source_name,
            product="multi",
            sector_type=sector_type,
            process_times=process_datetimes,
            num_products_created=num_products,
            num_products_deleted=len(removed_products),
            resource_usage_dict=mem_usage_stats,
        )
    return retval
