from geoips.interfaces.base_interface import BaseInterface

class FilenameFormattersInterface(BaseInterface):
    name = 'filename_formatters'
    entry_point = 'filename_formats'
    deprecated_family_attr = 'filename_type'

filename_formatters = FilenameFormattersInterface()