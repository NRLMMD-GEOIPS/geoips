from geoips.interfaces.base import BaseInterface, BasePlugin


class ColorMapsInterface(BaseInterface):
    name = "colormaps"
    entry_point_group = "user_colormaps"
    deprecated_family_attr = "cmap_type"


colormaps = ColorMapsInterface()


# class ColorMapsPlugin(BasePlugin):
#     interface = colormaps
