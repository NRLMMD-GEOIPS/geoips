# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Filename specification using minimal basic attributes, and no subdirs."""

import logging
from os.path import join as pathjoin

from geoips.filenames.base_paths import PATHS as gpaths

LOG = logging.getLogger(__name__)

interface = "filename_formatters"
family = "xarray_area_product_to_filename"
name = "basic_fname"


def call(
    xarray_obj,
    area_def,
    product_name,
    output_type=".png",
    basedir=pathjoin(gpaths["ANNOTATED_IMAGERY_PATH"]),
    extra_field=None,
):
    """Create basic filename, in a specific directory (with no subdirectories).

    This filename format includes only the start time, platform name, source
    name, product name, sector name, and data provider, and a full path
    to basedir with no additional subdirectories.
    """
    sector_name = "unk"
    if area_def:
        sector_name = area_def.area_id

    path = basedir
    fname = ".".join(
        [
            xarray_obj.attrs["start_datetime"].strftime("%Y%m%d"),
            xarray_obj.attrs["start_datetime"].strftime("%H%M%S"),
            xarray_obj.attrs["platform_name"],
            xarray_obj.attrs["source_name"],
            product_name,
            sector_name,
            xarray_obj.attrs["data_provider"],
        ]
    )
    fname = "{0}.{1}".format(fname, output_type)
    return pathjoin(path, fname)
