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
from datetime import datetime, timedelta, timezone
import numpy as np
import xarray as xr

LOG = logging.getLogger(__name__)

interface = "output_formatters"
family = "xrdict_area_product_to_outlist"
name = "smap_awips2"


def call(
    xarray_dict, varlist, output_fnames, append=False, overwrite=True, source_names=None
):
    """Write SMAP AWIPS2 files"""
    # Connect to FTP server and get file info
    # breakpoint()
    success_outputs = []
    working_dir = Path("/mnt/shnas12/users/coleman/smap")
    utc_date_format = "%Y-%m-%d %H:%M:%S UTC"

    ascending_nodes = xarray_dict["WINDSPEED_1"]
    descending_nodes = xarray_dict["WINDSPEED_2"]
    asc_minutes = ascending_nodes["minute"].values
    des_minutes = descending_nodes["minute"].values
    asc_speeds = ascending_nodes["wind_speed"].values
    des_speeds = descending_nodes["wind_speed"].values
    lon = ascending_nodes["longitude"].values
    lat = ascending_nodes["latitude"].values

    start_datetime = xarray_dict["METADATA"].attrs["start_datetime"]

    mintime = min(ascending_nodes.attrs["min_time"], descending_nodes.attrs["min_time"])
    maxtime = max(ascending_nodes.attrs["max_time"], descending_nodes.attrs["max_time"])
    start_time = mintime - (mintime % 60)  # Round down to the nearest hour
    # # Create a new xarray_dict for each 60-minute time step
    # breakpoint()
    for minute_step in range(start_time, maxtime + 60, 60):
        time_split = start_datetime + timedelta(minutes=minute_step)
        base_file = "CIRA_A2WIND_SMAP_" + time_split.strftime("%Y%m%d_%H%M")
        awips2_file = Path(working_dir, "awips2_products", f"{base_file}.nc")
        # if awips2_file.exists():
        # LOG.info(f"awips2 file already exists {awips2_file}\n")
        # continue

        new_smap_data = np.full(asc_minutes.shape, -999.0)
        asc_mask = np.where(
            (asc_minutes >= minute_step)
            & (asc_minutes < minute_step + 60)
            & np.logical_not(np.isnan(asc_minutes))
        )
        new_smap_data[asc_mask] = asc_speeds[asc_mask]

        des_mask = np.where(
            (des_minutes >= minute_step)
            & (des_minutes < minute_step + 60)
            & np.logical_not(np.isnan(des_minutes))
        )
        new_smap_data[des_mask] = des_speeds[des_mask]

        # breakpoint()  # Only make one during debugging
        new_xarray_dict = make_smap_dataset(
            lat, lon, new_smap_data, datetime.strftime(time_split, utc_date_format)
        )

        # LOG.info(f"Creating {awips2_file}\n")
        new_xarray_dict.to_netcdf(awips2_file, format="NETCDF4")

        success_outputs.append(awips2_file.resolve())
    return success_outputs


def make_smap_dataset(lat, lon, new_smap_data, start_time: str):
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
            "units": "m s-1",
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
    )
    new_dataset = xr.Dataset(
        {"latitude": latitude, "longitude": longitude, "smap_wind": smap_wind},
        attrs={
            "title": "SMAP winds at 10-m height neutral stability",
            "source": "RSS/CIRA",
            "answrs:answrs_product_name": "SMAP-derived wind speed",
            "answrs:platform_name": "SMAP",
            "answrs:acquistion_time": start_time,
            "answrs:acq_date_time_begin": start_time,
            "approx_local_equatorial_crossing_time": "node_dimension 1 = 18:00h,  node_dimension 2 = 06:00h",
            "swath_sector": "node_dimension 1 = ascending,  node_dimension 2 = descending",
        },
    )

    return new_dataset
