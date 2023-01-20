from geoips.interfaces.base import BaseInterface, BasePlugin


class TitleFormattersInterface(BaseInterface):
    name = "title_formatters"
    entry_point_group = "title_formats"
    deprecated_family_attr = "title_type"


title_formatters = TitleFormattersInterface()


# class TitleFormattersPlugin(BasePlugin):
#     interface = title_formatters
