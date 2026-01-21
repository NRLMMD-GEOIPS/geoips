# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Utilities for manipulating xarray Datasets and DataArrays."""

# Python Standard Libraries
import logging

# Third Party Installed Libraries
import numpy
from pyresample import utils
import xarray

LOG = logging.getLogger(__name__)

# scipy.interpolate.griddata requires at least 4 points. Don't bother
# plotting if fewer than 4.
MIN_POINTS = 4


def get_lat_lon_points(checklat, checklon, diff, sect_xarray, varname, drop=False):
    """Pull values from xarray Datasets in specified geographic location.

    Return points a given distance around a specified lat/lon location,
    from xarray Datasets.

    Parameters
    ----------
    checklat : float
        latitude of interest
    checklon : float
        longitude of interest
    diff : float
        check +- diff of latitude and longitude
    sect_xarray : Dataset
        xarray dataset containing 'latitude' 'longitude' and varname variables
    varname : str
        variable name of data array to use for returning data values

    Returns
    -------
    float, float, int
        * min value in range
        * max value in range
        * and number of points in range
    """
    xinds = (
        (sect_xarray["longitude"] > checklon - diff)
        & (sect_xarray["longitude"] < checklon + diff)
        & (sect_xarray["latitude"] > checklat - diff)
        & (sect_xarray["latitude"] < checklat + diff)
    )
    import numpy

    if drop is True:
        retval = sect_xarray[varname].where(xinds, drop=drop).size
    else:
        retval = numpy.ma.count(sect_xarray[varname].where(xinds).to_masked_array())
    return (
        sect_xarray[varname].where(xinds).min(),
        sect_xarray[varname].where(xinds).max(),
        retval,
    )


def get_lat_lon_points_numpy(
    checklat, checklon, diff, lat_array, lon_array, data_array
):
    """Pull values from numpy arrays in specified geographic location.

    Return points a given distance around a specified lat/lon location,
    from numpy arrays.

    Parameters
    ----------
    checklat : float
        latitude of interest
    checklon : float
        longitude of interest
    diff : float
        check +- diff of latitude and longitude
    lat_array : ndarray
        numpy ndarray of latitude locations - same shape as lon_array and data_array
    lon_array : ndarray
        numpy ndarray of longitude locations - same shape as lat_array and data_array
    data_array : ndarray
        numpy ndarray data values - same shape as lat_array and lon_array

    Returns
    -------
    float, float, int
        * min value in range
        * max value in range
        * and number of points in range
    """
    import numpy

    inds = numpy.logical_and(
        lat_array > checklat - diff, lat_array < checklat + diff
    ) & numpy.logical_and(lon_array > checklon - diff, lon_array < checklon + diff)

    return (
        data_array[inds].min(),
        data_array[inds].max(),
        numpy.ma.count(data_array[inds]),
    )


