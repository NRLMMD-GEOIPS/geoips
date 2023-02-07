from geoips.interfaces.base import BaseInterface, BasePlugin


class MapInterface(BaseInterface):
    name = "boundaries"
    deprecated_family_attr = ""


boundaries = MapInterface()
