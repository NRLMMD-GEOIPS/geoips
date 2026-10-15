# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Colormappers plugin class."""

import xarray as xr

from geoips.interfaces.class_based_plugin import BaseClassPlugin
from geoips.utils.types.datatree_ditto import DataTreeDitto


class BaseColormapperPlugin(BaseClassPlugin, abstract=True):
    """Base class for GeoIPS colormapper plugins."""

    data_tree = False

    def _post_call(self, data=None, *args, _obp_initiated=False, **kwargs):
        """Wrap colormapper dict output into ``DataTreeDitto`` for OBP.

        Colormappers return a ``dict`` with matplotlib colormap information.
        OBP wraps this into ``DataTreeDitto`` with ``mpl_colors_info`` attrs
        so downstream steps can extract it.  SSP receives the raw dict.
        """
        if _obp_initiated and isinstance(data, dict):
            ds = xr.Dataset(attrs={"mpl_colors_info": data})
            return DataTreeDitto(ds, name=getattr(self, "name", "colormapper"))
        return data
