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

"""Matplotlib-based windbarb clean image output (no overlays or backgrounds)."""

import logging

from geoips.plugins.modules.output_formatters.imagery_windbarbs import (
    output_clean_windbarbs,
    format_windbarb_data,
)

LOG = logging.getLogger(__name__)

interface = "output_formatters"
family = "image"
name = "imagery_windbarbs_clean"


def call(
    area_def,
    xarray_obj,
    product_name,
    output_fnames,
    product_name_title=None,
    mpl_colors_info=None,
    existing_image=None,
    remove_duplicate_minrange=None,
    fig=None,
    main_ax=None,
    mapobj=None,
):
    """Plot clean windbarb imagery on matplotlib figure."""
    formatted_data_dict = format_windbarb_data(xarray_obj, product_name)

    success_outputs = output_clean_windbarbs(
        area_def,
        output_fnames,
        mpl_colors_info,
        xarray_obj.start_datetime,
        formatted_data_dict,
        fig,
        main_ax,
        mapobj,
    )

    return success_outputs
