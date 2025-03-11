# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""matplotlib utilities."""

# Python Standard Libraries
import logging
import matplotlib
import matplotlib.pyplot as plt

from geoips.filenames.base_paths import PATHS as gpaths
from geoips.interfaces import title_formatters
from geoips.image_utils.maps import draw_features, draw_gridlines

matplotlib.use("agg")
rc_params = matplotlib.rcParams
LOG = logging.getLogger(__name__)


def percent_unmasked_rgba(rgba):
    """
    Convert to percent.

    Return percentage of array that is NOT fully transparent / masked
    (ie, non-zero values in the 4th dimension)

    Parameters
    ----------
    rgba : numpy.ndarray
        4 dimensional array where the 4th dimension is the alpha transparency array:
        1 is fully opaque, 0 is fully transparent

    Returns
    -------
    coverage : float
        Coverage in percentage, between 0 and 100.
    """
    import numpy

    coverage = 100.0 * numpy.count_nonzero(rgba[:, :, 3]) / rgba[:, :, 3].size
    return coverage


def rgba_from_arrays(red, grn, blu, alp=None):
    """
    Return rgba from red, green, blue, and alpha arrays.

    Parameters
    ----------
    red : numpy.ndarray
        red gun values
    grn : numpy.ndarray
        green gun values
    blu : numpy.ndarray
        blue gun values
    alp : numpy.ndarray, optional
        alpha values 1 is fully opaque, 0 is fully transparent
        If none, calculate alpha from red, grn, blu guns

    Returns
    -------
    rgba : numpy.ndarray
        4 layer dimensional numpy.ndarray
    """
    import numpy

    if alp is None:
        alp = alpha_from_masked_arrays([red, grn, blu])
    red.fill_value = 0
    grn.fill_value = 0
    blu.fill_value = 0
    rgba = numpy.dstack([red.filled(), grn.filled(), blu.filled(), alp])
    return rgba


def alpha_from_masked_arrays(arrays):
    """
    Convert from arrays to alpha.

    Return an alpha transparency array based on the masks from a list of
    masked arrays. 0=transparent, 1=opaque

    Parameters
    ----------
    arrays : numpy.ndarray
        list of numpy masked arrays, must all be the same shape

    Returns
    -------
    alp : numpy.ndarray
        the alpha transparency layer in matplotlib, values between
        0 and 1, where 0 is fully transparent and 1 is fully opaque
    """
    import numpy

    alp = numpy.zeros(arrays[0].shape, dtype=bool)
    for img in arrays:
        try:
            if img.mask is not numpy.False_:
                alp += img.mask
        except AttributeError:
            pass
    # You will get yelled at by numpy if you removed the "alp.dtype" portion of this.
    #   It thinks you are trying to cast alp to be an integer.
    alp = numpy.array(alp, dtype=float)
    alp -= float(1)
    alp *= float(-1)
    return alp


def plot_overlays(
    mapobj,
    curr_ax,
    area_def,
    feature_annotator=None,
    gridline_annotator=None,
    features_zorder=None,
    gridlines_zorder=None,
):
    """
    Plot specified coastlines and gridlines on the matplotlib axes.

    Parameters
    ----------
    mapobj : map object
        Basemap or CRS object for boundary and gridline plotting.
    ax : matplotlib.axes._axes.Axes
        matplotlib Axes object for boundary and gridline plotting.
    area_def : AreaDefinition
        pyresample AreaDefinition object specifying the area covered by
        the current plot
    feature_annotator : YamlPlugin
        A feature annotator plugin instance.
    gridline_annotator : YamlPlugin
       A gridlines annotator plugin instance.
    """
    draw_features(mapobj, curr_ax, feature_annotator, zorder=features_zorder)
    draw_gridlines(
        mapobj, area_def, curr_ax, gridline_annotator, zorder=gridlines_zorder
    )