def sector_xarray_temporal(
    full_xarray, mindt, maxdt, varnames, verbose=False, drop=False
):
    """Sector an xarray object temporally.  If full_xarray is None, return None.

    Parameters
    ----------
    full_xarray : xarray.Dataset
        xarray object to sector temporally
    mindt : datetime.datetime
        minimum datetime of desired data
    maxdt : datetime.datetime
        maximum datetime of desired data
    varnames : list of str
        list of variable names that should be sectored based on 'time',
        mindt, maxdt

    Returns
    -------
    xarray Dataset, or None
        * if full_xarray is None, return None
        * return full original xarray object if 'time' is not included in
          varnames list
        * else, return sectored xarray object with only the desired times,
          specified by mindt and maxdt
    """
    import numpy

    if full_xarray is None:
        LOG.info(
            "    full_xarray is None - not attempting to sector temporally, "
            "returning None"
        )
        return None

    import xarray

    time_xarray = xarray.Dataset()
    time_xarray.attrs = full_xarray.attrs.copy()

    if "time" not in varnames:
        LOG.info(
            "    time variable not included in list - not temporally sectoring, "
            "returning all data"
        )
        return full_xarray

    for varname in varnames:
        # To masked array can have a performance hit for dask arrays,
        # do not use them unnecessarily.
        # good_speeds = numpy.ma.count(full_xarray[varname].to_masked_array())
        if verbose:
            LOG.info(
                "    STARTED TIME WITH %s points for %s",
                full_xarray[varname].size,
                varname,
            )
    mindt64 = numpy.datetime64(mindt)
    maxdt64 = numpy.datetime64(maxdt)

    xarray_time_mask = (full_xarray["time"] > mindt64) & (full_xarray["time"] < maxdt64)

    time_inds = numpy.where(xarray_time_mask)

    if len(time_inds[0]) == 0:
        LOG.warning(
            "    NO TIME DATA between %s and %s for any vars, skipping", mindt, maxdt
        )
        return None

    min_y = time_inds[0].min()
    max_y = time_inds[0].max() + 1
    if len(time_inds) == 2:
        min_x = time_inds[1].min()
        max_x = time_inds[1].max() + 1

    # covg = False
    # final_good_points = 0
    for varname in varnames:
        if drop is True:
            if len(time_inds) == 2:
                # time_xarray[varname] =
                #                full_xarray[varname].where(xarray_time_mask, drop=drop)
                time_xarray[varname] = full_xarray[varname][min_y:max_y, min_x:max_x]
            else:
                # time_xarray[varname] =
                #                full_xarray[varname].where(xarray_time_mask, drop=drop)
                time_xarray[varname] = full_xarray[varname][min_y:max_y]
        else:
            time_xarray[varname] = full_xarray[varname].where(xarray_time_mask)

        # To masked array can have a performance hit for dask arrays,
        # do not use them unnecessarily.
        # good_speeds = numpy.ma.count(time_xarray[varname].to_masked_array())
        # if good_speeds > final_good_points:
        #     final_good_points = good_speeds
        # if good_speeds < MIN_POINTS:
        #     if verbose:
        #         LOG.warning('    INSUFFICIENT TIME DATA between %s and %s for var %s,
        #                     %s points', mindt, maxdt, varname, good_speeds)
        # else:
        #     if verbose:
        #         LOG.info('    MATCHED TIME %s points for var %s', good_speeds,
        #                  varname)
        #     covg = True

    # if not covg:
    if time_xarray["time"].size == 0:
        LOG.warning(
            "    INSUFFICIENT TIME DATA between %s and %s for any vars, skipping",
            mindt,
            maxdt,
        )
        return None
    LOG.info(
        "    SUFFICIENT TIME DATA between %s and %s for any var %s points",
        mindt,
        maxdt,
        time_xarray["time"].size,
    )
    return time_xarray


