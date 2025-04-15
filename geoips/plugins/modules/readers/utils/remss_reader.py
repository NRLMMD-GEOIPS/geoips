# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Read derived surface winds from REMSS SMAP, WINDSAT, and AMSR netcdf data."""

import logging

LOG = logging.getLogger(__name__)

MS_TO_KTS = 1.94384
DEG_TO_KM = 111.321

# interface = None indicates to the GeoIPS interfaces that this is not a valid
# plugin, and this module will not be added to the GeoIPS plugin registry.
# This allows including python modules within the geoips/plugins directory
# that provide helper or utility functions to the geoips plugins, but are
# not full GeoIPS plugins on their own.
interface = None


def read_remss_data(wind_xarray, data_type):
    """
    Reformat SMAP or WindSat xarray object appropriately.

    variables: latitude, longitude, time, wind_speed_kts
    attributes: source_name, platform_name, data_provider,
    interpolation_radius_of_influence
    """
    import xarray
    import numpy
    from datetime import datetime

    # Set attributes appropriately
    if data_type == "smap":
        LOG.info("Reading SMAP data")
        wind_varname = "wind"
        day_of_month_varname = "day_of_month_of observation"
        minute_varname = "minute"
    elif data_type == "windsat":
        LOG.info("Reading WindSat data")
        wind_varname = "wind_speed_TC"
        day_of_month_varname = "day_of_month_of_observation"
        minute_varname = "time"
    elif data_type == "amsr2":
        LOG.info("Reading AMSR2 data")
        wind_varname = "wind_speed_TC"
        day_of_month_varname = "day_of_month_of_observation"
        minute_varname = "time"
    wind_xarray.attrs["full_day_file"] = True

    wind_xarray_1 = xarray.Dataset()
    wind_xarray_1.attrs = wind_xarray.attrs.copy()
    wind_xarray_1.attrs["current_node_dimension"] = "node_dimension = 1"

    wind_xarray_2 = xarray.Dataset()
    wind_xarray_2.attrs = wind_xarray.attrs.copy()
    wind_xarray_2.attrs["current_node_dimension"] = "node_dimension = 2"

    # Set wind_speed_kts appropriately
    winds_1 = numpy.flipud(wind_xarray[wind_varname].values[:, :, 0])
    winds_2 = numpy.flipud(wind_xarray[wind_varname].values[:, :, 1])

    # Full dataset is 720x1440x2, break that up into ascending and descending nodes.
    wind_xarray_1["wind_speed_kts"] = xarray.DataArray(
        winds_1 * MS_TO_KTS, name="wind_speed_kts"
    )
    wind_xarray_1["wind_speed_kts"].attrs = wind_xarray[wind_varname].attrs
    wind_xarray_1["wind_speed_kts"].attrs["units"] = "kts"

    wind_xarray_2["wind_speed_kts"] = xarray.DataArray(
        winds_2 * MS_TO_KTS, name="wind_speed_kts"
    )
    wind_xarray_2["wind_speed_kts"].attrs = wind_xarray[wind_varname].attrs
    wind_xarray_2["wind_speed_kts"].attrs["units"] = "kts"

    # Set lat/lons appropriately
    # These are (1440x720)
    lats2d, lons2d = numpy.meshgrid(wind_xarray.lat, wind_xarray.lon)
    # lats2d = numpy.dstack([lats2d.transpose(), lats2d.transpose()])
    # lons2d = numpy.dstack([lons2d.transpose(), lons2d.transpose()])
    lats2d = lats2d.transpose()
    lons2d = lons2d.transpose()
    wind_xarray_1["latitude"] = xarray.DataArray(data=numpy.flipud(lats2d))
    wind_xarray_1["longitude"] = xarray.DataArray(data=lons2d)
    wind_xarray_2["latitude"] = xarray.DataArray(data=numpy.flipud(lats2d))
    wind_xarray_2["longitude"] = xarray.DataArray(data=lons2d)
    wind_xarray_1 = wind_xarray_1.set_coords(["latitude", "longitude"])
    wind_xarray_2 = wind_xarray_2.set_coords(["latitude", "longitude"])

    from numpy import datetime64

    # Set time appropriately
    year = wind_xarray.year_of_observation
    month = wind_xarray.month_of_observation
    day = wind_xarray.attrs[day_of_month_varname]
    basedt = datetime.strptime(
        "{0:04d}{1:02d}{2:02d}".format(year, month, day), "%Y%m%d"
    )
    # minarr = wind_xarray.minute
    minarr = numpy.flipud(wind_xarray[minute_varname])
    # NOTE there is a version of numpy 2.x that will break for masked datetime64
    # arrays.  The latest stable version of numpy 2.2.4 works without modification,
    # but beware that some versions were broken.
    timearr = datetime64(basedt) + minarr
    wind_xarray_1["time"] = xarray.DataArray(timearr[:, :, 0])
    wind_xarray_2["time"] = xarray.DataArray(timearr[:, :, 1])
    wind_xarray_1 = wind_xarray_1.set_coords(["time"])
    wind_xarray_2 = wind_xarray_2.set_coords(["time"])
    return {"WINDSPEED_1": wind_xarray_1, "WINDSPEED_2": wind_xarray_2}