def save_image(
    fig,
    out_fname,
    is_final=True,
    image_datetime=None,
    remove_duplicate_minrange=None,
    savefig_kwargs=None,
):
    """
    Save the image specified by the matplotlib figure "fig" to the filename out_fname.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        Figure object that needs to be written to a file.
    out_fname : str
        full path to the output filename
    is_final : bool, default=True
        Final imagery must set_axis_on for all axes. Non-final imagery
        must be transparent with set_axis_off for all axes, and no pad
        inches.

    Notes
    -----
    No return values (image is written to disk and IMAGESUCCESS is
    written to log file)
    """
    rc_params = matplotlib.rcParams
    from os.path import dirname, exists as pathexists
    from geoips.filenames.base_paths import make_dirs

    if savefig_kwargs is None:
        savefig_kwargs = {}

    if is_final:
        if not pathexists(dirname(out_fname)):
            make_dirs(dirname(out_fname))
        for ax in fig.axes:
            LOG.info("Adding ax to %s", ax)
            ax.set_axis_on()
        # final with titles, labels, etc.
        # Note bbox_inches='tight' removes white space, pad_inches=0.1 puts back in
        # a bit of white space.
        LOG.interactive("Writing %s", out_fname)
        fig.savefig(
            out_fname,
            dpi=rc_params["figure.dpi"],
            pad_inches=0.1,
            bbox_inches="tight",
            transparent=False,
        )
        if remove_duplicate_minrange is not None:
            remove_duplicates(out_fname, remove_duplicate_minrange)
    else:
        # Get rid of the colorbar axis for non-final imagery
        if not pathexists(dirname(out_fname)):
            make_dirs(dirname(out_fname))
        # no annotations
        # frameon=False makes it have no titles / lat/lons. does not avoid
        # colorbar, since that is its own ax
        for ax in fig.axes:
            LOG.info("Removing ax from %s", ax)
            ax.set_axis_off()

        LOG.info("Writing %s", out_fname)

        fig.savefig(
            out_fname,
            dpi=rc_params["figure.dpi"],
            pad_inches=0.0,
            transparent=True,
            facecolor="none",
            **savefig_kwargs,
        )
        if remove_duplicate_minrange is not None:
            remove_duplicates(out_fname, remove_duplicate_minrange)

    LOG.info("IMAGESUCCESS wrote %s", out_fname)
    if image_datetime is not None:
        from datetime import datetime

        LOG.info("LATENCY %s %s", datetime.utcnow() - image_datetime, out_fname)
    return [out_fname]


def remove_duplicates(fname, min_range):
    """Not implemented."""
    pass


def get_title_string_from_objects(
    area_def,
    xarray_obj,
    product_name_title,
    product_datatype_title=None,
    bg_xarray=None,
    bg_product_name_title=None,
    bg_datatype_title=None,
    title_copyright=None,
    title_formatter=None,
):
    """
    Get the title from object information.

    Parameters
    ----------
    area_def : AreaDefinition
        pyresample AreaDefinition object specifying the area covered by
        the current plot
    xarray_obj : xarray.Dataset
        data used to produce product
    product_name_title : str
        name to display for the title
    product_datatype_title : str, optional
        the data type
    bg_xarray : xarray, optional
        data used for background
    bg_product_name_title : str, optional
        background product title
    bg_datatype_title : str, optional
        background data type
    title_copyright : str, optional
        string for copyright
    title_formatter : str, optional
        format for title

    Returns
    -------
    title_string : str
        the title to use for matplotlib
    """
    if title_copyright is None:
        title_copyright = gpaths["GEOIPS_COPYRIGHT"]

    from geoips.sector_utils.utils import is_sector_type

    if product_datatype_title is None:
        product_source_name = xarray_obj.source_name
        product_platform_name = xarray_obj.platform_name
        if "model" in product_name_title:
            try:
                product_source_name = xarray_obj.model_source
                product_platform_name = ""
            except AttributeError:
                LOG.info("No model source in xarray")
        product_datatype_title = "{0} {1}".format(
            product_platform_name.upper(), product_source_name.upper()
        )

    if bg_xarray is not None and bg_datatype_title is None:
        bg_datatype_title = "{0} {1}".format(
            bg_xarray.platform_name.upper(), bg_xarray.source_name.upper()
        )

    if title_formatter is not None:
        title_formatter_plugin = title_formatters.get_plugin(title_formatter)
    elif is_sector_type(area_def, "tc"):
        title_formatter_plugin = title_formatters.get_plugin("tc_standard")
    else:
        title_formatter_plugin = title_formatters.get_plugin("static_standard")

    title_string = title_formatter_plugin(
        area_def,
        xarray_obj,
        product_name_title,
        product_datatype_title=product_datatype_title,
        bg_xarray=bg_xarray,
        bg_product_name_title=bg_product_name_title,
        bg_datatype_title=bg_datatype_title,
        title_copyright=title_copyright,
    )

    return title_string