def sector_xarray_spatial(
    full_xarray,
    area_def,
    varnames,
    lon_pad=3,
    lat_pad=0,
    verbose=False,
    drop=False,
):
    """Sector an xarray object spatially.  If full_xarray is None, return None.

    Parameters
    ----------
    full_xarray : xarray.Dataset
        xarray object to sector spatially
    area_def: pyresample.AreaDefinition
        The requested region to sector spatially from the full_xarray.
        If None, no spatial sectoring required.
    varnames : list of str
        list of variable names that should be sectored based on 'time'
    drop : bool
        Specify whether to remove points with no coverage (rather than masking)

    Returns
    -------
    xarray.Dataset
        * if full_xarray is None, return None,
        * else return resulting xarray Dataset.
    """
    if full_xarray is None:
        if verbose:
            LOG.info(
                "    full_xarray is None - not attempting to sector spatially, "
                "returning None"
            )
        return None

    sector_xarray = xarray.Dataset()
    sector_xarray.attrs = full_xarray.attrs.copy()

    if verbose:
        LOG.info("    Padding longitudes")
    if verbose:
        LOG.info("    Padding latitudes")

    min_lon, min_lat, max_lon, max_lat = get_minmax_latlon_from_area_def(
        area_def, lon_pad, lat_pad
    )

    if verbose:
        LOG.info("    Wrapping longitudes")
    lons = utils.wrap_longitudes(full_xarray["longitude"])

    if verbose:
        LOG.info("    Handling dateline")
    if lons.max() > 179.5 and lons.min() < -179.5 and max_lon > 0 and min_lon > 0:
        lons = xarray.where(
            full_xarray["longitude"] < 0,
            full_xarray["longitude"] + 360,
            full_xarray["longitude"],
        )
    lats = full_xarray["latitude"]

    # To masked array can have a performance hit for dask arrays,
    # do not use them unnecessarily
    # for varname in varnames:
    #     good_speeds = numpy.ma.count(full_xarray[varname].to_masked_array())
    #     if verbose:
    #         LOG.info('    STARTED SPATIAL WITH %s points for %s', good_speeds,
    #                  varname)

    if verbose:
        LOG.info(
            "    Getting appropriate sector area lon %s to %s lat %s to %s, data "
            "minlon %s, maxlon %s, minlat %s, maxlat %s, %s points",
            min_lon,
            max_lon,
            min_lat,
            max_lat,
            lons.min().data,
            lons.max().data,
            lats.min().data,
            lats.max().data,
            lats.size,
        )
        # lons.min().data, lons.max().data, lats.min().data, lats.max().data,
        # good_speeds)

    xarray_sector_mask = (
        (lons > min_lon) & (lons < max_lon) & (lats > min_lat) & (lats < max_lat)
    )

    sector_inds = numpy.where(xarray_sector_mask)

    if not len(sector_inds[0]):
        LOG.warning(
            "    NO SPATIAL DATA between %0.2f and %0.2f lon and %0.2f and %0.2f lat",
            min_lon,
            max_lon,
            min_lat,
            max_lat,
        )
        return None

    min_y = sector_inds[0].min()
    max_y = sector_inds[0].max() + 1
    if len(sector_inds) == 2:
        min_x = sector_inds[1].min()
        max_x = sector_inds[1].max() + 1

    # covg = False
    # final_good_points = 0
    for varname in varnames:
        if drop is True:
            if len(sector_inds) == 2:
                # sector_xarray[varname] =
                #              full_xarray[varname].where(xarray_sector_mask, drop=drop)
                sector_xarray[varname] = full_xarray[varname][min_y:max_y, min_x:max_x]
            else:
                # sector_xarray[varname] =
                #              full_xarray[varname].where(xarray_sector_mask, drop=drop)
                sector_xarray[varname] = full_xarray[varname][min_y:max_y]
        else:
            sector_xarray[varname] = full_xarray[varname].where(xarray_sector_mask)

        # To masked array can have a performance hit for dask arrays,
        # do not use them unnecessarily
        # good_speeds = numpy.ma.count(sector_xarray[varname].to_masked_array())
        # if good_speeds > final_good_points:
        #     final_good_points = good_speeds

        # if sector_xarray[varname].size < MIN_POINTS or good_speeds < MIN_POINTS:
        #     if verbose:
        #         LOG.warning('    INSUFFICIENT SPATIAL DATA between %0.2f and %0.2f lon
        #                     and %0.2f and %0.2f lat, varname %s, %s points',
        #                     extent_lonlat[0], extent_lonlat[2], extent_lonlat[1],
        #                     extent_lonlat[3], varname, good_speeds)
        # else:
        #     if verbose:
        #         LOG.info('    MATCHED SPATIAL %s points for var %s after location
        #                  sectoring', good_speeds, varname)
        #     covg = True

    # if covg:
    if sector_xarray["latitude"].size == 0:
        LOG.warning(
            "    OVERALL INSUFFICIENT SPATIAL DATA between %0.2f and %0.2f lon"
            " and %0.2f and %0.2f lat",
            min_lat,
            max_lon,
            min_lat,
            max_lat,
        )
        return None

    LOG.info(
        "    OVERALL SUFFICIENT SPATIAL DATA between %0.2f and %0.2f lon and %0.2f"
        " and %0.2f lat %0.2f points",
        min_lon,
        max_lon,
        min_lat,
        max_lat,
        sector_xarray["latitude"].size,
    )
    # extent_lonlat[0], extent_lonlat[2], extent_lonlat[1], extent_lonlat[3],
    # final_good_points)
    return sector_xarray


