# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Sector spec generators interface module."""

from geoips.interfaces.base import BaseClassInterface


class SectorSpecGeneratorsInterface(BaseClassInterface):
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
