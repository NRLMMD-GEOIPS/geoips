# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Matplotlib-based windbarb annotated image output."""

import logging

import numpy
import cartopy.crs as crs

from geoips.image_utils.mpl_utils import (
    create_figure_and_main_ax_and_mapobj,
    save_image,
)
from geoips.image_utils.colormap_utils import set_matplotlib_colors_standard
from geoips.image_utils.mpl_utils import plot_image, plot_overlays, create_colorbar
from geoips.image_utils.mpl_utils import get_title_string_from_objects, set_title

LOG = logging.getLogger(__name__)

interface = "output_formatters"
family = "image_overlay"
name = "imagery_windbarbs"


def plot_barbs(
    main_ax, mapobj, mpl_colors_info, formatted_data_dict, barb_color_variable="speed"
):
    """Plot windbarbs on matplotlib figure."""
    # main_ax.extent = area_def.area_extent_ll
    main_ax.set_extent(mapobj.bounds, crs=mapobj)
    # main_ax.extent = mapobj.bounds
    # NOTE this does not work if transform=mapobj.
    # Something about transforming to PlateCarree projection, then
    # reprojecting to mapobj.  I don't fully understand it, but this
    # works beautifully, and transform=mapobj puts all the vectors
    # in the center of the image.
    main_ax.scatter(
        x=formatted_data_dict["lon"].data[formatted_data_dict["rain_inds"]],
        y=formatted_data_dict["lat"].data[formatted_data_dict["rain_inds"]],
        transform=crs.PlateCarree(),
        marker="D",
        color="k",
        s=formatted_data_dict["rain_size"],
        zorder=2,
    )
    main_ax.barbs(
        formatted_data_dict["lon"].data,
        formatted_data_dict["lat"].data,
        formatted_data_dict["u"].data,
        formatted_data_dict["v"].data,
        formatted_data_dict[barb_color_variable].data,
        transform=crs.PlateCarree(),
        pivot="tip",
        rounding=False,
        cmap=mpl_colors_info["cmap"],
        flip_barb=formatted_data_dict["flip_barb"],
        # barb_increments=dict(half=10, full=20, flag=50),
        sizes=formatted_data_dict["sizes_dict"],
        length=formatted_data_dict["barb_length"],
        linewidth=formatted_data_dict["line_width"],
        norm=mpl_colors_info["norm"],
        zorder=1,
    )


def output_clean_windbarbs(
    area_def,
    clean_fnames,
    mpl_colors_info,
    image_datetime,
    formatted_data_dict,
    fig=None,
    main_ax=None,
    mapobj=None,
    barb_color_variable="speed",
):
    """Plot and save "clean" windbarb imagery.

    No background imagery, coastlines, gridlines, titles, etc.

    Returns
    -------
    list of str
        Full paths to all resulting output files.
    """
    LOG.info("Starting clean_fname")
    if fig is None and main_ax is None and mapobj is None:
        # Create matplotlib figure and main axis, where the main image will be plotted
        fig, main_ax, mapobj = create_figure_and_main_ax_and_mapobj(
            area_def.x_size, area_def.y_size, area_def, noborder=True
        )

    plot_barbs(
        main_ax,
        mapobj,
        mpl_colors_info,
        formatted_data_dict,
        barb_color_variable=barb_color_variable,
    )

    success_outputs = []

    if clean_fnames is not None:
        for clean_fname in clean_fnames:
            success_outputs += save_image(
                fig, clean_fname, is_final=False, image_datetime=image_datetime
            )

    return success_outputs