def plot_image(main_ax, data, mapobj, mpl_colors_info, zorder=None, bkgrnd_clr=None):
    """
    Plot the "data" array and map in the matplotlib "main_ax".

    Parameters
    ----------
    main_ax : Axes
        matplotlib Axes object for plotting data and overlays
    data : numpy.ndarray)
        Numpy array of data to plot
    mapobj : Map Object
        Basemap or Cartopy CRS instance
    mpl_colors_info : dict
        Specifies matplotlib Colors parameters for use in both plotting and colorbar
    bkgrnd_clr: string (default = None)
        - The background color to apply to the image. If None, the image background will
          be white.

    See Also
    --------
    geoips.image_utils.mpl_utils.create_colorbar
        for field descriptions for mpl_colors_info
    """
    # main_ax.set_aspect('auto')
    if bkgrnd_clr:
        main_ax.set_facecolor(bkgrnd_clr)

    LOG.info("imshow")
    import numpy
    from geoips.image_utils.maps import is_crs

    if is_crs(mapobj):
        # Apparently cartopy handles the flipud

        # NOTE passing zorder=None is NOT the same as not passing zorder.
        # Ensure if zorder is passed, it is propagated to imshow.
        extra_args = {}
        if zorder is not None:
            extra_args = {"zorder": zorder}
        main_ax.imshow(
            data,
            transform=mapobj,
            extent=mapobj.bounds,
            cmap=mpl_colors_info["cmap"],
            norm=mpl_colors_info["norm"],
            **extra_args,
        )
    else:
        mapobj.imshow(
            numpy.flipud(data),
            ax=main_ax,
            cmap=mpl_colors_info["cmap"],
            norm=mpl_colors_info["norm"],
            aspect="auto",
        )

    return mapobj