def get_minmax_latlon_from_area_def(area_def, lon_pad, lat_pad):
    """Retrieve the Min/Max Lat/Lon from the provided area_def.

    Given a PyResample AreaDefinition Object, retrieve the minimum and maximum
    latitude and longitude values that should be used to sector the xarray efficiently.

    If the provided area def encapsulates either of the poles, set the min/max latitude
    value to -90/90 degrees accordingly, and match the other latitude value to what was
    provided in the area_def bounds.

    For longitudes, if the sector doesn't contain a pole, wrap them to ensure they exist
    in the 0-360 range, otherwise set to -180, 180.

    Parameters
    ----------
    area_def: PyResample AreaDefinition()
        - The area_definition that defines the bounds of the data we will be sectoring.
    lon_pad: float
        - The amount (in degrees) of padding to be added to the longitude bounds.
    lat_pad: float
        - The amount (in degrees) of padding to be added to the latitude bounds.

    Returns
    -------
    min_lon, min_lat, max_lon, max_lat: float
        - These degree (float) values will be returned in the order listed above.
    """
    extent_lonlat = list(
        area_def.area_extent_ll
    )  # [min_lon, min_lat, max_lon, max_lat]
    min_lon, max_lon = -180, 180

    # Check if the area_def includes either North or South Pole. If it does, we have to
    # manually adjust the lat_lon extent to reflect the correct extent for both lat/lon.
    # Otherwise go about business as usual.
    LOG.info("Checking if area_def includes the North Pole.")
    if point_in_area_def(area_def, 0, 90):
        LOG.info("North Pole exists within area_def.")
        min_lat = extent_lonlat[1] - lat_pad
        max_lat = 90
        return min_lon, min_lat, max_lon, max_lat

    LOG.info("North Pole not in area_def, checking South Pole.")
    if point_in_area_def(area_def, 0, -90):
        LOG.info("South Pole exists within area_def.")
        min_lat = -90
        max_lat = extent_lonlat[3] + lat_pad
        return min_lon, min_lat, max_lon, max_lat

    LOG.info(
        "Neither North or South Pole are in area def, using custom bounds.",
    )
    # Area Definition doesn't include a pole, get the natural bounds from the area_def.
    # convert extent longitude to be within [-180, 180] range
    min_lon = utils.wrap_longitudes(extent_lonlat[0]) - lon_pad
    max_lon = utils.wrap_longitudes(extent_lonlat[2]) + lon_pad
    if min_lon > max_lon and max_lon < 0:
        max_lon = max_lon + 360
    min_lat = extent_lonlat[1] - lat_pad
    max_lat = extent_lonlat[3] + lat_pad
    # Make sure we don't extend latitudes beyond -90 / +90
    if min_lat < -90.0:
        min_lat = -90.0
    if max_lat > 90.0:
        max_lat = 90.0
    return min_lon, min_lat, max_lon, max_lat


def point_in_area_def(area_def, lon, lat):
    """Determine whether or not the provided point (in degrees) is within area_def.

    Parameters
    ----------
    area_def: PyResample AreaDefinition()
        - The area_definition that defines the bounds of the data we will be sectoring.
    lon: float
        - The longitude value in degrees.
    lat: float
        - The latitude value in degrees.

    Returns
    -------
    bool:
        - Whether or not the point is contained in the area definition.
    """
    try:
        area_def.get_array_indices_from_lonlat(lon, lat)
        return True
    except ValueError:
        return False


