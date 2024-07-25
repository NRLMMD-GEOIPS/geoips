# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Filename formatter for text windspeed products."""

import logging

from os.path import join as pathjoin

from geoips.filenames.base_paths import PATHS as gpaths

LOG = logging.getLogger(__name__)

interface = "filename_formatters"
family = "xarray_metadata_to_filename"
name = "text_winds_full_fname"


def call(
    xarray_obj,
    extension=".txt",
    basedir=pathjoin(gpaths["ANNOTATED_IMAGERY_PATH"], "text_winds"),
):
    """Create a single text winds file for all data in the current xarray.

    This text windspeed filename includes YYYYMMDD.HHMN in the filename
    in order to include only the current datafile in the file.

    See Also
    --------
    geoips.plugins.modules.filename_formatters.text_winds_full_fname.
        assemble_windspeeds_text_full_fname
        Shared utility to create filenames with similar formatting requirements.
    """
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
    """Produce full output product path using product / sensor specifications.

    Parameters
    ----------
    basedir : str
         base directory
    source_name : str
        Name of source (sensor)
    platform_name : str
        Name of platform (satellite)
    data_provider : str
        Name of data provider
    product_datetime : datetime.datetime
        Start time of data used to generate product
    dt_format : str, default="%Y%m%d.%H%M"
        Format used to display product_datetime within filename
    extension : str, default=".txt"
        File extension, specifying type.
    creation_time : datetime.datetime, default=None
        Include given creation_time of file in filename
        If None, do not include creation time.

    Returns
    -------
    str
        full path of output filename of the format:
          <basedir>/<source_name>_<data_provider>_<platform_name>_
          surface_winds_<YYYYMMDDHHMN>

    Examples
    --------
    >>> startdt = datetime.strptime('20200216T001412', '%Y%m%dT%H%M%S')
    >>> assemble_windspeeds_text_full_fname(
    ...     '/outdir',
    ...     'smap-spd',
    ...     'smap',
    ...     'remss',
    ...     startdt,
    ...     '%Y%m%d'
    ...     )
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
