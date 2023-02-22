from geoips.interfaces.base import BaseInterface, BasePlugin


class MapInterface(BaseInterface):
    """Interface for overlaying boundaries and gridlines on output images."""
    name = "boundaries"
    deprecated_family_attr = ""


boundaries = MapInterface()
