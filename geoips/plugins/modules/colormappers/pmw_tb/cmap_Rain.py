# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Module containing colormap for Rain Rate products."""

import logging

LOG = logging.getLogger(__name__)

interface = "colormappers"
family = "matplotlib"
name = "pmw_Rain"


def call(data_range=[0.05, 50.0], cbar_label=r"Rainrate $(mm hr^{-1})$"):
    """Colormap for displaying Rain Rate products.

    Parameters
    ----------
    data_range : list of float, default=[0.05, 50.0]
        * Min and max value for colormap.
        * Ensure the data range matches the range of the algorithm specified for
          use with this colormap
        * This colormap MUST include 0.05 and 50.0

    Returns
    -------
    mpl_colors_info : dict
        Dictionary of matplotlib plotting parameters, to ensure consistent
        image output
    """
    min_tb = data_range[0]
    max_tb = data_range[1]

    if min_tb >= 0.1 or max_tb <= 40:
        raise ("Rain rate range must include 0.1 and 40")
    ticks = [min_tb, 0.1, 0.2, 0.3, 0.5, 1, 2, 3, 5, 10, 15, 20, 30, 40, max_tb]
    colorlist = [
        "silver",
        "slategray",
        "navy",
        "blue",
        "royalblue",
        "cyan",
        "limegreen",
        "green",
        "yellow",
        "gold",
        "lightsalmon",
        "coral",
        "red",
        "maroon",
        "black",
    ]

    from matplotlib.colors import ListedColormap, BoundaryNorm

    mpl_cmap = ListedColormap(colorlist, N=len(colorlist))

    LOG.info("Setting norm")
    bounds = ticks + [max_tb + 1]
    mpl_norm = BoundaryNorm(bounds, mpl_cmap.N)

    # Must be uniform or proportional, None not valid for Python 3
    cbar_spacing = "uniform"  # for discrete bounds of a  color bar
    mpl_tick_labels = None
    mpl_boundaries = None

    # from geoips.image_utils.mpl_utils import create_colorbar
    # only create colorbar for final imagery
    # cbar = create_colorbar(fig, mpl_cmap, mpl_norm, ticks, cbar_label=cbar_label)
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
        "colorbar_kwargs": {
            "extend": "both",
        },
        "set_ticks_kwargs": {
            "size": "small",
        },
    }

    # return cbar, min_tb, max_tb
    return mpl_colors_info
