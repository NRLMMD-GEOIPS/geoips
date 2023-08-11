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

"""Module containing Legacy colormap for ~37GHz PMW products."""

import logging

LOG = logging.getLogger(__name__)

interface = "colormappers"
family = "matplotlib"
name = "cloud_type"


def call(data_range=[1, 4], cbar_label="Cloud-Type"):
    """Legacy Colormap for displaying ~37GHz PMW data.

    Parameters
    ----------
    data_range : list of float, default=[1, 4]
        * Min and max value for colormap.
        * Ensure the data range matches the range of the algorithm specified
          for use with this colormap
        * 1 -- Water
        * 2 -- Supercooled
        * 3 -- Mixed
        * 4 -- Ice

    Returns
    -------
    mpl_colors_info : dict
        Dictionary of matplotlib plotting parameters,
        to ensure consistent image output
    """
    min_type = data_range[0]
    max_type = data_range[1]

    # if min_type > 1 or max_type < 4:
    #     raise ("Not All Cloud Type are present in this slice.")

    # use the Cloud Type color table for GEOring_3D products
    from matplotlib.colors import ListedColormap, to_rgba, get_named_colors_mapping

    # transition_vals = [
    #     (min_type, 1.99),
    #     (2, 2.99),
    #     (3, 3.98),
    #     (3.99, max_type),
    # ]

    color_dict = get_named_colors_mapping()

    LOG.info("Setting cmap")
    mpl_cmap = ListedColormap([to_rgba(color_dict["blue"]), to_rgba(color_dict["lightseagreen"]), 
              to_rgba(color_dict["paleturquoise"]), to_rgba(color_dict["ghostwhite"])])

    # special selection of label
    ticks = [1, 2, 3, 4]

    # selection of min and max values for colormap if needed
    # ticks = ticks + [transition_vals[-1][1]]


    LOG.info("Setting norm")
    from matplotlib.colors import Normalize

    mpl_norm = Normalize(vmin=min_type, vmax=max_type)

    # Must be uniform or proportional, None not valid for Python 3
    cbar_spacing = "proportional"
    mpl_tick_labels = ["Water", "Supercooled", "Mixed", "Ice"]
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
