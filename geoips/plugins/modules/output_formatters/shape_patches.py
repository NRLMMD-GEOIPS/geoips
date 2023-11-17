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

"""Matplot-lib based annotated image output."""

import logging

from geoips.interfaces import products
from geoips.errors import PluginError
from jsonschema.exceptions import ValidationError
import numpy as np
from geoips.image_utils.mpl_utils import create_figure_and_main_ax_and_mapobj
from geoips.image_utils.colormap_utils import set_matplotlib_colors_standard
from geoips.image_utils.mpl_utils import (
    plot_image,
    save_image,
    plot_overlays,
    create_colorbar,
    add_shape_patches,
)
import matplotlib
from geoips.image_utils.mpl_utils import get_title_string_from_objects, set_title

LOG = logging.getLogger(__name__)

interface = "output_formatters"
family = "image_overlay"
name = "shape_patches"


def call(
    area_def,
    xarray_obj,
    product_name,
    output_fnames,
    shape_type="circle",
    product_name_title=None,
    mpl_colors_info=None,
    feature_annotator=None,
    gridline_annotator=None,
    product_datatype_title=None,
    bg_xarray=None,
    bg_product_name_title=None,
    bg_datatype_title=None,
    remove_duplicate_minrange=None,
    title_copyright=None,
    title_formatter=None,
    output_dict=None,
):
    """Plot annotated imagery."""
    if product_name_title is None:
        product_name_title = product_name

    success_outputs = []
    plot_data = xarray_obj[product_name].to_masked_array()


    if not mpl_colors_info:
        # Create the matplotlib color info dict - the fields in this dictionary
        # (cmap, norm, features, etc) will be used in plot_image to ensure the image
        # matches the colorbar.
        mpl_colors_info = set_matplotlib_colors_standard(
            data_range=[plot_data.min(), plot_data.max()],
            cmap_name=None,
            cbar_label=None,
        )
    mapobj = None

    # Create matplotlib figure and main axis, where the main image will be plotted
    fig, main_ax, mapobj = create_figure_and_main_ax_and_mapobj(
        area_def.x_size,
        area_def.y_size,
        area_def,
        existing_mapobj=mapobj,
        noborder=False,
    )
    LOG.info(matplotlib.get_backend())

    # Plot the actual data on a map
    # empty_data = np.zeros([area_def.x_size, area_def.y_size])
    empty_data = np.zeros([1, 1])
    plot_image(main_ax, empty_data, mapobj, mpl_colors_info=mpl_colors_info)

    main_ax = add_shape_patches(
        main_ax,
        {
            "latitude": xarray_obj["latitude"].data,
            "longitude": xarray_obj["longitude"].data,
            "product": xarray_obj[product_name].data,
        },
        mapobj,
        shape_type,
        mpl_colors_info["cmap"],
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
    set_title(main_ax, title_string, area_def.y_size)

    if mpl_colors_info["colorbar"] is True:
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

    if output_fnames is not None:
        for annotated_fname in output_fnames:
            # Save the final image
            success_outputs += save_image(
                fig,
                annotated_fname,
                is_final=True,
                image_datetime=xarray_obj.start_datetime,
                remove_duplicate_minrange=remove_duplicate_minrange,
            )

    return success_outputs
