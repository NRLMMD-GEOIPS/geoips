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

"""Routines for writing SMAP or SMOS windspeed data in AWIPS2 compatible format."""
import logging
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np
import xarray as xr
from geoips.xarray_utils.time import (
    get_min_from_xarray_time,
    get_max_from_xarray_time,
    get_datetime_from_datetime64,
)
from geoips.filenames.base_paths import PATHS as geoips_variables

LOG = logging.getLogger(__name__)

interface = "output_formatters"
family = "xrdict_to_outlist"
name = "awips2_goesr_tiles"


def call(
    xarray_dict,
    working_directory=geoips_variables["GEOIPS_OUTDIRS"],
):
    """Write AWIPS2 compatible NetCDF files from SMAP or SMOS windspeed data.

    Parameters
    ----------
    xarray_dict : Dict[str, xarray.Dataset]
    working_directory : str

    Returns
    -------
    List[str]
    """
    working_dir = Path(working_directory)
    utc_date_format = "%Y-%m-%d %H:%M:%S UTC"
    success_outputs = []
