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

"""Module containing tpw_cimss ASCII palette based colormap."""
import logging

LOG = logging.getLogger(__name__)

interface = "colormaps"
family = "matplotlib"
name = "tpw_cimss"


def call():
    """Colormap for displaying data using TPW CIMSS ascii colormap.

    Data range of ASCII palette is 5 to 65 mm, with transitions at
    15, 25, 35, 45, and 55.

    Returns
    -------
    mpl_colors_info : dict
        Dictionary of matplotlib plotting parameters, to ensure consistent
        image output

    See Also
    --------
    :ref:`api`
        ASCII palette is found in image_utils/ascii_palettes/tpw_cimss.txt
    """
    from os.path import join as pathjoin
    from geoips.filenames.base_paths import PATHS as gpaths
    from geoips.image_utils.colormap_utils import from_ascii
    from matplotlib.colors import Normalize

    min_val = 5
    max_val = 65

    mpl_colors_info = {
        "cmap": from_ascii(
            pathjoin(
                gpaths["BASE_PATH"], "plugins", "txt", "ascii_palettes", "tpw_cimss.txt"
            )
        ),
        "norm": Normalize(vmin=min_val, vmax=max_val),
        "cbar_ticks": [min_val, 15, 25, 35, 45, 55, max_val],
        "cbar_tick_labels": None,
        "cbar_label": r"TPW (mm)",
        "boundaries": None,
        "cbar_spacing": "proportional",
        "colorbar": True,
        "cbar_full_width": True,
    }

    return mpl_colors_info
