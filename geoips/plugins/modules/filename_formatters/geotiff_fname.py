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

"""Standard GeoIPS GEOTIFF filename formatter."""

# Python Standard Libraries
import logging

from geoips.filenames.base_paths import PATHS as gpaths

LOG = logging.getLogger(__name__)

interface = "filename_formatters"
family = "standard"
name = "geotiff_fname"


def call(
    area_def,
    xarray_obj,
    product_name,
    coverage=None,
    output_type="tif",
    output_type_dir=None,
    product_dir=None,
    product_subdir=None,
    source_dir=None,
    basedir=gpaths["ANNOTATED_IMAGERY_PATH"],
    output_dict=None,
):
    """GEOTIFF filename formatter.

    This uses the standard "geoips_fname" formatter, but with a default
    output type of "tif".
    """
    from geoips.interfaces import filename_formatters
    from geoips.sector_utils.utils import is_sector_type

    if is_sector_type(area_def, "tc"):
        fname_fmt_plugin = filename_formatters.get_plugin("tc_fname")
        basedir = gpaths["TCWWW"]
    else:
        fname_fmt_plugin = filename_formatters.get_plugin("geoips_fname")
    geotiff_fname = fname_fmt_plugin(
        area_def,
        xarray_obj,
        product_name,
        coverage=coverage,
        output_type=output_type,
        output_type_dir=output_type_dir,
        product_dir=product_dir,
        product_subdir=product_subdir,
        source_dir=source_dir,
        basedir=basedir,
        output_dict=output_dict,
    )

    return geotiff_fname
