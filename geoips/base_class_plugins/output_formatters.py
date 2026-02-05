# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Module implementing the BaseOutputFormatterPlugin class."""

from geoips.interfaces.class_based_plugin import BaseClassPlugin


class BaseOutputFormatterPlugin(BaseClassPlugin, abstract=True):
    """Base class for GeoIPS output_formatter plugins."""

    pass
