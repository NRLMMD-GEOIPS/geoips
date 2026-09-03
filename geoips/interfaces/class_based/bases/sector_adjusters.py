# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Sector adjusters plugin class."""

from geoips.interfaces.class_based_plugin import BaseClassPlugin


class BaseSectorAdjusterPlugin(BaseClassPlugin, abstract=True):
    """Base class for GeoIPS sector_adjuster plugins."""

    data_tree = False

    pass
