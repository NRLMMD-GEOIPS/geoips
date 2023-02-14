from geoips.interfaces.base import BaseInterface, BasePlugin


class ColorMapsInterface(BaseInterface):
    """Interface for the colormap to apply to the resulting product."""
    name = "colormaps"
    entry_point_group = "user_colormaps"
    deprecated_family_attr = "cmap_type"


colormaps = ColorMapsInterface()

