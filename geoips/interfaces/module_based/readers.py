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

"""Readers interface module."""

from geoips.interfaces.base import BaseModuleInterface


class ReadersInterface(BaseModuleInterface):
    """Interface for ingesting a specific data type.

    Provides specification for ingensting a specific data type, and storing in
    the GeoIPS xarray-based internal format.
    """

    name = "readers"
    required_args = {"standard": ["fnames"]}
    required_kwargs = {
        "standard": ["metadata_only", "chans", "area_def", "self_register"]
    }


readers = ReadersInterface()
