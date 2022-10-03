from geoips.interfaces.base_interface import BaseInterface

class OutputFormatsInterface(BaseInterface):
    name = 'output_formats'
    deprecated_family_attr = 'output_type'

output_formats = OutputFormatsInterface()
