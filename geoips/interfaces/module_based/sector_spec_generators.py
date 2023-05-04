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

"""Sector spec generators interface module."""

from geoips.interfaces.base import BaseModuleInterface


class SectorSpecGeneratorsInterface(BaseModuleInterface):
    """Interface for generating appropriate specifications for a sector.

    Generates a sector specification (location, resolution, etc)
    using a dynamically determined subset of information (ie, center
    lat/lon of the region determined at run time, while the resolution
    and width/height are predetermined)
    """

    name = "sector_spec_generators"
    required_args = {"area_definition": []}
    required_kwargs = {"area_definition": []}


sector_spec_generators = SectorSpecGeneratorsInterface()
