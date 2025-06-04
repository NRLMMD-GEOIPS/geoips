# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Read Advanced Microwave Scanning Radiometer (AMSR2) data products."""

# Python Standard Libraries
from glob import glob
import logging
from os.path import basename

# Third-Party Libraries
import numpy
import pandas
import xarray

LOG = logging.getLogger(__name__)

varnames = {
    "Brightness_Temperature_10_GHzH": "tb10h",
    "Brightness_Temperature_10_GHzV": "tb10v",
    "Brightness_Temperature_18_GHzH": "tb18h",
    "Brightness_Temperature_18_GHzV": "tb18v",
    "Brightness_Temperature_23_GHzH": "tb23h",
    "Brightness_Temperature_23_GHzV": "tb23v",
    "Brightness_Temperature_36_GHzH": "tb36h",
    "Brightness_Temperature_36_GHzV": "tb36v",
    "Brightness_Temperature_6_GHzH": "tb6h",
    "Brightness_Temperature_6_GHzV": "tb6v",
    "Brightness_Temperature_7_GHzH": "tb7h",
    "Brightness_Temperature_7_GHzV": "tb7v",
    "Brightness_Temperature_89_GHz_AH": "tb89hA",
    "Brightness_Temperature_89_GHz_AV": "tb89vA",
    "Brightness_Temperature_89_GHz_BH": "tb89hB",
    "Brightness_Temperature_89_GHz_BV": "tb89hB",
}
land_num = {"6": 0, "7": 1, "10": 2, "18": 3, "23": 4, "36": 5, "89A": 0, "89B": 1}
land_var = {
    "6": "Land_Ocean_Flag_6_to_36",
    "7": "Land_Ocean_Flag_6_to_36",
    "10": "Land_Ocean_Flag_6_to_36",
    "18": "Land_Ocean_Flag_6_to_36",
    "23": "Land_Ocean_Flag_6_to_36",
    "36": "Land_Ocean_Flag_6_to_36",
    "89A": "Land_Ocean_Flag_89",
    "89B": "Land_Ocean_Flag_89",
}
chan_nums = {
    "Brightness_Temperature_6_GHzV": 1,
    "Brightness_Temperature_6_GHzH": 2,
    "Brightness_Temperature_7_GHzV": 3,
    "Brightness_Temperature_7_GHzH": 4,
    "Brightness_Temperature_10_GHzV": 5,
    "Brightness_Temperature_10_GHzH": 6,
    "Brightness_Temperature_18_GHzV": 7,
    "Brightness_Temperature_18_GHzH": 8,
    "Brightness_Temperature_23_GHzV": 9,
    "Brightness_Temperature_23_GHzH": 10,
    "Brightness_Temperature_36_GHzV": 11,
    "Brightness_Temperature_36_GHzH": 12,
    "Brightness_Temperature_89_GHz_AV": 13,
    "Brightness_Temperature_89_GHz_AH": 14,
    "Brightness_Temperature_89_GHz_BV": 13,
    "Brightness_Temperature_89_GHz_BH": 14,
}

interface = "readers"
family = "standard"
name = "amsr2_netcdf"
source_names = ["amsr2"]


