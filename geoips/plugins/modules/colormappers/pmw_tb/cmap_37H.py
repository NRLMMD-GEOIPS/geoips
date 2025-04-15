# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Module containing colormap for ~37GHz PMW products."""

import logging

LOG = logging.getLogger(__name__)

interface = "colormappers"
family = "matplotlib"
name = "pmw_37H"


def call(data_range=[125, 310], cbar_label="TB (K)"):
    """Colormap for displaying ~37GHz PMW data.

    Parameters
    ----------
    data_range : list of float, default=[125, 310]
        * Min and max value for colormap.
        * Ensure the data range matches the range of the algorithm specified
          for use with this colormap
        * The 37GHz colormap MUST include 125 and 310

    Returns
    -------
    mpl_colors_info : dict
        Dictionary of matplotlib plotting parameters, to ensure consistent
        image output
    """
    min_tb = data_range[0]
    max_tb = data_range[1]

    if min_tb > 125 or max_tb < 300:
        raise ("37GHz TB range must include 125 and 300")

    from geoips.image_utils.colormap_utils import create_linear_segmented_colormap

    transition_vals = [
        (min_tb, 180),
        (180, 195),
        (195, 210),
        (210, 220),
        (220, 230),
        (230, 240),
        (240, 260),
        (260, 280),
        (280, max_tb),
    ]
    transition_colors = [
        ("lightyellow", "darkmagenta"),
        ("#80007F", "#0080FF"),
        ("#0080FF", "#3AB9FF"),
        ("#3AB9FF", "#7DFDFF"),
        ("#7DFDFF", "#80FF82"),
        ("#80FF82", "#FFFF80"),
        ("#FFFF80", "#FF8000"),
        ("#FF8000", "#800000"),
        ("silver", "black"),
    ]

    # special selection of label
    ticks = [125, 150, 180, 200, 220, 240, 260, 280, 300]

    # selection of min and max values for colormap if needed
    min_tb = transition_vals[0][0]
    max_tb = transition_vals[-1][1]
    ticks = ticks + [int(max_tb)]

    LOG.info("Setting cmap")
    mpl_cmap = create_linear_segmented_colormap(
        "pmw_37ghz", min_tb, max_tb, transition_vals, transition_colors
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
