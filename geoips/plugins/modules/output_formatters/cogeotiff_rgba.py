# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Geotiff image rasterio-based output format."""

import logging

# Internal utilities
from geoips.interfaces import output_formatters

LOG = logging.getLogger(__name__)

interface = "output_formatters"
family = "image"
name = "cogeotiff_rgba"


def call(
    area_def,
    xarray_obj,
    product_name,
    output_fnames,
    product_name_title=None,
    mpl_colors_info=None,
    existing_image=None,
):
    """Create standard geotiff output using rasterio."""
    cogeotiff = output_formatters.get_plugin("cogeotiff")
    output_fnames = cogeotiff(
        area_def,
        xarray_obj,
        product_name,
        output_fnames,
        product_name_title,
        mpl_colors_info,
        existing_image,
    )

    return output_fnames