def read_amsr2_winds(wind_xarray):
    """Reformat AMSR2 xarray object appropriately.

    * variables: latitude, longitude, time, wind_speed_kts
    * attributes: source_name, platform_name, data_provider,
      interpolation_radius_of_influence
    """
    MS_TO_KTS = 1.94384
    LOG.info("Reading AMSR2 data")
    # Set attributes appropriately
    wind_xarray.attrs["source_name"] = "amsr2"
    wind_xarray.attrs["platform_name"] = "gcom-w1"
    wind_xarray.attrs["interpolation_radius_of_influence"] = 10000
    # AMSR2 is one text file per datafile, so don't append
    wind_xarray.attrs["overwrite_text_file"] = True
    wind_xarray.attrs["append_text_file"] = False
    # https://www.ospo.noaa.gov/Products/atmosphere/gpds/about_amsr2.html
    # OCEAN Winds based on 37GHz, which is 7km x 12km ground resolution
    wind_xarray.attrs["sample_distance_km"] = 7.0
    if "creator_name" in wind_xarray.attrs and "NOAA" in wind_xarray.creator_name:
        wind_xarray.attrs["data_provider"] = "star"

    # Set lat/lons appropriately
    wind_xarray = wind_xarray.rename(
        {
            "Latitude_for_Low_Resolution": "latitude",
            "Longitude_for_Low_Resolution": "longitude",
        }
    )
    wind_xarray = wind_xarray.set_coords(["latitude", "longitude"])
    wind_xarray = wind_xarray.reset_coords(
        ["Latitude_for_High_Resolution", "Longitude_for_High_Resolution"]
    )

    # Set wind_speed_kts appropriately
    # convert to kts
    wind_xarray["wind_speed_kts"] = wind_xarray["WSPD"] * MS_TO_KTS

    # # Only keep the good wind speeds
    # wind_xarray['wind_speed_kts'] = xarray.where(wind_xarray['WSPD_QC'] == 0,
    # wind_xarray['wind_speed_kts'], numpy.nan)

    wind_xarray["wind_speed_kts"].attrs = wind_xarray["WSPD"].attrs
    wind_xarray["wind_speed_kts"].attrs["units"] = "kts"
    wind_xarray["wind_speed_kts"] = wind_xarray["wind_speed_kts"].assign_coords(
        latitude=wind_xarray.latitude, longitude=wind_xarray.longitude
    )

    # Set time array appropriately

    dtstrs = []
    LOG.info("Reading scan_times")
    for scan_time in wind_xarray["Scan_Time"]:
        dtstrs += [
            "{0:04.0f}{1:02.0f}{2:02.0f}T{3:02.0f}{4:02.0f}{5:02.0f}".format(
                *tuple([xx for xx in scan_time.values])
            )
        ]
    # Have to set it on the actual xarray so it becomes a xarray format time series
    # (otherwise if you set it directly to ts, it is a pandas format time series, and
    # expand_dims doesn't exist).
    time_array = pandas.to_datetime(
        dtstrs, format="%Y%m%dT%H%M%S", errors="coerce"
    ).tolist()
    LOG.info("Setting list of times")
    tss = [time_array for ii in range(0, wind_xarray["wind_speed_kts"].shape[1])]
    LOG.info("Setting time DataArray")
    wind_xarray["time"] = xarray.DataArray(
        data=numpy.array(tss).transpose(),
        coords=wind_xarray.wind_speed_kts.coords,
        name="time",
    )
    wind_xarray = wind_xarray.set_coords(["time"])
    return {"WINDS": wind_xarray}


