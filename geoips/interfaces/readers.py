from geoips.interfaces.base_interface import BaseInterface

class ReadersInterface(BaseInterface):
    name = 'readers'
    deprecated_family_attr = 'reader_type'

readers = ReadersInterface()
