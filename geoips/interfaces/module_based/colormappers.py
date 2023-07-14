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

"""Colormappers interface module."""

from geoips.interfaces.base import BaseModuleInterface


class ColormappersInterface(BaseModuleInterface):
    """Interface for the colormapper to apply to the resulting product."""

    name = "colormappers"
    required_args = {
        "matplotlib": [],
    }

    required_kwargs = {
        "matplotlib": [],
    }

    allowable_kwargs = {
        "matplotlib": [
            "data_range",
            "cmap_name",
            "ascii_path",
            "create_colorbar",
            "cbar_label",
            "cbar_ticks",
            "cbar_tick_labels",
            "cbar_spacing",
            "cbar_full_width",
            "colorbar_kwargs",
            "set_ticks_kwargs",
            "set_label_kwargs",
        ]
    }


colormappers = ColormappersInterface()
