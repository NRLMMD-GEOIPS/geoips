from geoips.interfaces.base_interface import BaseInterface, BaseInterfacePlugin


class ColorMapsInterface(BaseInterface):
    name = "colormaps"
    entry_point_group = "user_colormaps"
    deprecated_family_attr = "cmap_type"


colormaps = ColorMapsInterface()


class ColorMapsInterfacePlugin(BaseInterfacePlugin):
    interface = colormaps
