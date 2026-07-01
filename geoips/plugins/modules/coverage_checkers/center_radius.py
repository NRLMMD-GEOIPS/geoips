# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Coverage check routine for center radius coverage checks."""

from geoips.interfaces.class_based.coverage_checkers import BaseCoverageCheckerPlugin

import logging

import numpy

from geoips.utils.coverage_checkers import create_radius

LOG = logging.getLogger(__name__)


class CenterRadiusCoverageCheckerPlugin(BaseCoverageCheckerPlugin):
    """Center Radius Coverage checker plugin class."""

    interface = "coverage_checkers"
    family = "standard"
    name = "center_radius"

    def plot_coverage(self, main_ax, area_def, covg_args):
        """Plot the coverage specified by the 'center_radius' function.

        Parameters
        ----------
        main_ax : matplotlib.axis
            Axis on which to plot coverage representation
        area_def : pyresample.AreaDefinition
            area def for current plot
        covg_args : dict
            product params dictionary for current product -
            to ensure we plot the correct coverage params

        Returns
        -------
        No return value
        """
        plot_color = "black"

        if "radius_km" in covg_args:
            radius_km = covg_args["radius_km"]
            res_km = max(area_def.pixel_size_x, area_def.pixel_size_y) / 1000
            radius_pixels = radius_km / res_km
            main_ax.scatter(
                0, 0, s=2 * radius_pixels**2, facecolors="none", edgecolors=plot_color
            )

    def call(
        self,
        xarray_obj,
        variable_name,
        area_def=None,
        radius_km=300,
    ):
        """Coverage check routine for xarray objects with masked projected arrays.

        Parameters
        ----------
        xarray_obj : xarray.Dataset
            xarray object containing variable "variable_name"
        variable_name : str
            variable name to check percent unmasked
        radius_km : float
            Radius of center disk to check for coverage. Defaults to 300 km.

        Returns
        -------
        float
            Percent coverage of variable_name
        """
        if variable_name not in xarray_obj:
            raise KeyError(
                f"Variable {variable_name} did not exist. Can not calculate coverage."
            )

        temp_arr = xarray_obj[variable_name].to_masked_array()

        res_km = (
            min(
                xarray_obj.area_definition.pixel_size_x,
                xarray_obj.area_definition.pixel_size_y,
            )
            / 1000
        )
        radius_pixels = radius_km / res_km
        LOG.info(
            "Using %s km radius, %s pixels radius, "
            "%s km resolution, variable %s, area_def %s",
            radius_km,
            radius_pixels,
            res_km,
            variable_name,
            area_def,
        )

        dumby_arr = create_radius(
            temp_arr,
            radius_pixels=radius_pixels,
            x_center=temp_arr.shape[0] / 2,
            y_center=temp_arr.shape[1] / 2,
        )

        num_valid_in_radius = numpy.count_nonzero(
            numpy.where(dumby_arr & ~temp_arr.mask, 1, 0)
        )
        num_total_in_radius = numpy.count_nonzero(dumby_arr)

        return (float(num_valid_in_radius) / num_total_in_radius) * 100


PLUGIN_CLASS = CenterRadiusCoverageCheckerPlugin
