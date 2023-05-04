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

"""Sector metadata generators interface module."""

from geoips.interfaces.base import BaseModuleInterface


class SectorMetadataGeneratorsInterface(BaseModuleInterface):
    """Interface for generating appropriate metadata for a sector.

    Provides specification for generating a dictionary-based set of
    metadata that corresponds to a given sector.  The sector "family"
    determines the formatting and contents of the metadata dictionary.
    """

    name = "sector_metadata_generators"
    required_args = {"tc": ["trackfile_name"]}
    required_kwargs = {"tc": []}


sector_metadata_generators = SectorMetadataGeneratorsInterface()
