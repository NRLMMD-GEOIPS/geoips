# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Module implementing the BaseInterpolatorPlugin class."""

from geoips.interfaces.class_based_plugin import BaseClassPlugin


class BaseInterpolatorPlugin(BaseClassPlugin, abstract=True):
    """Base class for GeoIPS interpolator plugins."""

    pass
