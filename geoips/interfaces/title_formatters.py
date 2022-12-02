from geoips.interfaces.base_interface import BaseInterface, BaseInterfacePlugin


class TitleFormattersInterface(BaseInterface):
    name = 'title_formatters'
    entry_point_group = 'title_formats'
    deprecated_family_attr = 'title_type'


title_formatters = TitleFormattersInterface()


class TitleFormattersInterfacePlugin(BaseInterfacePlugin):
    interface = title_formatters
