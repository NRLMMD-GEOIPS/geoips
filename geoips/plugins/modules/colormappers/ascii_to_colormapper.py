"""Colormapper module which transforms a text-based ascii palette into a colormapper."""

import logging

from matplotlib.colors import Normalize

from geoips.interfaces import ascii_palettes

LOG = logging.getLogger(__name__)

interface = "colormappers"
family = "matplotlib"
name = "ascii_to_colormapper"


def call(
    ascii_name,
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
):
    """Set the matplotlib colors information for matplotlib linear norm cmaps.

    This information used in both colorbar and image production throughout
    GeoIPS image output specifications.

    Parameters
    ----------
    ascii_name : str, default="Greys"
        * Specify the name of the resulting matplotlib colormap.
        * If no ascii_path specified, will use builtin matplotlib
          colormap of name cmap_name.
    data_range : list, default=None
        * [min_val, max_val], matplotlib.colors.Normalize(vmin=min_val, vmax=max_val)
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
    min_val = None
    max_val = None
    if data_range is not None:
        min_val = data_range[0]
        max_val = data_range[1]
    try:
        mpl_cmap = ascii_palettes.get_plugin(ascii_name).colormap
    except ValueError:
        raise ValueError(
            "Colormap {cmap_name} not found in source {cmap_source}"
        )

    LOG.info("Setting norm")

    mpl_norm = Normalize(vmin=min_val, vmax=max_val)
    if cbar_ticks:
        mpl_ticks = cbar_ticks
    elif min_val is not None:
        mpl_ticks = [int(min_val), int(max_val)]
    else:
        mpl_ticks = None

    if cbar_tick_labels is None:
        mpl_tick_labels = mpl_ticks

    # Must be uniform or proportional, None not valid for Python 3
    mpl_boundaries = None

    mpl_colors_info = {
        "cmap": mpl_cmap,
        "norm": mpl_norm,
        "boundaries": mpl_boundaries,
        "colorbar": create_colorbar,
        "cbar_ticks": mpl_ticks,
        "cbar_tick_labels": mpl_tick_labels,
        "cbar_label": cbar_label,
        "cbar_spacing": cbar_spacing,
        "cbar_full_width": cbar_full_width,
        "colorbar_kwargs": colorbar_kwargs,
        "set_ticks_kwargs": set_ticks_kwargs,
        "set_label_kwargs": set_label_kwargs,
    }

    return mpl_colors_info