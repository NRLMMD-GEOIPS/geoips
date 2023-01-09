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

""" Specifications for output filename formats for text windspeed product types. """

import logging

from os.path import join as pathjoin, splitext as pathsplitext
from os.path import dirname as pathdirname, basename as pathbasename
from datetime import datetime, timedelta
from glob import glob
from os import unlink as osunlink

from geoips.filenames.base_paths import PATHS as gpaths
from geoips.data_manipulations.merge import minrange

LOG = logging.getLogger(__name__)

filename_type = "xarray_metadata_to_filename"


def text_winds_full_fname(
    xarray_obj,
    extension=".txt",
    basedir=pathjoin(gpaths["ANNOTATED_IMAGERY_PATH"], "text_winds"),
):
    return assemble_windspeeds_text_full_fname(
        basedir=basedir,
        source_name=xarray_obj.source_name,
        platform_name=xarray_obj.platform_name,
        data_provider=xarray_obj.data_provider,
        product_datetime=xarray_obj.start_datetime,
        dt_format="%Y%m%d.%H%M",
        extension=extension,
        creation_time=None,
    )


def assemble_windspeeds_text_full_fname(
    basedir,
    source_name,
    platform_name,
    data_provider,
    product_datetime,
    dt_format="%Y%m%d.%H%M",
    extension=".txt",
    creation_time=None,
):
    """Produce full output product path from product / sensor specifications.

    Parameters:
        basedir (str) :  base directory
        num_points(int) :  Number of points (lines) included in the text file
        source_name (str) : Name of source (sensor)
        platform_name (str) : Name of platform (satellite)
        data_provider (str) : Name of data provider
        product_datetime (datetime) : Start time of data used to generate product
        dt_format (str) : Format used to display product_datetime within filename
        creation_time (datetime) : Default None: Include given creation_time of file in filename

    Returns:
        str: to full path of output filename of the format:
          <basedir>/<source_name>_<data_provider>_<platform_name>_surface_winds_<YYYYMMDDHHMN>

    Usage:
        >>> startdt = datetime.strptime('20200216T001412', '%Y%m%dT%H%M%S')
        >>> assemble_windspeeds_text_full_fname('/outdir', 'smap-spd', 'smap', 'remss', startdt, '%Y%m%d')
        '/outdir/smap-spd_remss_smap_surface_winds_20200216'
    """

    fname = "_".join(
        [
            source_name,
            data_provider,
            platform_name,
            "surface_winds",
            product_datetime.strftime(dt_format),
        ]
    )

    if creation_time is not None:
        fname = fname + "_creationtime_" + creation_time.strftime("%Y%m%dT%H%MZ")

    if extension is not None:
        fname = fname + extension

    return pathjoin(basedir, fname)