def sector_xarray_dataset(
    full_xarray,
    area_def,
    varnames,
    lon_pad=3,
    lat_pad=0,
    verbose=False,
    hours_before_sector_time=18,
    hours_after_sector_time=6,
    drop=False,
    window_start_time=None,
    window_end_time=None,
):
    """Use the xarray to appropriately sector out data by lat/lon and time.

    Parameters
    ----------
    full_xarray: xarray.Dataset
        The full input xarray Dataset
    area_def: pyresample.AreaDefinition
        The requested region to sector spatially from the full_xarray.
        If None, no spatial sectoring required.
    varnames: list of str
        List of variable names within full_xarray to include in the final
        xarray Dataset
    lon_pad: float, default=3
        Amount of padding to include around the longitude dimension
    lat_pad: float, default=0
        Amount of padding to include around the latitude dimension
    verbose: bool, default=False
        If True, include log output, otherwise return silently.
    hours_before_sector_time: float, default=18
        For dynamic sectors, number of hours before sector start time
        to include when sectoring temporally.
    hours_after_sector_time: float, default=6
        For dynamic sectors, number of hours after sector end time
        to include when sectoring temporally.
    drop: bool, default=False
        If True, drop data outside range, temporally and spatially.
        If False, mask outside range.
    window_start_time: datetime.datetime, default=None
        If specified, sector temporally between window_start_time and window_end_time.
        hours_before_sector_time and hours_after_sector_time are ignored if
        window start/end time are set!
    window_end_time: datetime.datetime, default=None
        If specified, sector temporally between window_start_time and window_end_time.
        hours_before_sector_time and hours_after_sector_time are ignored if
        window start/end time are set!

    Returns
    -------
    xarray.Dataset
        sectored dataset containing requested "varnames" sectored spatially and
        temporally as requested.
    """
    from datetime import timedelta

    LOG.debug(
        "Full xarray start/end datetime: %s %s",
        full_xarray.start_datetime,
        full_xarray.end_datetime,
    )
    # numpy.ma.count(full_xarray[varnames[0]].to_masked_array()))

    if area_def is not None:
        if (
            hasattr(area_def, "sector_start_datetime")
            and area_def.sector_start_datetime
        ):
            if not window_start_time:
                # If it is a dynamic sector and we did not specify window
                # start/end time, sector temporally to make sure we use the
                # appropriate data
                mindt = area_def.sector_start_datetime - timedelta(
                    hours=hours_before_sector_time
                )
                maxdt = area_def.sector_start_datetime + timedelta(
                    hours=hours_after_sector_time
                )
            else:
                # If we requested window start/end time, use it.
                mindt = window_start_time
                maxdt = window_end_time
            time_xarray = sector_xarray_temporal(
                full_xarray, mindt, maxdt, varnames, verbose=verbose
            )
        elif window_start_time:
            # If this is not a dynamic sector, but we requested start/end
            # time, still apply the requested window.
            mindt = window_start_time
            maxdt = window_end_time
            time_xarray = sector_xarray_temporal(
                full_xarray, mindt, maxdt, varnames, verbose=verbose
            )
        else:
            # If it is not a dynamic sector, and we didn't pass window
            # start/end time, just return all of the data, because all
            # we care about is spatial coverage.
            time_xarray = full_xarray.copy()

        sector_xarray = sector_xarray_spatial(
            time_xarray,
            area_def,
            varnames,
            lon_pad,
            lat_pad,
            verbose=verbose,
            drop=drop,
        )
        if (
            sector_xarray is not None
            and "time" in varnames
            and hasattr(area_def, "sector_start_datetime")
            and area_def.sector_start_datetime
        ):
            from geoips.xarray_utils.time import (
                get_min_from_xarray_time,
                get_max_from_xarray_time,
            )

            sector_xarray.attrs["area_definition"] = area_def
            sector_xarray.attrs["start_datetime"] = get_min_from_xarray_time(
                sector_xarray, "time"
            )
            sector_xarray.attrs["end_datetime"] = get_max_from_xarray_time(
                sector_xarray, "time"
            )
        elif sector_xarray is not None:
            sector_xarray.attrs["area_definition"] = area_def
            sector_xarray.attrs["start_datetime"] = full_xarray.start_datetime
            sector_xarray.attrs["end_datetime"] = full_xarray.end_datetime

    elif window_start_time:
        # If the area_def is not specified, but we requested start and end time,
        # apply requested window here.
        mindt = window_start_time
        maxdt = window_end_time
        sector_xarray = sector_xarray_temporal(
            full_xarray, mindt, maxdt, varnames, verbose=verbose
        )
    else:
        # If we did not request temporal or spatial sectoring,
        # just return full xarray
        sector_xarray = full_xarray.copy()

    if sector_xarray is not None:
        if verbose:
            LOG.info(
                "Sectored data start/end datetime: %s %s",
                sector_xarray.start_datetime,
                sector_xarray.end_datetime,
            )
            # numpy.ma.count(full_xarray[varnames[0]].to_masked_array()))

    return sector_xarray


