# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Product Defaults interface module."""

from geoips.interfaces.base import BaseYamlInterface
from geoips.filenames.base_paths import PATHS as gpaths


class ProductDefaultsInterface(BaseYamlInterface):
    """Default values that can be applied to products."""

    name = "product_defaults"
    use_pydantic = gpaths["GEOIPS_USE_PYDANTIC"]


product_defaults = ProductDefaultsInterface()
