# # # This source code is protected under the license referenced at
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
        tc_area_id=area_def.area_id,
        tc_year=int(area_def.sector_info["storm_year"]),
        tc_basin=area_def.sector_info["storm_basin"],
        tc_stormnum=int(area_def.sector_info["storm_num"]),
        source_name=xarray_obj.source_name,
        platform_name=xarray_obj.platform_name,
        product_datetime=xarray_obj.start_datetime,
        data_provider=xarray_obj.data_provider,
        extension=extension,
        output_dict=output_dict,
        sector_info=area_def.sector_info,
    )


def assemble_windspeeds_text_tc_fname(
    basedir,
    tc_area_id,
    tc_year,
    tc_basin,
    tc_stormnum,
    source_name,
    platform_name,
    product_datetime,
    data_provider,
    extension=".txt",
    output_dict=None,
    sector_info=None,
):
    """Produce full output product path from product / sensor specifications.

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
    platform_name : str
        Name of platform (satellite)
    product_datetime : datetime
        Start time of data used to generate product

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

    path = pathjoin(
        tc_storm_basedir(
            basedir,
            tc_year,
            tc_basin,
            tc_stormnum,
            output_dict=output_dict,
            sector_info=sector_info,
        ),
        "txt",
    )
    fname = "_".join(
        [
            source_name,
            "surface_winds",
            data_provider,
            platform_name,
            tc_area_id,
            product_datetime.strftime("%Y%m%d%H%M"),
        ]
    )
    if extension is not None:
        fname = f"{fname}{extension}"
    return pathjoin(path, fname)
