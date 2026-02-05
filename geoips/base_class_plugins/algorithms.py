# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Module implementing the BaseAlgorithmPlugin class."""

from geoips.interfaces.class_based_plugin import BaseClassPlugin


class BaseAlgorithmPlugin(BaseClassPlugin, abstract=True):
    """Base class for GeoIPS algorithm plugins."""

    pass
