# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Module implementing the BaseSectorSpecGeneratorPlugin class."""

from geoips.interfaces.class_based_plugin import BaseClassPlugin


class BaseSectorSpecGeneratorPlugin(BaseClassPlugin, abstract=True):
    """Base class for GeoIPS sector_spec_generator plugins."""

    pass
