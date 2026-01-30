# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Interpolators interface class."""

from geoips.interfaces.base import BaseClassInterface


class CoverageCheckersInterface(BaseClassInterface):
    """Interpolation routine to apply when reprojecting data."""

    name = "coverage_checkers"
    required_args = {"standard": ["xarray_obj", "variable_name"]}
    required_kwargs = {"standard": {}}
    allowable_kwargs = {
        "standard": {
            "area_def",
            "radius_km",
        }
    }

    def get_plugin_for_product(self, product, checker_field="coverage_checker"):
        """Get plugin for product."""
        if checker_field in product:
            self.get_plugin(product[checker_field]["name"])
        else:
            self.get_plugin("masked_array")


coverage_checkers = CoverageCheckersInterface()
