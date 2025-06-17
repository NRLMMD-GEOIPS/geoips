# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Processing workflow for single data source processing."""

from os import getenv, getpid
from os.path import basename, exists
import logging
from datetime import timedelta
import inspect
import xarray

# Internal utilities
from geoips.errors import PluginError
from geoips.errors import OutputFormatterDatelineError
from geoips.errors import OutputFormatterInvalidProjectionError
from geoips.filenames.duplicate_files import remove_duplicates
from geoips.geoips_utils import copy_standard_metadata, output_process_times
from geoips.utils.memusg import PidLog
from geoips.xarray_utils.data import sector_xarrays
from geoips.sector_utils.utils import filter_area_defs_actual_time, is_dynamic_sector
from geoips.geoips_utils import replace_geoips_paths

# Old interfaces (YAML, not updated to classes yet!)
from geoips.dev.product import (
    get_required_variables,
    get_requested_datasets_for_variables,
    get_covg_from_product,
    get_covg_args_from_product,
)
from geoips.dev.output_config import (
    get_filename_formatters,
    get_filename_formatter_kwargs,
    get_output_formatter,
    get_output_formatter_kwargs,
    get_metadata_filename_formatter,
    get_metadata_filename_formatter_kwargs,
    get_metadata_output_formatter,
    get_metadata_output_formatter_kwargs,
    get_minimum_coverage,
)

# New class-based interfaces
from geoips.interfaces import (
    algorithms,
    colormappers,
    filename_formatters,
    interpolators,
    output_formatters,
    products,
    readers,
    sector_adjusters,
)

# These output families require an input filename list, AND require the returned
# list of products to match what was passed in
OUTPUT_FAMILIES_WITH_OUTFNAMES_ARG = [
    "xrdict_varlist_outfnames_to_outlist",
    "xrdict_area_product_outfnames_to_outlist",
    "image",
    "unprojected",
    "image_overlay",
    "xarray_data",
]
# These output families do NOT take in a list of filenames, and an arbitrary
# list of output products can be returned - there is no expected output file
# list
OUTPUT_FAMILIES_WITH_NO_OUTFNAMES_ARG = [
    "xrdict_area_product_to_outlist",
    "xrdict_to_outlist",
]

FILENAME_FORMATS_WITHOUT_COVG = [
    "xarray_metadata_to_filename",
    "xarray_area_product_to_filename",
]

FILENAME_FORMATS_FOR_XARRAY_DICT_TO_OUTPUT_FORMAT = [
    "xarray_metadata_to_filename",
    "xarray_area_product_to_filename",
]

# Organizing lists at the top of the single source procflow of all of the
# xarray-dict based product families to better track how they flow through
# the procflow.  In the end, there should be one of
# each xarray-dict based family (with/without algorithm, with/without area,
# with/without sectoring for the area-based ones)
# Including lists at the top so we can more easily identify what families
# are used/supported in the procflows, and if we notice duplicate supported
# families we can add them to this list.
PRODUCT_FAMILIES_OF_UNSECTORED_XARRAY_DICT_WITHOUT_ALGORITHM_WITHOUT_AREA = [
    "unsectored_xarray_dict_to_output_format",
]
PRODUCT_FAMILIES_OF_UNSECTORED_XARRAY_DICT_WITH_ALGORITHM_WITHOUT_AREA = [
    "unsectored_xarray_dict_to_algorithm_to_output_format",
]
PRODUCT_FAMILIES_OF_UNSECTORED_XARRAY_DICT_WITHOUT_ALGORITHM_WITH_AREA = [
    "unsectored_xarray_dict_area_to_output_format",
]
PRODUCT_FAMILIES_OF_SECTORED_XARRAY_DICT_WITHOUT_ALGORITHM_WITH_AREA = [
    "sectored_xarray_dict_to_output_format",
]
PRODUCT_FAMILIES_OF_XARRAY_DICT_WITH_AREA = (
    PRODUCT_FAMILIES_OF_SECTORED_XARRAY_DICT_WITHOUT_ALGORITHM_WITH_AREA
    + PRODUCT_FAMILIES_OF_UNSECTORED_XARRAY_DICT_WITHOUT_ALGORITHM_WITH_AREA
)
PRODUCT_FAMILIES_OF_XARRAY_DICT_WITHOUT_AREA = (
    PRODUCT_FAMILIES_OF_UNSECTORED_XARRAY_DICT_WITHOUT_ALGORITHM_WITHOUT_AREA
    + PRODUCT_FAMILIES_OF_UNSECTORED_XARRAY_DICT_WITH_ALGORITHM_WITHOUT_AREA
)

PMW_NUM_PIXELS_X = 1400
PMW_NUM_PIXELS_Y = 1400
PMW_PIXEL_SIZE_X = 1000
PMW_PIXEL_SIZE_Y = 1000

LOG = logging.getLogger(__name__)

interface = "procflows"
family = "standard"
name = "single_source"


def output_all_metadata(
    output_dict, output_fnames, metadata_fnames, xarray_obj, area_def=None
):
    """Output all metadata."""
    final_outputs = output_fnames.copy()
    metadata_output_formatter = get_metadata_output_formatter(output_dict)
    metadata_output_formatter_kwargs = get_metadata_output_formatter_kwargs(output_dict)
    for metadata_fname, output_fname in zip(metadata_fnames, output_fnames):
        if metadata_fname is not None:
            # Optional arguments for standard metadata formats (like "output_dict")
            metadata_output_formatter_kwargs["metadata_fname_dict"] = metadata_fnames[
                metadata_fname
            ]
            metadata_output_formatter_kwargs["output_fname_dict"] = output_fnames[
                output_fname
            ]
            metadata_output_formatter_kwargs["output_dict"] = output_dict
            output_plugin = output_formatters.get_plugin(metadata_output_formatter)
            output_kwargs = remove_unsupported_kwargs(
                output_plugin, metadata_output_formatter_kwargs
            )
            if output_plugin.family == "standard_metadata":
                curr_outputs = output_plugin(
                    area_def,
                    xarray_obj=xarray_obj,
                    metadata_yaml_filename=metadata_fname,
                    product_filename=output_fname,
                    **output_kwargs,
                )
                if curr_outputs != [metadata_fname]:
                    raise ValueError("Did not produce expected products")

                for curr_output in curr_outputs:
                    final_outputs[curr_output] = metadata_fnames[curr_output]

    return final_outputs


def get_output_filenames(
    fname_formats,
    output_dict,
    prod_plugin,
    xarray_obj=None,
    area_def=None,
    supported_filenamer_types=None,
):
    """Get output filenames."""
    output_fnames = {}
    metadata_fnames = {}
    for filename_formatter in fname_formats:
        filename_formatter_kwargs = get_filename_formatter_kwargs(
            filename_formatter, output_dict
        )
        metadata_filename_formatter = get_metadata_filename_formatter(
            filename_formatter, output_dict
        )
        metadata_filename_formatter_kwargs = get_metadata_filename_formatter_kwargs(
            metadata_filename_formatter, output_dict
        )

        output_fname = get_filename(
            filename_formatter,
            prod_plugin,
            xarray_obj,
            area_def,
            output_dict=output_dict,
            supported_filenamer_types=supported_filenamer_types,
            filename_formatter_kwargs=filename_formatter_kwargs,
        )

        # If we weren't able to get a valid output filename, do not proceed.
        if output_fname is None:
            continue

        output_fnames[output_fname] = {
            "filename_formatter": filename_formatter,
            "filename_formatter_kwargs": filename_formatter_kwargs,
            "product_name": prod_plugin.name,
        }

        metadata_fname = None
        if metadata_filename_formatter:
            fname_fmt_plugin = filename_formatters.get_plugin(
                metadata_filename_formatter
            )
            if fname_fmt_plugin.family == "standard_metadata":
                metadata_filename_formatter_kwargs = remove_unsupported_kwargs(
                    fname_fmt_plugin, metadata_filename_formatter_kwargs
                )
                metadata_fname = fname_fmt_plugin(
                    area_def,
                    xarray_obj,
                    output_fname,
                    **metadata_filename_formatter_kwargs,
                )
        metadata_fnames[metadata_fname] = {
            "filename_formatter": filename_formatter,
            "filename_formatter_kwargs": filename_formatter_kwargs,
            "metadata_filename_formatter": metadata_filename_formatter,
            "metadata_filename_formatter_kwargs": metadata_filename_formatter_kwargs,
            "product_name": prod_plugin.name,
        }
    return output_fnames, metadata_fnames


def add_attrs_from_area_def(final_xarray, source_xarray, area_def):
    """Add attributes from an area_def."""
    # MLS I think this should actually just be final_xarray and final_xarray,
    # no source_xarray!  We might be losing information...
    # Ensure we have the "adjustment"id" in the filename appropriately
    if area_def and "adjustment_id" in area_def.sector_info:
        final_xarray = add_filename_extra_field(
            source_xarray, "adjustment_id", area_def.sector_info["adjustment_id"]
        )
    return final_xarray


def resector_xarrays(
    resector, sect_xarrays, area_def, variables, window_start_time, window_end_time
):
    """Resector xarrays if requested."""
    # If the initial sectoring was to a padded area definition, must sector to final
    # area_def here.
    # Allow specifying whether it needs to be resectored or not via kwargs.
    if resector:
        LOG.interactive("Resectoring xarrays without padding...")
        curr_sect_xarrays = sector_xarrays(
            sect_xarrays,
            area_def,
            varlist=variables,
            hours_before_sector_time=6,
            hours_after_sector_time=9,
            drop=True,
            window_start_time=window_start_time,
            window_end_time=window_end_time,
        )
        # hours_before_sector_time=6, hours_after_sector_time=6, drop=True)
    else:
        curr_sect_xarrays = sect_xarrays
    return curr_sect_xarrays


def get_interp_plugin_from_product(prod_plugin):
    """Get the interpolator plugin from the product spec.

    Reassign interp_plugin based on CURRENT sect_xarray
    Allow re-defining interpolation for different datasets.
    """
    interp_plugin = None
    if "interpolator" in prod_plugin["spec"]:
        interp_plugin = interpolators.get_plugin(
            prod_plugin["spec"]["interpolator"]["plugin"]["name"]
        )
        interp_args = prod_plugin["spec"]["interpolator"]["plugin"]["arguments"]
        interp_args = remove_unsupported_kwargs(interp_plugin, interp_args)
    return interp_plugin, interp_args


