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

"""Standard GeoIPS xarray dictionary based GLM netcdf data reader."""
from datetime import datetime
import logging
import xarray
import numpy as np

LOG = logging.getLogger(__name__)

interface = "readers"
family = "standard"
name = "glm_netcdf"


def merge_xarray_data(curr_ds, new_ds):
    """Merge variables from new_ds into curr_ds as it is a series of continuous data.

    Since we are working with GLM data, we should merge data collected in each file into
    a single xarray Dataset at the end. This is because GLM data is disimilar to other
    data collected from variables, as they are collected continuously rather than every
    5 minutes (or more).

    Parameters
    ----------
    curr_ds: xarray.Dataset
        - The dataset we want to add new data to.
    new_ds: xarray.Dataset
        - The dataset the want to merge into curr_ds.

    Returns
    -------
    xarray.Dataset
    """
    for var_name in new_ds.variables.keys():
        if var_name in curr_ds.variables.keys():
            curr_ds_data = curr_ds.variables[var_name]
            new_ds_data = new_ds.variables[var_name]
            merged_data_array = xarray.DataArray(
                data=np.concatenate([curr_ds_data, new_ds_data]),
                dims=["number_of_groups"]
            )
        else:
            merged_data_array = xarray.DataArray(new_ds.variables[var_name])
        if var_name == "group_lat":
            group_lat = merged_data_array
        elif var_name == "group_lon":
            group_lon = merged_data_array
        elif var_name == "glm_area":
            glm_area = merged_data_array
            # group_area = merged_data_array
        elif var_name == "group_quality_flag":
            group_quality_flag = merged_data_array
    ds = xarray.Dataset(
        data_vars=dict(
            group_lat=group_lat,
            group_lon=group_lon,
            group_quality_flag=group_quality_flag,
            glm_area=glm_area,
        ),
        attrs=curr_ds.attrs,
    )
    return ds


def call(fnames, metadata_only=False, chans=None, area_def=None, self_register=False):
    """
    Read GLM NetCDF data from a list of filenames.

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
        * Specify region to read
        * Read all data if None.
    self_register : str or bool, default=False
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
    all_xobj = xarray.Dataset()
    for idx, fname in enumerate(fnames):
        xobj = xarray.open_dataset(fname)
        # Grab the start datetime, this assumes the files are listed in temporal order
        if idx == 0:
            start_dt = xobj.attrs["time_coverage_start"]
            start_dt = datetime.strptime(start_dt, "%Y-%m-%dT%H:%M:%S.%fZ")
            all_xobj.attrs["start_datetime"] = start_dt
        # Grab the end datetime, this assumes the files are listed in temporal order
        if idx == len(fnames) - 1:
            end_dt = xobj.attrs["time_coverage_end"]
            end_dt = datetime.strptime(end_dt, "%Y-%m-%dT%H:%M:%S.%fZ")
            all_xobj.attrs["end_datetime"] = end_dt
        # If the full xarray object is requested, grab the corresponding variables and
        # add that dataset to the dataset list. Created as a xarray.Dataset(), with
        # underlying DataArray variables and attributes
        if not metadata_only:
            group_lat = xarray.DataArray(xobj.variables["group_lat"])
            group_lon = xarray.DataArray(xobj.variables["group_lon"])
            group_area = xarray.DataArray(xobj.variables["group_area"])
            group_quality_flag = xarray.DataArray(
                    xobj.variables["group_quality_flag"]
            )
            ds = xarray.Dataset(
                data_vars=dict(
                    group_lat=group_lat,
                    group_lon=group_lon,
                    glm_area=np.sqrt(group_area/ np.pi) / 1000.0,
                    group_quality_flag=group_quality_flag,
                ),
                attrs=dict(
                    start_datetime=xobj.attrs["time_coverage_start"],
                    end_datetime=xobj.attrs["time_coverage_end"],
                    source_name="glm"
                ),
                # coords=dict(latitude=(["x"], group_lat.data),
                #             longitude=(["y"], group_lon.data))
            )
            all_xobj = merge_xarray_data(all_xobj, ds)
            all_xobj.attrs["file" + str(idx)] = {
                "start_datetime": ds.attrs["start_datetime"],
                "end_datetime": ds.attrs["end_datetime"],
                "num_samples": len(ds.variables["glm_area"]),
            }
    all_xobj.attrs["data_provider"] = "gov.nesdis.noaa"
    all_xobj.attrs["platform_name"] = "GOES-18"
    all_xobj.attrs["source_file_datetimes"] = [start_dt, end_dt]
    all_xobj.attrs["source_name"] = "glm"
    all_xobj.attrs["interpolation_radius_of_influence"] = 150000
    # Just return the metadata of the file
    if metadata_only is True:
        return {"METADATA": all_xobj[[]]}

    LOG.info("Full xarray object requested, returning corresponding variables.")

    return {"GLM": all_xobj, "METADATA": all_xobj[[]]}