def create_figure_and_main_ax_and_mapobj(
    x_size,
    y_size,
    area_def,
    frame_clr=None,
    font_size=None,
    existing_mapobj=None,
    noborder=False,
):
    """
    Create a figure of x pixels horizontally and y pixels vertically.

    Use information from matplotlib.rcParams.

    Parameters
    ----------
    x_size : int
        number pixels horizontally
        xsize = (float(x_size)/dpi)/(right_margin - left_margin)
    y_size : int
        number pixels vertically
        ysize = (float(y_size)/dpi)/(top_margin - bottom_margin)
    area_def : AreaDefinition
        pyresample AreaDefinition object - used for
        initializing map object (basemap or cartopy)
    frame_clr: string (default = None)
        - The color to apply to the frame of the image (where title, label, colorbar...)
          is set. If None, the frame background color will be white.
    font_size : int
        matplotlib font size
    existing_mapobj : CRS or basemap, optional
        If specified, do not regenerate mapobj. If None, create
        CRS or basemap object from specified area_def.
    noborder : bool, default=False
        If true, use [0, 0, 1, 1] for axes (allowing for image exact
        shape of sector).

    Returns
    -------
    fig : matplotlib.figure.Figure
        matplotlib Figure object to subsequently use for plotting
        imagery / colorbars / etc
    main_ax : matplotlib.axes._axes.Axes
        matplotlib Axes object corresponding to the single main plotting area.
    mapobj : mapobject
        cartopy crs or Basemap object for plotting
    """
    import matplotlib

    matplotlib.use("agg")
    rc_params = matplotlib.rcParams

    set_fonts(y_size, font_size=font_size)

    # Gather needed rcParam constants
    dpi = rc_params["figure.dpi"]

    # I can't seem to get a clean image with no border unless the ax fills the
    # whole figure.
    # Titles / labels don't show up unless we use figure.subplot rc_params
    # It does not appear to be possible to plot the image only once for both
    # the clean and annotated image.
    if noborder:
        left_margin = 0.0
        right_margin = 1.0
        bottom_margin = 0.0
        top_margin = 1.0
    else:
        left_margin = rc_params[
            "figure.subplot.left"
        ]  # Fractional distance from left edge of figure for subplot
        right_margin = rc_params[
            "figure.subplot.right"
        ]  # Fractional distance from right edge of figure for subplot
        bottom_margin = rc_params[
            "figure.subplot.bottom"
        ]  # Fractional distance from bottom edge of figure for subplot
        top_margin = rc_params[
            "figure.subplot.top"
        ]  # Fractional distance from top edge of figure for subplot

    xsize = (float(x_size) / dpi) / (right_margin - left_margin)
    ysize = (float(y_size) / dpi) / (top_margin - bottom_margin)

    if existing_mapobj is None:
        LOG.info("creating mapobj instance")
        mapobj = area_def.to_cartopy_crs()
    else:
        LOG.info("mapobj already exists, not recreating")
        mapobj = existing_mapobj

    LOG.info(
        "Creating figure: left, right, bottom, top, xsize, ysize %s %s %s %s %s %s",
        left_margin,
        right_margin,
        bottom_margin,
        top_margin,
        xsize,
        ysize,
    )

    from geoips.image_utils.maps import is_crs

    if is_crs(mapobj):
        # frameon=False creates transparent titles with cartopy
        fig = plt.figure(facecolor=frame_clr)
    else:
        fig = plt.figure(frameon=False, facecolor=frame_clr)
    fig.set_size_inches(xsize, ysize)
    set_fonts(y_size, font_size=font_size)

    LOG.info(
        "Creating main ax: left, bottom, width, height %s %s %s %s",
        left_margin,
        bottom_margin,
        right_margin - left_margin,
        top_margin - bottom_margin,
    )

    # cartopy figure with non-transparent titles
    # In [71]: fig = plt.figure()
    # In [72]: main_ax = fig.add_axes([0, 0, 1, 1], projection=mapobj, frame_on=True)
    # In [73]: plt.imshow(plot_data, transform=mapobj, extent=mapobj.bounds)
    # Out[73]: <matplotlib.image.AxesImage at 0x7fcfe5f75eb0>
    # In [74]: main_ax.set_title('Hello', y=1.2, fontsize=20)
    # Out[74]: Text(0.5, 1.2, 'Hello')
    # In [75]: fig.savefig('test.png', transparent=False)

    if is_crs(mapobj):
        # Transparent behind titles without frame_on True
        main_ax = fig.add_axes(
            [
                left_margin,
                bottom_margin,
                right_margin - left_margin,
                top_margin - bottom_margin,
            ],
            projection=mapobj,
            frame_on=not noborder,
        )
    else:
        main_ax = plt.Axes(
            fig,
            [
                left_margin,
                bottom_margin,
                right_margin - left_margin,
                top_margin - bottom_margin,
            ],
        )
    main_ax.set_axis_off()
    fig.add_axes(main_ax)

    return fig, main_ax, mapobj


def set_fonts(figure_y_size, font_size=None):
    """
    Set the fonts in the matplotlib.rcParams dictionary, using matplotlib.rc.

    Parameters
    ----------
    figure_y_size : int
        Font size set relative to number of pixels in the y direction
    """
    import matplotlib

    matplotlib.use("agg")
    mplrc = matplotlib.rc

    # Update font size based on number of lines
    if font_size is not None:
        title_fsize = font_size
    elif int(figure_y_size) / 1000 != 0:
        title_fsize = 20 * int(figure_y_size) / 1000
    else:
        title_fsize = 20

    font = {"family": "sans-serif", "weight": "bold", "size": title_fsize}

    LOG.info("Setting font size to %s for figure_y_size %s", title_fsize, figure_y_size)
    mplrc("font", **font)


