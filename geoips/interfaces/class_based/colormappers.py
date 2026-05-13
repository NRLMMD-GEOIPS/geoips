# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Colormappers interface class."""

from geoips.interfaces.class_based_plugin import BaseClassPlugin
from geoips.interfaces.base import BaseClassInterface


class BaseColormapperPlugin(BaseClassPlugin, abstract=True):
    """Base class for GeoIPS colormapper plugins."""

    pass


class ColormappersInterface(BaseClassInterface):
    """Interface for the colormapper to apply to the resulting product."""

    name = "colormappers"
    plugin_class = BaseColormapperPlugin

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
