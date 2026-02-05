# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Module implementing the BaseCoverageCheckerPlugin class."""

from geoips.interfaces.class_based_plugin import BaseClassPlugin


class BaseCoverageCheckerPlugin(BaseClassPlugin, abstract=True):
    """Base class for GeoIPS coverage_checker plugins."""

    pass
