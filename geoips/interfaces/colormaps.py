from geoips.interfaces.base_interface import BaseInterface

class ColorMapsInterface(BaseInterface):
    name = 'colormaps'
    entry_point = 'user_colormaps'
    deprecated_family_attr = 'cmap_type'

colormaps = ColorMapsInterface()