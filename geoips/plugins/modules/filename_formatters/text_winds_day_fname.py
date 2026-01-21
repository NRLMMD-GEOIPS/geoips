# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Filename formatter for full-day text windspeed products."""

import logging

from os.path import join as pathjoin

from geoips.filenames.base_paths import PATHS as gpaths
from geoips.plugins.modules.filename_formatters.text_winds_full_fname import (
    assemble_windspeeds_text_full_fname,
)

LOG = logging.getLogger(__name__)

interface = "filename_formatters"
family = "xarray_metadata_to_filename"
name = "text_winds_day_fname"


def call(
    xarray_obj,
    extension=".txt",
    basedir=pathjoin(gpaths["ANNOTATED_IMAGERY_PATH"], "text_winds"),
):
    """Create full-day text windspeed filenames.

    text_winds_day_fname includes only YYYYMMDD in the filename, so all data for
    a full day is appended into a single file.

    See Also
    --------
    geoips.plugins.modules.filename_formatters.text_winds_full_fname.
        assemble_text_windspeeds_text_full_fname
        Shared utility for generating similarly formatted windspeed filenames.
    """
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
