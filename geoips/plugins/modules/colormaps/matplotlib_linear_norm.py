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

"""Matplotlib information for standard imagery with an existing system colormap."""
import logging

from geoips.image_utils.colormap_utils import from_ascii

LOG = logging.getLogger(__name__)

interface = "colormaps"
family = "matplotlib"
name = "matplotlib_linear_norm"


def call(
    data_range,
    cmap_name="Greys",
    cmap_path=None,
    create_colorbar=True,
    cbar_label=None,
    cbar_ticks=None,
    cbar_tick_labels=None,
    cbar_spacing="proportional",
    cbar_full_width=True,
    colorbar_kwargs=None,
    set_ticks_kwargs=None,
):
    """Set the matplotlib colors information for matplotlib linear norm cmaps.

    This information used in both colorbar and image production throughout
    GeoIPS image output specifications.

    Parameters
    ----------
    data_range : list
        * [min_val, max_val]
    cmap_name : str, default="Greys"
        * Specify the standard matplotlib colormap.
    cbar_label : str, default=None
        * If specified, use cbar_label string as colorbar label.
    create_colorbar : bool, default=True
        * Specify whether the image should contain a colorbar or not.
    cbar_ticks : list, default=None
        * Specify explicit list of ticks to include for colorbar.
        * None indicates ticks at int(min) and int(max) values

    Returns
    -------
    mpl_colors_info : dict
        * Specifies matplotlib Colors parameters for use in both plotting and
          colorbar generation

    See Also
    --------
    :ref:`api`
        See geoips.image_utils.mpl_utils.create_colorbar for field descriptions.
    """
    min_val = data_range[0]
    max_val = data_range[1]

    from matplotlib import cm

    if cmap_path is not None:
        mpl_cmap = from_ascii(cmap_path, name=cmap_name)
    else:
        mpl_cmap = cm.get_cmap(cmap_name)

    LOG.info("Setting norm")
    from matplotlib.colors import Normalize

    mpl_norm = Normalize(vmin=min_val, vmax=max_val)
    if cbar_ticks:
        mpl_ticks = cbar_ticks
    else:
        mpl_ticks = [int(min_val), int(max_val)]

    if cbar_tick_labels is None:
        mpl_tick_labels = mpl_ticks

    # Must be uniform or proportional, None not valid for Python 3
    mpl_boundaries = None

    mpl_colors_info = {
        "cmap": mpl_cmap,
        "norm": mpl_norm,
        "cbar_ticks": mpl_ticks,
        "cbar_tick_labels": mpl_tick_labels,
        "cbar_label": cbar_label,
        "boundaries": mpl_boundaries,
        "cbar_spacing": cbar_spacing,
        "colorbar": create_colorbar,
        "cbar_full_width": cbar_full_width,
        "colorbar_kwargs": colorbar_kwargs,
        "set_ticks_kwargs": set_ticks_kwargs,
    }

    return mpl_colors_info
