# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Interpolators interface class."""

import numpy

from geoips.interfaces.class_based_plugin import BaseClassPlugin
from geoips.interfaces.base import BaseClassInterface


class BaseCoverageCheckerPlugin(BaseClassPlugin, abstract=True):
    """Base class for GeoIPS coverage_checker plugins."""

    def create_radius(self, temp_arr, radius_pixels=300, x_center=0, y_center=0):
        """Create a radius around given x,y coordinates in the 2d array.

        Given the radius and the x,y coordinates it creates a circle around those
        points using the skimage.draw library

        Parameters
        ----------
        temp_arr : int
            The 2D array.
        radius_pixels : int, optional
            The radius of the circle. Defaults to 300.
        x_center : int, optional
            The x coordinate of middle circle point. 0 is default value.
        y_center : int, optional
            The y coordinate of middle circle point. 0 is default value.

        Returns
        -------
        numpy.ndarray
            2D array with circle created at the (x, y) coordinate with the given radius
            All circles are marked as 1.
        """
        dumby_arr = numpy.zeros((temp_arr.shape), dtype=numpy.uint8)
        r_points, c_points = disk(
            (x_center, y_center), radius_pixels, shape=dumby_arr.shape
        )

        dumby_arr[r_points, c_points] = 1

        return dumby_arr


class CoverageCheckersInterface(BaseClassInterface):
    """Interpolation routine to apply when reprojecting data."""

    name = "coverage_checkers"
    plugin_class = BaseCoverageCheckerPlugin

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
