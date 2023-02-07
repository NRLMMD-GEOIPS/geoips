from geoips.interfaces.base import BaseInterface, BasePlugin


class ReadersInterface(BaseInterface):
    name = "readers"
    deprecated_family_attr = "reader_type"


readers = ReadersInterface()

