# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Validators plugin class."""

from geoips.interfaces.class_based_plugin import BaseClassPlugin


class BaseValidatorPlugin(BaseClassPlugin, abstract=True):
    """Base class for GeoIPS validator plugins."""

    pass