def apply_interp_first(
    variables,
    curr_sect_xarrays,
    prod_plugin,
    datasets_for_vars,
    resampled_read,
    area_def,
    processed_xarrays,
):
    """Apply interpolation first.

    For product types that involve interpolation before algorithm.
    """
    # Default to empty xarray.Dataset() - will be populated within loop with
    # appropriate regridded variables.
    interp_xarray = xarray.Dataset()
    for varname in variables:
        LOG.info("TRYING variable %s", varname)
        for key, sect_xarray in curr_sect_xarrays.items():
            LOG.info("    TRYING dataset %s for variable %s", key, varname)

            if varname not in sect_xarray.variables:
                continue

            # Determine which interpolator to use based on the product definition.
            interp_plugin, interp_args = get_interp_plugin_from_product(prod_plugin)

            # Check if a specific dataset was specified for the current variable,
            # and ensure we are pulling the variable from the correct dataset.
            if not use_variable_from_current_dataset(
                varname,
                key,
                variables,
                sect_xarray,
                interp_xarray,
                resampled_read,
                datasets_for_vars,
            ):
                continue

            # Potential efficiency hit with to_masked_array for dask arrays, etc
            # LOG.info('Min/max %s %s / %s, dataset %s',
            #          varname,
            #          sect_xarray[varname].to_masked_array().min(),
            #          sect_xarray[varname].to_masked_array().max(),
            #          key)

            # It is much faster to interpolate all variables at once than
            # one at a time. Since we can assume "variables" is all of the
            # requested variables, just interpolate them all the first time
            # through, and add logic to NOT reinterpolate variables if they've
            # already been interpolated.
            # For reference, with 11 variables, it was 1 min 13s
            # to interpolate individually, 22s in one call.
            interp_args["varlist"] = variables
            if "time_dim" in sect_xarray.dims:
                # This is for a particularly formatted dataset, that includes
                # separate arrays for different times (ABI fire product).
                # We need to be careful this does not break for some other
                # dataset that includes a differently formatted "time"
                # dimension.
                tdims = len(sect_xarray.time_dim)

                interp_list = []
                for i in range(tdims):
                    interp_list.append(
                        perform_interpolation(
                            interp_plugin,
                            area_def,
                            sect_xarray.isel(time_dim=i),
                            xarray.Dataset(),
                            interp_args,
                            processed_xarrays,
                        )
                    )

                interp_xarray[varname] = xarray.concat(interp_list, dim="dim_2")[
                    varname
                ]
            else:
                interp_xarray = perform_interpolation(
                    interp_plugin,
                    area_def,
                    sect_xarray,
                    interp_xarray,
                    interp_args,
                    processed_xarrays,
                )

            # Potential efficiency hit with to_masked_array for dask arrays, etc
            # LOG.info('Min/max interp %s %s / %s',
            #          varname,
            #          interp_xarray[varname].to_masked_array().min(),
            #          interp_xarray[varname].to_masked_array().max())
    return interp_xarray


def use_variable_from_current_dataset(
    varname,
    key,
    variables,
    sect_xarray,
    interp_xarray,
    resampled_read,
    datasets_for_vars,
):
    """Use the variable from the current dataset.

    If a specific dataset was requested for the current variable, and
    this dataset was NOT requested via a resampled_read (in which case
    the native datasets won't exist, only the resampled dataset),
    then use the appropriately requested dataset.
    """
    if varname in datasets_for_vars and not resampled_read:
        if key in datasets_for_vars[varname]:
            LOG.info(
                "        USING %s varname from dataset %s, as specified in "
                "product_input YAML config",
                varname,
                key,
            )
        else:
            LOG.info(
                "        WAITING dataset %s not requested for variable %s in "
                "product_input YAML config",
                key,
                varname,
            )
            return False
    # If we've already interpolated this variable, check if it is needed
    # before interpolating again
    elif interp_xarray is not None and varname in list(interp_xarray.keys()):
        # If all of the required variables are in the current dataset, use this
        # version
        if set(variables).issubset(set(sect_xarray.variables.keys())):
            LOG.info(
                "        REPLACING %s with current dataset %s, all required "
                "variables in current dataset",
                varname,
                key,
            )
        # Otherwise, skip re-interpolating to avoid unecessary computation
        else:
            LOG.warning(
                "        SKIPPING %s, encountered multiple versions, skipping "
                "subsequent dataset %s",
                varname,
                key,
            )
            return False
    else:
        LOG.info(
            "        USING %s varname from dataset %s - first availalbe, and "
            "not specified in YAML",
            varname,
            key,
        )
    return True


def get_alg_and_interp_plugins(prod_plugin):
    """Get algorithm and interpolator plugins from prod_plugin definition."""
    # Only attempt to set algorithm function if algorithm requested in product type
    try:
        alg_args = prod_plugin["spec"]["algorithm"]["plugin"]["arguments"]
        alg_plugin = algorithms.get_plugin(
            prod_plugin["spec"]["algorithm"]["plugin"]["name"]
        )
    except KeyError:
        alg_args = None
        alg_plugin = None

    try:
        interp_args = prod_plugin["spec"]["interpolator"]["plugin"]["arguments"]
        interp_plugin = interpolators.get_plugin(
            prod_plugin["spec"]["interpolator"]["plugin"]["name"]
        )
        interp_args = remove_unsupported_kwargs(interp_plugin, interp_args)
    except KeyError:
        interp_args = None
        interp_plugin = None
    return alg_plugin, alg_args, interp_plugin, interp_args


def apply_alg_after_interp(
    interp_xarray,
    area_def,
    alg_plugin,
    alg_args,
    prod_plugin,
    variables,
    processed_xarrays,
):
    """Apply algorithm after interpolation.

    MLS need to add ability here to pull from processed_xarrays if algorithm
    was already applied.
    """
    if processed_xarrays and prod_plugin.name in processed_xarrays:
        return processed_xarrays[prod_plugin.name]
    # Specify the call signature and return value for different algorithm types:
    if prod_plugin.family in ["interpolator"]:
        # Note "interp" product type will NOT have a single variable named
        # "product_name", just the individual interpolated variables.
        interp_xarray = interp_xarray
    elif alg_plugin.family in ["xarray_to_numpy"]:
        # xarray_to_numpy will return a single array, which can be set to the
        # "product_name" variable.
        LOG.interactive(
            "  Applying '%s' family algorithm '%s' to data...",
            alg_plugin.family,
            alg_plugin.name,
        )
        interp_xarray[prod_plugin.name] = xarray.DataArray(
            alg_plugin(interp_xarray, **alg_args)
        )
    elif alg_plugin.family in ["xarray_to_xarray"]:
        # xarray_to_xarray algorithm type will return the full xarray object -
        # assume variable names have been set appropriately within the
        # algorithm.  This could be another good use of the
        # "alt_varname_for_covg" kwarg in the coverage checks - if we want to
        # just use a specific variable for the coverage checks rather than the
        # "product_name" variable.
        LOG.interactive(
            "  Applying '%s' family algorithm '%s' to data...",
            alg_plugin.family,
            alg_plugin.name,
        )
        interp_xarray = alg_plugin(
            interp_xarray, variables, prod_plugin.name, **alg_args
        )
    elif alg_plugin.family in [
        "single_channel",
        "channel_combination",
        "list_numpy_to_numpy",
        "rgb",
    ]:
        # Assume ANYTHING else takes in a list of numpy arrays, and returns a
        # single numpy array.
        # Perhaps we should be explicit here...
        LOG.interactive(
            "  Applying '%s' family algorithm '%s' to data...",
            alg_plugin.family,
            alg_plugin.name,
        )
        interp_xarray[prod_plugin.name] = xarray.DataArray(
            alg_plugin(
                [interp_xarray[varname].to_masked_array() for varname in variables],
                **alg_args,
            )
        )
    else:
        raise TypeError(
            f"UNSUPPORTED algorithm family '{alg_plugin.family}' or product family "
            f"'{prod_plugin.family}', please add to the single_source procflow's "
            "'get_alg_xarray' function appropriately"
        )
    return interp_xarray


def apply_alg_first(
    alg_plugin,
    alg_args,
    prod_plugin,
    curr_sect_xarrays,
    sect_xarrays,
    variables,
    variable_names,
    area_def,
):
    """Apply algorithm appropriately based on algorithm family.

    MLS
    Inexplicably some of these use curr_sect_xarrays, and some use sect_xarrays.
    Also, some use variables and some use variable_names.
    I am guessing there is no reason for the difference, but maintaining the
    original functionality for now.
    """
    alg_xarray = xarray.Dataset()
    alg_xarray.attrs = sect_xarrays["METADATA"].attrs.copy()
    if alg_plugin.family in ["xarray_to_numpy"]:
        # Why does this one use sect_xarrays and not curr_sect_xarrays?
        # And it uses variable_names, not variables.
        # print(variable_names,variables)
        alg_xarray = apply_alg_xarray_to_numpy(
            alg_xarray, alg_plugin, alg_args, prod_plugin, sect_xarrays, variables
        )
    elif alg_plugin.family in ["xarray_dict_area_def_to_numpy"]:
        # Why does this one use sect_xarrays and not curr_sect_xarrays?
        alg_xarray = apply_alg_xarray_dict_area_def_to_numpy(
            alg_xarray, alg_plugin, alg_args, prod_plugin, sect_xarrays, area_def
        )
    elif alg_plugin.family in ["xarray_dict_to_xarray"]:
        # This one uses sect_xarrays
        alg_xarray = apply_alg_xarray_dict_to_xarray(alg_plugin, alg_args, sect_xarrays)
    elif alg_plugin.family in ["xarray_dict_to_xarray_dict"]:
        # This one uses sect_xarrays
        alg_xarray = apply_alg_xarray_dict_to_xarray_dict(
            alg_plugin, alg_args, sect_xarrays
        )
    elif alg_plugin.family in ["xarray_to_xarray"]:
        # This one uses variables, not variable_names
        alg_xarray = apply_alg_xarray_to_xarray(
            alg_plugin, alg_args, prod_plugin, sect_xarrays, variables
        )
    elif alg_plugin.family in ["list_numpy_to_numpy"]:
        # Why does this one use curr_sect_xarrays and not sect_xarrays?
        # And variables, not variable_names ?
        alg_xarray = apply_alg_list_numpy_to_numpy(
            alg_xarray,
            alg_plugin,
            alg_args,
            prod_plugin,
            curr_sect_xarrays,
            variables,
        )
    return alg_xarray


def apply_interp_after_alg(
    alg_xarray, interp_plugin, interp_args, prod_plugin, area_def, processed_xarrays
):
    """Apply interpolation after algorithm."""
    # No interpolation required
    if prod_plugin.family in ["algorithm", "algorithm_colormapper"]:
        final_xarray = alg_xarray
    # If required, interpolate the result prior to returning
    elif prod_plugin.family == "algorithm_interpolator_colormapper":
        if interp_args.get("varlist") is None or interp_args["varlist"] is None:
            # Just assume the only thing we're interpolating is the product name itself
            interp_args["varlist"] = [prod_plugin.name]
        # Otherwise use the varlist that was provided. For example, a user could produce
        # Additional variables from their algorithm alongside their product name
        final_xarray = perform_interpolation(
            interp_plugin,
            area_def,
            alg_xarray,
            xarray.Dataset(),
            interp_args,
            processed_xarrays,
        )
    return final_xarray


