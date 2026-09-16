# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Databases plugin class."""

from geoips.interfaces.class_based_plugin import BaseClassPlugin


class BaseDatabasePlugin(BaseClassPlugin, abstract=True):
    """Base class for GeoIPS database plugins."""

    data_tree = False

    pass
