# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Product Defaults interface module."""

from geoips.interfaces.base import BaseYamlInterface
from geoips.pydantic_models.v1.products import ProductDefaultPluginModel


class ProductDefaultsInterface(BaseYamlInterface):
    """Default values that can be applied to products."""

    name = "product_defaults"
    validator = ProductDefaultPluginModel


product_defaults = ProductDefaultsInterface()