def set_title(ax, title_string, figure_y_size, xpos=None, ypos=None, fontsize=None):
    """
    Set the title on figure axis "ax" to string "title_string".

    Parameters
    ----------
    ax : Axes
        matplotlib.axes._axes.Axes object to add the title
    title_string : str
        string specifying title to attach to axis "ax"
    figure_y_size : int
        vertical size of the image, used to proportionally set the title size
    xpos : float, optional
        x position of the title
    ypos : float, optional
        y position of the title
    fontsize : int, optional
        matplotlib font size
    """
    import matplotlib

    matplotlib.use("agg")
    rc_params = matplotlib.rcParams

    # Provide pad room between characters
    fontspace = rc_params["font.size"]
    title_line_space = float(fontspace) / figure_y_size
    # num_title_lines = len(title_string.split('\n'))

    if xpos is None:
        xpos = 0.5  # This centers the title
    if ypos is None:
        # ypos = 1 + title_line_space*2
        ypos = (
            1 + title_line_space * 2
        )  # This is relative to main_ax, so greater than 1.
    LOG.info(
        "Setting title: font size %s, xpos %s ypos %s, title_line_space %s",
        fontspace,
        xpos,
        ypos,
        title_line_space,
    )
    LOG.info("    Title string: %s", title_string)

    # from cartopy.mpl.geoaxes import GeoAxes # isinstance(ax, GeoAxes)
    # Slightly more space between title and lon labels
    # ax.set_title(title_string, y=ypos, fontsize=fontsize)
    ax.set_title(title_string, position=[xpos, ypos], fontsize=fontsize)


