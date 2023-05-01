"""Products interface module."""

from geoips.interfaces.base import BaseYamlInterface


class ProductsInterface(BaseYamlInterface):
    """GeoIPS interface for Products plugins."""

    name = "products"


products = ProductsInterface()
