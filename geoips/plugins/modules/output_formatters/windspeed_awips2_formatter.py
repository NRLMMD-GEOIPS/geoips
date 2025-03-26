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

"""Routines for outputting formatted SMAP netcdf data files in AWIPS2 compatible format."""

import logging
from pathlib import Path
from typing import List
from datetime import datetime, timedelta, timezone
import numpy as np
import xarray as xr
from geoips.xarray_utils.time import (
    get_min_from_xarray_time,
    get_max_from_xarray_time,
    get_datetime_from_datetime64,
)

LOG = logging.getLogger(__name__)

interface = "output_formatters"
family = "xrdict_area_product_to_outlist"
name = "windspeed_awips2_formatter"


def call(
    xarray_dict,
    varlist,
    output_fnames,
    append=False,
    overwrite=True,
    source_names=None,
    working_directory=None,
):
    """Write AWIPS2 files"""
    breakpoint()
    working_dir = Path(working_directory)
    utc_date_format = "%Y-%m-%d %H:%M:%S UTC"
    if xarray_dict["METADATA"].attrs["source_name"] == "smap-spd":
        success_outputs = write_smap_awips2(xarray_dict, working_dir, utc_date_format)
    elif xarray_dict["METADATA"].attrs["source_name"] == "smos-spd":
        success_outputs = write_smos_awips2(xarray_dict, working_dir, utc_date_format)
    else:
        LOG.warning(
            "Unrecognized source_name, '%s' cannot be converted into AWIPS2-compatible windspeed NetCDF file",
            xarray_dict["METADATA"].attrs["source_name"],
        )

    # breakpoint()  # Only make one during debugging
    return success_outputs


def write_smap_awips2(xarray_dict, working_dir, utc_date_format) -> List[str]:
    success_outputs = []
    ascending_nodes = xarray_dict["WINDSPEED_1"]
    descending_nodes = xarray_dict["WINDSPEED_2"]
    asc_times = ascending_nodes["time"]
    des_times = descending_nodes["time"]
    asc_speeds = ascending_nodes["wind_speed_kts"].values
    des_speeds = descending_nodes["wind_speed_kts"].values
    longitude = ascending_nodes["longitude"].values
    latitude = ascending_nodes["latitude"].values

    start_datetime = xarray_dict["METADATA"].attrs["start_datetime"]
    mintime, maxtime = get_min_max_times_from_two_nodes(
        ascending_nodes, descending_nodes, "time"
    )

    # create roughly one section per hour
    sections_count = (maxtime - mintime).seconds // 3600
    seconds_per_section = (maxtime - mintime).seconds // sections_count

    for section_index in range(sections_count):
        split_start = start_datetime + timedelta(
            seconds=seconds_per_section * section_index
        )
        split_end = split_start + timedelta(seconds=seconds_per_section)
        base_file = "A2WIND_SMAP_" + split_start.strftime("%Y%m%d_%H%M")
        awips2_file = Path(working_dir, f"{base_file}.nc")
        # if awips2_file.exists():
        # LOG.info(f"awips2 file already exists {awips2_file}\n")
        # continue

        timestamp_data = np.full(asc_times.shape, -999.0)
        new_smap_data = np.full(asc_times.shape, -999.0)

        valid_asc_mask = (
            (asc_times >= np.datetime64(split_start))
            & (asc_times < np.datetime64(split_end))
            & (np.logical_not(np.isnat(asc_times)))
        )
        asc_mask = np.where(valid_asc_mask)
        new_smap_data[asc_mask] = asc_speeds[asc_mask]

        valid_des_mask = (
            (des_times >= np.datetime64(split_start))
            & (des_times < np.datetime64(split_end))
            & (np.logical_not(np.isnat(des_times)))
        )
        des_mask = np.where(valid_des_mask)
        new_smap_data[des_mask] = des_speeds[des_mask]

        for i in range(len(asc_mask[0])):
            j = asc_mask[0][i]
            k = asc_mask[1][i]
            scan_time = get_datetime_from_datetime64(asc_times[j][k].values)
            timestamp = scan_time.hour + scan_time.minute / 100
            timestamp_data[j][k] = timestamp

        for i in range(len(des_mask[0])):
            j = des_mask[0][i]
            k = des_mask[1][i]
            scan_time = get_datetime_from_datetime64(des_times[j][k].values)
            timestamp = scan_time.hour + scan_time.minute / 100
            timestamp_data[j][k] = timestamp

        new_xarray_dict = make_smap_dataset(
            latitude,
            longitude,
            new_smap_data,
            timestamp_data,
            datetime.strftime(split_start, utc_date_format),
        )

        new_xarray_dict.to_netcdf(awips2_file, format="NETCDF4")

        success_outputs.append(str(awips2_file))
    return success_outputs


