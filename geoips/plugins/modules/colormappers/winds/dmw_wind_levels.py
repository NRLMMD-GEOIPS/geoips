# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Module containing Infrared algorithm colormap."""

import logging

LOG = logging.getLogger(__name__)

interface = "colormappers"
family = "matplotlib"
name = "dmw_wind_levels"


def call(data_range=[0, 3], pressure_range_legend=None):
    """Colormap for displaying multi-level derived motion winds.

    Each level is assigned an integer, with 0 being unassigned.

    Parameters
    ----------
    data_range : list, optional
        Min and max value for colormap, by default [0, 3]
    pressure_range_legend : list, optional
        List of strings that are used for setting the cbar tick labels, by default None

    Returns
    -------
    dict
        Dictionary of matplotlib plotting parameters, to ensure consistent image output
    """
    if not pressure_range_legend:
        pressure_range_legend = ["Unassigned", "Low", "Mid", "High"]
    min_lev = int(data_range[0])
    max_lev = int(data_range[1])

    from geoips.image_utils.colormap_utils import create_linear_segmented_colormap

    transition_vals = [(-0.5, 0.5), (0.5, 1.5), (1.5, 2.5), (2.5, 3.5)]
    transition_colors = [
        ("grey", "grey"),
        ("yellow", "yellow"),
        ("cyan", "cyan"),
        ("magenta", "magenta"),
    ]

    # special selection of label

    ticks = [0, 1, 2, 3]

    # selection of min and max values for colormap if needed
    min_lev = transition_vals[0][0]
    max_lev = transition_vals[-1][1]

    LOG.info("Setting cmap")
    mpl_cmap = create_linear_segmented_colormap(
        "DMW_cmap", min_lev, max_lev, transition_vals, transition_colors
    )

    LOG.info("Setting norm")
    from matplotlib.colors import Normalize

    mpl_norm = Normalize(vmin=min_lev, vmax=max_lev)

    cbar_label = None

    # Must be uniform or proportional, None not valid for Python 3
    cbar_spacing = "proportional"
    mpl_tick_labels = pressure_range_legend
    mpl_boundaries = None

    mpl_colors_info = {
        "cmap": mpl_cmap,
        "norm": mpl_norm,
        "cbar_ticks": ticks,
        "cbar_tick_labels": mpl_tick_labels,
        "cbar_label": cbar_label,
        "boundaries": mpl_boundaries,
        "cbar_spacing": cbar_spacing,
        "colorbar": True,
        "cbar_full_width": True,
    }

    # return cbar, min_lev, max_lev
    return mpl_colors_info
