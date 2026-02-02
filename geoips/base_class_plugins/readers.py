# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Module implementing the BaseReaderPlugin class."""

from geoips.interfaces.class_based_plugin import BaseClassPlugin


class BaseReaderPlugin(BaseClassPlugin, abstract=True):
    """Base class for GeoIPS reader plugins."""

    pass
