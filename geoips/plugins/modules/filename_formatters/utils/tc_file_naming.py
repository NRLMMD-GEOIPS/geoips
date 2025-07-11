# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Utilities for TC filenaming, for use within geoips filename formatters."""

import logging
from datetime import datetime, timedelta, timezone
from glob import glob
from os.path import basename as pathbasename
from os.path import join as pathjoin
from geoips.interfaces import products

LOG = logging.getLogger(__name__)

# interface = None indicates to the GeoIPS interfaces that this is not a valid
# plugin, and this module will not be added to the GeoIPS plugin registry.
# This allows including python modules within the geoips/plugins directory
# that provide helper or utility functions to the geoips plugins, but are
# not full GeoIPS plugins on their own.
interface = None


def get_storm_subdir(
    basin_path, base_tc_stormname, tc_stormnum, output_dict, sector_info
):
    """Get the TC storm subdirectory."""
    # Default to just the "base" tc storm name (ie, WP932022 or SH162022)
    tc_stormname = base_tc_stormname

    # If it exists, get the storm_start_datetime from the sector_info dictionary
    storm_start_datetime = None
    if sector_info and "original_storm_start_datetime" in sector_info:
        storm_start_datetime = sector_info["original_storm_start_datetime"]
    elif sector_info and "storm_start_datetime" in sector_info:
        storm_start_datetime = sector_info["storm_start_datetime"]

    # Now check if any "file_path_modifications" were specified in the output config.
    # This will determine if we need a more specific/unique subdirectory for a specific
    # storm.
    # Ie, WP932022.2022020506 vs WP932022
    if (
        isinstance(output_dict, dict)
        and "file_path_modifications" in output_dict
        and isinstance(storm_start_datetime, datetime)
        and tc_stormnum >= 69
    ):
        path_mods = output_dict["file_path_modifications"]
        if "unique_invest_dirs" in path_mods and path_mods["unique_invest_dirs"]:
            tc_stormname = storm_start_datetime.strftime(
                f"{base_tc_stormname}.%Y%m%d%H"
            )
            LOG.info("SETTING unique storm dir %s", tc_stormname)
        if (
            "existing_invest_dirs_allowable_time_diff" in path_mods
            and path_mods["existing_invest_dirs_allowable_time_diff"]
        ):
            base_path = pathjoin(basin_path, base_tc_stormname)
            paths = glob(base_path + "*")
            # Make the minimum greater than the allowable - so we can track the lowest
            min_timediff = abs(
                timedelta(days=path_mods["existing_invest_dirs_allowable_time_diff"])
            )
            for path in paths:
                path_parts = pathbasename(path).split(".")
                if len(path_parts) > 1:
                    try:
                        existing_storm_start_datetime = datetime.strptime(
                            path_parts[1], "%Y%m%d%H"
                        ).replace(tzinfo=timezone.utc)
                    except ValueError:
                        LOG.warning(
                            "SKIPPING using existing invest dir, "
                            "no valid start datetime in path %s",
                            path,
                        )
                        continue
                    timediff = abs(storm_start_datetime - existing_storm_start_datetime)
                    if timediff < min_timediff:
                        LOG.info(
                            "SETTING unique storm dir to existing %s, %s < %s",
                            path_parts[1],
                            timediff,
                            min_timediff,
                        )
                        min_timediff = timediff
                        tc_stormname = pathbasename(path)
                    else:
                        LOG.info(
                            "SKIPPING not using existing dir %s, %s > %s",
                            path_parts[1],
                            timediff,
                            min_timediff,
                        )

        LOG.info("USING final storm dir %s", tc_stormname)
    return tc_stormname


def tc_storm_basedir(
    basedir, tc_year, tc_basin, tc_stormnum, output_dict=None, sector_info=None
):
    """Produce base storm directory for TC web output.

    Parameters
    ----------
    basedir : str
         base directory
    tc_year : int
         Full 4 digit storm year
    tc_basin : str
         2 character basin designation
            SH Southern Hemisphere
            WP West Pacific
            EP East Pacific
            CP Central Pacific
            IO Indian Ocean
            AL Atlantic
    tc_stormnum : int
        2 digit storm number
            90 through 99 for invests
            01 through 69 for named storms

    Returns
    -------
    path : str
        Path to base storm web directory
    """
    tc_date = "tc{0:04d}".format(tc_year)
    base_tc_stormname = "{0}{1:02d}{2:04d}".format(tc_basin, tc_stormnum, tc_year)
    basin_path = pathjoin(basedir, tc_date, tc_basin)
    tc_storm_subdir = get_storm_subdir(
        basin_path, base_tc_stormname, tc_stormnum, output_dict, sector_info
    )
    # Need to actually add a check to see if an invest directory exists that is "close"
    # If one does, use that instead of a new one (which will result in
    # creating the new directory downstream)
    path = pathjoin(basin_path, tc_storm_subdir)
    return path


def update_extra_field(
    output_dict,
    xarray_obj,
    area_def,
    product_name,
    extra_field_delimiter="_",
    existing_extra_field=None,
    extra_field_provider=True,
    extra_field_coverage_func=False,
    extra_field_resolution=False,
    include_filename_extra_fields=False,
):
    """Finalize extra field using standard geoips arguments."""
    if extra_field_provider is True:
        from geoips.filenames.base_paths import PATHS as gpaths

        extra_field_provider = gpaths["GEOIPS_COPYRIGHT_ABBREVIATED"]

    from geoips.dev.product import get_covg_args_from_product

    prod_spec_override = None
    if output_dict is not None:
        prod_spec_override = output_dict.get("product_spec_override")

    if "source_names" in xarray_obj.attrs:
        for source_name in xarray_obj.source_names:
            try:
                prod_plugin = products.get_plugin(
                    source_name, product_name, prod_spec_override
                )
                covg_args = get_covg_args_from_product(
                    prod_plugin,
                    covg_field="filename_coverage_checker",
                )
            except KeyError:
                continue
    else:
        prod_plugin = products.get_plugin(
            xarray_obj.source_name,
            product_name,
            prod_spec_override,
        )
        covg_args = get_covg_args_from_product(
            prod_plugin,
            covg_field="filename_coverage_checker",
        )

    extras = []

    if extra_field_provider:
        extras += [f"{extra_field_provider}"]
    if extra_field_coverage_func and "radius_km" in covg_args:
        extras += [f"cr{covg_args['radius_km']}"]
    if (
        include_filename_extra_fields
        and "filename_extra_fields" in xarray_obj.attrs
        and xarray_obj.filename_extra_fields
    ):
        for field in xarray_obj.filename_extra_fields:
            extras += [f"{xarray_obj.filename_extra_fields[field]}"]

    # This must go first - but no "res" if no other fields
    if extra_field_resolution:
        resolution = max(area_def.pixel_size_x, area_def.pixel_size_y) / 1000.0
        res_str = "{0:0.1f}".format(resolution).replace(".", "p")
        if len(extras) > 0:
            res_str = f"res{res_str}"
        extras = [res_str] + extras

    # This doesn't count towards "other fields" for the res in resolution.
    if existing_extra_field:
        extras += [f"{existing_extra_field}"]

    extra = extra_field_delimiter.join(extras)
    return extra
