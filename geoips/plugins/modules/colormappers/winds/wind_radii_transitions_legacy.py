# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Module containing wind speed colormap with transitions at 34, 50, 64, and 80."""

import logging

LOG = logging.getLogger(__name__)

interface = "colormappers"
family = "matplotlib"
name = "wind_radii_transitions_legacy"


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
        (min_wind_speed, 34),
        (34, 50),
        (50, 64),
        (64, 80),
        # (64, 72),
        # (72, 80),
        (80, 100),
        (100, 120),
        (120, 150),
        (150, max_wind_speed),
    ]
    transition_colors = [
        ("lightblue", "blue"),
        ("yellow", "orange"),
        ("red", "red"),
        # ('thistle', 'thistle'),
        # ('firebrick', 'firebrick'),
        # ('fuchsia', 'fuchsia'),
        # ('mediumvioletred', 'mediumvioletred'),
        ("rebeccapurple", "rebeccapurple"),
        # ('purple', 'rebeccapurple'),
        # ('rebeccapurple', 'rebeccapurple'),
        # ('mediumvioletred', 'mediumvioletred'),
        ("palevioletred", "palevioletred"),
        ("silver", "silver"),
        ("gray", "gray"),
        ("dimgray", "dimgray"),
    ]

    ticks = [xx[0] for xx in transition_vals]

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
    }

    # return cbar, min_wind_speed, max_wind_speed
    return mpl_colors_info
