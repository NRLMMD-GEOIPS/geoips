# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Interpolation routines from the scipy package."""

# Installed Libraries
import logging

# from matplotlib import cm, colors
import scipy
import numpy

# imports for alphashape-based masking
import alphashape
from skimage.measure import points_in_poly

LOG = logging.getLogger(__name__)

# interface = None indicates to the GeoIPS interfaces that this is not a valid
# plugin, and this module will not be added to the GeoIPS plugin registry.
# This allows including python modules within the geoips/plugins directory
# that provide helper or utility functions to the geoips plugins, but are
# not full GeoIPS plugins on their own.
interface = None


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
    list_of_lons = numpy.reshape(gridlons, -1)
    list_of_lats = numpy.reshape(gridlats, -1)

    # Free up memory ??
    gridlons = 1
    gridlats = 1

    # Zip data_lons and data_lats and compute alphashape
    datapts_2d = list(zip(data_lons.data, data_lats.data))
    returned_polygons = alphashape.alphashape(datapts_2d, 1.0)
    # If multiple polygons are returned, choose the one with the largest area
    if returned_polygons.geom_type == "MultiPolygon":
        alpha_shape = max(returned_polygons.geoms, key=lambda a: a.area)
    elif returned_polygons.geom_type == "Polygon":
        alpha_shape = returned_polygons

    interp_data = numpy.ma.masked_invalid(interp_data)
    interp_data = numpy.ma.masked_less(interp_data, data_array.min())
    interp_data = numpy.ma.masked_greater(interp_data, data_array.max())
    input_shape_interp_data = interp_data.shape

    zipped_lons_lats = numpy.asarray(list(zip(list_of_lons, list_of_lats)))
    mask_exterior_coords_xy = numpy.asarray(list(zip(*alpha_shape.exterior.coords.xy)))
    inside_hull_mask = numpy.reshape(
        points_in_poly(zipped_lons_lats, mask_exterior_coords_xy),
        input_shape_interp_data,
    )

    interp_data = numpy.ma.masked_where(
        numpy.logical_not(inside_hull_mask), interp_data
    )

    return interp_data
