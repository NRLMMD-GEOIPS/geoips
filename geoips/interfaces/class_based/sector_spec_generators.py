# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Sector spec generators interface class."""

from geoips.interfaces.class_based_plugin import BaseClassPlugin
from geoips.interfaces.base import BaseClassInterface


class BaseSectorSpecGeneratorPlugin(BaseClassPlugin, abstract=True):
    """Base class for GeoIPS sector_spec_generator plugins."""

    pass


class SectorSpecGeneratorsInterface(BaseClassInterface):
    """Interface for generating appropriate specifications for a sector.

    Generates a sector specification (location, resolution, etc)
    using a dynamically determined subset of information (ie, center
    lat/lon of the region determined at run time, while the resolution
    and width/height are predetermined)
    """

    name = "sector_spec_generators"
    plugin_class = BaseSectorSpecGeneratorPlugin

    required_args = {"area_definition": []}
    required_kwargs = {"area_definition": []}


sector_spec_generators = SectorSpecGeneratorsInterface()