def format_windbarb_data(xarray_obj, product_name):
    """Format windbarb data before plotting."""
    # lat=xarray_obj['latitude'].to_masked_array()
    # lon2=xarray_obj['longitude'].to_masked_array()
    # direction=xarray_obj['wind_dir_deg_met'].to_masked_array()
    # speed=xarray_obj['wind_speed_kts'].to_masked_array()

    # u=speed * numpy.sin((direction+180)*3.1415926/180.0)
    # v=speed * numpy.cos((direction+180)*3.1415926/180.0)

    # u=speed * numpy.sin(direction*3.1415926/180.0)
    # v=speed * numpy.cos(direction*3.1415926/180.0)

    data_cols = xarray_obj[product_name].attrs.get(
        "windbarb_data_columns", ["speed", "direction", "rain_flag"]
    )

    num_product_arrays = 1
    if len(xarray_obj[product_name].shape) == 3:
        num_product_arrays = xarray_obj[product_name].shape[2]

    # This is 2-D, with only one array per variable (speed, direction,
    # rain_flag) - meaning NO ambiguities
    if len(xarray_obj[product_name].shape) == 3 and num_product_arrays == 3:
        speed = xarray_obj[product_name].to_masked_array()[:, :, 0]
        direction = xarray_obj[product_name].to_masked_array()[:, :, 1]
        rain_flag = xarray_obj[product_name].to_masked_array()[:, :, 2]
    # This is 2-D, with FOUR arrays per variable (speed, direction, rain_flag)
    # - meaning 4 ambiguities
    elif len(xarray_obj[product_name].shape) == 3 and num_product_arrays == 12:
        speed = xarray_obj[product_name].to_masked_array()[:, :, 0:4]
        direction = xarray_obj[product_name].to_masked_array()[:, :, 4:8]
        rain_flag = xarray_obj[product_name].to_masked_array()[:, :, 8:12]
    # This is 1-D, with one vector per variable - no ambiguities.
    elif xarray_obj[product_name].ndim == 3:
        speed = xarray_obj[product_name].to_masked_array()[:, :, 0]
        direction = xarray_obj[product_name].to_masked_array()[:, :, 1]
        rain_flag = xarray_obj[product_name].to_masked_array()[:, :, 2]
        if "pressure" in data_cols:
            pressure = xarray_obj[product_name].to_masked_array()[:, :, 3]
    else:
        speed = xarray_obj[product_name].to_masked_array()[:, 0]
        direction = xarray_obj[product_name].to_masked_array()[:, 1]
        rain_flag = xarray_obj[product_name].to_masked_array()[:, 2]
        if "pressure" in data_cols:
            pressure = xarray_obj[product_name].to_masked_array()[:, 3]
    # These should probably be specified in the product dictionary.
    # It will vary per-sensor / data type, these basically only currently work with
    # ASCAT 25 km data.
    # This would also avoid having the product names hard coded in the output
    # module code.

    from geoips.interfaces import products

    source_prod_spec = products.get_plugin(xarray_obj.source_name, product_name)
    prod_plugin = xarray_obj.attrs.get("product_plugin", source_prod_spec)

    try:
        barb_args = prod_plugin["spec"]["windbarb_plotter"]["plugin"]["arguments"]
    except KeyError:
        barb_args = {}

    if barb_args:
        # Thinning the data points to better display the windbards
        thinning = barb_args["thinning"]
        barblength = barb_args["length"]
        linewidth = barb_args["width"]
        sizes_dict = barb_args["sizes_dict"]
        rain_size = barb_args["rain_size"]
    elif product_name == "windbarbs":
        # Thinning the data points to better display the windbards
        thinning = 1  # skip data points
        barblength = 5.0
        linewidth = 1.5
        sizes_dict = dict(height=0.7, spacing=0.3)
        rain_size = 10
    elif product_name == "wind-ambiguities" or "wind-ambiguities" in product_name:
        # Thinning the data points to better display the windbards
        thinning = 1  # skip data points
        barblength = 5  # Length of individual barbs
        linewidth = 2  # Width of individual barbs
        rain_size = 10  # Marker size for rain_flag
        sizes_dict = dict(
            height=0,
            spacing=0,
            width=0,  # flag width, relative to barblength
            emptybarb=0.5,
        )
    else:
        raise ValueError(f"Unknown product {product_name}")

    lat = xarray_obj["latitude"].to_masked_array()
    lon2 = xarray_obj["longitude"].to_masked_array()
    u = speed * numpy.sin((direction + 180) * 3.1415926 / 180.0)
    v = speed * numpy.cos((direction + 180) * 3.1415926 / 180.0)

    # convert longitudes to (-180,180)
    # lon=utils.wrap_longitudes(lon2)
    # Must be 0-360 for barbs
    lon = numpy.ma.where(lon2 < 0, lon2 + 360, lon2)
    thin_slice = [slice(0, None, thinning)] * lat.ndim

    lat2 = lat[tuple(thin_slice)]
    lon2 = lon[tuple(thin_slice)]
    u2 = u[tuple(thin_slice)]
    v2 = v[tuple(thin_slice)]
    speed2 = speed[tuple(thin_slice)]
    rain_flag2 = rain_flag[tuple(thin_slice)]
    if "pressure" in data_cols:
        pressure2 = pressure[tuple(thin_slice)]

    if lat2.min() > 0:
        flip_barb = False
    elif lat2.max() < 0:
        flip_barb = True
    else:
        flip_barb = numpy.ma.where(lat2 > 0, False, True).data
    good_inds = numpy.ma.where(speed2)
    return_dict = {}
    if len(lon2.shape) != len(speed2.shape):
        return_dict["lon"] = lon2[good_inds[0:2]]
    else:
        return_dict["lon"] = lon2[good_inds]
    if len(lat2.shape) != len(speed2.shape):
        return_dict["lat"] = lat2[good_inds[0:2]]
    else:
        return_dict["lat"] = lat2[good_inds]
    if flip_barb is not True and flip_barb is not False:
        if len(flip_barb.shape) != len(speed2.shape):
            return_dict["flip_barb"] = flip_barb[good_inds[0:2]]
        else:
            return_dict["flip_barb"] = flip_barb[good_inds]
    else:
        return_dict["flip_barb"] = flip_barb
    return_dict["u"] = u2[good_inds]
    return_dict["v"] = v2[good_inds]
    return_dict["speed"] = speed2[good_inds]
    return_dict["rain_inds"] = numpy.ma.where(rain_flag2[good_inds])
    return_dict["barb_length"] = barblength
    return_dict["line_width"] = linewidth
    return_dict["sizes_dict"] = sizes_dict
    return_dict["rain_size"] = rain_size
    if "pressure" in data_cols:
        return_dict["pressure"] = pressure2[good_inds]

    return return_dict


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
):
    """Plot annotated windbarbs on matplotlib figure."""
    LOG.info("Startig imagery_windbarbs")

    if product_name_title is None:
        product_name_title = product_name

    success_outputs = []

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

    # Plot windbarbs

    formatted_data_dict = format_windbarb_data(xarray_obj, product_name)

    if clean_fname is not None:
        success_outputs += output_clean_windbarbs(
            area_def,
            [clean_fname],
            mpl_colors_info,
            xarray_obj.start_datetime,
            formatted_data_dict,
        )

    if output_fnames is not None:
        LOG.info("Starting output_fnames")

        # Create matplotlib figure and main axis, where the main image will be plotted
        fig, main_ax, mapobj = create_figure_and_main_ax_and_mapobj(
            area_def.x_size,
            area_def.y_size,
            area_def,
            existing_mapobj=None,
            noborder=False,
            frame_clr=frame_clr,
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
            plot_image(
                main_ax,
                bg_data,
                mapobj,
                mpl_colors_info=bg_mpl_colors_info,
                bkgrnd_clr=bkgrnd_clr,
            )

        plot_barbs(main_ax, mapobj, mpl_colors_info, formatted_data_dict)

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

        for annotated_fname in output_fnames:
            # Save the final image
            success_outputs += save_image(
                fig,
                annotated_fname,
                is_final=True,
                image_datetime=xarray_obj.start_datetime,
            )

    return success_outputs