def apply_alg_xarray_to_xarray(
    alg_plugin, alg_args, prod_plugin, sect_xarrays, variable_names
):
    """Apply xarray_to_xarray algorithm."""
    input_alg_xarray = None
    for varname in variable_names:
        LOG.info("TRYING variable %s for non-interpolated algorithms", varname)
        for curr_sect_xarray in sect_xarrays.values():
            if varname in curr_sect_xarray:
                if input_alg_xarray is None:
                    LOG.info(
                        "    USING sectored xarray %s for non-interpolated "
                        "algorithms",
                        curr_sect_xarray,
                    )
                    input_alg_xarray = curr_sect_xarray
                else:
                    LOG.info(
                        "    SKIPPING For non-interpolated data processing, "
                        "all native variables must be the same resolution! "
                        "Skipping variable %s, shape %s, input_alg_xarrays: %s",
                        varname,
                        curr_sect_xarray[varname].shape,
                        input_alg_xarray,
                    )
    if input_alg_xarray is None:
        raise ValueError(
            "No required variables in any xarrays for 'xarray_to_xarray' "
            "algorithm type"
        )
    LOG.interactive(
        "  Applying '%s' family algorithm '%s' to data...",
        alg_plugin.family,
        alg_plugin.name,
    )
    alg_xarray = alg_plugin(
        input_alg_xarray, variable_names, prod_plugin.name, **alg_args
    )
    return alg_xarray


def apply_alg_xarray_dict_to_xarray(alg_plugin, alg_args, sect_xarrays):
    """Apply xarray_dict_to_xarray algorithm."""
    # Format the call signature for passing a dictionary of xarrays,
    # plus area_def, and return a single numpy array
    LOG.interactive(
        "  Applying '%s' family algorithm '%s' to data...",
        alg_plugin.family,
        alg_plugin.name,
    )
    alg_xarray = alg_plugin(sect_xarrays, **alg_args)
    return alg_xarray


def apply_alg_xarray_dict_to_xarray_dict(alg_plugin, alg_args, sect_xarrays):
    """Apply xarray_dict_to_xarray algorithm."""
    # Format the call signature for passing a dictionary of xarrays,
    # plus area_def, and return a single numpy array
    LOG.interactive(
        "  Applying '%s' family algorithm '%s' to data...",
        alg_plugin.family,
        alg_plugin.name,
    )
    alg_xarray_dict = alg_plugin(sect_xarrays, **alg_args)
    return alg_xarray_dict


def apply_alg_xarray_dict_area_def_to_numpy(
    alg_xarray, alg_plugin, alg_args, prod_plugin, sect_xarrays, area_def
):
    """Apply xarray_dict_area_def_to_numpy algorithm."""
    # Format the call signature for passing a dictionary of xarrays,
    # plus area_def, and return a single numpy array
    LOG.interactive(
        "  Applying '%s' family algorithm '%s' to data...",
        alg_plugin.family,
        alg_plugin.name,
    )
    alg_xarray[prod_plugin.name] = xarray.DataArray(
        alg_plugin(sect_xarrays, area_def, **alg_args)
    )
    return alg_xarray


def apply_alg_xarray_to_numpy(
    alg_xarray, alg_plugin, alg_args, prod_plugin, sect_xarrays, variable_names
):
    """Apply xarray_to_numpy algorithm."""
    # Format the call signature for passing a dictionary of xarrays,
    # plus area_def, and return a single numpy array
    for dsname in sect_xarrays.keys():
        if set(variable_names).issubset(set(sect_xarrays[dsname].variables.keys())):
            LOG.interactive(
                "  Applying '%s' family algorithm '%s' to data...",
                alg_plugin.family,
                alg_plugin.name,
            )
            alg_xarray = sect_xarrays[dsname]
            alg_xarray[prod_plugin.name] = xarray.DataArray(
                alg_plugin(sect_xarrays[dsname], **alg_args)
            )
            # drops geo values?
    return alg_xarray


def apply_alg_list_numpy_to_numpy(
    alg_xarray, alg_plugin, alg_args, prod_plugin, sect_xarrays, variables
):
    """Apply list_numpy_to_numpy algorithm."""
    # Need to pull all the required variables out of the various xarray datasets
    # and add them to numpy list.
    # Then assign the resulting numpy array to the "product_name" DataArray
    # within the xarray Dataset
    numpys = []
    for varname in variables:
        for curr_sect_xarray in sect_xarrays.values():
            if varname in list(curr_sect_xarray.variables.keys()):
                numpys += [curr_sect_xarray[varname].to_masked_array()]
                alg_xarray = curr_sect_xarray
    LOG.interactive(
        "  Applying '%s' family algorithm '%s' to data...",
        alg_plugin.family,
        alg_plugin.name,
    )
    alg_xarray[prod_plugin.name] = xarray.DataArray(alg_plugin(numpys, **alg_args))
    return alg_xarray


def perform_interpolation(
    interp_plugin, area_def, sect_xarray, interp_xarray, interp_args, processed_xarrays
):
    """Perform standard interpolation."""
    interp_args, interp_xarray = select_variables_to_interp(
        interp_args, area_def, sect_xarray, interp_xarray, processed_xarrays
    )
    LOG.interactive(
        "  Interpolating data with interpolator '%s' args '%s'...",
        interp_plugin.name,
        interp_args,
    )
    # Only attempt to interpolate if there are required variables left.
    if interp_args["varlist"]:
        interp_xarray = interp_plugin(
            area_def, sect_xarray, interp_xarray, **interp_args
        )
    else:
        LOG.info("No variables to interpolate, returning interp_xarray unchanged.")
    return interp_xarray


def get_unique_dataset_key(area_def, xobj):
    """Get a unique id for xarray dataset."""
    standard_attrs = (
        f"{xobj.attrs['start_datetime']}_"
        f"{xobj.attrs['end_datetime']}_"
        f"{xobj.attrs['platform_name']}_"
        f"{xobj.attrs['source_name']}"
    )
    return f"{area_def.area_id}_{hash(area_def)}_{standard_attrs}"


def select_variables_to_interp(
    interp_args, area_def, source_xarray, interp_xarray, processed_xarrays
):
    """Select interpolation variables."""
    curr_available_vars = set(list(source_xarray.variables.keys()))
    already_interped_vars = set(list(interp_xarray.variables.keys()))
    all_requested_vars = set(interp_args["varlist"])
    curr_requested_vars = curr_available_vars.intersection(all_requested_vars)
    interp_vars = curr_requested_vars.difference(already_interped_vars)
    final_interp_vars = list(interp_vars)
    # This is a unique identifier so we can re-use variables
    # and product arrays appropriately.
    area_def_key = get_unique_dataset_key(area_def, source_xarray)
    if processed_xarrays and area_def_key in processed_xarrays:
        LOG.info(
            "  Area def '%s' in processed_xarrays, "
            "with variables '%s', using existing array, "
            "in place of interp_xarray '%s'.",
            area_def_key,
            list(processed_xarrays[area_def_key].variables.keys()),
            interp_xarray,
        )
        # Just add to this existing array
        interp_xarray = processed_xarrays[area_def_key]
        final_interp_vars = []
        for varname in interp_vars:
            if varname not in processed_xarrays[area_def_key].variables.keys():
                final_interp_vars += [varname]
    interp_args["varlist"] = final_interp_vars
    return interp_args, interp_xarray


def remove_unsupported_kwargs(module, requested_kwargs):
    """Remove unsupported keyword arguments."""
    module_args = set(inspect.signature(module).parameters.keys())
    unsupported = list(set(requested_kwargs.keys()).difference(module_args))
    if "kwargs" not in module_args:
        for key in unsupported:
            LOG.warning("REMOVING UNSUPPORTED %s key %s", module, key)
            requested_kwargs.pop(key)
    return requested_kwargs


def add_filename_extra_field(xarray_obj, field_name, field_value):
    """Add filename extra field."""
    if "filename_extra_fields" not in xarray_obj.attrs:
        xarray_obj.attrs["filename_extra_fields"] = {}
    xarray_obj.attrs["filename_extra_fields"][field_name] = field_value
    return xarray_obj


def combine_filename_extra_fields(source_xarray, dest_xarray):
    """Combine filename extra fields."""
    if "filename_extra_fields" in source_xarray.attrs:
        for field in source_xarray.filename_extra_fields:
            if "filename_extra_fields" not in dest_xarray.attrs:
                dest_xarray.attrs["filename_extra_fields"] = {}
            dest_xarray.attrs["filename_extra_fields"][field] = (
                source_xarray.filename_extra_fields[field]
            )
    return dest_xarray


def process_sectored_data_output(
    xobjs, variables, prod_plugin, output_dict, area_def=None
):
    """Process sectored data output.

    If current product family requires a sectored dictionary of xarrays, does
    not apply an algorithm, and DOES require an area definition, call
    'process_xarray_dict_to_output_format', store the result in a list, and return it.
    """
    output_products = []
    # Currently this only supports NOT applying an algorithm.  Could expand
    # to additionally support algorithm application.
    if (
        prod_plugin.family
        in PRODUCT_FAMILIES_OF_SECTORED_XARRAY_DICT_WITHOUT_ALGORITHM_WITH_AREA
    ):
        output_products += process_xarray_dict_to_output_format(
            xobjs, variables, prod_plugin, output_dict, area_def=area_def
        )
    return output_products


