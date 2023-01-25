from geoips.interfaces.base import BaseInterface, BasePlugin


class TitleFormattersInterface(BaseInterface):
    name = "title_formats"
    entry_point_group = "title_formats"
    deprecated_family_attr = "title_type"


title_formats = TitleFormattersInterface()


# class TitleFormattersPlugin(BasePlugin):
#     interface = title_formats
