# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Read derived surface winds from BYU ASCAT UHR NetCDF data."""

# Python Standard Libraries
from datetime import datetime, timedelta
import logging
import os

# Third-Party Libraries
import numpy
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
name = "ascat_uhr_netcdf"
source_names = ["ascatuhr"]


def read_byu_data(wind_xarray, fname):
    """Reformat ascat xarray object appropriately.

    * variables: latitude, longitude, time,
      wind_speed_kts, wind_dir_deg_met
    * attributes: source_name, platform_name, data_provider,
      interpolation_radius_of_influence
    """
    if "L2B_filename" in wind_xarray.attrs and "metopa" in wind_xarray.L2B_filename:
        wind_xarray.attrs["source_name"] = "ascatuhr"
        wind_xarray.attrs["platform_name"] = "metop-a"
    elif "L2B_filename" in wind_xarray.attrs and "metopb" in wind_xarray.L2B_filename:
        wind_xarray.attrs["source_name"] = "ascatuhr"
        wind_xarray.attrs["platform_name"] = "metop-b"
    elif "L2B_filename" in wind_xarray.attrs and "metopc" in wind_xarray.L2B_filename:
        wind_xarray.attrs["source_name"] = "ascatuhr"
        wind_xarray.attrs["platform_name"] = "metop-c"
    elif "SZF_filenames" in wind_xarray.attrs and "M02" in wind_xarray.SZF_filenames:
        wind_xarray.attrs["source_name"] = "ascatuhr"
        wind_xarray.attrs["platform_name"] = "metop-a"
    elif "SZF_filenames" in wind_xarray.attrs and "M01" in wind_xarray.SZF_filenames:
        wind_xarray.attrs["source_name"] = "ascatuhr"
        wind_xarray.attrs["platform_name"] = "metop-b"
    elif "SZF_filenames" in wind_xarray.attrs and "M03" in wind_xarray.SZF_filenames:
        wind_xarray.attrs["source_name"] = "ascatuhr"
        wind_xarray.attrs["platform_name"] = "metop-c"
    elif (
        "source_file_names" in wind_xarray.attrs
        and "_C_" in wind_xarray.attrs["source_file_names"][0]
    ):
        wind_xarray.attrs["source_name"] = "ascatuhr"
        wind_xarray.attrs["platform_name"] = "metop-c"
    elif (
        "source_file_names" in wind_xarray.attrs
        and "_B_" in wind_xarray.attrs["source_file_names"][0]
    ):
        wind_xarray.attrs["source_name"] = "ascatuhr"
        wind_xarray.attrs["platform_name"] = "metop-b"

    new_file = False
    try:
        # Store the storm names lower case - only reference to it is in the filename..
        storm_name = (
            os.path.basename(wind_xarray.source_file_names[0]).split("_")[3].lower()
        )
        expected_yymmdd = os.path.basename(wind_xarray.source_file_names[0]).split("_")[
            4
        ]
        expected_hhmn = os.path.basename(
            wind_xarray.source_file_names[0]
            .replace(".WRave3.nc", "")
            .replace(".avewr.nc", "")
        ).split("_")[5]
        wind_xarray.attrs["expected_synoptic_time"] = datetime.strptime(
            expected_yymmdd + expected_hhmn, "%y%m%d%H%M"
        )
        wind_xarray.attrs["storms_with_coverage"] = [storm_name]
        new_file = False
    except IndexError:
        # New filenames as of 20220826, no time, only YYYYMMDD, orbit num, and A or D
        # for ascending or descending
        # MUIFA_20220911_19947_C_D-product.nc
        # Store the storm names lower case - only reference to it is in the filename..
        storm_name = (
            os.path.basename(wind_xarray.source_file_names[0]).split("_")[0].lower()
        )
        wind_xarray.attrs["storms_with_coverage"] = [storm_name]
        new_file = True
    except ValueError:
        # New filenames as of 20230906, only YYYYMMDD, orbit num,
        # and A or D for ascending or descending. Example file name:
        # LEE_20230912_25146_C_A-cmod5h-scaled_v2.nc
        # Store the storm names lower case - only reference to it is in the filename.
        storm_name = (
            os.path.basename(wind_xarray.source_file_names[0]).split("_")[0].lower()
        )
        wind_xarray.attrs["storms_with_coverage"] = [storm_name]
        new_file = True

    dsname = "DATA"
    if "wspeeds" in wind_xarray.variables:
        wind_xarray["wind_speed_kts"] = xarray.where(
            wind_xarray.ambiguity_select == 1, wind_xarray.wspeeds[:, :, 0], numpy.nan
        )
        wind_xarray["wind_speed_kts"] = xarray.where(
            wind_xarray.ambiguity_select == 2,
            wind_xarray.wspeeds[:, :, 1],
            wind_xarray.wind_speed_kts,
        )
        wind_xarray["wind_speed_kts"] = xarray.where(
            wind_xarray.ambiguity_select == 3,
            wind_xarray.wspeeds[:, :, 2],
            wind_xarray.wind_speed_kts,
        )
        wind_xarray["wind_speed_kts"] = xarray.where(
            wind_xarray.ambiguity_select == 4,
            wind_xarray.wspeeds[:, :, 3],
            wind_xarray.wind_speed_kts,
        )
        wind_xarray["wind_speed_kts"] = wind_xarray["wind_speed_kts"] * MS_TO_KTS

        wind_xarray["wind_dir_deg_met"] = xarray.where(
            wind_xarray.ambiguity_select == 1, wind_xarray.wdirs[:, :, 0], numpy.nan
        )
        wind_xarray["wind_dir_deg_met"] = xarray.where(
            wind_xarray.ambiguity_select == 2,
            wind_xarray.wdirs[:, :, 1],
            wind_xarray.wind_dir_deg_met,
        )
        wind_xarray["wind_dir_deg_met"] = xarray.where(
            wind_xarray.ambiguity_select == 3,
            wind_xarray.wdirs[:, :, 2],
            wind_xarray.wind_dir_deg_met,
        )
        wind_xarray["wind_dir_deg_met"] = xarray.where(
            wind_xarray.ambiguity_select == 4,
            wind_xarray.wdirs[:, :, 3],
            wind_xarray.wind_dir_deg_met,
        )
        # Set wind_speed_kts appropriately
        wind_xarray["wind_speed_kts"].attrs = wind_xarray["wspeeds"].attrs.copy()
        wind_xarray["wind_speed_kts"].attrs["units"] = "kts"
        if wind_xarray["wspeeds"].attrs.get("long_name"):
            wind_xarray["wind_speed_kts"].attrs["long_name"] = (
                wind_xarray["wspeeds"]
                .attrs["long_name"]
                .replace("ambiguities", "ambiguity selection")
            )

        wind_xarray["wind_dir_deg_met"].attrs = wind_xarray["wdirs"].attrs.copy()

        # Set lat/lons/time appropriately
        wind_xarray = wind_xarray.rename(
            {
                "wspeeds": "wind_speed_ambiguities_kts",
                "wdirs": "wind_dir_ambiguities_deg_met",
            }
        )
        wind_xarray["wind_speed_ambiguities_kts"] = (
            wind_xarray["wind_speed_ambiguities_kts"] * MS_TO_KTS
        )

        if "lat" in wind_xarray.variables:
            wind_xarray = wind_xarray.rename({"lat": "latitude", "lon": "longitude"})
        wind_xarray["latitude"] = xarray.where(
            wind_xarray.ambiguity_select == 0, numpy.nan, wind_xarray.latitude
        )
        if not new_file:
            # Old files were 0 to 180 latitude.
            wind_xarray["latitude"] = wind_xarray["latitude"] - 90

        wind_xarray["longitude"] = xarray.where(
            wind_xarray.ambiguity_select == 0, numpy.nan, wind_xarray.longitude
        )
        dsname = "WINDSPEED"

    if new_file:
        dsname = "ASCATUHR"
        wind_xarray["sigma0_mean"] = wind_xarray["sig"]

    # Old files were separate files for sigma (avewr) and windspeeds (WRave3)
    elif not new_file and "sig_fore" in wind_xarray.variables:
        dsname = "SIGMA"
        # bad vals where sigma 0 is -99.0
        wind_xarray["latitude"] = (
            xarray.where(wind_xarray.sig_fore < -98.0, numpy.nan, wind_xarray.latitude)
            - 90
        )

        wind_xarray["latitude"] = xarray.where(
            wind_xarray.latitude < -90.0, numpy.nan, wind_xarray.latitude
        )

        wind_xarray["longitude"] = xarray.where(
            wind_xarray.sig_fore < -98.0, numpy.nan, wind_xarray.longitude
        )
        wind_xarray["sigma0_mean"] = (
            wind_xarray["sig_fore"] + wind_xarray["sig_aft"] + wind_xarray["sig_mid"]
        ) / 3

    if "time" in wind_xarray.variables:
        # These files are not correct yet.  Pull YYYYMMDD from filename for now,
        # set hour to 1200.
        # Just to get something to plot.
        expected_yyyymmdd = os.path.basename(wind_xarray.source_file_names[0]).split(
            "_"
        )[1]
        dt = datetime.strptime(expected_yyyymmdd + "0000", "%Y%m%d%H%M")
        # Find the "true" minimum valid time of the data array.
        # Simply running min() on the time data array will
        # return "2000-01-01T00:00:00". The second lowest
        # value represents the true start time of the data
        # numpy.unique is a quick and easy way to do this,
        # it will return a sorted array of unique times.
        native_min_time = numpy.unique(wind_xarray["time"])[1]
        if abs((native_min_time - numpy.datetime64(dt)) * 1e-9) > 86400:
            # If the the native time difference is less than a day compared to the
            # expected, then assume the time array actually contains the correct dates!
            # Otherwise, time offset adjustments are needed
            timediff = numpy.datetime64(dt) - numpy.datetime64("2000-01-01T00:00:00")
            min_time = native_min_time + timediff
            min_time_diff = min_time - numpy.datetime64(dt)
            if min_time_diff * 1e-9 > 86400:
                LOG.info(
                    "Start time greater than 1day ahead of expected time. "
                    "Removing one day from applied offset"
                )
                timediff -= numpy.array(timedelta(days=1), dtype="timedelta64")
            wind_xarray["time"] = wind_xarray["time"] + timediff

        # This is all it will be in the end
        # wind_xarray = wind_xarray.rename({'time', 'time'})
        wind_xarray["time"] = xarray.where(
            wind_xarray["wind_speed_kts"] >= 0,
            wind_xarray["time"],
            numpy.datetime64("NaT"),
        )

    else:
        startdt = datetime.strptime(wind_xarray.SZF_start_time[:-1], "%Y%m%d%H%M%S")
        enddt = datetime.strptime(wind_xarray.SZF_stop_time[:-1], "%Y%m%d%H%M%S")
        middt = startdt + (enddt - startdt) / 2
        timearray = numpy.ma.array(
            numpy.zeros(shape=wind_xarray.latitude.shape).astype(int)
            + numpy.datetime64(middt)
        )
        wind_xarray["time"] = xarray.DataArray(
            timearray, name="time", coords=wind_xarray["latitude"].coords
        )
        wind_xarray = wind_xarray.set_coords(["time"])

    return {dsname: wind_xarray}


