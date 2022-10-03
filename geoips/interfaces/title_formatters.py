from geoips.interfaces.base_interface import BaseInterface

class TitleFormattersInterface(BaseInterface):
    name = 'title_formatters'
    entry_point = 'title_formats'
    deprecated_family_attr = 'title_type'

title_formatters = TitleFormattersInterface()