def write_smos_awips2(xarray_dict, working_dir, utc_date_format) -> List[str]:
    success_outputs = []
    dataset = xarray_dict["WINDSPEED"]
    time_array = xarray_dict["WINDSPEED"]["time"]
    wind_speed_array = xarray_dict["WINDSPEED"]["wind_speed_kts"].values
    longitude = xarray_dict["WINDSPEED"]["longitude"].values
    latitude = xarray_dict["WINDSPEED"]["latitude"].values

    quality_mask = np.where(
        (wind_speed_array >= 0.0) & (np.logical_not(np.isnan(wind_speed_array)))
    )

    # breakpoint()

    new_time_data = np.full(latitude.shape, -999.0)
    new_smos_data = np.full(latitude.shape, -999.0)
    new_smos_data[quality_mask] = wind_speed_array[quality_mask]

    for i in range(len(quality_mask[0])):
        j = quality_mask[0][i]
        k = quality_mask[1][i]
        pd_time = get_datetime_from_datetime64(time_array[j][k].values)
        timestamp = pd_time.hour + (pd_time.minute / 100)
        new_time_data[j][k] = timestamp

    # breakpoint()  # Only make one during debugging
    new_xarray_dict = make_smos_dataset(
        latitude,
        longitude,
        new_smos_data,
        new_time_data,
    )

    start_time = dataset.attrs["start_datetime"]
    end_time = dataset.attrs["end_datetime"]
    new_xarray_dict.attrs["time_coverage_start"] = dataset.attrs["time_coverage_start"]
    new_xarray_dict.attrs["time_coverage_end"] = dataset.attrs["time_coverage_end"]
    # new_xarray_dict.attrs["time_coverage_units"] = dataset.attrs["time_coverage_units"]
    # new_xarray_dict.attrs["time_coverage_duration"] = dataset.attrs["time_coverage_duration"]
    new_xarray_dict.attrs["time_coverage_resolution"] = dataset.attrs[
        "time_coverage_resolution"
    ]
    new_xarray_dict.attrs["answrs:acquistion_time"] = start_time.strftime(
        utc_date_format
    )
    # new_xarray_dict.attrs["answrs:acquistion_time_julian_seconds"] = dataset.attrs["time_coverage_end"]

    base_file = "CIRA_A2WIND_SMOS_" + start_time.strftime("%Y%m%d_%H%M")
    awips2_file = Path(working_dir, f"{base_file}.nc")

    new_xarray_dict.to_netcdf(awips2_file, format="NETCDF4")

    success_outputs.append(str(awips2_file))

    return success_outputs


def make_smos_dataset(lat, lon, smos_data, timestamp_data):
    latitude = xr.DataArray(
        lat,
        dims=("y", "x"),
        attrs={
            "units": "degrees_north",
            "long_name": "Latitude array in decimal degrees",
            "standard_name": "latitude",
        },
    )
    longitude = xr.DataArray(
        lon,
        dims=("y", "x"),
        attrs={
            "units": "degrees_east",
            "long_name": "Longitude array in decimal degrees",
            "standard_name": "longitude",
        },
    )
    smos_wind = xr.DataArray(
        smos_data,
        dims=("y", "x"),
        attrs={
            "units": "m s-1",
            "long_name": "SMOS-derived wind speed at 10-m height neutral stability",
            "standard_name": "wind_speed",
            "scale_factor": 1.0,
            "add_offset": 0.0,
            "coverage_content_type": "physicalMeasurement",
            "_FillValue": -999.0,
            "valid_min": 0.0,
            "valid_max": 100.0,
            "grid_mapping": "NONE",
            "source": "SMOS imagery European Space Agency (ESA)",
            "reference": "NONE",
            "platform": "SMOS WEST",
            "instrument": "SMOS",
            "Comment": "NONE",
            "coordinates": "longitude latitude",
        },
    ).astype(np.float32)
    timestamps = xr.DataArray(
        timestamp_data,
        dims=("y", "x"),
        attrs={
            "name": "SMAP_TIME",
            "long_name": "time of observation at nadir",
            "coordinates": "longitude latitude",
            "units": "Z",
            "_FillValue": -999.0,
        },
    ).astype(np.float32)
    new_dataset = xr.Dataset(
        {
            "latitude": latitude,
            "longitude": longitude,
            "smos_wind": smos_wind,
            "TTIME": timestamps,
        },
        attrs={
            "title": "SMOS winds at 10-m height neutral stability",
            "source": "SMOS imagery European Space Agency (ESA)",
            "Conventions": "CF-1.6",
            "license": "These data are available for use without restriction",
            "sensor": "SMOS",
            "grid_mapping": "Ground Projection samples in meters",
            "keywords": "Ocean > Wind Speed",
            "keywords_vocabulary": "UNKNOWN",
            "standard_name_vocabulary": "UNKNOWN",
            "process_level": "Level 2",
            "processing_level": "Level 2",
            "cdm_data_type": "Grid",
            "feature_type": "Grid",
            "summary": "'SMOS wind measurements'",
            "netcdf_version_id": "4.3.2",
            "rows": " 721.",
            "columns": " 1440.",
            "geospatial_vertical_min": "10",
            "geospatial_vertical_max": "10",
            "geospatial_units": "meters",
            "geospatial_resolution": "1",
            "answrs:answrs_product_name": "SMOS-derived wind speed",
            "answrs:platform_name": "SMOS",
            # :time_coverage_start = "20181031T203956" ;
            # :time_coverage_end = "20181031T221956" ;
            # :time_coverage_units = "days" ;
            # :time_coverage_duration = "P31Y128D" ;
            # :time_coverage_resolution = "P7D" ;
            # :answrs\:acquistion_time = "2018-10-31 20:39:52 UTC" ;
            # :answrs\:acquistion_time_julian_seconds = "585226179" ;
        },
    )

    return new_dataset


