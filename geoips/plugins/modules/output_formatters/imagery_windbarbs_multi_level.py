# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Matplotlib-based windbarb annotated image output."""

import logging

import numpy

from geoips.image_utils.mpl_utils import (
    create_figure_and_main_ax_and_mapobj,
    save_image,
)
from geoips.image_utils.colormap_utils import set_matplotlib_colors_standard
from geoips.image_utils.mpl_utils import plot_image, plot_overlays, create_colorbar
from geoips.image_utils.mpl_utils import get_title_string_from_objects, set_title
from geoips.plugins.modules.output_formatters.imagery_windbarbs import (
    format_windbarb_data,
    output_clean_windbarbs,
    plot_barbs,
)

LOG = logging.getLogger(__name__)

interface = "output_formatters"
family = "image_overlay"
name = "imagery_windbarbs_multi_level"


def assign_height_levels(windbarb_data_dict, pressure_range_dict):
    """Assing derived motion winds to specified height levels.

    Using the pressure associated with each retrieved wind observation, assign to
    a specified level (e.g. Low/Mid/High) based on predefined pressure ranges. Each
    pressure level is assigned an integer, and any unassigned are set to 0

    Parameters
    ----------
    formatted_data_dict : dict
        Dictionary holding DMW data - must include a pressure key
    pressure_range_dict : dict
        Dictionary specifying pressure range for each defined level.
        e.g. {"Low": [701, 1013.25], "Mid": [401, 700], "High": [0, 400]}

    Returns
    -------
    tuple
        Array of assigned level numbers, and list of associated labels that can be used
        to set the ticks on a colorbar
    """
    pressure = windbarb_data_dict["pressure"]
    n_valid = numpy.count_nonzero(pressure)
    height_num = numpy.zeros(pressure.shape)
    level_labels = ["Unassigned"]
    for i, (level, pressure_range) in enumerate(pressure_range_dict.items()):
        max_pres = max(pressure_range)
        min_pres = min(pressure_range)
        pressure_mask = (pressure.data >= min_pres) & (pressure.data <= max_pres)
        height_num[pressure_mask] = i + 1
        level_labels.append(f"{level}\n({max_pres} - {min_pres} hPa)")
        LOG.info(
            "Number of wind retrievals for %s: %s",
            level,
            numpy.count_nonzero(pressure_mask),
        )
    LOG.info("Assigned %s/%s retrievals", numpy.count_nonzero(height_num), n_valid)
    return height_num, level_labels


def call(
    area_def,
    xarray_obj,
    product_name,
    output_fnames,
    clean_fname=None,
    product_name_title=None,
    mpl_colors_info=None,
    feature_annotator=None,
    gridline_annotator=None,
    product_datatype_title=None,
    bg_data=None,
    bg_mpl_colors_info=None,
    bg_xarray=None,
    bg_product_name_title=None,
    bg_datatype_title=None,
    remove_duplicate_minrange=None,
    title_copyright=None,
    title_formatter=None,
    pressure_range_dict=None,
):
    """Plot annotated windbarbs on matplotlib figure."""
    LOG.info("Starting imagery_windbarbs")

    if product_name_title is None:
        product_name_title = product_name

    success_outputs = []

    # Plot windbarbs

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

    if clean_fname is not None:
        success_outputs += output_clean_windbarbs(
            area_def,
            [clean_fname],
            mpl_colors_info,
            xarray_obj.start_datetime,
            formatted_data_dict,
            barb_color_variable="height_numbers",
        )

    if output_fnames is not None:
        LOG.info("Starting output_fnames")

        # Create matplotlib figure and main axis, where the main image will be plotted
        fig, main_ax, mapobj = create_figure_and_main_ax_and_mapobj(
            area_def.width,
            area_def.height,
            area_def,
            existing_mapobj=None,
            noborder=False,
        )

        if bg_data is not None:
            if not bg_mpl_colors_info:
                bg_mpl_colors_info = set_matplotlib_colors_standard(
                    data_range=[bg_data.min(), bg_data.max()],
                    cmap_name="Greys",
                    cbar_label=None,
                    create_colorbar=False,
                )
            # Plot the background data on a map
            plot_image(main_ax, bg_data, mapobj, mpl_colors_info=bg_mpl_colors_info)

        plot_barbs(
            main_ax,
            mapobj,
            mpl_colors_info,
            formatted_data_dict,
            barb_color_variable="height_numbers",
        )

        # Set the title for final image
        title_string = get_title_string_from_objects(
            area_def,
            xarray_obj,
            product_name_title,
            product_datatype_title=product_datatype_title,
            bg_xarray=bg_xarray,
            bg_product_name_title=bg_product_name_title,
            bg_datatype_title=bg_datatype_title,
            title_copyright=title_copyright,
            title_formatter=title_formatter,
        )
        set_title(main_ax, title_string, area_def.height)

        if mpl_colors_info["colorbar"] is True:
            mpl_colors_info["cbar_tick_labels"] = level_labels
            mpl_colors_info["colorbar_kwargs"] = {"extend": "neither"}
            # Create the colorbar to match the mpl_colors
            create_colorbar(fig, mpl_colors_info)

        # Plot gridlines and feature overlays
        plot_overlays(
            mapobj,
            main_ax,
            area_def,
            feature_annotator=feature_annotator,
            gridline_annotator=gridline_annotator,
        )

        for annotated_fname in output_fnames:
            # Save the final image
            success_outputs += save_image(
                fig,
                annotated_fname,
                is_final=True,
                image_datetime=xarray_obj.start_datetime,
            )

    return success_outputs
