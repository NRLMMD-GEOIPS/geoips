# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Read derived surface winds from SAR, SMAP, SMOS, and AMSR netcdf data."""

# Python Standard Libraries
from datetime import datetime, timedelta
import logging
from os.path import basename

# Third-Party Libraries
import numpy as np
from netCDF4 import Dataset
import xarray

# GeoIPS imports
from geoips.xarray_utils.time import (
    get_min_from_xarray_time,
    get_max_from_xarray_time,
)

LOG = logging.getLogger(__name__)

MS_TO_KTS = 1.94384
DEG_TO_KM = 111.321

interface = "readers"
family = "standard"
name = "smos_winds_netcdf"
source_names = ["smos-spd"]


def read_smos_data(wind_xarray, fname):
    """Reformat SMOS xarray object appropriately.

    * variables: latitude, longitude, time, wind_speed_kts
    * attributes: source_name, platform_name, data_provider,
      interpolation_radius_of_influence
    """
    LOG.info("Reading SMOS data")

    # Attributes aren't set in the data files - use the file names to determine the
    # version.
    # 0 is good, 1 is fair, 2 is poor
    if "_110_" in fname:
        # Eliminate "poor" retrievals in the "old" version
        wind_xarray["wind_speed_kts"] = wind_xarray["wind_speed"].where(
            wind_xarray["quality_level"] < 2
        )[0, :, :]
    elif "_300_" in fname:
        # 2 eliminates everything anywhere close to land - initially we had kept
        # everything (< 3) because there were large data gaps without, but the data near
        # land really is poor quality so must remove.
        wind_xarray["wind_speed_kts"] = wind_xarray["wind_speed"].where(
            wind_xarray["quality_level"] < 2
        )[0, :, :]
    else:
        # Default to keeping at least fair quality, in case filenames change
        wind_xarray["wind_speed_kts"] = wind_xarray["wind_speed"].where(
            wind_xarray["quality_level"] < 2
        )[0, :, :]
    wind_xarray["wind_speed_kts"] = xarray.DataArray(
        data=np.flipud(wind_xarray.wind_speed_kts) * MS_TO_KTS,
        name="wind_speed_kts",
        coords=wind_xarray["wind_speed_kts"].coords,
    )

    # Set lat/lons appropriately
    # These are (1440x720)
    lats2d, lons2d = np.meshgrid(wind_xarray.lat, wind_xarray.lon)
    # Full dataset is 720x1440x2
    wind_xarray["latitude"] = xarray.DataArray(
        data=np.flipud(lats2d.transpose()),
        name="latitude",
        coords=wind_xarray["wind_speed_kts"].coords,
    )
    wind_xarray["longitude"] = xarray.DataArray(
        data=lons2d.transpose(),
        name="longitude",
        coords=wind_xarray["wind_speed_kts"].coords,
    )
    wind_xarray = wind_xarray.set_coords(["latitude", "longitude"])
    # timearray = np.zeros(wind_xarray.wind_speed_kts.shape).astype(int) +
    #                                                         wind_xarray.time.values[0]

    timearray = np.ma.masked_array(
        data=np.zeros(wind_xarray.wind_speed_kts.shape).astype(int)
        + wind_xarray.time.values[0],
        mask=True,
    )

    ncobj = Dataset(fname)
    basedt = np.datetime64(datetime.strptime("19900101", "%Y%m%d"))
    nctimearray = np.flipud(ncobj.variables["measurement_time"][...][0, :, :])
    timeinds = np.ma.where(nctimearray)
    # Check if there are any unmasked timeinds, if so update timearray
    if np.size(timeinds) > 0:
        timedata = nctimearray[timeinds].data.tolist()
        timevals = np.ma.masked_array(
            [basedt + np.timedelta64(timedelta(days=xx)) for xx in timedata]
        )
        timearray[timeinds] = timevals
    # Otherwise set timearray as unmasked values
    else:
        timearray = timearray.data
    wind_xarray["time"] = xarray.DataArray(
        data=timearray, name="time", coords=wind_xarray["wind_speed_kts"].coords
    )
    return {"WINDSPEED": wind_xarray}


