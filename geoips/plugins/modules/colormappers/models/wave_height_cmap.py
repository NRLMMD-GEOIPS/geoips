# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Module containing wave height colormap with transitions at 0,2,4,6,8."""

import logging

LOG = logging.getLogger(__name__)

interface = "colormappers"
family = "matplotlib"
name = "wave_height_cmap"


def call(data_range=[0, 8]):
    """Generate appropriate matplotlib colors for plotting standard wave heights.

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

    min_wave_height = data_range[0]
    max_wave_height = data_range[1]
    transition_vals = [
        (min_wave_height, 2),
        (2, 4),
        (4, 6),
        (6, max_wave_height),
    ]
    transition_colors = [
        ("white", "#08306b"),
        ("#9e9ac8", "#3f007d"),
        ("#e6f3cd", "#8ACE00"),
        ("yellow", "#de9d12"),
    ]

    # ticks = [xx[0] for xx in transition_vals]
    ticks = [0, 2, 4, 6, 8]

    LOG.info("Setting cmap")
    mpl_cmap = create_linear_segmented_colormap(
        "windspeed_cmap",
        min_wave_height,
        max_wave_height,
        transition_vals,
        transition_colors,
    )

    LOG.info("Setting norm")
    from matplotlib.colors import Normalize

    mpl_norm = Normalize(vmin=min_wave_height, vmax=max_wave_height)

    cbar_label = "Wave Height (m)"

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
