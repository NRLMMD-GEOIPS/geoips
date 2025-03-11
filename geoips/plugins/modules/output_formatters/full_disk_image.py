# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Full disk image matplotlib-based output format."""

import logging

LOG = logging.getLogger(__name__)

interface = "output_formatters"
family = "image_overlay"
name = "full_disk_image"


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
):
    """Plot full disk image."""
    if product_name_title is None:
        product_name_title = product_name

    success_outputs = []
    plot_data = xarray_obj[product_name].to_masked_array()
    from geoips.image_utils.mpl_utils import create_figure_and_main_ax_and_mapobj
    from geoips.image_utils.mpl_utils import (
        save_image,
        plot_overlays,
        create_colorbar,
    )
    from geoips.image_utils.mpl_utils import get_title_string_from_objects, set_title

    frame_clr = None
    # If a gridline_annotator plugin was supplied, attempt to get the frame background
    # color. Otherwise, just keep it as None.
    if gridline_annotator:
        frame_clr = gridline_annotator.get("spec", {}).get("background")

    if hasattr(area_def, "x_size"):
        x_size = area_def.x_size
        y_size = area_def.y_size
    else:
        x_size = area_def.get_lonlats()[0].shape[0]
        y_size = area_def.get_lonlats()[0].shape[1]

    import cartopy

    if hasattr(area_def, "proj_dict"):
        # mapobj = cartopy.crs.Orthographic(area_def.proj_dict['lon_0'],
        #                                   area_def.proj_dict['lat_0'])
        mapobj = cartopy.crs.Geostationary(area_def.proj_dict["lon_0"])
    else:
        # mapobj = cartopy.crs.Orthographic(area_def.sector_info['clon'],
        #                                   area_def.sector_info['clat'])
        mapobj = cartopy.crs.Geostationary(area_def.sector_info["clon"])
    fig, main_ax, mapobj = create_figure_and_main_ax_and_mapobj(
        x_size,
        y_size,
        area_def,
        existing_mapobj=mapobj,
        frame=frame_clr,
    )

    # Plot the actual data on a map

    main_ax.imshow(
        plot_data,
        transform=area_def.to_cartopy_crs(),
        # extent=area_def.area_extent_ll,
        cmap=mpl_colors_info["cmap"],
        norm=mpl_colors_info["norm"],
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
    )
    set_title(main_ax, title_string, y_size)

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
