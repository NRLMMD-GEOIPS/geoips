# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Module containing user-specified IR-BD algorithm colormap."""

import logging

LOG = logging.getLogger(__name__)

interface = "colormappers"
family = "matplotlib"
name = "IR_BD"


def call(data_range=[-90.0, 40.0]):
    """Colormap for displaying algorithms/visir/IR_BD.py processed data.

    Parameters
    ----------
    data_range : list of float, default=[-90, 40]
        * Min and max value for colormap.
        * Ensure the data range matches the range of the algorithm specified for
          use with this colormap
        * This colormap MUST include -90 and 40

    Returns
    -------
    mpl_colors_info : dict
        Dictionary of matplotlib plotting parameters, to ensure consistent
        image output
    """
    # for Infrared-Dvorak images at 11 um.  Unit: Celsius
    #     This special black-white color scheme is designed for TC intensity analysis
    min_tb = int(data_range[0])
    max_tb = int(data_range[1])

    if min_tb > -90 or max_tb < 40:
        raise ("Infrared TB range must include -90 and 40")

    from geoips.image_utils.colormap_utils import create_linear_segmented_colormap

    transition_vals = [
        (min_tb, -80.01),
        (-80, -75.01),
        (-75, -69.01),
        (-69, -63.01),
        (-63, -53.01),
        (-53, -41.01),
        (-41, -30.01),
        (-30, 9),
        (9.01, 28),
        (28.01, max_tb),
    ]
    LOG.info("inside util= %s", max_tb)

    # matching TerraScan Color scheme: noaa_bd_151
    transition_colors = [
        ("#555555", "#555555"),
        ("#878787", "#878787"),
        ("white", "white"),
        ("black", "black"),
        ("#A0A0A0", "#A0A0A0"),
        ("#6E6E6E", "#6E6E6E"),
        ("#3C3C3C", "#3C3C3C"),
        ("#C9C9C9", "#6D6D6D"),
        ("#F7F7F7", "#030303"),
        ("black", "black"),
    ]

    # special selection of label

    ticks = [min_tb, -80, -75, -69, -63, -53, -41, -30, -20, -10, 0, 9, 15, 28, max_tb]

    # selection of min and max values for colormap if needed
    min_tb = transition_vals[0][0]
    max_tb = transition_vals[-1][1]
    ticks = ticks + [int(max_tb)]

    LOG.info("Setting cmap")
    mpl_cmap = create_linear_segmented_colormap(
        "IRBD_cmap", min_tb, max_tb, transition_vals, transition_colors
    )

    LOG.info("Setting norm")
    from matplotlib.colors import Normalize

    mpl_norm = Normalize(vmin=min_tb, vmax=max_tb)

    cbar_label = r"11$\mu$m BT ($^\circ$C)"

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
