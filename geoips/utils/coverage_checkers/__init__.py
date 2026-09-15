"""Utility module for coverage_checker plugins."""


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
    # Buried as all __init__ are executed at runtime, hopefully will lower start time
    import numpy
    from skimage.draw import disk

    dumby_arr = numpy.zeros((temp_arr.shape), dtype=numpy.uint8)
    r_points, c_points = disk(
        (x_center, y_center), radius_pixels, shape=dumby_arr.shape
    )

    dumby_arr[r_points, c_points] = 1

    return dumby_arr
