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

"""Module containing matplotlib information for RGB or RGBA imagery."""

import logging

LOG = logging.getLogger(__name__)

interface = "colormappers"
family = "matplotlib"
name = "cmap_rgb"


def call():
    """For rgb imagery, we require no color information.

    colormap is entirely specified by the RGB(A) arrays, so no specific
    matplotlib color information required.

    Parameters
    ----------
        No arguments

    Returns
    -------
    mpl_colors_info : dict
        * Specifies matplotlib Colors parameters for use in both plotting
          and colorbar generation
        * For RGBA arrays, all fields are "None"
    """
    mpl_colors_info = {
        "cmap": None,
        "norm": None,
        "cbar_ticks": None,
        "cbar_tick_labels": None,
        "cbar_label": None,
        "boundaries": None,
        "cbar_spacing": "proportional",
        "colorbar": False,
    }
    return mpl_colors_info
