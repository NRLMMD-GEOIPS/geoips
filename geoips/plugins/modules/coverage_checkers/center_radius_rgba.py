# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Coverage check routine for RGBA center radius coverage checks."""

import logging

import numpy
from geoips.plugins.modules.coverage_checkers.center_radius import create_radius

LOG = logging.getLogger(__name__)

interface = "coverage_checkers"
family = "standard"
name = "center_radius_rgba"


def call(
    xarray_obj,
    variable_name,
    area_def=None,
    radius_km=300,
):
    """Coverage check routine for xarray objects with masked projected arrays.

    Only calculates coverage within a "radius_km" radius of center.

    Parameters
    ----------
    xarray_obj : xarray.Dataset
        xarray object containing variable "variable_name"
    variable_name : str
        variable name to check percent unmasked
        radius_km (float) : Radius of center disk to check for coverage

    Returns
    -------
    float
        Percent coverage of variable_name
    """
    if variable_name not in xarray_obj:
        raise KeyError(
            f"Variable {variable_name} did not exist. Can not calculate coverage."
        )

    temp_arr = xarray_obj[variable_name][:, :, 3]

    res_km = (
        min(
            xarray_obj.area_definition.pixel_size_x,
            xarray_obj.area_definition.pixel_size_y,
        )
        / 1000.0
    )
    radius_pixels = 1.0 * radius_km / res_km
    LOG.info(
        "Using %s km radius, %s pixels radius, %s km resolution, area_def %s",
        radius_km,
        radius_pixels,
        res_km,
        area_def,
    )

    dumby_arr = create_radius(
        temp_arr,
        radius_pixels=radius_pixels,
        x_center=temp_arr.shape[0] / 2,
        y_center=temp_arr.shape[1] / 2,
    )

    num_valid_in_radius = numpy.count_nonzero(
        numpy.logical_and(numpy.where(dumby_arr, 1, 0), numpy.where(temp_arr, 1, 0))
    )
    num_total_in_radius = numpy.count_nonzero(dumby_arr)
    return (float(num_valid_in_radius) / num_total_in_radius) * 100.0