def call(fnames, metadata_only=False, chans=None, area_def=None, self_register=False):
    """Read SMOS derived winds from netcdf data.

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
    ingested = []
    for fname in fnames:
        wind_xarray = xarray.open_dataset(str(fname))
        # Set attributes appropriately
        wind_xarray.attrs["source_file_names"] = [basename(fname)]
        wind_xarray.attrs["minimum_coverage"] = 20
        wind_xarray.attrs["source_name"] = "smos-spd"
        wind_xarray.attrs["platform_name"] = "smos"
        wind_xarray.attrs["data_provider"] = "esa"
        wind_xarray.attrs["interpolation_radius_of_influence"] = 25000
        # wind_xarray.attrs['sample_distance_km'] = DEG_TO_KM / 4
        wind_xarray.attrs["sample_distance_km"] = 25.0

        # Checking if the wind_xarray.time is valid
        if (
            not isinstance(wind_xarray.time.values[0], np.datetime64)
            and wind_xarray.time.values[0].year > 3000
        ):

            cov_start = datetime.strptime(
                wind_xarray.time_coverage_start, "%Y-%m-%dT%H:%M:%S Z"
            )
            cov_end = datetime.strptime(
                wind_xarray.time_coverage_end, "%Y-%m-%dT%H:%M:%S Z"
            )
            time = cov_start + timedelta(
                seconds=(cov_end - cov_start).total_seconds() / 2
            )
            time_attrs = wind_xarray.time.attrs
            wind_xarray["time"] = np.array([time], dtype=np.datetime64)
            wind_xarray["time"].attrs = time_attrs

        LOG.info("Read data from %s", fname)

        # SMOS time is not read in correctly natively with xarray - must pass fname so
        # we can get time information directly from netCDF4.Dataset open
        ingested += [read_smos_data(wind_xarray, fname)]

    final_wind_xarrays = {}
    # SMOS is a global
    for wind_xarrays in ingested:
        if "WINDSPEED" not in final_wind_xarrays:
            final_wind_xarrays["WINDSPEED"] = wind_xarrays["WINDSPEED"]
        else:
            curr_xobj = wind_xarrays["WINDSPEED"]
            final_xobj = final_wind_xarrays["WINDSPEED"]
            windspd = xarray.where(
                curr_xobj["wind_speed_kts"] >= 0,
                curr_xobj["wind_speed_kts"],
                final_xobj["wind_speed_kts"],
            )
            timestmp = xarray.where(
                curr_xobj["wind_speed_kts"] >= 0,
                curr_xobj["time"],
                final_xobj["time"],
            )
            # for varname in curr_xobj.variables:
            #     if curr_xobj["wind_speed_kts"].shape == curr_xobj[varname].shape:
            #         final_xobj[varname] = xarray.where(
            final_wind_xarrays["WINDSPEED"] = xarray.concat(
                [final_wind_xarrays["WINDSPEED"], wind_xarrays["WINDSPEED"]],
                dim="time",
            )
            # This is lame.  Interpolation did not immediately handle
            # 6x721x1442 array
            final_wind_xarrays["WINDSPEED"]["time"] = timestmp
            final_wind_xarrays["WINDSPEED"]["wind_speed_kts"] = windspd

    for wind_xarray in final_wind_xarrays.values():
        LOG.info("Setting standard metadata")
        wind_xarray.attrs["start_datetime"] = get_min_from_xarray_time(
            wind_xarray, "time"
        )
        wind_xarray.attrs["end_datetime"] = get_max_from_xarray_time(
            wind_xarray, "time"
        )

        if "wind_speed_kts" in wind_xarray.variables:
            # These text files store wind speeds natively in kts
            wind_xarray["wind_speed_kts"].attrs["units"] = "kts"

        LOG.info(
            "Read data %s start_dt %s source %s platform %s data_provider %s roi "
            "%s native resolution",
            wind_xarray.attrs["start_datetime"],
            wind_xarray.attrs["source_name"],
            wind_xarray.attrs["platform_name"],
            wind_xarray.attrs["data_provider"],
            wind_xarray.attrs["interpolation_radius_of_influence"],
            wind_xarray.attrs["sample_distance_km"],
        )

    final_wind_xarrays["METADATA"] = wind_xarray[[]]
    if (
        final_wind_xarrays["METADATA"].start_datetime
        == final_wind_xarrays["METADATA"].end_datetime
    ):
        # Use alternate attributes to set start and end datetime

        final_wind_xarrays["METADATA"].attrs["start_datetime"] = datetime.strptime(
            wind_xarray.time_coverage_start, "%Y-%m-%dT%H:%M:%S Z"
        )
        final_wind_xarrays["METADATA"].attrs["end_datetime"] = datetime.strptime(
            wind_xarray.time_coverage_end, "%Y-%m-%dT%H:%M:%S Z"
        )
    return final_wind_xarrays