def read_amsr2_mbt(full_xarray, varname, time_array=None):
    """
    Reformat AMSR2 xarray object appropriately.

    * variables: latitude, longitude, time,
      brightness temperature variables
    * attributes: source_name, platform_name, data_provider,
      interpolation_radius_of_influence
    """
    LOG.info("Reading AMSR data %s", varname)
    sub_xarray = xarray.Dataset()
    sub_xarray.attrs = full_xarray.attrs.copy()
    # Set attributes appropriately

    # Mappings are Brightness_Temperature_89_GHz_AH -> Latitude_for_89A, etc
    # Mappings are Brightness_Temperature_10_GHzH -> Latitude_for_10, etc
    chanstr = varname.replace("Brightness_Temperature_", "")
    chanstr = chanstr.replace("_GHz_", "")
    chanstr = chanstr.replace("_GHz", "")
    chanstr = chanstr.replace("H", "")
    chanstr = chanstr.replace("V", "")

    # Set lat/lons appropriately
    sub_xarray["latitude"] = full_xarray["Latitude_for_{0}".format(chanstr)]
    sub_xarray["longitude"] = full_xarray["Longitude_for_{0}".format(chanstr)]
    sub_xarray[varnames[varname]] = full_xarray[varname]
    sub_xarray[varnames[varname]].attrs["channel_number"] = chan_nums[varname]
    sub_xarray.set_coords(["latitude", "longitude"])

    # https://www.ospo.noaa.gov/Products/atmosphere/gpds/about_amsr2.html
    # 37GHz, 7km x 12km ground resolution
    # 89GHz, 3km x 5km ground resolution

    # MTIFs need to be "prettier" for PMW products, so 2km resolution for all channels
    # sub_xarray.attrs['sample_distance_km'] = 3.0
    sub_xarray.attrs["sample_distance_km"] = 2.0
    sub_xarray.attrs["interpolation_radius_of_influence"] = 10000
    for dim in sub_xarray.dims.keys():
        if "low_rez" in dim:
            # MTIFs need to be "prettier" for PMW products, so 2km resolution for all
            # channels. sub_xarray.attrs['sample_distance_km'] = 7.0
            sub_xarray.attrs["sample_distance_km"] = 2.0
            sub_xarray.attrs["interpolation_radius_of_influence"] = 20000

    # See dictionaries above for appropriate land mask array locations for each variable
    full_xarray["LandMask"] = xarray.DataArray(
        full_xarray[land_var[chanstr]].to_masked_array()[land_num[chanstr], :, :],
        coords=full_xarray[varname].coords,
    )

    if time_array is None:

        # Set time appropriately
        dtstrs = []
        LOG.info("Reading scan_times, for dims %s", sub_xarray[varnames[varname]].dims)
        for scan_time in full_xarray["Scan_Time"]:
            dtstrs += [
                "{0:04.0f}{1:02.0f}{2:02.0f}T{3:02.0f}{4:02.0f}{5:02.0f}".format(
                    *tuple([xx for xx in scan_time.values])
                )
            ]
        # Have to set it on the actual xarray so it becomes a xarray format time series
        # (otherwise if you set it directly to ts, it is a pandas format time series,
        # and expand_dims doesn't exist).
        curr_time_array = pandas.to_datetime(
            dtstrs, format="%Y%m%dT%H%M%S", errors="coerce"
        ).tolist()
        LOG.info("    Setting list of times")
        tss = [
            curr_time_array for ii in range(0, sub_xarray[varnames[varname]].shape[1])
        ]
        LOG.info("    Setting time DataArray")
        sub_xarray["time"] = xarray.DataArray(
            data=numpy.array(tss).transpose(),
            coords=full_xarray[varname].coords,
            name="time",
        )
        sub_xarray = sub_xarray.set_coords(["time"])
    else:
        LOG.info(
            "Using existing scan_times for dims %s", sub_xarray[varnames[varname]].dims
        )
        sub_xarray["time"] = time_array
    from geoips.xarray_utils.time import (
        get_min_from_xarray_time,
        get_max_from_xarray_time,
    )

    sub_xarray.attrs["start_datetime"] = get_min_from_xarray_time(sub_xarray, "time")
    sub_xarray.attrs["end_datetime"] = get_max_from_xarray_time(sub_xarray, "time")
    return sub_xarray


def read_amsr2_data(full_xarray, chans):
    """Read non-AMSR2_OCEAN data."""
    full_xarray = full_xarray.reset_coords(full_xarray.coords)

    sunzen = 90 - full_xarray.Sun_Elevation
    satzen = full_xarray.Earth_Incidence_Angle
    satazm = full_xarray.Earth_Azimuth_Angle
    loqf = full_xarray.Pixel_Data_Quality_6_to_36
    hiqf = full_xarray.Pixel_Data_Quality_89
    sunglint_flag = full_xarray.Sun_Glint_Flag
    sensor_scan_angle = full_xarray.Scan_Angle
    xarrays = {}
    # Every single channel has a different set of Lat/Lons!
    for varname in full_xarray.variables:
        if chans is not None and varname not in chans:
            LOG.info("SKIPPING: Variable %s not requested in %s", varname, chans)
        if "Brightness" in varname:
            usetime = None
            for xra in list(xarrays.values()):
                if xra.time.dims == full_xarray[varname].dims:
                    usetime = xra.time
            new_xarray = read_amsr2_mbt(full_xarray, varname, usetime)
            if sunzen.dims == tuple(new_xarray.dims):
                new_xarray["satellite_azimuth_angle"] = satazm
                new_xarray["satellite_zenith_angle"] = satzen
                new_xarray["solar_zenith_angle"] = sunzen
                new_xarray["QualityFlag"] = loqf
                new_xarray["SunGlintFlag"] = sunglint_flag
                new_xarray["sensor_scan_angle"] = sensor_scan_angle
            elif hiqf.dims == tuple(new_xarray.dims):
                new_xarray["QualityFlag"] = hiqf
            xarrays[varname] = new_xarray
        else:
            LOG.info("SKIPPING variable %s", varname)

    return xarrays


