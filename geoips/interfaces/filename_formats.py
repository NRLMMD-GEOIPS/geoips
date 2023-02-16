from geoips.interfaces.base import BaseInterface, BasePlugin


class FilenameFormatsInterface(BaseInterface):
    name = "filename_formats"
    entry_point_group = "filename_formats"
    deprecated_family_attr = "filename_type"

    required_args = {
        "standard": ["area_def", "xarray_obj", "product_name"],
        "xarray_metadata_to_filename": ["xarray_obj"],
        "data": ["area_def", "xarray_obj", "product_names"],
        "standard_metadata": ["area_def", "xarray_obj", "product_filename"],
    }
    required_kwargs = {
        "standard": [
            "coverage",
            "output_type",
            "output_type_dir",
            "product_dir",
            "product_subdir",
            "source_dir",
            "basedir",
        ],
        "xarray_metadata_to_filename": ["extension", "basedir"],
        "data": [
            "coverage",
            "output_type",
            "output_type_dir",
            "product_dir",
            "product_subdir",
            "source_dir",
            "basedir",
        ],
        "standard_metadata": ["metadata_dir", "metadata_type", "basedir"],
    }

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
