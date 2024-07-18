# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

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
