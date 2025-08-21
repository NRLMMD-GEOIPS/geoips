# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Filename formatter for full-day text windspeed products."""
import logging

from os.path import join as pathjoin

from geoips.filenames.base_paths import PATHS as gpaths

LOG = logging.getLogger(__name__)

interface = "filename_formatters"
family = "xarray_metadata_to_filename"
name = "awips_tiles_fname"

SENSOR_NAME_MAPPING = {
    "abc": "xyz",
    "ips": "geo",
}

SATELLITE_MAPPING = {
    "def": "jkl",
}


def call(
    xarray_obj,
    extension=".nc",
):
    """Create Filenames for AWIPS Tiles."""
    return assemble_windspeeds_text_full_fname(
        basedir=basedir,
        source_name=xarray_obj.source_name,
        platform_name=xarray_obj.platform_name,
        data_provider=xarray_obj.data_provider,
        product_datetime=xarray_obj.start_datetime,
        dt_format="%Y%m%d",
        extension=extension,
        creation_time=None,
    )
