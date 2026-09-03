# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Utilities for TC filenaming, for use within geoips filename formatters."""

import logging
from os.path import join as pathjoin
from geoips.interfaces import products

LOG = logging.getLogger(__name__)

# interface = None indicates to the GeoIPS interfaces that this is not a valid
# plugin, and this module will not be added to the GeoIPS plugin registry.
# This allows including python modules within the geoips/plugins directory
# that provide helper or utility functions to the geoips plugins, but are
# not full GeoIPS plugins on their own.
interface = None


def tc_storm_basedir(basedir, sector_info):
    """Produce base storm directory for TC web output.

    Parameters
    ----------
    basedir : str
        Base directory for TC web output
    sector_info: dict
         Dictionary of TC sector info, including storm_year, storm_basin, storm_id, etc.

    Returns
    -------
    path : str
        Path to base storm web directory
    """
    # Directories are of the format:
    # basedir/tcYYYY/BASIN/STORMID/
    tc_date = "tc{0:04d}".format(sector_info["storm_year"])
    basin_path = pathjoin(basedir, tc_date, sector_info["storm_basin"].upper())
    # No longer checking for existing invest subdirectories - assume we are just
    # writing to the current storm_id (which will include the storm start datetime
    # for invests).  Add '.' delimiter back into storm id for path for readability
    # and consistency/backwards compatibility.
    storm_path_name = sector_info["storm_id"].upper()
    if len(storm_path_name) > 8:
        storm_path_name = storm_path_name[0:8] + "." + storm_path_name[8:]
    path = pathjoin(basin_path, storm_path_name)
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
