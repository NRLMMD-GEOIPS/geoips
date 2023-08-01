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

"""Matplotlib-based unprojected image output."""

import logging

import matplotlib.pyplot as plt
import matplotlib

from geoips.image_utils.mpl_utils import save_image

matplotlib.use("agg")

LOG = logging.getLogger(__name__)

interface = "output_formatters"
family = "unprojected"
name = "unprojected_image"


def call(
    xarray_obj,
    product_name,
    output_fnames,
    product_name_title=None,
    mpl_colors_info=None,
    x_size=None,
    y_size=None,
    savefig_kwargs=None,
):
    """Plot unprojected image to matplotlib figure."""
    if savefig_kwargs is None:
        # Default to no arguments, empty dictionary.  Will result in masked background
        savefig_kwargs = {}
        # black background
        # savefig_kwargs = {'facecolor': 'k'}

    if product_name_title is None:
        product_name_title = product_name
    if x_size is None and y_size is None:
        x_size = xarray_obj[product_name].shape[1]
        y_size = xarray_obj[product_name].shape[0]
    elif y_size is None:
        ratio = float(x_size) / float(xarray_obj[product_name].shape[1])
        y_size = float(ratio) * float(xarray_obj[product_name].shape[0])
    elif x_size is None:
        ratio = float(y_size) / float(xarray_obj[product_name].shape[0])
        x_size = float(ratio) * float(xarray_obj[product_name].shape[1])

    rc_params = matplotlib.rcParams
    dpi = rc_params["figure.dpi"]

    image_width = float(x_size) / dpi
    image_height = float(y_size) / dpi

    fig = plt.figure(facecolor="none")
    fig.set_size_inches(image_width, image_height)
    main_ax = plt.Axes(fig, [0, 0, 1, 1])
    main_ax.set_axis_off()
    fig.add_axes(main_ax)

    main_ax.imshow(
        xarray_obj[product_name],
        norm=mpl_colors_info["norm"],
        cmap=mpl_colors_info["cmap"],
    )

    success_outputs = []
    for fname in output_fnames:
        LOG.info("Plotting %s with plt", fname)
        # This just handles cleaning up the axes, creating directories, etc
        success_outputs += save_image(
            fig,
            fname,
            is_final=False,
            image_datetime=xarray_obj.start_datetime,
            savefig_kwargs=savefig_kwargs,
        )

    return success_outputs