def get_vis_ir_bg(sect_xarray):
    """Find matching vis/ir background for data in sect_xarray."""
    from geoips.data_manipulations.merge import get_matching_files
    from geoips.filenames.base_paths import PATHS as gpaths

    irfnames = get_matching_files(
        sect_xarray.area_definition.area_id,
        [sect_xarray.area_definition.area_id],
        ["himawari-8", "goes-16", "goes-17", "msg-1", "msg-4"],
        ["ahi", "abi", "abi", "seviri", "seviri"],
        [30, 30, 30, 30, 30],
        gpaths["PRECALCULATED_DATA_PATH"],
        sect_xarray.start_datetime,
        "Infrared-Gray_latitude_longitude",
        time_format="%H%M*",
        buffer_mins=75,
        verbose=False,
        single_match=True,
    )
    visfnames = get_matching_files(
        sect_xarray.area_definition.area_id,
        [sect_xarray.area_definition.area_id],
        ["himawari-8", "goes-16", "goes-17", "msg-1", "msg-4"],
        ["ahi", "abi", "abi", "seviri", "seviri"],
        [30, 30, 30, 30, 30],
        gpaths["PRECALCULATED_DATA_PATH"],
        sect_xarray.start_datetime,
        "Visible_latitude_longitude",
        time_format="%H%M*",
        buffer_mins=75,
        verbose=False,
        single_match=True,
    )
    LOG.info("irfnames: %s", irfnames)
    LOG.info("visfnames: %s", visfnames)
    ret_arr = {}
    from geoips.plugins.modules.readers.geoips_netcdf import read_xarray_netcdf

    if irfnames:
        ir_bg = read_xarray_netcdf(irfnames[0])
        ret_arr["IR"] = ir_bg
        ret_arr["METADATA"] = ir_bg[[]]
    if visfnames:
        vis_bg = read_xarray_netcdf(visfnames[0])
        ret_arr["VIS"] = vis_bg
        ret_arr["METADATA"] = vis_bg[[]]
    LOG.info("ret_arr: %s", ret_arr)
    return ret_arr


