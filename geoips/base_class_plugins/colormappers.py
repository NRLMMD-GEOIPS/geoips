# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Module implementing the BaseColormapperPlugin class."""

from geoips.interfaces.class_based_plugin import BaseClassPlugin


class BaseColormapperPlugin(BaseClassPlugin, abstract=True):
    """Base class for GeoIPS colormapper plugins."""

    pass
