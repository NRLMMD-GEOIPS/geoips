# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Module containing Legacy colormap for ~37GHz PMW products."""

import logging

LOG = logging.getLogger(__name__)

interface = "colormappers"
family = "matplotlib"
name = "pmw_37H_Legacy"


def call(data_range=[180, 280], cbar_label="TB (K)"):
    """Legacy Colormap for displaying ~37GHz PMW data.

    Parameters
    ----------
    data_range : list of float, default=[180, 280]
        * Min and max value for colormap.
        * Ensure the data range matches the range of the algorithm specified
          for use with this colormap
        * The 37GHz colormap MUST include 180 and 280

    Returns
    -------
    mpl_colors_info : dict
        Dictionary of matplotlib plotting parameters,
        to ensure consistent image output
    """
    min_tb = data_range[0]
    max_tb = data_range[1]

    if min_tb > 180 or max_tb < 280:
        raise ("Legacy 37GHz TB range must include 180 and 280")

    # use the TC 37 GHz legacy color table for 37 GHz products
    from geoips.image_utils.colormap_utils import create_linear_segmented_colormap

    transition_vals = [
        (min_tb, 195),
        (195, 210),
        (210, 220),
        (220, 230),
        (230, 240),
        (240, 260),
        (260, max_tb),
    ]
    transition_colors = [
        ("#80007F", "#0080FF"),
        ("#0080FF", "#3AB9FF"),
        ("#3AB9FF", "#7DFDFF"),
        ("#7DFDFF", "#80FF82"),
        ("#80FF82", "#FFFF80"),
        ("#FFFF80", "#FF8000"),
        ("#FF8000", "#800000"),
    ]

    # special selection of label
    ticks = [180, 190, 200, 210, 220, 230, 240, 250, 260, 270, 280]

    # selection of min and max values for colormap if needed
    min_tb = transition_vals[0][0]
    max_tb = transition_vals[-1][1]
    ticks = ticks + [int(max_tb)]

    LOG.info("Setting cmap")
    mpl_cmap = create_linear_segmented_colormap(
        "pmw_37ghz_legacy", min_tb, max_tb, transition_vals, transition_colors
    )

    LOG.info("Setting norm")
    from matplotlib.colors import Normalize

    mpl_norm = Normalize(vmin=min_tb, vmax=max_tb)

    # Must be uniform or proportional, None not valid for Python 3
    cbar_spacing = "proportional"
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
    }

    # return cbar, min_tb, max_tb
    return mpl_colors_info
