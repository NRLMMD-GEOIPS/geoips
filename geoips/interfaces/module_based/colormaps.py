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

"""Colormaps interface module."""

from geoips.interfaces.base import BaseModuleInterface


class ColormapsInterface(BaseModuleInterface):
    """Interface for the colormap to apply to the resulting product."""

    name = "colormaps"
    required_args = {
        "rgb": [],
        "ascii": [],
        "linear_segmented": [],
        "linear_norm": [],
        "product_based": [],
        "explicit": [],
        "builtin_matplotlib_cmap": ["data_range"],
    }

    required_kwargs = {
        "rgb": [],
        "ascii": [],
        "linear_segmented": [("data_range",)],
        "linear_norm": [("data_range",)],
        "product_based": [("product_name",), ("data_range",)],
        "explicit": [],
        "builtin_matplotlib_cmap": [
            ("cmap_name",),
            ("cbar_label",),
            ("create_colorbar",),
        ],
    }


colormaps = ColormapsInterface()