def process_xarray_dict_to_output_format(
    xobjs, variables, prod_plugin, output_dict, area_def=None
):
    """Process xarray dict to output format."""
    output_formatter = get_output_formatter(output_dict)
    output_formatter_kwargs = get_output_formatter_kwargs(output_dict)
    # All xarray dict based products can be processed here - this function is
    # called from both within the loop through all area_defs, and before it.
    # As well as for both sectored / non-sectored products.
    supported_product_types = (
        PRODUCT_FAMILIES_OF_XARRAY_DICT_WITH_AREA
        + PRODUCT_FAMILIES_OF_XARRAY_DICT_WITHOUT_AREA
    )

    if prod_plugin.family not in supported_product_types:
        raise TypeError(
            f"UNSUPPORTED product_type {prod_plugin.family} "
            f'for product {prod_plugin.name} source {xobjs["METADATA"].source_name} \n'
            f"      product_type must be one of {supported_product_types}"
        )

    # These are all the supported oututter familes
    supported_output_plugin_types = (
        OUTPUT_FAMILIES_WITH_OUTFNAMES_ARG + OUTPUT_FAMILIES_WITH_NO_OUTFNAMES_ARG
    )

    output_plugin = output_formatters.get_plugin(output_formatter)
    # Default to empty dict for output_fnames
    output_fnames = {}

    # Only get output filenames if needed
    if output_plugin.family in OUTPUT_FAMILIES_WITH_OUTFNAMES_ARG:
        supported_filenamer_types = FILENAME_FORMATS_FOR_XARRAY_DICT_TO_OUTPUT_FORMAT
        fname_formats = get_filename_formatters(output_dict)
        output_fnames, metadata_fnames = get_output_filenames(
            fname_formats,
            output_dict,
            prod_plugin,
            xarray_obj=xobjs["METADATA"],
            area_def=area_def,
            supported_filenamer_types=supported_filenamer_types,
        )
        LOG.interactive(
            "Output filenames for family %s: %s",
            output_plugin.family,
            output_fnames,
        )
    else:
        LOG.interactive(
            "No output filenames required for family %s", output_plugin.family
        )

    if "output_dict" not in output_formatter_kwargs:
        output_formatter_kwargs["output_dict"] = output_dict
    output_formatter_kwargs = remove_unsupported_kwargs(
        output_plugin, output_formatter_kwargs
    )

    LOG.interactive("Running output plugin of family %s", output_plugin.family)
    if output_plugin.family == "xrdict_varlist_outfnames_to_outlist":
        curr_products = output_plugin(
            xobjs, variables, list(output_fnames.keys()), **output_formatter_kwargs
        )
        # If we pass it a list of filenames, assume we create exactly those filenames
        if curr_products != list(output_fnames.keys()):
            raise (ValueError("Did not produce expected products"))

    elif output_plugin.family == "xrdict_area_product_outfnames_to_outlist":
        curr_products = output_plugin(
            xobjs,
            area_def,
            prod_plugin,
            list(output_fnames.keys()),
            **output_formatter_kwargs,
        )
        # If we pass it a list of filenames, assume we create exactly those filenames
        if curr_products != list(output_fnames.keys()):
            raise (ValueError("Did not produce expected products"))

    elif output_plugin.family == "xrdict_area_product_to_outlist":
        curr_products = output_plugin(
            xobjs, area_def, prod_plugin, **output_formatter_kwargs
        )
        # No input filename list, no check that output filename list matches
        LOG.info(
            "Not checking output file list for output family %s", output_plugin.family
        )
    elif output_plugin.family == "xrdict_to_outlist":
        curr_products = output_plugin(xobjs, **output_formatter_kwargs)
        # No input filename list, no check that output filename list matches
        LOG.info(
            "Not checking output file list for output family %s", output_plugin.family
        )

    # We theoretically can do this for all output_formatters that don't require an area
    # definition
    elif output_plugin.family == "unprojected":
        # If there is not a colormap dictionary already provided in output_formatter
        # kwargs, then try to retrieve it here. If it's not possible, raise a
        # PluginError which points out that no colormapper plugin was provided and
        # therefore we can't produce an unprojected image.
        if "mpl_colors_info" not in output_formatter_kwargs:
            prd_plg = products.get_plugin(
                prod_plugin["source_names"][0], prod_plugin.name
            )
            cmap_name = (
                prd_plg["spec"].get("colormapper", {}).get("plugin", {}).get("name")
            )
            if cmap_name:
                cmap_plg = colormappers.get_plugin(cmap_name)
                output_formatter_kwargs["mpl_colors_info"] = cmap_plg(
                    **prd_plg["spec"]["colormapper"]["plugin"]["arguments"]
                )
        else:
            raise PluginError(
                f"Error: product plugin '{prod_plugin.name}' does not have a "
                "colormapper plugin that is needed for the 'unprojected_image'"
                "output formatter. Please add a colormapper plugin to your product, and"
                " try again."
            )
        # Unprojected Output formatter expects the xarray including the data for your
        # product rather than a dictionary containing that xarray. We probably could
        # just default to 'xobjs[prod_plugin.name]', however adding this conditional
        # doesn't hurt in the case xobjs is an xarray.Dataset(). Shouldn't happen,
        # but again, doesn't hurt to add this functionality.
        if isinstance(xobjs, dict):
            in_xobjs = xobjs[prod_plugin.name]
        else:
            in_xobjs = xobjs
        # Apply unprojected image output formatter
        LOG.info("Applying output formatter of family %s", output_plugin.family)
        curr_products = output_plugin(
            in_xobjs,
            prod_plugin.name,
            output_fnames,
            **output_formatter_kwargs,
        )

    else:
        raise TypeError(
            f'UNSUPPORTED output_formatter "{output_formatter}" '
            f"for product_family {prod_plugin.family}\n"
            f'      output_plugin_family: "{output_plugin.family}"\n'
            f"      output_plugin_type must be one of {supported_output_plugin_types}"
        )

    # We only pre-generated metadata filenames if we also pre-generated output
    # product filenames
    if output_plugin.family in OUTPUT_FAMILIES_WITH_OUTFNAMES_ARG:
        LOG.interactive(
            "Writing out all metadata for products of family %s", output_plugin.family
        )
        final_products = output_all_metadata(
            output_dict,
            output_fnames,
            metadata_fnames,
            xobjs["METADATA"],
            area_def=area_def,
        )
    else:
        final_products = curr_products

    return final_products


def pad_area_definition(
    area_def, source_name=None, force_pad=False, x_scale_factor=1.5, y_scale_factor=1.5
):
    """Pad area definition."""
    from geoips.sector_utils.utils import is_sector_type

    # Always pad TC sectors, and if "force_pad=True" is passed into the function
    if is_sector_type(area_def, "tc") or force_pad:
        LOG.info("Trying area_def %s, %s", area_def.name, area_def.sector_info)
        # Get an extra 50% size for TCs so we can handle recentering and not have
        # missing data. --larger area for possibly moved center for vis/ir backgrounds
        # Default to 1.5x padding
        num_lines = int(area_def.height * y_scale_factor)
        num_samples = int(area_def.width * x_scale_factor)
        # Need full swath width for AMSU-B and MHS. Need a better solution for this.
        if source_name is not None and source_name in ["amsu-b", "mhs"]:
            num_lines = int(area_def.height * 1)
            num_samples = int(area_def.width * 5)

        # TC sectors have center lat and center lon defined within the sector_info
        # For other sectors, use lat_0 and lon_0 from proj_dict
        # Do not use proj_dict for TC sectors, because we want the center of the
        # storm, not current center of image.
        if is_sector_type(area_def, "tc"):
            clat = area_def.sector_info["clat"]
            clon = area_def.sector_info["clon"]
        else:
            clat = area_def.proj_dict["lat_0"]
            clon = area_def.proj_dict["lon_0"]

        from geoips.plugins.modules.sector_spec_generators.center_coordinates import (
            call,
        )

        pad_area_def = call(
            area_id=area_def.area_id,
            long_description=area_def.description,
            clat=clat,
            clon=clon,
            projection="eqc",
            num_lines=num_lines,
            num_samples=num_samples,
            pixel_width=area_def.pixel_size_x,
            pixel_height=area_def.pixel_size_y,
        )
        from geoips.sector_utils.utils import copy_sector_info

        pad_area_def = copy_sector_info(area_def, pad_area_def)
    else:
        pad_area_def = area_def
    return pad_area_def


def get_filename(
    filename_formatter,
    prod_plugin=None,
    alg_xarray=None,
    area_def=None,
    supported_filenamer_types=None,
    output_dict=None,
    filename_formatter_kwargs=None,
):
    """Get filename."""
    filename_fmt_plugin = filename_formatters.get_plugin(filename_formatter)
    if (
        supported_filenamer_types is not None
        and filename_fmt_plugin.family not in supported_filenamer_types
    ):
        raise TypeError(
            f'UNSUPPORTED filename_formatter "{filename_formatter}" '
            f'      filenamer_type: "{filename_fmt_plugin.family}"\n'
            f"      filenamer_type must be one of {supported_filenamer_types}"
        )

    # They all use covg except those in list
    if filename_fmt_plugin.family not in FILENAME_FORMATS_WITHOUT_COVG:
        covg_plugin = get_covg_from_product(
            prod_plugin,
            covg_field="filename_coverage_checker",
        )
        covg_args = get_covg_args_from_product(
            prod_plugin,
            covg_field="filename_coverage_checker",
        )
        # Set variable_name to prod_plugin.name if not defined.
        # Always use variable_name if it is defined.
        # Remove from args so there is not a duplicate are when passing
        # (since we are passing covg_varname explicitly).
        # Note get_covg_args_from_product was updated to return a copy of
        # covg_args, so this does not impact future uses of the product.
        covg_varname = covg_args.pop("variable_name", prod_plugin.name)
        # Note variables can be specified as DATASET:VARIABLE, since this is a
        # preprocessed alg_xarray, and not a dictionary of datasets, just use the
        # variable name (we expect the correct variable will exist in this final
        # processed array)
        if ":" in covg_varname:
            covg_varname = covg_varname.split(":")[1]
        covg = covg_plugin(
            alg_xarray,
            covg_varname,
            area_def,
            **covg_args,
        )

    curr_kwargs = remove_unsupported_kwargs(
        filename_fmt_plugin, filename_formatter_kwargs
    )
    if filename_fmt_plugin.family == "data":
        fname = filename_fmt_plugin(
            area_def,
            alg_xarray,
            [prod_plugin.name, "latitude", "longitude"],
            covg,
            **curr_kwargs,
        )
    elif filename_fmt_plugin.family == "xarray_metadata_to_filename":
        fname = filename_fmt_plugin(alg_xarray, **curr_kwargs)
    elif filename_fmt_plugin.family == "xarray_area_product_to_filename":
        fname = filename_fmt_plugin(
            alg_xarray, area_def, prod_plugin.name, **curr_kwargs
        )
    else:
        fname = filename_fmt_plugin(
            area_def, alg_xarray, prod_plugin.name, covg, **curr_kwargs
        )
    return fname


