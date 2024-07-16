# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Module containing colormap for ~89GHz PMW products."""

import logging

LOG = logging.getLogger(__name__)

interface = "colormappers"
family = "matplotlib"
name = "pmw_89H"


def call(data_range=[105, 305], cbar_label="TB (K)"):
    """Colormap for displaying ~89GHz PMW data.

    Parameters
    ----------
    data_range : list of float, default=[105, 305]
        * Min and max value for colormap.
        * Ensure the data range matches the range of the algorithm specified for
          use with this colormap
        * This colormap MUST include 105 and 305

    Returns
    -------
    mpl_colors_info : dict
        Dictionary of matplotlib plotting parameters, to ensure consistent
        image output
    """
    min_tb = data_range[0]
    max_tb = data_range[1]

    if min_tb >= 180 or max_tb <= 280:
        raise ("89H TB range MUST include 180 and 280")

    from geoips.image_utils.colormap_utils import create_linear_segmented_colormap

    transition_vals = [
        (min_tb, 180),
        (180, 212),
        (212, 228),
        (228.1, 254),
        (254.1, 280),
        (280, max_tb),
    ]
    transition_colors = [
        ("white", "black"),
        ("#A4641A", "#FC0603"),
        ("#F4CD03", "#F2F403"),
        ("#8CF303", "#0FB503"),
        ("#06DCFD", "#0708B5"),
        ("navy", "white"),
    ]

    # ticks = [xx[0] for xx in transition_vals]

    # special selection of label

    # ticks = [105, 125, 150, 175, 200, 225, 250, 275, 305]
    ticks = [105, 150, 180, 212, 228, 254, 280, 305]

    # selection of min and max values for colormap if needed
    min_tb = transition_vals[0][0]
    max_tb = transition_vals[-1][1]

    LOG.info("Setting cmap")
    mpl_cmap = create_linear_segmented_colormap(
        "pmw_89h", min_tb, max_tb, transition_vals, transition_colors
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
