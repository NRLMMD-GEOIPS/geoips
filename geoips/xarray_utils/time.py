# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Utils to handle time stamp information within xarray objects."""

import calendar
from datetime import datetime
from itertools import starmap
import numpy as np
from cftime import num2pydate


def get_posix_from_datetime(dt):
    """Return the POSIX timestamp in seconds.

    Parameters
    ----------
    dt : datetime.datetime
        datetime object to convert to posix timestamp

    Returns
    -------
    long
        representing seconds since 1 January 1970 at 00Z (epoch seconds)
    """
    return calendar.timegm(dt.timetuple())


def get_datetime_from_datetime64(dt64):
    """Get a python datetime object from a numpy datetime64 object.

    Parameters
    ----------
    dt64 : numpy.datetime64'
        numpy.datetime64 object

    Returns
    -------
    datetime.datetime
        Python datetime object

    Notes
    -----
    Backwards compatible with numpy versions
    """
    # Scaling issues resolved as of numpy 2.x.
    # numpy < 2 appeared to think ALL datetime64 objects were of
    # units nanoseconds, even if the dtype was seconds, so previously
    # we used a hard coded scale factor of 1e-9 at all times. numpy 2
    # appears to store the datetime64 object based on the specified
    # units, so cash as datetime64[s], then int.
    dt64_seconds = dt64.astype("datetime64[s]").astype(int)
    return datetime.utcfromtimestamp(dt64_seconds)


def get_min_from_xarray_time(xarray_obj, varname):
    """Get the minimum time as a datetime object from xarray object.

    Parameters
    ----------
    xarray_obj : xarray.Dataset or xarray.DataArray
        xarray object from which to extract the minimum time
    varname : str
        Timestamp variable name from which to extract the minimum time

    Returns
    -------
    datetime.datetime
        Python datetime.datetime object representing minimum time of the
        Dataset or DataArray
    """
    # If requested varname is not even in the xarray object, just
    # return None rather than failing.
    if varname not in xarray_obj.variables:
        return None
    minval = xarray_obj[varname].min().to_dict()["data"]
    # Hack to get around bug in most recent version of numpy
    if minval is None:
        goodinds = np.ma.where(xarray_obj[varname].to_masked_array())
        minval = get_datetime_from_datetime64(
            xarray_obj[varname].to_masked_array()[goodinds].min()
        )
    return minval


def get_max_from_xarray_time(xarray_obj, varname):
    """Get the maximum time as a datetime object from xarray object.

    Parameters
    ----------
    xarray_obj : xarray.Dataset or xarray.DataArray
        xarray object from which to extract the maximum time
    varname : str
        Timestamp variable name from which to extract the maximum time

    Returns
    -------
    datetime.datetime
        Python datetime.datetime object representing maximum time of the
        Dataset or DataArray
    """
    # If requested varname is not even in the xarray object, just
    # return None rather than failing.
    if varname not in xarray_obj.variables:
        return None
    maxval = xarray_obj[varname].max().to_dict()["data"]
    # Hack to get around bug in most recent version of numpy
    if maxval is None:
        goodinds = np.ma.where(xarray_obj[varname].to_masked_array())
        maxval = get_datetime_from_datetime64(
            xarray_obj[varname].to_masked_array()[goodinds].max()
        )
    return maxval


def fix_datetime(inxr):
    """Masks the input xarray that has improper datetimes (negatives).

    Parameters
    ----------
    inxr : xarray.Dataset
        Input xarray with datetimes in raw float64 value

    Returns
    -------
    xarray.Dataset
        Xarray with times reformatted as datetimes

    Notes
    -----
    Depreciated versions of xarray cast this as a functional NaT value
    """
    tmp_mask = np.where(inxr.time.values < 0, np.nan, inxr.time.values)
    refactor_date = list(starmap(xarray_to_time, zip(tmp_mask, np.isnan(tmp_mask))))
    inxr.time.values = np.asarray(refactor_date)

    return inxr


def xarray_to_time(inarr, mask):
    """Convert a input array (inarr) with a bool mask (mask) to datetime.

    Notes
    -----
    Uses a nan mask on the array to convert real values.
    """
    dt64_arr = np.full(inarr.shape, np.datetime64("nat"), dtype="datetime64[ns]")
    dt64_arr[~mask] = num2pydate(inarr[~mask], "seconds since 1990-01-01 00:00:00")
    return dt64_arr
