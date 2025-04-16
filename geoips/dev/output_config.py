# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Interpolation interface will be deprecated v2.0.

Wrapper functions for geoips output_config specifications.

This functionality will be replaced with a class-based implementation v2.0,
and deprecated at that time.
"""
import logging
from geoips.interfaces import products
from geoips.interfaces import colormappers
from geoips.interfaces import feature_annotators
from geoips.interfaces import gridline_annotators

LOG = logging.getLogger(__name__)


# ### Output config dictionaries ###
def is_valid_output_config(output_config_dict):
    """Interface will be deprecated v2.0.

    Check that requested output_config dictionary is properly formatted.

    The dictionary of output_config
    parameters fully determines the outputs required for a given set of
    data files.

    Dictionary of output_config parameters currently specified by a
    full path to a YAML file:
    and requested via commandline with:
    ``--output_config <full_path_to_YAML_output_config>``

    Parameters
    ----------
    output_config_dict : dict
        Dictionary of output config parameters

    Returns
    -------
    is_valid : bool
        * True if ``output_config_dict`` is a properly formatted dictionary of
          output parameters.
        * False if output_config_dict:
            * does not contain supported ``output_config_type``,
            * does not contain all ``required`` fields,
            * contains non-supported ``optional`` fields

    Notes
    -----
    output_config_types currently one of:
        * ``single_source``
        * ``fused``
    """
    required_keys = {}
    optional_keys = {}

    required_keys["single_source"] = {
        "output_config_type": [],
        "reader_name": [],
        "file_names": [],
        "sectored_read": [],
        "available_sectors": [],
        "outputs": [
            "requested_sector_type",
            "output_formatter",
            "filename_formatters",
            "product_names",
        ],
    }

    optional_keys["single_source"] = {
        "available_sectors": [
            "sector_list",
            "trackfile_parser",
            "trackfiles",
            "tc_spec_template",
        ],
        "outputs": [
            "remove_duplicates",
            "metadata_filename_formatter",
            "metadata_filename_formatters",
            "metadata_filename_formatters_kwargs",
            "minimum_coverages",
            "minimum_coverage",
            "compare_path",
            "feature_annotator",
            "gridline_annotator",
        ],
    }

    required_keys["fused"] = required_keys["single_source"].copy()
    optional_keys["fused"] = optional_keys["single_source"].copy()
    optional_keys["fused"] = {
        "fuse_files": [],
        "fuse_reader": [],
        "fuse_product": [],
        "outputs": {"background_products": ["config_names", "product_names"]},
    }

    if "output_config_type" not in output_config_dict:
        LOG.error(
            "INVALID OUTPUT CONFIG '%s': "
            "'output_config_type' must be defined within output config dictionary",
            output_config_dict.keys(),
        )
        return False

    if output_config_dict["output_config_type"] not in required_keys:
        LOG.error(
            "INVALID OUTPUT CONFIG '%s': "
            "'output_config_type' in output config dictionary must be one of '%s'",
            output_config_dict.keys(),
            list(required_keys.keys()),
        )
        return False

    output_config_type = output_config_dict["output_config_type"]

    # If we don't have all of the required keys, return False
    if not set(required_keys[output_config_type]).issubset(set(output_config_dict)):
        LOG.error(
            "INVALID OUTPUT CONFIG '%s': "
            "'%s' output config dictionary must contain the following fields: '%s'",
            output_config_dict.keys(),
            output_config_type,
            list(required_keys[output_config_type]),
        )
        return False

    # If we have non-allowed keys, return False
    if not set(output_config_dict).issubset(
        required_keys[output_config_type] + optional_keys[output_config_type]
    ):
        LOG.error(
            "INVALID OUTPUT CONFIG'%s': "
            "Unknown fields in '%s' output config dictionary: '%s'",
            output_config_dict.keys(),
            output_config_type,
            set(output_config_dict).difference(
                required_keys[output_config_type] + optional_keys[output_config_type]
            ),
        )
        return False

    # Probably need to add in the nested fields too...

    # If we get here, then the output config dictionary format is valid.
    return True


def get_output_config_type(output_config_dict):
    """Interface will be deprecated v2.0.

    Retrieve output_config_type of the passed output_config_dict, found in:
           output_config_dict['output_config_type']

    See: geoips.dev.output_config.is_valid_output_config for full list of
    supported output_config types.

    Parameters
    ----------
    output_config_dict : dict
        dictionary of complete output config parameters

    Returns
    -------
        (str) : output_config type, found in output_config_dict['output_config_type']
    """
    return output_config_dict["output_config_type"]


def get_filename_formatters(output_dict):
    """Interface will be deprecated v2.0."""
    if "filename_formatter" in output_dict and isinstance(
        output_dict["filename_formatter"], str
    ):
        return [output_dict["filename_formatter"]]
    else:
        return output_dict["filename_formatters"]


def get_output_formatter(output_dict):
    """Interface will be deprecated v2.0."""
    return output_dict["output_formatter"]


def get_metadata_output_formatter(output_dict):
    """Interface will be deprecated v2.0."""
    if "metadata_output_formatter" in output_dict:
        return output_dict["metadata_output_formatter"]
    return None


def get_metadata_filename_formatter(filename_formatter, output_dict):
    """Interface will be deprecated v2.0."""
    fname_format = None

    if "metadata_filename_formatter" in output_dict and isinstance(
        output_dict["metadata_filename_formatter"], str
    ):
        fname_format = output_dict["metadata_filename_formatter"]

    elif (
        "metadata_filename_formatters" in output_dict
        and filename_formatter in output_dict["metadata_filename_formatters"]
    ):
        fname_format = output_dict["metadata_filename_formatters"][filename_formatter]

    elif (
        "metadata_filename_formatters" in output_dict
        and "all" in output_dict["metadata_filename_formatters"]
    ):
        fname_format = output_dict["metadata_filename_formatters"]["all"]

    return fname_format


def get_minimum_coverage(product_name, output_dict):
    """Interface will be deprecated v2.0."""
    minimum_coverage = None

    if (
        "minimum_coverage" in output_dict
        and output_dict["minimum_coverage"] is not None
    ):
        minimum_coverage = float(output_dict["minimum_coverage"])

    elif (
        "minimum_coverages" in output_dict
        and product_name in output_dict["minimum_coverages"]
    ):
        minimum_coverage = float(output_dict["minimum_coverages"][product_name])

    elif (
        "minimum_coverages" in output_dict and "all" in output_dict["minimum_coverages"]
    ):
        minimum_coverage = float(output_dict["minimum_coverages"]["all"])

    if minimum_coverage is not None and (
        minimum_coverage < 0 or minimum_coverage > 100
    ):
        raise ValueError(
            "Minimum coverage must be percentage between 0 and 100, "
            f"{minimum_coverage} invalid"
        )

    return minimum_coverage


def get_filename_formatter_kwargs(filename_formatter, output_dict):
    """Interface will be deprecated v2.0.

    Return dictionary of filename_formatters_kwargs.

    based on what was passed in via the YAML output config
    dictionary, as well as default kwargs.

    If "filename_formatter_kwargs (singular) is passed command line, use
    that to override ALL filename_formatters_kwargs specified in YAML output config.
    """
    filename_formatter_kwargs = {}

    # YAML output config arguments
    if (
        "filename_formatters_kwargs" in output_dict
        and "all" in output_dict["filename_formatters_kwargs"]
    ):
        filename_formatter_kwargs = output_dict["filename_formatters_kwargs"]["all"]
    if (
        "filename_formatters_kwargs" in output_dict
        and filename_formatter in output_dict["filename_formatters_kwargs"]
    ):
        filename_formatter_kwargs = output_dict["filename_formatters_kwargs"][
            filename_formatter
        ]
    # Command line argument overrides all
    if "filename_formatter_kwargs" in output_dict:
        filename_formatter_kwargs = output_dict["filename_formatter_kwargs"]

    filename_formatter_kwargs["output_dict"] = output_dict

    return filename_formatter_kwargs


def get_metadata_filename_formatter_kwargs(filename_formatter, output_dict):
    """Interface will be deprecated v2.0.

    Return dictionary of filename_formatters_kwargs.

    based on what was passed in via the YAML output config
    dictionary, as well as default kwargs
    """
    metadata_filename_formatter_kwargs = {}

    if (
        "metadata_filename_formatters_kwargs" in output_dict
        and "all" in output_dict["metadata_filename_formatters_kwargs"]
    ):
        metadata_filename_formatter_kwargs = output_dict[
            "metadata_filename_formatters_kwargs"
        ]["all"]

    if (
        "metadata_filename_formatters_kwargs" in output_dict
        and filename_formatter in output_dict["metadata_filename_formatters_kwargs"]
    ):
        metadata_filename_formatter_kwargs = output_dict[
            "metadata_filename_formatters_kwargs"
        ][filename_formatter]

    metadata_filename_formatter_kwargs["output_dict"] = output_dict

    return metadata_filename_formatter_kwargs


def set_lonlat_spacing(gridline_annotator, area_def):
    """Interface will be deprecated v2.0."""
    if (
        gridline_annotator is None
        or "grid_lat_spacing" not in gridline_annotator.keys()
        or "grid_lon_spacing" not in gridline_annotator.keys()
        or gridline_annotator["grid_lon_spacing"] == "auto"
        or gridline_annotator["grid_lat_spacing"] == "auto"
    ):
        from pyresample import utils

        minlat = area_def.area_extent_ll[1]
        maxlat = area_def.area_extent_ll[3]
        minlon = utils.wrap_longitudes(area_def.area_extent_ll[0])
        maxlon = utils.wrap_longitudes(area_def.area_extent_ll[2])
        if minlon > maxlon and maxlon < 0:
            maxlon = maxlon + 360
        lon_extent = maxlon - minlon
        lat_extent = maxlat - minlat

        if lon_extent > 5:
            lon_spacing = int(lon_extent / 5)
        elif lon_extent > 2.5:
            lon_spacing = 1
        else:
            lon_spacing = lon_extent / 5.0

        if lat_extent > 5:
            lat_spacing = int(lat_extent / 5)
        elif lat_extent > 2.5:
            lat_spacing = 1
        else:
            lat_spacing = lat_extent / 5.0

        LOG.info("lon_extent: %s, lon_spacing: %s", lon_extent, lon_spacing)
        gridline_annotator["grid_lat_spacing"] = lat_spacing
        gridline_annotator["grid_lon_spacing"] = lon_spacing

    return gridline_annotator


def get_output_formatter_kwargs(
    output_dict,
    xarray_obj=None,
    area_def=None,
    sector_type=None,
    bg_files=None,
    bg_xarrays=None,
    bg_product_name=None,
):
    """Interface will be deprecated v2.0."""
    output_formatter_kwargs = {}
    if "output_formatter_kwargs" in output_dict:
        output_formatter_kwargs = output_dict["output_formatter_kwargs"].copy()

    if (
        "gridline_annotator" in output_dict
        and output_dict["gridline_annotator"] is not None
    ):
        gridline_annotator = gridline_annotators.get_plugin(
            output_dict["gridline_annotator"]
        )
        gridline_annotator = set_lonlat_spacing(gridline_annotator, area_def)
        output_formatter_kwargs["gridline_annotator"] = gridline_annotator

    if (
        "feature_annotator" in output_dict
        and output_dict["feature_annotator"] is not None
    ):
        feature_annotator = feature_annotators.get_plugin(
            output_dict["feature_annotator"]
        )
        output_formatter_kwargs["feature_annotator"] = feature_annotator

    if bg_files and "background_products" in output_dict and sector_type in bg_xarrays:
        output_formatter_kwargs["bg_xarray"] = bg_xarrays[sector_type]
        output_formatter_kwargs["bg_data"] = output_formatter_kwargs["bg_xarray"][
            bg_product_name
        ].to_masked_array()
        output_formatter_kwargs["bg_product_name_title"] = bg_product_name
        output_formatter_kwargs["bg_mpl_colors_info"] = None
        if bg_product_name:
            bg_prod_plugin = products.get_plugin(
                output_formatter_kwargs["bg_xarray"].source_name,
                bg_product_name,
                output_dict.get("product_spec_override"),
            )
            bg_cmap_plugin = colormappers.get_plugin(
                bg_prod_plugin["spec"]["colormapper"]["plugin"]["name"]
            )
            bg_cmap_args = bg_prod_plugin["spec"]["colormapper"]["plugin"]["arguments"]

            output_formatter_kwargs["bg_mpl_colors_info"] = bg_cmap_plugin(
                **bg_cmap_args
            )

    output_formatter_kwargs["output_dict"] = output_dict

    return output_formatter_kwargs


def get_metadata_output_formatter_kwargs(output_dict):
    """Interface will be deprecated v2.0."""
    metadata_output_formatter_kwargs = {}
    if "metadata_output_formatter_kwargs" in output_dict:
        metadata_output_formatter_kwargs = output_dict[
            "metadata_output_formatter_kwargs"
        ].copy()
        metadata_output_formatter_kwargs["output_dict"] = output_dict
    return metadata_output_formatter_kwargs


def produce_current_time(config_dict, metadata_xobj, output_dict_keys=None):
    """Interface will be deprecated v2.0.

    Determine if the current data file needs to be processed,
        based on the requested times.
    If output_dict_key is included, apply to only the currently
        requested output_dict.
    If output_dict_key is None, check ALL outputs to determine if
        ANY need the current time.
    """
    if output_dict_keys is None:
        output_dict_keys = config_dict["outputs"].keys()

    retval = False
    for output_dict_key in output_dict_keys:
        LOG.info("CHECKING for required time in output_dict: %s", output_dict_key)
        output_dict = config_dict["outputs"][output_dict_key]
        # If 'produce_times' is not in the current output_dict,
        # it means we DO NOT filter based on time, so we
        # will need this file time processed.
        if "produce_times" not in output_dict:
            LOG.info(
                'WILL PROCESS "produce_times" not included in output_dict: %s',
                output_dict_key,
            )
            retval = True
        elif "required_minutes" in output_dict["produce_times"]:
            if (
                metadata_xobj.start_datetime.minute
                in output_dict["produce_times"]["required_minutes"]
            ):
                LOG.info(
                    "WILL PROCESS produce_times['required_minutes']=%s "
                    "includes current minute '%s', '%s'",
                    output_dict["produce_times"]["required_minutes"],
                    metadata_xobj.start_datetime.minute,
                    metadata_xobj.start_datetime,
                )
                retval = True

    return retval


def test_output_config_interface(output_config_dict):
    """Interface will be deprecated v2.0.

    Finds and opens every product params dict available within the current
    geoips instantiation

    See geoips.dev.output_config.is_valid_output_config?
        for a list of available product params dict types and
        associated call signatures / return values.

    Returns
    -------
    list
        List of all successful output_config information
    """
    out_dict = {}
    # LOG.info('Checking source %s', source_name)
    out_dict["validity_check"] = is_valid_output_config(output_config_dict)
    out_dict["get_output_config_type"] = get_output_config_type(output_config_dict)

    # Need to loop through all the outputs and available sectors...

    return out_dict