def create_colorbar(fig, mpl_colors_info):
    """
    Routine to create a single colorbar.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        Figure object to attach the colorbar - the colorbar will create its own ax
    mpl_colors_info : dict
        Dictionary of matplotlib Color information, required fields in Notes below.

    Returns
    -------
    cbar : matplotlib.colorbar.Colorbar
        This will have all the pertinent information for ensuring plot and
        colorbar use the same parameters

    Notes
    -----
    Required mpl_colors_info fields::

        mpl_colors_info['cmap'] (Colormap):
            matplotlib.colors.Colormap object (LinearSegmentedColormap, etc)
            this is used to plot the image and to generated the colorbar
        mpl_colors_info['norm'] (Normalize):
            matplotlib.colors.Normalize object (BoundaryNorm, Normalize, etc)
            again, this should be used to plot the data also
        mpl_colors_info['cbar_ticks'] (list):
            list of floats - values requiring tick marks on the colorbar
        mpl_colors_info['cbar_tick_labels'] (list)
            list of values to use to label tick marks, if other than
            found in cbar_ticks
        mpl_colors_info['boundaries'] (list):
            if cmap_norm is BoundaryNorm, list of boundaries for discrete colors
        mpl_colors_info['cbar_spacing'] (string):
            DEFAULT 'proportional', 'uniform' or 'proportional'
        mpl_colors_info['cbar_label'] (string):
            string label for colorbar
        mpl_colors_info['colorbar']: (bool)
            True if a colorbar should be included in the image, False if no cbar


    Colorbar set as::

        cbar_ax = fig.add_axes([<cbar_start_pos>, <cbar_bottom_pos>,
                                <cbar_width>, <cbar_height>])
        cbar = fig.colorbar(mappable=matplotlib.cm.ScalarMappable(norm=cmap_norm,
                                                                  cmap=mpl_cmap),
                            cax=cbar_ax,
                            norm=cmap_norm,
                            boundaries=cmap_boundaries,
                            spacing=cbar_spacing,
                            **cbar_kwargs)
        cbar.set_ticks(cbar_ticks, labels=cbar_tick_labels, **set_ticks_kwargs)
        if cbar_label:
            cbar.set_label(cbar_label, **set_label_kwargs)
    """
    # Required - needed for both colormaps and colorbars.
    cmap_norm = mpl_colors_info["norm"]
    mpl_cmap = mpl_colors_info["cmap"]
    cmap_boundaries = mpl_colors_info["boundaries"]

    # Required, for setting colorbar labels with set_label and ticks with set_ticks
    cbar_label = mpl_colors_info["cbar_label"]
    cbar_ticks = mpl_colors_info["cbar_ticks"]
    if cbar_ticks is None:
        cbar_ticks = [cmap_norm.vmin, cmap_norm.vmax]

    # Optional - can be specified in colorbar_kwargs
    cbar_spacing = "proportional"
    if mpl_colors_info.get("cbar_spacing") is not None:
        cbar_spacing = mpl_colors_info["cbar_spacing"]

    # Optional - can be specified in set_ticks_kwargs. None will be mapped to
    # cbar_ticks.
    cbar_tick_labels = None
    if "cbar_tick_labels" in mpl_colors_info:
        cbar_tick_labels = mpl_colors_info["cbar_tick_labels"]
    if mpl_colors_info["cbar_tick_labels"] is None:
        cbar_tick_labels = cbar_ticks

    # Allow arbitrary kwargs to colorbar, but ensure our defaults for extend
    # and orientation are set.
    cbar_kwargs = {}
    if mpl_colors_info.get("colorbar_kwargs") is not None:
        cbar_kwargs = mpl_colors_info["colorbar_kwargs"].copy()
    if "extend" not in cbar_kwargs:
        cbar_kwargs["extend"] = "both"
    if "spacing" not in cbar_kwargs:
        cbar_kwargs["spacing"] = cbar_spacing
    if "orientation" not in cbar_kwargs:
        cbar_kwargs["orientation"] = "horizontal"

    # Allow arbitrary kwargs to set_ticks, but ensure our defaults for labels
    # and font sizes are set
    set_ticks_kwargs = {}
    if mpl_colors_info.get("set_ticks_kwargs") is not None:
        set_ticks_kwargs = mpl_colors_info["set_ticks_kwargs"].copy()
    if "size" not in set_ticks_kwargs:
        set_ticks_kwargs["size"] = "small"
    if "labels" not in set_ticks_kwargs or set_ticks_kwargs["labels"] is None:
        set_ticks_kwargs["labels"] = cbar_tick_labels

    # Allow arbitrary kwargs to set_label
    set_label_kwargs = {}
    if mpl_colors_info.get("set_label_kwargs") is not None:
        set_label_kwargs = mpl_colors_info["set_label_kwargs"].copy()
    if "size" not in set_label_kwargs:
        set_label_kwargs["size"] = rc_params["font.size"]

    left_margin = rc_params[
        "figure.subplot.left"
    ]  # Fractional distance from left edge of figure for subplot
    right_margin = rc_params[
        "figure.subplot.right"
    ]  # Fractional distance from left edge of figure for subplot

    # Optional positioning information for the colorbar axis - default
    # location appropriately
    if mpl_colors_info.get("cbar_ax_left_start_pos") is not None:
        ax_left_start_pos = mpl_colors_info["cbar_ax_left_start_pos"]
    else:
        ax_left_start_pos = 2 * left_margin
        if mpl_colors_info.get("cbar_full_width") is True:
            ax_left_start_pos = left_margin  # Full width colorbar

    ax_bottom_start_pos = 0.05
    if mpl_colors_info.get("cbar_ax_bottom_start_pos") is not None:
        ax_bottom_start_pos = mpl_colors_info["cbar_ax_bottom_start_pos"]

    if mpl_colors_info.get("cbar_ax_width") is not None:
        ax_width = mpl_colors_info["cbar_ax_width"]
    else:
        ax_width = 1 - 4 * left_margin
        if mpl_colors_info.get("cbar_full_width") is True:
            ax_width = right_margin - left_margin  # Full width colorbar

    ax_height = 0.020
    if mpl_colors_info.get("cbar_ax_height") is not None:
        ax_height = mpl_colors_info["cbar_ax_height"]

    # Note - if we want to support "automated" pyplot.colorbar placement,
    # may need a method to "turn off" cbar_ax
    # [left, bottom, width, height]
    cbar_ax = fig.add_axes(
        [ax_left_start_pos, ax_bottom_start_pos, ax_width, ax_height]
    )
    cbar = plt.colorbar(
        mappable=matplotlib.cm.ScalarMappable(norm=cmap_norm, cmap=mpl_cmap),
        cax=cbar_ax,
        norm=cmap_norm,
        boundaries=cmap_boundaries,
        **cbar_kwargs,
    )

    if cbar_ticks:
        # matplotlib 3.6.0 sometimes has inconsistent results with including
        # minor ticks or not.
        # Unclear why it impacts some colorbars and not others.
        # We may eventually add support for including minor ticks within
        # mpl_colors_info, but for now explicitly turn off minor ticks so
        # outputs will continue to match (use the old default).
        cbar.minorticks_off()
        cbar.set_ticks(cbar_ticks, **set_ticks_kwargs)
    if cbar_label:
        cbar.set_label(cbar_label, **set_label_kwargs)

    return cbar
