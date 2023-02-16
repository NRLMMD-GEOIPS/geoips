from geoips.interfaces.base import BaseInterface, BasePlugin


class FilenameFormatsInterface(BaseInterface):
    """Specification for formatting the full path and file name.

    File path and name formatting is determined using attributes within the
    GeoIPS xarray objects.
    """
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


filename_formats = FilenameFormatsInterface()

