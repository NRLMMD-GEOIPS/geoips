# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Module implementing the BaseProcflowPlugin class."""

from geoips.interfaces.class_based_plugin import BaseClassPlugin


class BaseProcflowPlugin(BaseClassPlugin, abstract=True):
    """Base class for GeoIPS procflow plugins."""

    pass
