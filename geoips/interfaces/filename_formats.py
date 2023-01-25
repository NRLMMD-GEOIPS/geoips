from geoips.interfaces.base import BaseInterface, BasePlugin


class FilenameFormattersInterface(BaseInterface):
    name = "filename_formats"
    entry_point_group = "filename_formats"
    deprecated_family_attr = "filename_type"

    def find_duplicates(self, *args, **kwargs):
        try:
            func = self.get_plugin_attr(name, "find_duplicates")
        except AttributeError:
            raise AttributeError(
                f'Plugin {name} does not have a "find_duplicates" function.'
            )

        duplicates = func()

    def remove_duplicates(self):
        duplicates = self.find_duplicates()


filename_formats = FilenameFormattersInterface()


# class FilenameFormattersPlugin(BasePlugin):
#     interface = filename_formats