def plot_data(
    output_dict,
    alg_xarray,
    area_def,
    prod_plugin,
    output_kwargs,
    fused_xarray_dict=None,
    no_output=False,
):
    """Plot data.

    alg_xarray used for filename formats, etc.
    If included, fused_xarray_dict used for output format call
    """
    # If keyword argument is allowed for output function, include it
    output_kwargs["output_dict"] = output_dict
    output_formatter = get_output_formatter(output_dict)
    output_plugin = output_formatters.get_plugin(output_formatter)
    output_kwargs = remove_unsupported_kwargs(output_plugin, output_kwargs)
    exclude_platforms = prod_plugin["spec"].get("exclude_platforms")
    include_platforms = prod_plugin["spec"].get("include_platforms")
    if exclude_platforms and alg_xarray.platform_name in exclude_platforms:
        LOG.interactive(
            "SKIPPING Platform %s not requested for product '%s'"
            "Excluded platforms: '%s'...",
            alg_xarray.platform_name,
            prod_plugin.name,
            exclude_platforms,
        )
        return {}
    if include_platforms and (alg_xarray.platform_name not in include_platforms):
        LOG.interactive(
            "SKIPPING Platform %s not requested for product '%s' "
            "Only included platforms: '%s'...",
            alg_xarray.platform_name,
            prod_plugin.name,
            include_platforms,
        )
        return {}

    LOG.interactive(
        "Producing product '%s' final outputs as type '%s'...",
        prod_plugin.name,
        output_plugin.name,
    )

    if no_output or output_plugin.family in OUTPUT_FAMILIES_WITH_NO_OUTFNAMES_ARG:
        output_fnames = {}
        metadata_fnames = {}
    else:
        fname_formats = get_filename_formatters(output_dict)
        output_fnames, metadata_fnames = get_output_filenames(
            fname_formats, output_dict, prod_plugin, alg_xarray, area_def
        )

    if output_plugin.family == "xarray_data":
        LOG.interactive(
            "  Producing '%s' family final outputs '%s'...",
            output_plugin.family,
            output_plugin.name,
        )
        output_products = output_plugin(
            xarray_obj=alg_xarray,
            product_names=[prod_plugin.name, "latitude", "longitude"],
            output_fnames=list(output_fnames.keys()),
            **output_kwargs,
        )
        # Disabling output_fnames check
        if output_products != list(output_fnames.keys()):
            raise ValueError("Did not produce expected products")
    else:
        mpl_colors_info = None
        if "colormapper" in prod_plugin["spec"]:
            cmap_plugin = colormappers.get_plugin(
                prod_plugin["spec"]["colormapper"]["plugin"]["name"]
            )
            cmap_args = prod_plugin["spec"]["colormapper"]["plugin"]["arguments"]
            mpl_colors_info = cmap_plugin(**cmap_args)

        output_plugin = output_formatters.get_plugin(output_formatter)
        output_kwargs = remove_unsupported_kwargs(output_plugin, output_kwargs)
        display_name = prod_plugin["spec"].get("display_name", prod_plugin.name)
        if output_plugin.family == "image":
            # This returns None if not specified
            LOG.interactive(
                "  Producing '%s' family final outputs '%s'...",
                output_plugin.family,
                output_plugin.name,
            )
            try:
                output_products = output_plugin(
                    area_def,
                    xarray_obj=alg_xarray,
                    product_name=prod_plugin.name,
                    output_fnames=list(output_fnames.keys()),
                    product_name_title=display_name,
                    mpl_colors_info=mpl_colors_info,
                    **output_kwargs,
                )
            except OutputFormatterInvalidProjectionError as e:
                LOG.warning(
                    "Failed to produce %s output: %s",
                    output_plugin.name,
                    "; ".join(list(output_fnames.keys())),
                )
                LOG.warning("OutputFormatterInvalidProjectionError: %s", e)
                output_fnames = {}
                output_products = []
            except OutputFormatterDatelineError as e:
                LOG.warning(
                    "Failed to produce %s output: %s",
                    output_plugin.name,
                    "; ".join(list(output_fnames.keys())),
                )
                LOG.warning("OutputFormatterDatelineError: %s", e)
                output_fnames = {}
                output_products = []
            if output_products != list(output_fnames.keys()):
                raise ValueError("Did not produce expected products")
        elif output_plugin.family == "unprojected":
            # This returns None if not specified
            LOG.interactive(
                "  Producing '%s' family final outputs '%s'...",
                output_plugin.family,
                output_plugin.name,
            )
            output_products = output_plugin(
                xarray_obj=alg_xarray,
                product_name=prod_plugin.name,
                output_fnames=list(output_fnames.keys()),
                product_name_title=display_name,
                mpl_colors_info=mpl_colors_info,
                **output_kwargs,
            )
            if output_products != list(output_fnames.keys()):
                raise ValueError("Did not produce expected products")
        elif output_plugin.family == "image_overlay":
            # This can include background information, feature/gridline annotations,
            # information, etc
            LOG.interactive(
                "  Producing '%s' family final outputs '%s'...",
                output_plugin.family,
                output_plugin.name,
            )
            output_products = output_plugin(
                area_def,
                xarray_obj=alg_xarray,
                product_name=prod_plugin.name,
                output_fnames=list(output_fnames.keys()),
                product_name_title=display_name,
                mpl_colors_info=mpl_colors_info,
                **output_kwargs,
            )
            if output_products != list(output_fnames.keys()):
                raise ValueError("Did not produce expected products")
        elif output_plugin.family == "xrdict_area_product_outfnames_to_outlist":
            # For xarray_dict type, pass the full fused_xarray_dict.
            output_kwargs["product_name_title"] = (display_name,)
            output_kwargs["mpl_colors_info"] = mpl_colors_info
            output_kwargs = remove_unsupported_kwargs(output_plugin, output_kwargs)
            LOG.interactive(
                "  Producing '%s' family final outputs '%s'...",
                output_plugin.family,
                output_plugin.name,
            )
            output_products = output_plugin(
                xarray_dict=fused_xarray_dict,
                area_def=area_def,
                product_name=prod_plugin.name,
                output_fnames=list(output_fnames.keys()),
                **output_kwargs,
            )
            if output_products != list(output_fnames.keys()):
                raise ValueError("Did not produce expected products")
        elif output_plugin.family == "xrdict_area_product_to_outlist":
            # For xarray_dict type, pass the full fused_xarray_dict.
            output_kwargs["product_name_title"] = (display_name,)
            output_kwargs["mpl_colors_info"] = mpl_colors_info
            output_kwargs = remove_unsupported_kwargs(output_plugin, output_kwargs)
            LOG.interactive(
                "  Producing '%s' family final outputs '%s'...",
                output_plugin.family,
                output_plugin.name,
            )
            output_products = output_plugin(
                xarray_dict=fused_xarray_dict,
                area_def=area_def,
                product_name=prod_plugin.name,
                **output_kwargs,
            )
            for output_product in output_products:
                output_fnames[output_product] = {}
            # No input filename list, no check that output filename list matches
            LOG.info(
                "Not checking output file list for output family %s",
                output_plugin.family,
            )
        else:
            raise ValueError(
                f"Unsupported output family {output_plugin.family} "
                f"for output format {output_formatter}"
            )

    all_final_products = output_all_metadata(
        output_dict, output_fnames, metadata_fnames, alg_xarray, area_def
    )

    return all_final_products


def get_area_defs_from_command_line_args(
    command_line_args, xobjs, variables=None, filter_time=True
):
    """Get area def from command line args."""
    from geoips.sector_utils.utils import (
        get_static_area_defs_for_xarray,
        get_tc_area_defs_for_xarray,
    )
    from geoips.sector_utils.utils import get_trackfile_area_defs
    from geoips.sector_utils.utils import filter_area_defs_actual_time

    sector_list = None
    tcdb_sector_list = None
    tcdb = None
    trackfile_sector_list = None
    trackfiles = None
    trackfile_parser = None
    tc_spec_template = None
    self_register_dataset = None
    self_register_source = None
    area_defs = []

    # If we are requesting an area definition that is tied directly to the reader
    # METADATA, identify it here.
    # This is useful for datasets that are pre-registered to a specific region
    # (like TCs, etc)
    if (
        "reader_defined_area_def" in command_line_args
        and command_line_args["reader_defined_area_def"]
    ):
        area_def = xobjs["METADATA"].attrs["area_definition"]

        # Provide standard area_def information that GeoIPS expects
        if not hasattr(area_def, "sector_type"):
            area_def.attrs["sector_type"] = "reader_defined"

        if not hasattr(area_def, "name"):
            setattr(area_def, "name", area_def.sector_type)

        if not hasattr(area_def, "area_id"):
            setattr(area_def, "area_id", area_def.name)

        if not hasattr(area_def, "description"):
            setattr(area_def, "description", area_def.name)

        area_defs += [area_def]
    LOG.interactive("Getting all area defs from command line args:")
    if "sector_list" in command_line_args:
        sector_list = command_line_args["sector_list"]
        LOG.interactive("  sector_list: %s", sector_list)
    if "tcdb_sector_list" in command_line_args:
        tcdb_sector_list = command_line_args["tcdb_sector_list"]
        LOG.interactive("  tcdb_sector_list: %s", tcdb_sector_list)
    if "tcdb" in command_line_args:
        tcdb = command_line_args["tcdb"]
        LOG.interactive("  tcdb: %s", tcdb)
    if "trackfile_sector_list" in command_line_args:
        trackfile_sector_list = command_line_args["trackfile_sector_list"]
        LOG.interactive("  trackfile_sector_list: %s", trackfile_sector_list)
    if "trackfiles" in command_line_args:
        trackfiles = command_line_args["trackfiles"]
        LOG.interactive("  trackfiles: %s", trackfiles)
    if "trackfile_parser" in command_line_args:
        trackfile_parser = command_line_args["trackfile_parser"]
        LOG.interactive("  trackfile_parser: %s", trackfile_parser)
    if "tc_spec_template" in command_line_args:
        tc_spec_template = command_line_args["tc_spec_template"]
        LOG.interactive("  tc_spec_template: %s", tc_spec_template)

    # This indicates that the "area_definition" will be the definition for one
    # of the native datasets
    if (
        "self_register_dataset" in command_line_args
        and "self_register_source" in command_line_args
    ):
        self_register_dataset = command_line_args["self_register_dataset"]
        self_register_source = command_line_args["self_register_source"]

    if self_register_dataset and self_register_source:
        if (
            "area_definition" in xobjs[self_register_dataset].attrs
            and xobjs[self_register_dataset].attrs["area_definition"] is not None
        ):
            area_def = xobjs[self_register_dataset].attrs["area_definition"]
        else:
            import pyresample

            orig_lons = xobjs[self_register_dataset]["longitude"]
            lons = pyresample.utils.wrap_longitudes(orig_lons)
            area_def = pyresample.geometry.SwathDefinition(
                lons=lons,
                lats=xobjs[self_register_dataset]["latitude"],
            )
            min_lat = xobjs[self_register_dataset]["latitude"].min()
            max_lat = xobjs[self_register_dataset]["latitude"].max()
            min_lon = xobjs[self_register_dataset]["longitude"].min()
            max_lon = xobjs[self_register_dataset]["longitude"].max()
            if max_lon > 180 and min_lon < 180:
                min_lon = lons.where(lons > 0).min()
                max_lon = lons.where(lons < 0).max()
            else:
                min_lon = lons.min()
                max_lon = lons.max()
            area_def.area_extent_ll = [min_lon, min_lat, max_lon, max_lat]
            if (
                "interpolation_radius_of_influence"
                in xobjs[self_register_dataset].attrs
            ):
                area_def.pixel_size_x = xobjs[self_register_dataset].attrs[
                    "interpolation_radius_of_influence"
                ]
                area_def.pixel_size_y = xobjs[self_register_dataset].attrs[
                    "interpolation_radius_of_influence"
                ]
            elif "sample_distance_km" in xobjs[self_register_dataset].attrs:
                area_def.pixel_size_x = xobjs[self_register_dataset].attrs[
                    "sample_distance_km"
                ]
                area_def.pixel_size_y = xobjs[self_register_dataset].attrs[
                    "sample_distance_km"
                ]

        if not hasattr(area_def, "sector_info"):
            setattr(
                area_def,
                "sector_info",
                {
                    "self_register_dataset": self_register_dataset,
                    "self_register_source": self_register_source,
                },
            )
        else:
            area_def.sector_info["self_register_dataset"] = self_register_dataset
            area_def.sector_info["self_register_source"] = self_register_source

        # Provide standard area_def information that GeoIPS expects
        if not hasattr(area_def, "sector_type"):
            setattr(area_def, "sector_type", "self_register")

        if not hasattr(area_def, "name"):
            setattr(area_def, "name", area_def.sector_type)

        if not hasattr(area_def, "area_id"):
            setattr(area_def, "area_id", area_def.name)

        if not hasattr(area_def, "description"):
            setattr(area_def, "description", area_def.name)

        # Add it to the list
        area_defs += [area_def]

    if sector_list:
        if xobjs is None:
            area_defs += get_static_area_defs_for_xarray(None, sector_list)
        else:
            area_defs += get_static_area_defs_for_xarray(xobjs["METADATA"], sector_list)
    if tcdb:
        if xobjs is None:
            raise (TypeError, "Must have xobjs defined for tcdb sectors")
        area_defs += get_tc_area_defs_for_xarray(
            xobjs["METADATA"],
            tcdb_sector_list=tcdb_sector_list,
            tc_spec_template=tc_spec_template,
            trackfile_parser=trackfile_parser,
            aid_type="BEST",
        )
    if trackfiles:
        area_defs += get_trackfile_area_defs(
            trackfiles,
            trackfile_parser,
            trackfile_sector_list,
            tc_spec_template,
            aid_type="BEST",
            start_datetime=xobjs["METADATA"].start_datetime - timedelta(hours=8),
            end_datetime=xobjs["METADATA"].end_datetime + timedelta(hours=3),
        )

    # If we have a "short" data file, return only a single dynamic sector closest to the
    # start time. If longer than one swath for polar orbiters, we may have more than one
    # "hit", so don't filter.
    if (
        filter_time
        and xobjs is not None
        and xobjs["METADATA"].end_datetime - xobjs["METADATA"].start_datetime
        < timedelta(hours=3)
    ):
        area_defs = filter_area_defs_actual_time(
            area_defs, xobjs["METADATA"].start_datetime
        )

    LOG.info("Allowed area_defs: %s", [ad.name for ad in area_defs])
    return list(area_defs)


