# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Coverage check routine for center radius coverage checks."""

import logging

import numpy
from skimage.draw import disk

LOG = logging.getLogger(__name__)

interface = "coverage_checkers"
family = "standard"
name = "center_radius"


def plot_coverage(main_ax, area_def, covg_args):
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


def create_radius(temp_arr, radius_pixels=300, x_center=0, y_center=0):
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


def call(
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
