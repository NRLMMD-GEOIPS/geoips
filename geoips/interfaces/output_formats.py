from geoips.interfaces.base import BaseInterface, BasePlugin


class OutputFormatsInterface(BaseInterface):
    name = "output_formats"
    deprecated_family_attr = "output_type"


output_formats = OutputFormatsInterface()


# class OutputFormatsPlugin(BasePlugin):
#     interface = output_formats