def get_alg_xarray(
    sect_xarrays,
    area_def,
    prod_plugin,
    processed_xarrays=None,
    resector=True,
    resampled_read=False,
    variable_names=None,
    window_start_time=None,
    window_end_time=None,
):
    """Get alg xarray.

    Parameters
    ----------
    sect_xarrays: dict of xarray.Dataset
        dictionary of xarray Datasets to apply algorithm.
    area_def: pyresample.AreaDefinition
        Spatial region required in the final xarray Datasets.
    prod_plugin: ProductPlugin
        GeoIPS Product Plugin obtained through interfaces.products.get_plugin("name").
    resector: bool, default=True
        Specify whether to resector the data prior to applying the algorithm.
    resampled_read: bool, default=False
        Specify whether a resampled read is required, needed for datatypes that
        will be read within "get_alg_xarray"
    variable_names: list of str
        List of variable names within xarray Datasets to include in the final
        sectored xarray Datasets
    window_start_time: datetime.datetime, default=None
        If specified, sector temporally between window_start_time and window_end_time.
    window_end_time: datetime.datetime, default=None
        If specified, sector temporally between window_start_time and window_end_time.

    Returns
    -------
    xarray.Dataset
        xarray Dataset containing the final data after interpolation, algorithm,
        resectoring, etc have been applied.
    """
    if not variable_names:
        # original input variables from sensor.py (i.e., abi.py)
        variables = get_required_variables(prod_plugin)
    else:
        # If variable_names are passed, actually use them
        # Previously was only being used for checking existence of variables in
        # sectored xarray.
        variables = variable_names

    LOG.interactive("Applying algorithms and interpolation...")

    datasets_for_vars = get_requested_datasets_for_variables(prod_plugin)

    # Get the algorithm and interpolator plugins we need to use, based
    # on the contents of prod_plugin.
    alg_plugin, alg_args, interp_plugin, interp_args = get_alg_and_interp_plugins(
        prod_plugin
    )

    # Re-sector the xarrays if requested.
    curr_sect_xarrays = resector_xarrays(
        resector, sect_xarrays, area_def, variables, window_start_time, window_end_time
    )

    LOG.info("get_alg_xarray required variables: %s", variables)
    LOG.info("get_alg_xarray requested datasets for variables: %s", datasets_for_vars)

    # If we want to run the algorithm prior to interpolation, apply the algorithm here,
    # and return either the unprojected result or interpolated result appropriately.
    # For the xarray dict option, it should probably be more general than JUST
    # unsectored xarray dict with algorithm / without area, but that was the
    # originally supported family. An issue could be created to support xarray
    # dict formats more generally.
    if (
        prod_plugin.family
        in ["algorithm_colormapper", "algorithm_interpolator_colormapper", "algorithm"]
        + PRODUCT_FAMILIES_OF_UNSECTORED_XARRAY_DICT_WITH_ALGORITHM_WITHOUT_AREA
    ):
        LOG.interactive("  Applying algorithms...")
        # All of these apply the algorithm first, so go ahead and
        # apply the algorithm.
        # Some use variables and some use variable_names... So pass both.
        # Some use curr_sect_xarrays and some use sect_xarrays... So pass both.
        # MLS I'm guessing this random selection is not right.
        alg_xarray = apply_alg_first(
            alg_plugin,
            alg_args,
            prod_plugin,
            curr_sect_xarrays,
            sect_xarrays,
            variables,
            variable_names,
            area_def,
        )

        if prod_plugin.family in ["algorithm_interpolator_colormapper"]:
            # Now apply the intepolator after applying the algorithm.
            final_xarray = apply_interp_after_alg(
                alg_xarray,
                interp_plugin,
                interp_args,
                prod_plugin,
                area_def,
                processed_xarrays,
            )
        else:
            final_xarray = alg_xarray

        # MLS This appears to update alg_xarray, not final_xarray, with the
        # area_def information.  So this might not be right..
        final_xarray = add_attrs_from_area_def(final_xarray, alg_xarray, area_def)
        # return here - we are done for either alg_cmap or alg_interp_cmap type
        return final_xarray

    # NOTE if algorithm specified first in product_type, we will not get to this point!
    # Returned from above if statement
    LOG.interactive("  Applying interpolators...")

    # For products that first require interpolator, start with interpolator.
    # These appear to consistently use curr_sect_xarrays and variables.
    # Don't re-interpolate if a variable is found in processed_xarrays.
    interp_xarray = apply_interp_first(
        variables,
        curr_sect_xarrays,
        prod_plugin,
        datasets_for_vars,
        resampled_read,
        area_def,
        processed_xarrays,
    )

    # Make sure we have all the appropriate attributes attached to the current
    # interp_xarray.
    # Use force=False so if attributes were set above, we do not overwrite them.
    # MLS This was originally using sect_xarray, which would have just been
    # the last sect_xarray when looping through the datasets.  Not sure that
    # is what we wanted. Also not sure how much this is going to change outputs.
    copy_standard_metadata(sect_xarrays["METADATA"], interp_xarray, force=False)

    LOG.interactive("  Applying algorithms after interpolators...")

    # Now apply the algorithm after interpolating. Don't reapply if it is
    # found in processed_xarrays.
    interp_xarray = apply_alg_after_interp(
        interp_xarray,
        area_def,
        alg_plugin,
        alg_args,
        prod_plugin,
        variables,
        processed_xarrays,
    )

    # Make sure we have all the appropriate attributes attached to the current
    # interp_xarray.
    # Use force=False so if attributes were set above, we do not overwrite them.
    # MLS This was originally using sect_xarray, which would have just been
    # the last sect_xarray when looping through the datasets.  Not sure that
    # is what we wanted. Also not sure how much this is going to change outputs.
    LOG.interactive("  Setting metadata on final xarray...")
    copy_standard_metadata(sect_xarrays["METADATA"], interp_xarray, force=False)
    # Attach final product_name to the interp_xarray as well (the end goal of
    # this routine).
    if (
        interp_xarray.attrs.get("product_name")
        and interp_xarray.attrs["product_name"] != prod_plugin.name
    ):
        # Only include product_names if there is more than one product_name
        if "product_names" not in interp_xarray.attrs:
            interp_xarray.attrs["product_names"] = [prod_plugin.name]
        else:
            interp_xarray.attrs["product_names"].append(prod_plugin.name)
    interp_xarray.attrs["product_name"] = prod_plugin.name
    # MLS This one uses interp_xarray and interp_xarray...
    # The other one I think passed the wrong ones.
    interp_xarray = add_attrs_from_area_def(interp_xarray, interp_xarray, area_def)

    return interp_xarray


def verify_area_def(
    area_defs,
    check_area_def,
    data_start_datetime,
    data_end_datetime,
    time_range_hours=3,
):
    """Verify current area definition is the closest to the actual data time.

    When looping through multiple dynamic area definitions for a full data file that
    temporally covers more than one dynamic area_def, there is no way of knowing
    which dynamic area_def has the best coverage until AFTER we have actually
    sectored the data to the specific area_def.

    Call this utility on the current area_def (check_area_def) for the sectored
    data file, plus the full list of area definitions (area_defs) that cover the
    FULL data file.

    Returns
    -------
    bool

        * True if the current area definition is NOT dynamic
        * True if the current area definition IS dynamic and
          is the closest temporally to the sectored data.
        * False if the current area definition is removed when
          filtering the list of area definitions based on the
          actual sectored data time.

    """
    retval = True
    # If this is not a dynamic sector, then there is no need to check the
    # temporal matching between the data time and the sector time, because
    # there is no sector time to check.
    if not is_dynamic_sector(check_area_def):
        retval = True
    # If the data coverage is more than time_range_hours, do not check
    # because it may be ambiguous which area definition is actually the "closest".
    elif data_end_datetime - data_start_datetime < timedelta(hours=time_range_hours):
        new_area_defs = filter_area_defs_actual_time(area_defs, data_start_datetime)
        LOG.info("Allowed area_defs: %s", [ad.name for ad in new_area_defs])
        if check_area_def.name not in [ad.name for ad in new_area_defs]:
            retval = False

    return retval


