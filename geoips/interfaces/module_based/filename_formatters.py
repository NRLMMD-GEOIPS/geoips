# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Filename formatters interface module."""

from geoips.interfaces.base import BaseClassInterface


class FilenameFormattersInterface(BaseClassInterface):
    """Specification for formatting the full path and file name.

    File path and name formatting is determined using attributes within the
    GeoIPS xarray objects.
    """

    name = "filename_formatters"

    required_args = {
        "standard": ["area_def", "xarray_obj", "product_name"],
        "xarray_metadata_to_filename": ["xarray_obj"],
        "data": ["area_def", "xarray_obj", "product_names"],
        "standard_metadata": ["area_def", "xarray_obj", "product_filename"],
        "xarray_area_product_to_filename": ["xarray_obj", "area_def", "product_name"],
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
        "xarray_area_product_to_filename": ["output_type", "basedir", "extra_field"],
    }

    # The functions below were commented out as they included errors, and were not used
    # by GeoIPS at this time. 9/27/23

    # def find_duplicates(self, *args, **kwargs):
    #     """Find duplicate files."""
    #     try:
    #         func = self.get_plugin_attr(name, "find_duplicates")
    #     except AttributeError:
    #         raise AttributeError(
    #             f'Plugin {name} does not have a "find_duplicates" function.'
    #         )

    #     duplicates = func()

    # def remove_duplicates(self):
    #     """Remove duplicate files."""
    #     duplicates = self.find_duplicates()


filename_formatters = FilenameFormattersInterface()
