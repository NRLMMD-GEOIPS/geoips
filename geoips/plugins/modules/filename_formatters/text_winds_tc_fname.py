# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Filename formatter for TC-specific text windspeed outputs."""

import logging

from os.path import join as pathjoin

from geoips.filenames.base_paths import PATHS as gpaths

interface = "filename_formatters"
family = "xarray_metadata_to_filename"
name = "text_winds_tc_fname"

LOG = logging.getLogger(__name__)


def call(xarray_obj, extension=".txt", basedir=gpaths["TCWWW"], output_dict=None):
    """Create TC-specific text windspeed filename.

    See Also
    --------
    geoips.plugins.modules.filename_formatters.text_winds_tc_fname.
        assemble_windspeeds_text_tc_fname
        Shared utility to facilitate creating multiple similar filenames
        from the same code.
    """
    area_def = xarray_obj.area_definition
    return assemble_windspeeds_text_tc_fname(
        basedir=basedir,
        source_name=xarray_obj.source_name,
        platform_name=xarray_obj.platform_name,
        product_datetime=xarray_obj.start_datetime,
        data_provider=xarray_obj.data_provider,
        extension=extension,
        sector_info=area_def.sector_info,
    )


def assemble_windspeeds_text_tc_fname(
    basedir,
    source_name,
    platform_name,
    product_datetime,
    data_provider,
    extension=".txt",
    sector_info=None,
):
    """Produce full output product path from product / sensor specifications.

    Parameters
    ----------
    basedir : str
         base directory
    source_name : str
        Name of source (sensor)
    platform_name : str
        Name of platform (satellite)
    product_datetime : datetime
        Start time of data used to generate product
    extension: str
        Extension of filename (default .txt).
    sector_info: dict
        Dictionary of sector_info used in compiling the file path and filename.

    Returns
    -------
    str:
        full path of output filename of the format:
          <basedir>/tc<tc_year>/<tc_basin>/<tc_basin><tc_stormnum><tc_year>/
            txt/<source_name>_<platform_name>_surface_winds_<data_provider>_
            <YYYYMMDDHHMN>

    Examples
    --------
    >>> startdt = datetime.strptime('20200216T001412', '%Y%m%dT%H%M%S')
    >>> assemble_windspeeds_text_tc_fname('/outdir',
    ...     2020,
    ...     'SH',
    ...     16,
    ...     'smap-spd',
    ...     'smap',
    ...     startdt,
    ...     'remss')
    '/outdir/tc2020/SH/SH162020/txt/
    """
    from geoips.plugins.modules.filename_formatters.utils.tc_file_naming import (
        tc_storm_basedir,
    )

    path = pathjoin(tc_storm_basedir(basedir, sector_info=sector_info), "txt")
    fname = "_".join(
        [
            source_name,
            "surface_winds",
            data_provider,
            platform_name,
            sector_info["storm_id"],
            product_datetime.strftime("%Y%m%d%H%M"),
        ]
    )
    if extension is not None:
        fname = f"{fname}{extension}"
    return pathjoin(path, fname)
