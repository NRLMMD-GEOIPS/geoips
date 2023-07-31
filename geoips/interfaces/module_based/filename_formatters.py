# # # Distribution Statement A. Approved for public release. Distribution unlimited.
# # #
# # # Author:
# # # Naval Research Laboratory, Marine Meteorology Division
# # #
# # # This program is free software: you can redistribute it and/or modify it under
# # # the terms of the NRLMMD License included with this program. This program is
# # # distributed WITHOUT ANY WARRANTY; without even the implied warranty of
# # # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the included license
# # # for more details. If you did not receive the license, for more information see:
# # # https://github.com/U-S-NRL-Marine-Meteorology-Division/

"""Filename formatters interface module."""

from geoips.interfaces.base import BaseModuleInterface


class FilenameFormattersInterface(BaseModuleInterface):
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
        """Find duplicate files."""
        try:
            func = self.get_plugin_attr(name, "find_duplicates")
        except AttributeError:
            raise AttributeError(
                f'Plugin {name} does not have a "find_duplicates" function.'
            )

        duplicates = func()

    def remove_duplicates(self):
        """Remove duplicate files."""
        duplicates = self.find_duplicates()


filename_formatters = FilenameFormattersInterface()