def call(fnames, command_line_args=None):
    """Workflow for running products from a single data source.

    Parameters
    ----------
    fnames : list
        List of strings specifying full paths to input file names to process
    command_line_args : dict
        dictionary of command line arguments

    Returns
    -------
    list
        Return list of strings specifying full paths to output products that
        were produced

    See Also
    --------
    ``geoips.commandline.args``
        Complete list of available command line args.
    """
    from datetime import datetime

    process_datetimes = {}
    process_datetimes["overall_start"] = datetime.utcnow()
    final_products = []
    removed_products = []
    saved_products = []
    database_writes = []
    ss_pid = getpid()

    pid_track = PidLog(ss_pid, logstr="MEMUSG")

    from geoips.commandline.args import check_command_line_args

    # These args should always be checked
    check_args = [
        "sector_list",
        "tcdb",
        "tcdb_sector_list",  # TC Database sectors,
        "trackfiles",
        "trackfile_parser",
        "trackfile_sector_list",  # Flat text trackfile,
        "reader_name",
        "product_name",
        "gridline_annotator",
        "feature_annotator",
        "product_spec_override",
        "output_formatter",
        "filename_formatter",
        "output_formatter_kwargs",
        "filename_formatter_kwargs",
        "output_checker_kwargs",
        "metadata_output_formatter",
        "metadata_filename_formatter",
        "metadata_output_formatter_kwargs",
        "metadata_filename_formatter_kwargs",
        "no_presectoring",
        "sector_adjuster",
        "sector_adjuster_kwargs",
        "reader_defined_area_def",
        "self_register_source",
        "self_register_dataset",
        "window_start_time",
        "window_end_time",
        "sectored_read",
        "resampled_read",
        "product_db",
    ]

    check_command_line_args(check_args, command_line_args)

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

    window_start_time = command_line_args.get("window_start_time")
    window_end_time = command_line_args.get("window_end_time")
    product_name = command_line_args["product_name"]  # 89HNearest
    output_formatter = command_line_args[
        "output_formatter"
    ]  # output_formatters.imagery_annotated
    reader_name = command_line_args["reader_name"]  # ssmis_binary
    reader_kwargs = command_line_args.get("reader_kwargs")
    if not reader_kwargs:
        reader_kwargs = {}
    compare_path = command_line_args["compare_path"]
    output_file_list_fname = command_line_args["output_file_list_fname"]
    sector_adjuster = command_line_args["sector_adjuster"]
    sector_adjuster_kwargs = command_line_args["sector_adjuster_kwargs"]
    self_register_source = command_line_args["self_register_source"]
    self_register_dataset = command_line_args["self_register_dataset"]
    reader_defined_area_def = command_line_args["reader_defined_area_def"]
    sectored_read = command_line_args["sectored_read"]
    resampled_read = command_line_args["resampled_read"]
    product_db = command_line_args["product_db"]
    product_db_writer = command_line_args["product_db_writer"]
    product_db_writer_kwargs = command_line_args["product_db_writer_kwargs"]
    presector_data = not command_line_args["no_presectoring"]
    output_checker_kwargs = command_line_args["output_checker_kwargs"]

    if product_db:
        from geoips.interfaces import databases

        db_writer = databases.get_plugin(product_db_writer)
        if not getenv("GEOIPS_DB_URI"):
            raise ValueError("Need to set $GEOIPS_DB_URI")

    # Load plugins
    reader_plugin = readers.get_plugin(reader_name)

    pid_track.print_mem_usg()

    num_jobs = 0
    LOG.interactive(
        "Reading metadata from dataset with reader '%s'...", reader_plugin.name
    )
    xobjs = reader_plugin(fnames, metadata_only=True, **reader_kwargs)
    source_name = xobjs["METADATA"].source_name
    pid_track.print_mem_usg()

    prod_plugin = products.get_plugin(
        source_name, product_name, command_line_args["product_spec_override"]
    )

    variables = get_required_variables(prod_plugin)

    # If we need to pull area_defs from the reader, then we need to read in
    # order to determin what to run
    if (not sectored_read and not resampled_read) and (
        reader_defined_area_def or (self_register_source and self_register_dataset)
    ):
        LOG.interactive(
            "Reading full dataset "
            "for self registered products "
            "with reader '%s'...",
            reader_plugin.name,
        )
        xobjs = reader_plugin(
            fnames, metadata_only=False, chans=variables, **reader_kwargs
        )

    # Use the xarray objects and command line args to determine required area_defs
    pid_track.print_mem_usg()
    area_defs = get_area_defs_from_command_line_args(
        command_line_args, xobjs, variables, filter_time=True
    )

    # If we do not need to pull area_defs from the reader, read the data AFTER
    # we determine we have areas to run
    if area_defs and (
        not reader_defined_area_def
        and not self_register_source
        and not sectored_read
        and not resampled_read
    ):
        pid_track.print_mem_usg()
        LOG.interactive("Reading full dataset with reader '%s'...", reader_plugin.name)
        xobjs = reader_plugin(
            fnames, metadata_only=False, chans=variables, **reader_kwargs
        )

    pid_track.print_mem_usg()
    # If we have a product of a family that does not require an area definition,
    # and operates on dictionaries of xarrays, process it here.
    # This will not have any required area_defs, so will never make it into
    # the loop through all area_defs below.
    if prod_plugin.family in PRODUCT_FAMILIES_OF_XARRAY_DICT_WITHOUT_AREA:
        LOG.interactive(
            "Reading full dataset for unsectored products with reader '%s'...",
            reader_plugin.name,
        )
        xdict = reader_plugin(fnames, metadata_only=False, **reader_kwargs)
        # If this product family requires an algorithm to be applied, apply here.
        if (
            prod_plugin.family
            in PRODUCT_FAMILIES_OF_UNSECTORED_XARRAY_DICT_WITH_ALGORITHM_WITHOUT_AREA
        ):
            xdict = get_alg_xarray(
                xdict,
                area_def=None,
                prod_plugin=prod_plugin,
                resector=False,
                resampled_read=resampled_read,
                window_start_time=window_start_time,
                window_end_time=window_end_time,
            )
        # This is a workaround so these products can use single source and other
        # algorithms which don't return a dictionary of xarrays. Just convert this back
        # to a dictionary under the hood and hope the metadata included in 'xdict.attrs'
        # is enough for your filename formatter.
        if not isinstance(xdict, dict):
            xdict = {prod_plugin.name: xdict, "METADATA": xdict[[]]}

        final_products += process_xarray_dict_to_output_format(
            xdict, variables, prod_plugin, command_line_args
        )
    # If we do NOT want to apply an algorithm to a dataset, but we DO want
    # to allow sectoring to a given area, just read in the data at this point,
    # and sectoring will be handled within the loop over all area defs below.
    # This looks like we are missing an option for applying an algorithm
    # and sectoring the dataset to a given area. We may need to create an
    # issue to resolve this missing "order of operations" if anyone needs it
    # before the order based procflow is finalized.
    elif (
        prod_plugin.family
        in PRODUCT_FAMILIES_OF_UNSECTORED_XARRAY_DICT_WITHOUT_ALGORITHM_WITH_AREA
    ):
        LOG.interactive(
            "Reading full dataset for unsectored products requiring area "
            "definition, using reader '%s'...",
            reader_plugin.name,
        )
        # Note we only read in the data in this case, and do NOT process to
        # the final products.  Since we use the area definitions for these
        # product families, the final products will be obtained during the
        # loop through all area defs below.
        xdict = reader_plugin(fnames, metadata_only=False, **reader_kwargs)

    pid_track.print_mem_usg()

    new_attrs = {"filename_extra_fields": {}}
    # This is the main loop over all area defs - used for any processing that
    # either sectors or interpolates the datasets (even products that self
    # register to one of the existing datasets will use area definitions -
    # an area definition is created from the dataset that is being self
    # registered to in that case).  Only cases where no sectoring or
    # interpolation are needed will bypass this loop
    # (PRODUCT_FAMILIES_OF_XARRAY_DICT_WITHOUT_AREA).
    for area_def in area_defs:
        # If the current product is of family that DOES NOT require sectoring,
        # DOES NOT apply an algorithm, and DOES require an area_definition,
        # then process it here.
        if (
            prod_plugin.family
            in PRODUCT_FAMILIES_OF_UNSECTORED_XARRAY_DICT_WITHOUT_ALGORITHM_WITH_AREA
        ):
            LOG.interactive(
                "Producing outputs for unsectored product '%s'...", prod_plugin.name
            )
            final_products += process_xarray_dict_to_output_format(
                xdict, variables, prod_plugin, command_line_args, area_def
            )
            continue

        LOG.info("\n\n\n\nNEXT area definition: %s", area_def)
        pad_area_def = pad_area_definition(area_def, xobjs["METADATA"].source_name)

        # Only attempt to read within the area_def loop if we have requested
        # "sectored_read" or "resampled_read"
        if sectored_read or resampled_read:
            try:
                LOG.interactive(
                    "Reading sectored dataset "
                    "for self registered products "
                    "with reader '%s'...",
                    reader_plugin.name,
                )
                xobjs = reader_plugin(
                    fnames,
                    metadata_only=False,
                    chans=variables,
                    area_def=pad_area_def,
                    **reader_kwargs,
                )
            # geostationary satellites fail with IndexError when the area_def
            # does not intersect the data.  Just skip those.  We need a better
            # method for handling this generally, but for
            # now skip IndexErrors.
            except IndexError as resp:
                LOG.error("SKIPPING no coverage for %s, %s", area_def.name, str(resp))
                continue

        process_datetimes[area_def.area_id] = {}
        process_datetimes[area_def.area_id]["start"] = datetime.utcnow()
        # add satellite_azimuth_angle and solar_azimuth_angle into list of the variables
        # for ABI only (come from ABI reader)
        if area_def.sector_type in ["reader_defined", "self_register"]:
            LOG.interactive(
                "CONTINUE Not sectoring sector_type %s", area_def.sector_type
            )
            pad_sect_xarrays = xobjs
        else:
            if presector_data:
                LOG.interactive("Sectoring xarrays, variables %s...", variables)
                # Note window start/end time overrides hours before/after sector time
                pad_sect_xarrays = sector_xarrays(
                    xobjs,
                    pad_area_def,
                    varlist=variables,
                    hours_before_sector_time=6,
                    hours_after_sector_time=9,
                    drop=True,
                    window_start_time=window_start_time,
                    window_end_time=window_end_time,
                )
            else:
                pad_sect_xarrays = xobjs

        pid_track.print_mem_usg()
        if len(pad_sect_xarrays.keys()) == 0:
            LOG.interactive(
                "SKIPPING no sectored xarrays returned for %s", area_def.name
            )
            continue

        # Now we check to see if the current area_def is the closest one to
        # the dynamic time, if appropriate. We could end up with multiple
        # area_defs for a single dynamic sector, and we can't truly test to see
        # how close each one is to the actual data until we sector it...
        # So, check now to see if any of the area_defs in list_area_defs is
        # closer than pad_area_def
        if not verify_area_def(
            area_defs,
            pad_area_def,
            pad_sect_xarrays["METADATA"].start_datetime,
            pad_sect_xarrays["METADATA"].end_datetime,
        ):
            LOG.info(
                "SKIPPING duplicate area_def, out of time range, for %s", area_def.name
            )
            continue

        LOG.interactive("Producing sectored outputs...")
        curr_output_products = process_sectored_data_output(
            pad_sect_xarrays,
            variables,
            prod_plugin,
            command_line_args,
            area_def=area_def,
        )

        pid_track.print_mem_usg()
        # If we had a request for sectored data processing, skip the rest of the loop
        if curr_output_products:
            final_products += curr_output_products
            continue

        if sector_adjuster:
            sect_adj_plugin = sector_adjusters.get_plugin(sector_adjuster)
            # Use normal size sectored xarray when running sector_adjuster, not padded
            # Center time (mintime + (maxtime - mintime)/2) is very slightly
            # different for different size sectored arrays, so for consistency
            # if we change padding amounts, use the fully sectored array for
            # adjusting the area_def.
            if pad_sect_xarrays["METADATA"].source_name not in ["amsu-b", "mhs"]:
                if area_def.sector_type in ["reader_defined", "self_register"]:
                    LOG.interactive(
                        "CONTINUE Not sectoring sector_type %s", area_def.sector_type
                    )
                    sect_xarrays = pad_sect_xarrays
                else:
                    LOG.interactive("Sectoring padded xarrays...")
                    if presector_data:
                        # Note window start/end time overrides hours
                        # before/after sector time
                        sect_xarrays = sector_xarrays(
                            pad_sect_xarrays,
                            area_def,
                            varlist=variables,
                            hours_before_sector_time=6,
                            hours_after_sector_time=9,
                            drop=True,
                            window_start_time=window_start_time,
                            window_end_time=window_end_time,
                        )
                    else:
                        sect_xarrays = pad_sect_xarrays
                if (
                    sect_adj_plugin.family
                    == "list_xarray_list_variables_to_area_def_out_fnames"
                ):
                    LOG.interactive("Adjusting sectors with %s...", sector_adjuster)
                    area_def, adadj_fnames = sect_adj_plugin(
                        list(sect_xarrays.values()),
                        area_def,
                        variables,
                        **sector_adjuster_kwargs,
                    )
                else:
                    LOG.interactive("Adjusting sectors with %s...", sector_adjuster)
                    area_def = sect_adj_plugin(
                        list(sect_xarrays.values()),
                        area_def,
                        variables,
                        **sector_adjuster_kwargs,
                    )
            else:
                # AMSU-b specifically needs full swath width...
                if (
                    sect_adj_plugin.family
                    == "list_xarray_list_variables_to_area_def_out_fnames"
                ):
                    LOG.interactive("Adjusting sectors with %s...", sector_adjuster)
                    area_def, adadj_fnames = sect_adj_plugin(
                        list(pad_sect_xarrays.values()),
                        area_def,
                        variables,
                        **sector_adjuster_kwargs,
                    )
                else:
                    LOG.interactive("Adjusting sectors with %s...", sector_adjuster)
                    area_def = sect_adj_plugin(
                        list(pad_sect_xarrays.values()),
                        area_def,
                        variables,
                        **sector_adjuster_kwargs,
                    )
            # These will be added to the alg_xarray
            # new_attrs['area_definition'] = area_def
            if "adjustment_id" in area_def.sector_info:
                new_attrs["filename_extra_fields"]["adjustment_id"] = (
                    area_def.sector_info["adjustment_id"]
                )

        pid_track.print_mem_usg()
        all_vars = []
        for key, xobj in pad_sect_xarrays.items():
            # Double check the xarray object actually contains data
            for var in list(xobj.variables.keys()):
                if xobj[var].count() > 0:
                    all_vars.append(var)
        # If the required variables are not contained within the xarray objects, do not
        # attempt to process (variables in product algorithm are not available)
        if set(variables).issubset(all_vars):
            # We want to write out the padded xarray for "xarray_data" output types
            # Otherwise, we need the fully sectored output
            output_plugin = output_formatters.get_plugin(output_formatter)
            if output_plugin.family == "xarray_data":
                alg_xarray = get_alg_xarray(
                    pad_sect_xarrays,
                    pad_area_def,
                    prod_plugin,
                    resector=False,
                    resampled_read=resampled_read,
                    window_start_time=window_start_time,
                    window_end_time=window_end_time,
                )
            elif area_def.sector_type in ["reader_defined", "self_register"]:
                alg_xarray = get_alg_xarray(
                    pad_sect_xarrays,
                    pad_area_def,
                    prod_plugin,
                    resector=False,
                    resampled_read=resampled_read,
                    variable_names=variables,
                    window_start_time=window_start_time,
                    window_end_time=window_end_time,
                )
            else:
                alg_xarray = get_alg_xarray(
                    pad_sect_xarrays,
                    area_def,
                    prod_plugin,
                    resector=presector_data,
                    resampled_read=resampled_read,
                    window_start_time=window_start_time,
                    window_end_time=window_end_time,
                )

            pid_track.print_mem_usg()

            # This defaults to "covg_func" and "covg_args" - if
            # image_production_covg_* exist, it will use those.
            covg_plugin = get_covg_from_product(
                prod_plugin,
                covg_field="image_production_coverage_checker",
            )
            covg_args = get_covg_args_from_product(
                prod_plugin,
                covg_field="image_production_coverage_checker",
            )
            # Set variable_name to prod_plugin.name if not defined.
            # Always use variable_name if it is defined.
            # Remove from args so there is not a duplicate are when passing
            # (since we are passing covg_varname explicitly).
            # Note get_covg_args_from_product was updated to return a copy of
            # covg_args, so this does not impact future uses of the product.
            covg_varname = covg_args.pop("variable_name", prod_plugin.name)
            # Note variables can be specified as DATASET:VARIABLE, since this is a
            # preprocessed alg_xarray, and not a dictionary of datasets, just use the
            # variable name (we expect the correct variable will exist in this final
            # processed array)
            if ":" in covg_varname:
                covg_varname = covg_varname.split(":")[1]

            covg = covg_plugin(
                alg_xarray,
                covg_varname,
                area_def,
                **covg_args,
            )

            fname_covg_plugin = get_covg_from_product(
                prod_plugin,
                covg_field="filename_coverage_checker",
            )
            fname_covg_args = get_covg_args_from_product(
                prod_plugin,
                covg_field="filename_coverage_checker",
            )
            # Set variable_name to prod_plugin.name if not defined.
            # Always use variable_name if it is defined.
            # Remove from args so there is not a duplicate are when passing
            # (since we are passing covg_varname explicitly).
            # Note get_covg_args_from_product was updated to return a copy of
            # covg_args, so this does not impact future uses of the product.
            fname_covg_varname = fname_covg_args.pop("variable_name", prod_plugin.name)
            # Note variables can be specified as DATASET:VARIABLE, since this is a
            # preprocessed alg_xarray, and not a dictionary of datasets, just use the
            # variable name (we expect the correct variable will exist in this final
            # processed array)
            if ":" in fname_covg_varname:
                fname_covg_varname = fname_covg_varname.split(":")[1]
            fname_covg = fname_covg_plugin(
                alg_xarray,
                fname_covg_varname,
                area_def,
                **fname_covg_args,
            )

            for attrname in new_attrs:
                LOG.info(
                    "ADDING attribute %s %s to alg_xarray",
                    attrname,
                    new_attrs[attrname],
                )
                alg_xarray.attrs[attrname] = new_attrs[attrname]

            # Apply a new coverage scheme (coverage within 300km radical range
            # from TC center) to be done  ????

            minimum_coverage = 10
            command_line_minimum_coverage = get_minimum_coverage(
                prod_plugin, command_line_args
            )
            if hasattr(alg_xarray, "minimum_coverage"):
                minimum_coverage = alg_xarray.minimum_coverage
            if command_line_minimum_coverage is not None:
                minimum_coverage = command_line_minimum_coverage
            LOG.interactive(
                "Required coverage %s for product %s, actual coverage %s",
                minimum_coverage,
                prod_plugin.name,
                covg,
            )
            if covg < minimum_coverage and fname_covg < minimum_coverage:
                LOG.interactive(
                    "SKIPPING: Insufficient coverage %s / %s for "
                    "data products for %s, %s required",
                    covg,
                    fname_covg,
                    area_def.name,
                    minimum_coverage,
                )
                continue

            output_formatter_kwargs = get_output_formatter_kwargs(
                command_line_args, xarray_obj=alg_xarray, area_def=area_def
            )

            curr_products = plot_data(
                command_line_args,
                alg_xarray,
                area_def,
                prod_plugin,
                output_formatter_kwargs,
            )
            if not curr_products:
                continue

            pid_track.print_mem_usg()
            final_products += curr_products
            curr_removed_products, curr_saved_products = remove_duplicates(
                curr_products, remove_files=True
            )
            removed_products += curr_removed_products
            saved_products += curr_saved_products

            if product_db:
                for fprod, fname_fmt in curr_products.items():
                    additional_attrs = {
                        "coverage": covg,
                        "product": product_name,
                        "fileType": fprod.split(".")[-1],
                    }
                    if db_writer.family == "xarray_area_def_to_table":
                        product_added = db_writer(
                            product_filename=fprod,
                            xarray_obj=alg_xarray,
                            area_def=area_def,
                            additional_attrs=additional_attrs,
                            **product_db_writer_kwargs,
                        )
                        database_writes += [product_added]
                    elif db_writer.family == "xarray_dict_to_table":
                        product_added = db_writer(
                            product_filename=fprod,
                            xarray_dict=alg_xarray,
                            area_def=area_def,
                            additional_attrs=additional_attrs,
                            **product_db_writer_kwargs,
                        )
                        database_writes += [product_added]
                    else:
                        LOG.error(
                            "FAILED DB WRITE: Only "
                            "xarray_area_def_to_table and xarray_dict_to_table "
                            "db_writer families supported. Either reformat "
                            "db_writer plugin as correct family, or add support "
                            "for additional families in the procflow and "
                            "databases interface."
                        )

            process_datetimes[area_def.area_id]["end"] = datetime.utcnow()
            num_jobs += 1
        else:
            LOG.interactive(
                'SKIPPING No coverage or required variables "%s" for %s %s',
                variables,
                xobjs["METADATA"].source_name,
                area_def.name,
            )

    LOG.interactive(
        "\n\n\nProcessing complete! Checking outputs...\n\n",
    )
    process_datetimes["overall_end"] = datetime.utcnow()

    if output_file_list_fname:
        LOG.info("Writing successful outputs to %s", output_file_list_fname)
        with open(output_file_list_fname, "w", encoding="utf8") as fobj:
            fobj.writelines(
                "\n".join([replace_geoips_paths(fname) for fname in final_products])
            )
            # If we don't write out the last newline, then wc won't return the
            # appropriate number, and we won't get to the last file when attempting to
            # loop through
            fobj.writelines(["\n"])

    retval = 0
    if compare_path:
        from geoips.interfaces.module_based.output_checkers import output_checkers

        for output_product in final_products:
            plugin_name = output_checkers.identify_checker(output_product)
            output_checker = output_checkers.get_plugin(plugin_name)
            kwargs = {}
            if output_checker.name in output_checker_kwargs:
                kwargs = output_checker_kwargs[output_checker.name]
            retval += output_checker(
                output_checker,
                compare_path.replace("<product>", product_name)
                .replace("<procflow>", "single_source")
                .replace("<output>", output_formatter),
                [output_product],
                **kwargs,
            )

    LOG.interactive(
        "\n\n\nThe following products were produced from procflow %s\n\n",
        basename(__file__),
    )
    for output_product in final_products:
        LOG.interactive(
            "    \u001b[34mSINGLESOURCESUCCESS\033[0m %s",
            replace_geoips_paths(output_product, curly_braces=True),
        )
        if output_product in database_writes:
            LOG.interactive("    DATABASESUCCESS %s", output_product)
    for removed_product in removed_products:
        LOG.interactive("    DELETEDPRODUCT %s", removed_product)

    pid_track.print_mem_usg(verbose=True)

    LOG.interactive("READER_NAME: %s", reader_name)
    LOG.interactive("PRODUCT_NAME: %s", product_name)
    LOG.interactive("NUM_PRODUCTS: %s", len(final_products))
    LOG.interactive("NUM_DELETED_PRODUCTS: %s", len(removed_products))
    output_process_times(process_datetimes, num_jobs, job_str="single_source procflow")
    pid_track.save_exit()
    return retval