def sector_xarrays(
    xobjs,
    area_def,
    varlist,
    verbose=False,
    hours_before_sector_time=18,
    hours_after_sector_time=6,
    check_center=True,
    drop=False,
    lon_pad=3,
    lat_pad=0,
    window_start_time=None,
    window_end_time=None,
):
    """Return dict of sectored xarray objects.

    Parameters
    ----------
    xobjs: dict of xarray.Dataset
        The full input xarray Datasets, with dataset names as keys to the dictionary.
    area_def: pyresample.AreaDefinition
        The requested region to sector spatially from the full_xarray.
        If None, no spatial sectoring required.
    varlist: list of str
        List of variable names within xarray Datasets to include in the final
        sectored xarray Datasets
    verbose: bool, default=False
        If True, include log output, otherwise return silently.
    hours_before_sector_time: float, default=18
        For dynamic sectors, number of hours before sector start time
        to include when sectoring temporally.
    hours_after_sector_time: float, default=6
        For dynamic sectors, number of hours after sector end time
        to include when sectoring temporally.
    check_center: bool, default=True
        If True and sector_type is "tc", check that there is coverage in the
        center of the image prior to sectoring. Skip dataset altogether if no
        center coverage.
    drop: bool, default=False
        If True, drop data outside range, temporally and spatially.
        If False, mask outside range.
    lon_pad: float, default=3
        Amount of padding to include around the longitude dimension
    lat_pad: float, default=0
        Amount of padding to include around the latitude dimension
    window_start_time: datetime.datetime, default=None
        If specified, sector temporally between window_start_time and window_end_time.
        hours_before_sector_time and hours_after_sector_time are ignored if
        window start/end time are set!
    window_end_time: datetime.datetime, default=None
        If specified, sector temporally between window_start_time and window_end_time.
        hours_before_sector_time and hours_after_sector_time are ignored if
        window start/end time are set!

    Returns
    -------
    dict of xarray.Dataset
        Dictionary of sectored datasets containing requested "varnames",
        sectored spatially and temporally as requested.
    """
    ret_xobjs = {}
    from geoips.xarray_utils.time import (
        get_min_from_xarray_time,
        get_max_from_xarray_time,
    )

    for key, xobj in xobjs.items():
        LOG.info("SECTORING dataset %s area_def %s", key, area_def.description)
        LOG.info(" requested variables %s", set(varlist))
        LOG.info(" dataset variables %s", set(xobj.variables.keys()))
        LOG.info(" dataset data_vars %s", set(xobj.data_vars))
        LOG.info("  Min time: %s", get_min_from_xarray_time(xobj, "time"))
        LOG.info("  Max time: %s", get_max_from_xarray_time(xobj, "time"))
        # Compile a list of variables that will be used to sector - the current data
        # variable, and we will add in the appropriate latitude and longitude variables
        # (of the same shape as data), and if it exists the appropriately shaped time
        # array.
        # Use data_vars here - since coordinates (lat/lon/time) get added below
        if len(varlist) > 0:
            vars_to_interp = list(set(varlist) & set(xobj.data_vars))
        else:
            vars_to_interp = list(set(xobj.data_vars))
        if not vars_to_interp:
            LOG.info("  SKIPPING no required variables in dataset %s", key)
            continue

        from geoips.sector_utils.utils import is_dynamic_sector

        if is_dynamic_sector(area_def):
            LOG.info(
                "  Trying to sector %s with dynamic time %s, data time %s to %s, "
                "%s points",
                area_def.area_id,
                area_def.sector_start_datetime,
                xobj.start_datetime,
                xobj.end_datetime,
                xobj["latitude"].size,
            )
        else:
            LOG.info(
                "  Trying to sector %s, %s points",
                area_def.area_id,
                xobj["latitude"].size,
            )

        vars_to_sect = []
        vars_to_sect += vars_to_interp
        # we have to have 'latitude','longitude" in the full_xarray, and 'time' if we
        # want temporal sectoring.
        # Note if lat/lon/time are included as coordinates, they will NOT show up
        # in data_vars, so must use variables
        if "latitude" in list(xobj.variables.keys()):
            vars_to_sect += ["latitude"]
        if "longitude" in list(xobj.variables.keys()):
            vars_to_sect += ["longitude"]
        if "time" in list(xobj.variables.keys()):
            vars_to_sect += ["time"]

        from geoips.xarray_utils.data import sector_xarray_dataset

        # The list of variables in vars_to_sect must ALL be the same shape
        sect_xarray = sector_xarray_dataset(
            xobj,
            area_def,
            vars_to_sect,
            verbose=verbose,
            hours_before_sector_time=hours_before_sector_time,
            hours_after_sector_time=hours_after_sector_time,
            drop=drop,
            lon_pad=lon_pad,
            lat_pad=lat_pad,
            window_start_time=window_start_time,
            window_end_time=window_end_time,
        )

        # numpy arrays fail if numpy_array is None, and xarrays fail if x_array == None
        if sect_xarray is None:
            if verbose:
                LOG.info("  No coverage - skipping dataset %s", key)
            continue

        # check for any obs  near TC center (with a box of 8deg X 8deg), i.e.,
        # within a  range of 400km)
        from geoips.sector_utils.utils import is_sector_type

        if is_sector_type(area_def, "tc") and check_center:
            from geoips.sector_utils.utils import check_center_coverage

            has_covg, covg_xarray = check_center_coverage(
                sect_xarray,
                area_def,
                varlist=vars_to_sect,
                covg_varlist=vars_to_sect,
                width_degrees=8,
                height_degrees=8,
                verbose=verbose,
            )
            if not has_covg:
                LOG.info(
                    "  SKIPPING DATASET %s, NO COVERAGE IN center box - NOT PROCESSING",
                    key,
                )
                continue

            # If the time within the box is > 50 min, we have two overpasses. ALL PMW
            # sensors are polar orbiters.
            if (covg_xarray.end_datetime - covg_xarray.start_datetime).seconds > 3000:
                LOG.info(
                    "Original sectored xarray contains more than one overpass - "
                    "switching to start/datetime in center"
                )
                sect_xarray.attrs["start_datetime"] = covg_xarray.start_datetime
                sect_xarray.attrs["end_datetime"] = covg_xarray.end_datetime

        sect_xarray.attrs["area_definition"] = (
            area_def  # add name of this sector to sector attribute
        )
        if hasattr(sect_xarray, "time"):

            sect_xarray.attrs["start_datetime"] = get_min_from_xarray_time(
                sect_xarray, "time"
            )
            sect_xarray.attrs["end_datetime"] = get_max_from_xarray_time(
                sect_xarray, "time"
            )
            # Note:  need to test whether above two lines can reselect min and max
            # time_info for this sector

        LOG.debug(
            "  Sectored data start/end datetime: %s %s, %s points from var %s, "
            "all vars %s",
            sect_xarray.start_datetime,
            sect_xarray.end_datetime,
            sect_xarray[vars_to_interp[0]].size,
            vars_to_interp[0],
            vars_to_interp,
        )
        sect_xarray.attrs["sectored"] = True
        ret_xobjs[key] = sect_xarray
        ret_xobjs["METADATA"] = sect_xarray[[]]
        LOG.info("  Min time: %s", get_min_from_xarray_time(sect_xarray, "time"))
        LOG.info("  Max time: %s", get_max_from_xarray_time(sect_xarray, "time"))

    return ret_xobjs


