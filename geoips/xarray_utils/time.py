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

"""Utils to handle time stamp information within xarray objects."""


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
    import calendar

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
    scale = 1e-9
    if "[ns]" in dt64.dtype.name:
        scale = 1e-9
    from datetime import datetime

    return datetime.utcfromtimestamp(dt64.astype(int) * scale)


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
    minval = xarray_obj[varname].min().to_dict()["data"]
    # Hack to get around bug in most recent version of numpy
    if minval is None:
        import numpy

        goodinds = numpy.ma.where(xarray_obj[varname].to_masked_array())
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
    maxval = xarray_obj[varname].max().to_dict()["data"]
    # Hack to get around bug in most recent version of numpy
    if maxval is None:
        import numpy

        goodinds = numpy.ma.where(xarray_obj[varname].to_masked_array())
        maxval = get_datetime_from_datetime64(
            xarray_obj[varname].to_masked_array()[goodinds].max()
        )
    return maxval
