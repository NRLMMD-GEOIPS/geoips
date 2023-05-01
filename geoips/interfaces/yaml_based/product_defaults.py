"""Product Defaults interface module."""

from geoips.interfaces.base import BaseYamlInterface


class ProductDefaultsInterface(BaseYamlInterface):
    """Default values that can be applied to products."""

    name = "product_defaults"


product_defaults = ProductDefaultsInterface()