def call(
    fnames,
    metadata_only=False,
    chans=None,
    area_def=None,
    self_register=False,
    test_arg="AMSR2 Default Test Arg",
):
    """
    Read AMSR2 netcdf data products.

    Parameters
    ----------
    fnames : list
        * List of strings, full paths to files
    metadata_only : bool, default=False
        * Return before actually reading data if True
    chans : list of str, default=None
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
    LOG.debug("AMSR2 reader test_arg: %s", test_arg)
    ingested = []
    for fname in fnames:
        # full_xarray = xarray.open_dataset(str(fname))
        full_xarrays = [xarray.open_dataset(str(x)) for x in fnames]
        full_xarray = xarray.merge(full_xarrays)
        full_xarray.attrs["data_provider"] = "unknown"
        full_xarray.attrs["source_file_names"] = [basename(fname)]
        full_xarray.attrs["source_name"] = "amsr2"
        full_xarray.attrs["platform_name"] = "gcom-w1"
        full_xarray.attrs["interpolation_radius_of_influence"] = 10000
        if "creator_name" in full_xarray.attrs and "NOAA" in full_xarray.creator_name:
            full_xarray.attrs["data_provider"] = "star"
        full_xarray.attrs["minimum_coverage"] = 20
        LOG.info("Read data from %s", fname)
        if metadata_only is True:
            from datetime import datetime

            full_xarray.attrs["start_datetime"] = datetime.strptime(
                full_xarray.attrs["time_coverage_start"][0:19], "%Y-%m-%dT%H:%M:%S"
            )
            full_xarray.attrs["end_datetime"] = datetime.strptime(
                full_xarray.attrs["time_coverage_end"][0:19], "%Y-%m-%dT%H:%M:%S"
            )
            LOG.info("metadata_only requested, returning without readind data")
            return {"METADATA": full_xarray}

        if hasattr(full_xarray, "title") and "AMSR2_OCEAN" in full_xarray.title:
            xarrays = read_amsr2_winds(full_xarray)

        elif hasattr(full_xarray, "title") and "MBT" in full_xarray.title:
            xarrays = read_amsr2_data(full_xarray, chans)

        elif hasattr(full_xarray, "title") and "PRECIP" in full_xarray.title:
            xarrays = read_amsr2_data(full_xarray, chans)
        ingested.append(xarrays)

    # Merge all datasets together:
    final_xarrays = {}
    for xr_key in xarrays.keys():
        xars = [xar[xr_key] for xar in ingested]
        final_xarrays[xr_key] = xarray.concat(xars, dim="Number_of_Scans")

    for dsname, curr_xarray in final_xarrays.items():
        LOG.info("Setting standard metadata")
        from geoips.xarray_utils.time import (
            get_min_from_xarray_time,
            get_max_from_xarray_time,
        )

        curr_xarray.attrs["start_datetime"] = get_min_from_xarray_time(
            curr_xarray, "time"
        )
        curr_xarray.attrs["end_datetime"] = get_max_from_xarray_time(
            curr_xarray, "time"
        )
    final_xarrays["METADATA"] = list(final_xarrays.values())[0][[]]
    return final_xarrays


def get_test_files(test_data_dir):
    """Generate test files for unit testing reader."""
    filepath = test_data_dir + "/test_data_amsr2/data/AMSR2-MBT*.nc"
    filelist = glob(filepath)
    tmp_xr = call(filelist)

    return tmp_xr


def get_test_parameters():
    """Generate a data key for unit testing."""
    return [{"data_key": "Brightness_Temperature_10_GHzH", "data_var": "tb10h"}]
