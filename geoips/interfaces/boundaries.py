from geoips.interfaces.base_interface import BaseInterface, BaseInterfacePlugin


class MapInterface(BaseInterface):
    name = "boundaries"
    deprecated_family_attr = ""


boundaries = MapInterface()
