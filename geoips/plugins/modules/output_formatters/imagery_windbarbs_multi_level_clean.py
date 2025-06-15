# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Matplotlib-based windbarb annotated image output clean."""

import logging


from geoips.plugins.modules.output_formatters.imagery_windbarbs import (
    format_windbarb_data,
    output_clean_windbarbs,
)

from geoips.plugins.modules.output_formatters.imagery_windbarbs_multi_level import (
    assign_height_levels,
)

LOG = logging.getLogger(__name__)

interface = "output_formatters"
family = "image"
name = "imagery_windbarbs_multi_level_clean"


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
    pressure_range_dict=None,
):
    """Plot clean windbarb imagery on matplotlib figure."""
    formatted_data_dict = format_windbarb_data(xarray_obj, product_name)

    if not pressure_range_dict:
        pressure_range_dict = {
            "Low": [701, 1013.25],
            "Mid": [401, 700],
            "High": [0, 400],
        }
    height_numbers, level_labels = assign_height_levels(
        formatted_data_dict, pressure_range_dict
    )
    formatted_data_dict["height_numbers"] = height_numbers

    success_outputs = output_clean_windbarbs(
        area_def,
        output_fnames,
        mpl_colors_info,
        xarray_obj.start_datetime,
        formatted_data_dict,
        fig,
        main_ax,
        mapobj,
        barb_color_variable="height_numbers",
    )

    return success_outputs
