# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Module implementing the BaseSectorMetadataAdjusterPlugin class."""

from geoips.interfaces.class_based_plugin import BaseClassPlugin


class BaseSectorMetadataAdjusterPlugin(BaseClassPlugin, abstract=True):
    """Base class for GeoIPS sector_metadata_adjuster plugins."""

    pass