def call(fnames, metadata_only=False, chans=None, area_def=None, self_register=False):
    """Read ASCAT UHR derived winds or normalized radar cross section data.

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
    fname = fnames[0]
    wind_xarray = xarray.open_dataset(str(fname))
    wind_xarray.attrs["source_name"] = "unknown"
    wind_xarray.attrs["platform_name"] = "unknown"

    wind_xarray.attrs["source_file_names"] = [os.path.basename(fname)]
    wind_xarray.attrs["interpolation_radius_of_influence"] = 20000
    # 1.25km grid, 4km accuracy
    wind_xarray.attrs["sample_distance_km"] = 4
    wind_xarray.attrs["data_provider"] = "byu"
    wind_xarray.attrs["minimum_coverage"] = 20

    LOG.info("Read data from %s", fname)

    if (
        hasattr(wind_xarray, "institution")
        and "Brigham Young University" in wind_xarray.institution
    ):
        wind_xarrays = read_byu_data(wind_xarray, fname)

    for wind_xarray in wind_xarrays.values():
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
            "Read data %s start_dt %s source %s platform %s data_provider %s roi"
            " %s native resolution",
            wind_xarray.attrs["start_datetime"],
            wind_xarray.attrs["source_name"],
            wind_xarray.attrs["platform_name"],
            wind_xarray.attrs["data_provider"],
            wind_xarray.attrs["interpolation_radius_of_influence"],
            wind_xarray.attrs["sample_distance_km"],
        )

    wind_xarrays["METADATA"] = wind_xarray[[]]
    if (
        wind_xarrays["METADATA"].start_datetime == wind_xarrays["METADATA"].end_datetime
        and "SZF_start_time" in wind_xarray.attrs
    ):
        # Use alternate attributes to set start and end datetime
        from datetime import datetime

        wind_xarrays["METADATA"].attrs["start_datetime"] = datetime.strptime(
            wind_xarray.SZF_start_time, "%Y%m%d%H%M%SZ"
        )
        wind_xarrays["METADATA"].attrs["end_datetime"] = datetime.strptime(
            wind_xarray.SZF_stop_time, "%Y%m%d%H%M%SZ"
        )

    return wind_xarrays
