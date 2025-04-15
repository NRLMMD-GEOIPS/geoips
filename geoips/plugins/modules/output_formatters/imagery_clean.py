# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Matplotlib-based clean image output."""

import logging

LOG = logging.getLogger(__name__)

interface = "output_formatters"
family = "image"
name = "imagery_clean"


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
    """Plot clean image on matplotlib figure."""
    success_outputs = []
    plot_data = xarray_obj[product_name].to_masked_array()
    plot_kwargs = {}
    if hasattr(xarray_obj, "fuse_order"):
        plot_kwargs = {"zorder": int(xarray_obj.fuse_order)}
    from geoips.image_utils.mpl_utils import create_figure_and_main_ax_and_mapobj
    from geoips.image_utils.colormap_utils import set_matplotlib_colors_standard
    from geoips.image_utils.mpl_utils import plot_image, save_image

    if not mpl_colors_info:
        # Create the matplotlib color info dict - the fields in this dictionary
        # (cmap, norm, features, etc) will be used in plot_image to ensure the image
        # matches the colorbar.
        mpl_colors_info = set_matplotlib_colors_standard(
            data_range=[plot_data.min(), plot_data.max()],
            cmap_name=None,
            cbar_label=None,
        )

    if fig is None and main_ax is None and mapobj is None:
        # Create matplotlib figure and main axis, where the main image will be plotted
        fig, main_ax, mapobj = create_figure_and_main_ax_and_mapobj(
            area_def.x_size, area_def.y_size, area_def, noborder=True
        )

    # Plot the actual data on a map
    plot_image(
        main_ax, plot_data, mapobj, mpl_colors_info=mpl_colors_info, **plot_kwargs
    )

    if output_fnames is not None:
        for clean_fname in output_fnames:
            LOG.info("Saving the clean image %s", clean_fname)
            # Save the clean image with no gridlines or coastlines
            success_outputs += save_image(
                fig,
                clean_fname,
                is_final=False,
                image_datetime=xarray_obj.start_datetime,
                remove_duplicate_minrange=remove_duplicate_minrange,
            )

    return success_outputs