def get_sectored_xarrays(
    xobjs, area_def, varlist, get_bg_xarrays=False, check_center=True, drop=False
):
    """Get all xarray objects sectored to area_def.

    Return primary dataset, as well as VIS/IR overlay datasets.
    """
    # All datasets will be of the same data type
    sect_xarrays = sector_xarrays(
        xobjs, area_def, varlist, check_center=check_center, drop=drop
    )
    if get_bg_xarrays and sect_xarrays:
        bg_xarrays = get_vis_ir_bg(sect_xarrays["METADATA"])
        sect_xarrays += sector_xarrays(
            bg_xarrays,
            area_def,
            ["Infrared-Gray", "Visible"],
            check_center=check_center,
            drop=drop,
        )
    else:
        LOG.info(
            "SKIPPING BACKGROUNDS, no coverage for %s %s",
            xobjs[0].source_name,
            area_def.description,
        )
    return sect_xarrays


def combine_preproc_xarrays_with_alg_xarray(
    dict_of_xarrays,
    alg_xarray,
    rgb_var=None,
    covg_plugin=None,
    covg_varname=None,
    area_def=None,
    covg_args=None,
):
    """Combine preprocessed xarrays with an xarray output from an algorithm.

    The dimensions of the preprocessed xarrays must match the algorithm xarray.

    Parameters
    ----------
    dict_of_xarrays : dict
        Dictionary of xarray objects (e.g. output from geoips_netcdf reader).
    alg_xarray : xarray dataset
        xarray dataset returned from algorithm.
    rgb_var : bool
        Specify the product name produced by an algorithm that outputs RGB values.
        If so, there will not be any NaNs to replace and a composite will not be made.
        This function will first set all 0s to NaN during the merge process,
        then replace any remaining NaNs back to 0.

    Returns
    -------
    xarray.Dataset
        Combined xarray dataset of input xarrays datasets
    """
    # Merge xarray objects from newest to oldest
    # Otherwise older swaths will be overlaid on newer
    keys = sorted(dict_of_xarrays)[::-1]
    # Set merged xarray object to alg_xarray, NaNs in this xarray dataset will
    # be replaced with increasingly older pre-processed swaths
    merged = alg_xarray
    if rgb_var:
        from numpy import nan

        merged[rgb_var] = merged[rgb_var].where(merged[rgb_var] != 0, nan)
    for i, key in enumerate(keys):
        if key == "METADATA":
            continue
        preproc = dict_of_xarrays[key]
        if rgb_var:
            preproc[rgb_var] = preproc[rgb_var].where(preproc[rgb_var] != 0, nan)
        # # Replace NaNs in new dataset with composited xarray
        # merged = new_dset.combine_first(merged)
        merged = merged.combine_first(preproc)
        LOG.info("Processed %s", key)
        if covg_plugin is not None:
            curr_covg = 0
            if covg_varname in preproc.keys():
                curr_covg = covg_plugin(preproc, covg_varname, area_def, **covg_args)
            LOG.info(
                "  Current %-7.3f %s %s %s %s %s Vars: %s",
                curr_covg,
                preproc.start_datetime,
                preproc.end_datetime,
                preproc.source_name,
                preproc.platform_name,
                preproc.data_provider,
                list(preproc.data_vars.keys()),
            )
            comp_covg = covg_plugin(merged, covg_varname, area_def, **covg_args)
            LOG.info(
                "Merged %-7.3f    %s %s %s %s %s Vars: %s",
                comp_covg,
                merged.start_datetime,
                merged.end_datetime,
                merged.source_name,
                merged.platform_name,
                merged.data_provider,
                list(merged.data_vars.keys()),
            )
    if rgb_var:
        merged[rgb_var] = merged[rgb_var].fillna(0)
    return merged
