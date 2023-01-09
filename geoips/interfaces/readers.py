from geoips.interfaces.base_interface import BaseInterface, BaseInterfacePlugin


class ReadersInterface(BaseInterface):
    name = "readers"
    deprecated_family_attr = "reader_type"


readers = ReadersInterface()


class ReadersInterfacePlugin(BaseInterfacePlugin):
    interface = readers
