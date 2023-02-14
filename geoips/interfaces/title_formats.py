from geoips.interfaces.base import BaseInterface, BasePlugin


class TitleFormattersInterface(BaseInterface):
    name = "title_formats"
    entry_point_group = "title_formats"
    deprecated_family_attr = "title_type"
    required_args = {'standard': []}


title_formats = TitleFormattersInterface()

