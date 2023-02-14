from geoips.interfaces.base import BaseInterface, BasePlugin


class ColorMapsInterface(BaseInterface):
    name = "colormaps"
    entry_point_group = "user_colormaps"
    deprecated_family_attr = "cmap_type"
    required_args = {'rgb': [],
                     'ascii': [],
                     'linear_segmented': [],
                     'linear_norm': [],
                     'product_based': [],
                     'explicit': [],
                     'builtin_matplotlib_cmap': ['data_range']}


colormaps = ColorMapsInterface()

