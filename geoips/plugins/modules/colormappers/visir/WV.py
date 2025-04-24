# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Module containing WV (water vapor) algorithm colormap."""

import logging

LOG = logging.getLogger(__name__)

interface = "colormappers"
family = "matplotlib"
name = "WV"


def call(data_range=[-70.0, 0.0]):
    """Colormap developed for displaying algorithms/WV.py processed data.

    Parameters
    ----------
    data_range : list of float, default=[-70, 0]
        * Min and max value for colormap.
        * Ensure the data range matches the range of the algorithm specified for
          use with this colormap
        * This colormap MUST include -70 and 0

    Returns
    -------
    mpl_colors_info : dict
        Dictionary of matplotlib plotting parameters, to ensure consistent
        image output
    """
    min_tb = int(data_range[0])
    max_tb = int(data_range[1])

    if min_tb > -70 or max_tb < 0:
        raise ("Infrared TB range must include -70 and 0")

    from geoips.image_utils.colormap_utils import create_linear_segmented_colormap

    transition_vals = [
        (min_tb, -69.9),
        (-69.9, -50),
        (-50, -40),
        (-40, -35),
        (-35, -30),
        (-30, -20),
        (-20, -10),
        (-10, -0.1),
        (-0.1, max_tb),
    ]
    # LOG.info("inside util= ", max_tb)

    # matching TerraScan Color scheme: noaa_bd_151
    transition_colors = [
        ("#800000", "#800000"),
        ("#820200", "#FFB266"),
        ("#FFB266", "#FFFF7B"),
        ("#FFFF80", "#66FFB2"),
        ("#66FFB2", "#80FFFC"),
        ("#80FFFC", "#3399FF"),
        ("#3399FF", "#146CEB"),
        ("#146CEB", "#7D0382"),
        ("black", "black"),
    ]

    # special selection of label

    ticks = [min_tb, -60, -50, -40, -30, -20, -10, max_tb]

    # selection of min and max values for colormap if needed
    min_tb = transition_vals[0][0]
    max_tb = transition_vals[-1][1]
    ticks = ticks + [int(max_tb)]

    LOG.info("Setting cmap")
    mpl_cmap = create_linear_segmented_colormap(
        "WV_cmap", min_tb, max_tb, transition_vals, transition_colors
    )

    LOG.info("Setting norm")
    from matplotlib.colors import Normalize

    mpl_norm = Normalize(vmin=min_tb, vmax=max_tb)

    cbar_label = r"BT ($^\circ$C)"

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
