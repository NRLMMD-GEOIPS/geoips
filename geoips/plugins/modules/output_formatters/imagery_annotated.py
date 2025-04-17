# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Matplot-lib based annotated image output."""

import logging

from geoips.interfaces import products
from geoips.errors import PluginError
from jsonschema.exceptions import ValidationError

LOG = logging.getLogger(__name__)

interface = "output_formatters"
family = "image_overlay"
name = "imagery_annotated"


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
    output_dict=None,
):
    """Plot annotated imagery."""
    if product_name_title is None:
        product_name_title = product_name

    success_outputs = []
    plot_data = xarray_obj[product_name].to_masked_array()
    from geoips.image_utils.mpl_utils import create_figure_and_main_ax_and_mapobj
    from geoips.image_utils.colormap_utils import set_matplotlib_colors_standard
    from geoips.image_utils.mpl_utils import (
        plot_image,
        save_image,
        plot_overlays,
        create_colorbar,
    )
    from geoips.image_utils.mpl_utils import get_title_string_from_objects, set_title

    bkgrnd_clr = None
    frame_clr = None
    # If a feature_annotator plugin was supplied, attempt to get the image background
    # color. Otherwise, just keep it as None.
    if feature_annotator:
        bkgrnd_clr = feature_annotator.get("spec", {}).get("background")
    # If a gridline_annotator plugin was supplied, attempt to get the frame background
    # color. Otherwise, just keep it as None.
    if gridline_annotator:
        frame_clr = gridline_annotator.get("spec", {}).get("background")

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
    if clean_fname:
        # Create matplotlib figure and main axis, where the main image will be plotted
        fig, main_ax, mapobj = create_figure_and_main_ax_and_mapobj(
            area_def.x_size,
            area_def.y_size,
            area_def,
            noborder=True,
            frame_clr=frame_clr,
        )

        # Plot the actual data on a map
        plot_image(
            main_ax,
            plot_data,
            mapobj,
            mpl_colors_info=mpl_colors_info,
            bkgrnd_clr=bkgrnd_clr,
        )

        LOG.info("Saving the clean image %s", clean_fname)
        # Save the clean image with no gridlines or coastlines
        success_outputs += save_image(
            fig,
            clean_fname,
            is_final=False,
            image_datetime=xarray_obj.start_datetime,
            remove_duplicate_minrange=remove_duplicate_minrange,
        )

    # Create matplotlib figure and main axis, where the main image will be plotted
    fig, main_ax, mapobj = create_figure_and_main_ax_and_mapobj(
        area_def.x_size,
        area_def.y_size,
        area_def,
        existing_mapobj=mapobj,
        noborder=False,
        frame_clr=frame_clr,
    )

    # Plot the actual data on a map
    plot_image(
        main_ax,
        plot_data,
        mapobj,
        mpl_colors_info=mpl_colors_info,
        bkgrnd_clr=bkgrnd_clr,
    )

    if bg_data is not None and (
        hasattr(plot_data, "mask") or len(plot_data.shape) == 3
    ):
        if not bg_mpl_colors_info:
            bg_mpl_colors_info = set_matplotlib_colors_standard(
                data_range=[plot_data.min(), plot_data.max()],
                cmap_name=None,
                cbar_label=None,
                create_colorbar=False,
            )
        import numpy

        # Plot the background data on a map. Support either RGBA arrays or masked arrays
        if len(plot_data.shape) == 3 and plot_data.shape[2] == 4:
            plot_image(
                main_ax,
                numpy.ma.masked_where(plot_data[:, :, 3], bg_data),
                mapobj,
                mpl_colors_info=bg_mpl_colors_info,
                bkgrnd_clr=bkgrnd_clr,
            )
        else:
            plot_image(
                main_ax,
                numpy.ma.masked_where(~plot_data.mask, bg_data),
                mapobj,
                mpl_colors_info=bg_mpl_colors_info,
                bkgrnd_clr=bkgrnd_clr,
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
    prod_plugin = None
    try:
        prod_plugin = products.get_plugin(
            xarray_obj.source_name,
            product_name,
            output_dict.get("product_spec_override"),
        )
    except (PluginError, ValidationError):
        LOG.warning(
            "SKIPPING products.get_plugin: Invalid product specification %s / %s",
            product_name,
            xarray_obj.source_name,
        )
    if prod_plugin and "coverage_checker" in prod_plugin:
        from geoips.dev.product import get_covg_from_product
        from importlib import import_module
        from geoips.dev.product import get_covg_args_from_product

        covg_func = get_covg_from_product(prod_plugin)
        covg_args = get_covg_args_from_product(prod_plugin)
        plot_covg_func = getattr(import_module(covg_func.__module__), "plot_coverage")
        plot_covg_func(main_ax, area_def, covg_args)

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
