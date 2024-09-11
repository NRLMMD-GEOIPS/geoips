"""Generate dict of colormap info based on ascii-palette plugins."""

from matplotlib import colors

from geoips.interfaces import ascii_palettes

interface = "colormappers"
family = "matplotlib"
name = "ascii_based"


def call(
    cmap_name="tpw_cimss",
    data_range=None,
    create_colorbar=True,
    cbar_label=None,
    cbar_ticks=None,
    cbar_tick_labels=None,
    cbar_spacing="proportional",
    cbar_full_width=False,
    colorbar_kwargs=None,
    set_ticks_kwargs=None,
    set_label_kwargs=None,
    ascii_kwargs={},
):
    """Create a mpl Colors parameters dictionary using an ascii-based plugin.

    This information used in both colorbar and image production throughout
    GeoIPS image output specifications.

    Parameters
    ----------
    cmap_name : str, default="tpw_cimss"
        * Specify the name of the resulting ascii palette plugin.
    data_range : list, default=None
        * [min_val, max_val],
            matplotlib.colors.Normalize(vmin=min_val, vmax=max_val)
        * If data_range not specified, vmin and vmax both None.
    cbar_label : str, default=None
        * Positional parameter passed to cbar.set_label
        * If specified, use cbar_label string as colorbar label.
    create_colorbar : bool, default=True
        * Specify whether the image should contain a colorbar or not.
    cbar_ticks : list, default=None
        * Positional parameter passed to cbar.set_ticks
        * Specify explicit list of ticks to include for colorbar.
        * None indicates ticks at int(min) and int(max) values
    cbar_tick_labels : list, default=None
        * "labels" argument to pass to cbar.set_ticks.
        * can also specify directly within "set_ticks_kwargs"
    cbar_spacing : string, default="proportional"
        * "spacing" argument to pass to fig.colorbar
        * can also specify directly within "colorbar_kwargs"
    cbar_full_width : bool, default=True
        * Extend the colorbar across the full width of the image.
    colorbar_kwargs : dict, default=None
        * keyword arguments to pass through directly to "fig.colorbar"
    set_ticks_kwargs : dict, default=None
        * keyword arguments to pass through directly to "cbar.set_ticks"
    set_label_kwargs : dict, default=None
        * keyword arguments to pass through directly to "cbar.set_label"
    ascii_kwargs : dict, default={}
        * keyword arguments to pass through directly to
          "geoips.interfaces.text_based.ascii_palettes.AsciiPalettesPlugin:call"

    Returns
    -------
    mpl_colors_info : dict
        * Specifies matplotlib Colors parameters for use in both plotting and
            colorbar generation

    See Also
    --------
    :ref:`api`
        See geoips.image_utils.mpl_utils.create_colorbar for field descriptions.
    """
    if ascii_kwargs.get("norm_type"):
        norm_type = ascii_kwargs.pop("norm_type")
        # More normalization routines exist, however they take different arguments. The
        # first three normalization methods share the same arguments and 'BoundaryNorm'
        # can be constructed using data_range or cbar_ticks if specified.
        if norm_type not in ["Normalize", "NoNorm", "LogNorm", "BoundaryNorm"]:
            raise TypeError(
                f"Error: supplied ascii_kwarg 'norm_type', with value '{norm_type}' is "
                "not a valid Normalization routine of matplotlib.colors. Please "
                f"provide one of: ['Normalize', 'NoNorm', 'LogNorm', 'BoundaryNorm']."
            )
    else:
        norm_type = "Normalize"

    boundaries = None
    min_val = None
    max_val = None
    if data_range is not None:
        min_val = data_range[0]
        max_val = data_range[1]

    # Call the requested ascii plugin
    mpl_cmap = ascii_palettes.get_plugin(cmap_name)(**ascii_kwargs)

    # Apply normalization routine. Defaults to 'colors.Normalization'
    if norm_type != "BoundaryNorm":
        mpl_norm = getattr(colors, norm_type)(vmin=min_val, vmax=max_val)
    else:
        # Apply BoundaryNorm routine. Assert that enough information has been provided
        # to run this routine.
        if data_range is None and cbar_ticks is None:
            raise ValueError(
                "Error: Normalization routine 'BoundaryNorm' was selected but no "
                "information on the actual boundaries were supplied. Please either "
                "specify 'cbar_ticks' or 'data_range'. 'cbar_ticks' have higher "
                "priority than 'data_range'."
            )
        if cbar_ticks:
            boundaries = cbar_ticks + [cbar_ticks[-1] + 1]
        else:
            boundaries = data_range + [data_range[-1] + 1]
        mpl_norm = colors.BoundaryNorm(boundaries, mpl_cmap.N)

    # Set ticks for colorbar
    if cbar_ticks:
        mpl_ticks = cbar_ticks
    elif min_val is not None:
        mpl_ticks = [int(min_val), int(max_val)]
    else:
        mpl_ticks = None

    # Set tick labels for colorbar
    if cbar_tick_labels is None:
        mpl_tick_labels = mpl_ticks
    else:
        mpl_tick_labels = cbar_tick_labels

    mpl_colors_info = {
        "cmap": mpl_cmap,
        "norm": mpl_norm,
        "boundaries": None,
        "colorbar": create_colorbar,
        "cbar_ticks": cbar_ticks,
        "cbar_tick_labels": mpl_tick_labels,
        "cbar_label": cbar_label,
        "cbar_spacing": cbar_spacing,
        "cbar_full_width": cbar_full_width,
        "colorbar_kwargs": colorbar_kwargs,
        "set_ticks_kwargs": set_ticks_kwargs,
        "set_label_kwargs": set_label_kwargs,
    }
    return mpl_colors_info
