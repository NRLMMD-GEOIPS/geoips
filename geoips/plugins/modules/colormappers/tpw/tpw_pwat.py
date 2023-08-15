# # # Distribution Statement A. Approved for public release. Distribution unlimited.
# # #
# # # Author:
# # # Naval Research Laboratory, Marine Meteorology Division
# # #
# # # This program is free software: you can redistribute it and/or modify it under
# # # the terms of the NRLMMD License included with this program. This program is
# # # distributed WITHOUT ANY WARRANTY; without even the implied warranty of
# # # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the included license
# # # for more details. If you did not receive the license, for more information see:
# # # https://github.com/U-S-NRL-Marine-Meteorology-Division/

"""Module containing tpw_pwat ASCII palette based colormap."""

import logging

LOG = logging.getLogger(__name__)

interface = "colormappers"
family = "matplotlib"
name = "tpw_pwat"


def call():
    """Colormap for displaying data using TPW PWAT ascii colormap.

    Data range of ASCII palette is 1 to 90 mm, with numerous transitions

    Returns
    -------
    mpl_colors_info : dict
        Dictionary of matplotlib plotting parameters, to ensure consistent
        image output

    See Also
    --------
    :ref:`api`
        ASCII palette is found in image_utils/ascii_palettes/tpw_pwat.txt
    """
    # levels in mm (evenly spaced by 2 mm except for 1-6):
    values = [
        1,
        2,
        3,
        4,
        5,
        6,
        8,
        10,
        12,
        14,
        16,
        18,
        20,
        22,
        24,
        26,
        28,
        30,
        32,
        34,
        36,
        38,
        40,
        42,
        44,
        46,
        48,
        50,
        52,
        54,
        56,
        58,
        60,
        62,
        64,
        66,
        68,
        70,
        72,
        74,
        76,
        78,
        80,
        82,
        84,
        86,
        88,
        90,
    ]

    from geoips.image_utils.colormap_utils import from_ascii
    from matplotlib.colors import BoundaryNorm
    from geoips.geoips_utils import find_ascii_palette

    bounds = values + [values[-1] + 1]
    mpl_cmap = from_ascii(find_ascii_palette(name))

    mpl_colors_info = {
        "cmap": mpl_cmap,
        "norm": BoundaryNorm(bounds, mpl_cmap.N),
        "cbar_ticks": values,
        "cbar_tick_labels": None,
        "cbar_label": r"TPW (mm)",
        "boundaries": None,
        "cbar_spacing": "uniform",
        "colorbar": True,
        "cbar_full_width": True,
    }

    return mpl_colors_info
