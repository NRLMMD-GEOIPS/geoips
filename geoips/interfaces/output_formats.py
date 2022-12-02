from geoips.interfaces.base_interface import BaseInterface, BaseInterfacePlugin


class OutputFormatsInterface(BaseInterface):
    name = 'output_formats'
    deprecated_family_attr = 'output_type'


output_formats = OutputFormatsInterface()


class OutputFormatsInterfacePlugin(BaseInterfacePlugin):
    interface = output_formats
