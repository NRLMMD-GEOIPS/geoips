# # # Distribution Statement A. Approved for public release. Distribution unlimited.
# # #
# # # Author:
# # # Naval Research Laboratory, Marine Meteorology Division
# # #
# # # This program is free software: you can redistribute it and/or modify it under
# # # the terms of the NRLMMD License included with this program. This program is
# # # distributed WITHOUT ANY WARRANTY; without even the implied warranty of
# # # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the included license
# # # for more details. If you did not receive the license, for more information see:
# # # https://github.com/U-S-NRL-Marine-Meteorology-Division/

"""Interpolation routines from the scipy package."""

# Installed Libraries
import logging

# from matplotlib import cm, colors
import scipy
import numpy

LOG = logging.getLogger(__name__)


def interp_gaussian_kde(data_lons, data_lats, target_lons, target_lats, vw_method=None):
    """
    Interpolate a given array of non-uniform data using scipy.stats.gaussian_kde.

    This is not finalized.

    Parameters
    ----------
    data_array : numpy.ma.core.MaskedArray
        numpy array of data to interpolate
    data_lons : numpy.ma.core.MaskedArray
        numpy array of longitudes corresponding to original data,
        same shape as data_array
    data_lats : numpy.ma.core.MaskedArray
        numpy array of latitudes corresponding to original data,
        same shape as data_array
    target_lons : numpy.ma.core.MaskedArray
        2d numpy array of desired longitudes
    target_lats : numpy.ma.core.MaskedArray
        2d numpy array of desired latitudes
    bw_method : str
        Bandwidth selection method (see scipy.stats.gaussian_kde)|

    See Also
    --------
    scipy.stats.gaussian_kde
    """
    from scipy import stats

    interp_data = None

    positions = numpy.vstack([target_lons.ravel(), target_lats.ravel()])
    values = numpy.vstack([data_lons, data_lats])
    kernel = stats.gaussian_kde(values)
    kernel(positions)

    return interp_data


def interp_griddata(
    data_array,
    data_lons,
    data_lats,
    min_gridlon,
    max_gridlon,
    min_gridlat,
    max_gridlat,
    numx_grid,
    numy_grid,
    method="linear",
):
    """
    Interpolate a given array of non-uniform data to a specified grid.

    Uses scipy.interpolate.griddata

    Parameters
    ----------
    data_array : numpy.ma.core.MaskedArray
        numpy array of original data to be interpolated
    data_lons : numpy.ma.core.MaskedArray
        numpy array of longitudes corresponding to original data,
        same shape as data_array
    data_lats : numpy.ma.core.MaskedArray
        numpy array of latitudes corresponding to original data,
        same shape as data_array
    min_gridlon : float
        minimum desired lon for the output grid
          * -180.0 < min_gridlon < 180.0
    max_gridlon : float
        maximum desired lon for the output grid
          * -180.0 < max_gridlon < 180.0
    min_gridlat : float
        minimum desired lat for the output grid
          * -90.0 < min_gridlat < 90.0
    max_gridlat : float
        maximum desired lat for the output grid
          * -90.0 < max_gridlat < 90.0
    numx_grid : int
        number desired longitude points in the output grid
    numy_grid : int
        number desired latitude points in the output grid

    Other Parameters
    ----------------
    method: str, default='linear'
        A string specifying the interpolation method to use
        for scipy.interpolate.griddata.
        One of 'nearest', 'linear' or 'cubic'
    """
    # make sure that 'longitude' is in 0-360 deg if the sector is crosssing the dateline

    if min_gridlon > 0 and max_gridlon < 0:
        data_lons = numpy.where(data_lons > 0, data_lons, 360 + data_lons)
        max_gridlon = 360 + max_gridlon

    # data_lons = numpy.where(data_lons >0,data_lons,360+data_lons)

    if len(data_lons.shape) > 1:
        data_lons = data_lons.flatten()
        data_lats = data_lats.flatten()
        data_array = data_array.flatten()

    if hasattr(data_array, "mask"):
        inds = numpy.ma.where(data_array)
        data_lons = data_lons[inds]
        data_lats = data_lats[inds]
        data_array = data_array[inds]
    # ocnvert negative longituge into 0-360 if needed
    # if min_gridlon <0:
    #    min_gridlon = 360 + min_gridlon
    # if max_gridlon <0:
    #    max_gridlon = 360 + max_gridlon

    xx = numpy.linspace(min_gridlon, max_gridlon, int(numx_grid))
    yy = numpy.linspace(max_gridlat, min_gridlat, int(numy_grid))
    gridlons, gridlats = numpy.meshgrid(xx, yy)

    # Free up memory ??
    xx = 0
    yy = 0

    interp_data = scipy.interpolate.griddata(
        (data_lats, data_lons), data_array, (gridlats, gridlons), method=method
    )
    # Free up memory ??
    gridlons = 1
    gridlats = 1

    interp_data = numpy.ma.masked_invalid(interp_data)
    interp_data = numpy.ma.masked_less(interp_data, data_array.min())
    interp_data = numpy.ma.masked_greater(interp_data, data_array.max())

    return interp_data