def make_smap_dataset(lat, lon, new_smap_data, timestamp_data, acquisition_time):
    latitude = xr.DataArray(
        lat,
        dims=("y", "x"),
        attrs={
            "units": "degrees_north",
            "long_name": "Latitude array in decimal degrees",
            "standard_name": "latitude",
        },
    )
    longitude = xr.DataArray(
        lon,
        dims=("y", "x"),
        attrs={
            "units": "degrees_east",
            "long_name": "Longitude array in decimal degrees",
            "standard_name": "longitude",
        },
    )
    smap_wind = xr.DataArray(
        new_smap_data,
        dims=("y", "x"),
        attrs={
            "units": "kts",
            "long_name": "SMAP-derived wind speed at 10-m height neutral stability",
            "standard_name": "wind_speed",
            "scale_factor": 1.0,
            "add_offset": 0.0,
            "coverage_content_type": "physicalMeasurement",
            "_FillValue": -999.0,
            "valid_min": 0.0,
            "valid_max": 100.0,
            "grid_mapping": "NONE",
            "source": "RSS",
            "reference": "NONE",
            "platform": "SMAP",
            "instrument": "SMAP",
            "coordinates": "longitude latitude",
        },
    ).astype(np.float32)
    timestamps = xr.DataArray(
        timestamp_data,
        dims=("y", "x"),
        attrs={
            "name": "SMAP_TIME",
            "long_name": "time of observation at nadir",
            "coordinates": "longitude latitude",
            "units": "Z",
            "_FillValue": -999.0,
        },
    ).astype(np.float32)
    new_dataset = xr.Dataset(
        {
            "latitude": latitude,
            "longitude": longitude,
            "smap_wind": smap_wind,
            "TTIME": timestamps,
        },
        attrs={
            "title": "SMAP winds at 10-m height neutral stability",
            "source": "RSS/CIRA",
            "answrs:answrs_product_name": "SMAP-derived wind speed",
            "answrs:platform_name": "SMAP",
            "answrs:acquistion_time": acquisition_time,
            "answrs:acq_date_time_begin": acquisition_time,
            # "approx_local_equatorial_crossing_time": "node_dimension 1 = 18:00h,  node_dimension 2 = 06:00h",
            # "swath_sector": "node_dimension 1 = ascending,  node_dimension 2 = descending",
        },
    )

    return new_dataset


def get_min_max_times_from_two_nodes(ascending_nodes, descending_nodes, varname):
    asc_min = get_min_from_xarray_time(ascending_nodes, varname)
    des_min = get_min_from_xarray_time(descending_nodes, varname)
    asc_max = get_max_from_xarray_time(ascending_nodes, varname)
    des_max = get_max_from_xarray_time(descending_nodes, varname)
    if asc_min < des_min:
        mintime = asc_min
    else:
        mintime = des_min
    if asc_max > des_max:
        maxtime = asc_max
    else:
        maxtime = des_max

    return mintime, maxtime
