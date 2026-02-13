# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Module implementing the BaseDatabasePlugin class."""

from geoips.interfaces.class_based_plugin import BaseClassPlugin


class BaseDatabasePlugin(BaseClassPlugin, abstract=True):
    """Base class for GeoIPS database plugins."""

    pass
