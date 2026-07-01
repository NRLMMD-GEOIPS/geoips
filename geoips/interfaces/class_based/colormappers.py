# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Colormappers interface class."""

from geoips.interfaces.class_based_plugin import BaseClassPlugin
from geoips.interfaces.base import BaseClassInterface


class BaseColormapperPlugin(BaseClassPlugin, abstract=True):
    """Base class for GeoIPS colormapper plugins."""

    data_tree = False

    def _post_call(self, data=None, *args, _obp_initiated=False, **kwargs):
        """Wrap colormapper dict output into ``DataTreeDitto`` for OBP.

        Colormappers return a ``dict`` with matplotlib colormap information.
        OBP wraps this into ``DataTreeDitto`` with ``_mpl_colors_info`` attrs
        so downstream steps can extract it.  SSP receives the raw dict.
        """
        if _obp_initiated and isinstance(data, dict):
            import xarray as xr
            from geoips.utils.types.datatree_ditto import DataTreeDitto

            ds = xr.Dataset(attrs={"_mpl_colors_info": data})
            return DataTreeDitto(ds, name=getattr(self, "name", "colormapper"))
        return data


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
