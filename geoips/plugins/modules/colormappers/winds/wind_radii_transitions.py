# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Module containing wind speed colormap with transitions at 34, 50, 64, and 80."""

import logging

LOG = logging.getLogger(__name__)

interface = "colormappers"
family = "matplotlib"
name = "wind_radii_transitions"


def call(data_range=[0, 200]):
    """Generate appropriate matplotlib colors for plotting standard wind speeds.

    wind_radii_transitions contains hard coded transition values for different
    colors, in order to have consistent imagery across all sensors / products.

    Parameters
    ----------
    data_range : list of float, default=[0, 200]
        * Min and max value for colormap.
        * Ensure the data range matches the range of the algorithm specified for
          use with this colormap
        * This colormap MUST include 0 and 200

    Returns
    -------
    mpl_colors_info : dict
        Dictionary of matplotlib plotting parameters, to ensure consistent
        image output
    """
    from geoips.image_utils.colormap_utils import create_linear_segmented_colormap

    min_wind_speed = data_range[0]
    max_wind_speed = data_range[1]
    transition_vals = [
        (min_wind_speed, 12),
        (12, 25),
        (25, 34),
        (34, 50),
        (50, 64),
        (64, 80),
        (80, 100),
        (100, 120),
        (120, max_wind_speed),
    ]
    transition_colors = [
        ("white", "#739FE1"),
        ("#3f82ff", "blue"),
        ("#94d9a7", "#317E0B"),
        ("yellow", "orange"),
        ("#ff7878", "#C90A0A"),
        ("#C285F6", "rebeccapurple"),
        ("#fcb4cc", "palevioletred"),
        # Grays
        # ("#BCB8B8", "#999898"),
        # ("#999898", "#808080"),
        # ("#808080", "#737373"),
        # ("#737373", "#5a5a5a"),
        # ("#5a5a5a", "#3d3d3d"),
        ("#BCB8B8", "dimgray"),
        ("darkslategray", "black"),
    ]

    # ticks = [xx[0] for xx in transition_vals]
    ticks = [0, 12, 25, 34, 50, 64, 80, 100, 120, 150, 200]

    min_wind_speed = transition_vals[0][0]
    max_wind_speed = transition_vals[-1][1]

    LOG.info("Setting cmap")
    mpl_cmap = create_linear_segmented_colormap(
        "windspeed_cmap",
        min_wind_speed,
        max_wind_speed,
        transition_vals,
        transition_colors,
    )

    LOG.info("Setting norm")
    from matplotlib.colors import Normalize

    mpl_norm = Normalize(vmin=min_wind_speed, vmax=max_wind_speed)

    cbar_label = "Surface Wind (knots)"

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

    # return cbar, min_wind_speed, max_wind_speed
    return mpl_colors_info
