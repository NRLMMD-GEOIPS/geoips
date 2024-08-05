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

"""Read derived surface winds from REMSS SMAP netcdf data."""

import logging
import xarray as xr
import numpy as np
from os.path import basename
from glob import glob

LOG = logging.getLogger(__name__)

MS_TO_KTS = 1.94384
DEG_TO_KM = 111.321

interface = "readers"
family = "standard"
name = "smap_awips2_reader"


def call(fnames, metadata_only=False, chans=None, area_def=None, self_register=False):
    """Read one of SMAP derived winds from netcdf data.

    Parameters
    ----------
    fnames : list
        * List of strings, full paths to files
    metadata_only : bool, default=False
        * NOT YET IMPLEMENTED
        * Return before actually reading data if True
    chans : list of str, default=None
        * NOT YET IMPLEMENTED
        * List of desired channels (skip unneeded variables as needed).
        * Include all channels if None.
    area_def : pyresample.AreaDefinition, default=None
        * NOT YET IMPLEMENTED
        * Specify region to read
        * Read all data if None.
    self_register : str or bool, default=False
        * NOT YET IMPLEMENTED
        * register all data to the specified dataset id (as specified in the
          return dictionary keys).
        * Read multiple resolutions of data if False.

    Returns
    -------
    dict of xarray.Datasets
        * dictionary of xarray.Dataset objects with required Variables and
          Attributes.
        * Dictionary keys can be any descriptive dataset ids.

    See Also
    --------
    :ref:`xarray_standards`
        Additional information regarding required attributes and variables
        for GeoIPS-formatted xarray Datasets.
    """

    # Only SAR reads multiple files
    wind_xarrays = {}
    fname = fnames[0]
    with xr.open_dataset(fname, decode_cf=False) as dataset:
        dataset["minute"] = xr.apply_ufunc(
            _decode_minute, dataset["minute"], vectorize=True
        )
        dataset["wind"] = xr.apply_ufunc(_decode_wind, dataset["wind"], vectorize=True)

        wind_xarray_1, wind_xarray_2 = read_smap_data(dataset)
        wind_xarrays["WINDSPEED_1"] = wind_xarray_1
        wind_xarrays["WINDSPEED_2"] = wind_xarray_2

        metadata = xr.Dataset()
        metadata.attrs["source_name"] = "smap-spd"
        metadata.attrs["platform_name"] = "smap"
        metadata.attrs["data_provider"] = "rss"
        metadata.attrs["source_file_names"] = [basename(fname)]
        metadata.attrs["interpolation_radius_of_influence"] = 20000
        metadata.attrs["sample_distance_km"] = DEG_TO_KM / 4
        metadata.attrs["minimum_coverage"] = 20

        from datetime import datetime, timedelta

        year = dataset.attrs["year_of_observation"]
        month = dataset.attrs["month_of_observation"]
        day = dataset.attrs["day_of_month_of observation"]
        basedt = datetime.strptime(
            "{0:04d}{1:02d}{2:02d}".format(year, month, day), "%Y%m%d"
        )

        min_1 = int(np.nanmin(wind_xarray_1["minute"]))
        min_2 = int(np.nanmin(wind_xarray_2["minute"]))
        max_1 = int(np.nanmax(wind_xarray_1["minute"]))
        max_2 = int(np.nanmax(wind_xarray_2["minute"]))
        min_delta = min(min_1, min_2)
        max_delta = max(max_1, max_2)
        wind_xarray_1.attrs["min_time"] = min_1
        wind_xarray_1.attrs["max_time"] = max_1
        wind_xarray_2.attrs["min_time"] = min_2
        wind_xarray_2.attrs["max_time"] = max_2

        metadata.attrs["start_datetime"] = basedt + timedelta(minutes=min_delta)
        metadata.attrs["end_datetime"] = basedt + timedelta(minutes=max_delta)
        wind_xarrays["METADATA"] = metadata[[]]

        LOG.info("Read data from %s", fname)
        # breakpoint()

    return wind_xarrays


def get_test_files(test_data_dir):
    """Generate test xarray from test files for unit testing."""
    filepath = test_data_dir + "/test_data_smap/data/*.nc"
    filelist = glob(filepath)
    tmp_xr = call(filelist)
    if len(filelist) == 0:
        raise NameError("No files found")
    return tmp_xr


def get_test_parameters():
    """Generate test data key for unit testing."""
    return {"data_key": "WINDSPEED_1", "data_var": "wind_speed_kts"}


def _decode_minute(minute_offset):
    if minute_offset == -9999:
        return np.nan
    else:
        return int(minute_offset)


def _decode_wind(wind_speed):
    if wind_speed == -9999:
        return np.nan
    else:
        return wind_speed * 0.01  # Apply the proper scaling factor


def read_smap_data(wind_xarray):
    """
    Reformat SMAP or WindSat xarray object appropriately.

    variables: latitude, longitude, time, wind_speed_kts
    attributes: source_name, platform_name, data_provider,
    interpolation_radius_of_influence
    """
    # Set attributes appropriately
    LOG.info("Reading SMAP data")
    wind_varname = "wind"
    # day_of_month_varname = "day_of_month_of observation"
    minute_varname = "minute"

    # wind_xarray.attrs["full_day_file"] = True

    winds_1 = wind_xarray[wind_varname].values[:, :, 0]
    winds_2 = wind_xarray[wind_varname].values[:, :, 1]

    # Set lat/lons appropriately
    # These are (1440x720)
    lats2d, lons2d = np.meshgrid(wind_xarray.lat, wind_xarray.lon)
    lats2d = lats2d.transpose()
    lons2d = lons2d.transpose()

    wind_xarray_1 = xr.Dataset()
    wind_xarray_1.attrs = wind_xarray.attrs.copy()
    wind_xarray_1.attrs["current_node_dimension"] = "node_dimension = 1"

    wind_xarray_2 = xr.Dataset()
    wind_xarray_2.attrs = wind_xarray.attrs.copy()
    wind_xarray_2.attrs["current_node_dimension"] = "node_dimension = 2"

    # breakpoint()
    # Full dataset is 720x1440x2, break that up into ascending and descending nodes.
    wind_xarray_1["wind_speed"] = xr.DataArray(winds_1, name="wind_speed")
    wind_xarray_1["wind_speed"].attrs = wind_xarray[wind_varname].attrs
    wind_xarray_1["wind_speed"].attrs["units"] = "m/s"

    wind_xarray_2["wind_speed"] = xr.DataArray(winds_2, name="wind_speed")
    wind_xarray_2["wind_speed"].attrs = wind_xarray[wind_varname].attrs
    wind_xarray_2["wind_speed"].attrs["units"] = "m/s"

    wind_xarray_1["latitude"] = xr.DataArray(data=lats2d)
    wind_xarray_1["longitude"] = xr.DataArray(data=lons2d)
    wind_xarray_2["latitude"] = xr.DataArray(data=lats2d)
    wind_xarray_2["longitude"] = xr.DataArray(data=lons2d)
    wind_xarray_1 = wind_xarray_1.set_coords(["latitude", "longitude"])
    wind_xarray_2 = wind_xarray_2.set_coords(["latitude", "longitude"])

    wind_xarray_1["minute"] = xr.DataArray(wind_xarray[minute_varname][:, :, 0])
    wind_xarray_2["minute"] = xr.DataArray(wind_xarray[minute_varname][:, :, 1])
    wind_xarray_1 = wind_xarray_1.set_coords(["minute"])
    wind_xarray_2 = wind_xarray_2.set_coords(["minute"])

    return wind_xarray_1, wind_xarray_2
