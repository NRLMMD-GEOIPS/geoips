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

"""ABI Level 2 NetCDF reader."""

# Python Standard Libraries
from datetime import datetime
import logging


# Installed Libraries
import satpy
import xarray as xr

log = logging.getLogger(__name__)

interface = "readers"
family = "standard"
name = "abi_l2_netcdf"


def get_metadata(fname):
    """Get metadata."""
    import netCDF4 as ncdf
    from geoips.plugins.modules.readers.abi_netcdf import (
        _get_metadata as get_metadata,
    )

    with ncdf.Dataset(fname, "r") as df:
        metadata = get_metadata(df, fname)
    return metadata


def calculate_abi_geolocation(metadata, area_def):
    """Calculate ABI geolocation."""
    from geoips.plugins.modules.readers import abi_netcdf

    geometa = abi_netcdf._get_geolocation_metadata(metadata)
    sdt = datetime.strptime(
        metadata["file_info"]["time_coverage_start"], "%Y-%m-%dT%H:%M:%S.%fZ"
    )
    fldk_lats, fldk_lons = abi_netcdf.get_latitude_longitude(
        geometa, abi_netcdf.BADVALS, area_def
    )
    geo = abi_netcdf.get_geolocation(
        sdt, geometa, fldk_lats, fldk_lons, abi_netcdf.BADVALS, area_def
    )
    geo["fldk_lats"] = fldk_lats
    geo["fldk_lons"] = fldk_lons
    return geo


def call(fnames, area_def=None, metadata_only=False, chans=False, self_register=False):
    """
    Read ABI Level 2 NetCDF data from a list of filenames.

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
    # Start with pulling metadata from the first and last files
    metadata = get_metadata(fnames[0])
    end_metadata = get_metadata(fnames[-1])
    geoips_attrs = {
        "area_definition": area_def,
        "start_datetime": datetime.strptime(
            metadata["file_info"]["time_coverage_start"], "%Y-%m-%dT%H:%M:%S.%fZ"
        ),
        "end_datetime": datetime.strptime(
            end_metadata["file_info"]["time_coverage_end"], "%Y-%m-%dT%H:%M:%S.%fZ"
        ),
        "vertical_data_type": "surface",
        "source_name": "abi",
        "data_provider": "noaa",
        "interpolation_radius_of_influence": 2000,
    }
    if area_def:
        geoips_attrs["area_id"] = area_def.area_id
    else:
        geoips_attrs["area_id"] = metadata["file_info"]["scene_id"]
    meta_dataset = xr.Dataset(attrs=dict(metadata, **geoips_attrs))
    if metadata_only:
        return {"METADATA": meta_dataset}

    # C.P.C. - 20 May 2021
    # Can't figure out how to calculate the geolocation  using satpy,
    # so relying on the abi_netcdf reader for the time being until I figure it out
    # Deal with geolocation outside of loop to avoid hitting the disk numerous times
    geo = calculate_abi_geolocation(metadata, area_def)
    if area_def:
        lats = geo["latitude"]
        lons = geo["longitude"]
    else:
        lats = geo["fldk_lats"]
        lons = geo["fldk_lons"]
    xarrays = []
    for fname in fnames:
        log.info("Reading %s" % fname)
        scene = satpy.Scene([fname], reader="abi_l2_nc")
        available_vars = scene.available_dataset_names()
        if not chans:
            load_chans = available_vars
        else:
            load_chans = set(chans).intersection(set(available_vars))
            if not load_chans:
                log.info("Requested chans not in file, skipping")
                continue
        scene.load(load_chans)
        xarray = scene.to_xarray_dataset()
        if area_def:
            coords = dict(xarray.coords)
            coords["x"] = range(area_def.x_size)
            coords["y"] = range(area_def.y_size)
            area_dataset = xr.Dataset(coords=coords)
            area_dataset.attrs = xarray.attrs
            lines = geo["Lines"]
            samps = geo["Samples"]
            for key in xarray.keys():
                array = xarray[key].values[lines, samps]
                area_dataset[key] = (("y", "x"), array)
            xarray = area_dataset
        xarray["latitude"] = (("y", "x"), lats)
        xarray["longitude"] = (("y", "x"), lons)
        # Add metadata needed by downstream GeoIPS utils
        xarray.attrs = dict(xarray.attrs, **geoips_attrs)
        xarray.attrs["start_datetime"] = xarray.start_time
        xarray.attrs["end_datetime"] = xarray.end_time
        xarrays.append(xarray)
    # If more than one file is passed, assuming more than one scan was passed.
    # This might not work if multiple L2 product types are passed that are of
    # different resolutions
    if len(xarrays) > 1:
        start_times = [x.attrs["start_datetime"] for x in xarrays]
        xarray_dset = xr.concat(xarrays, dim="time_dim")
        xarray_dset.attrs["start_datetime"] = min(start_times)
        xarray_dset = xarray_dset.assign_coords({"time_dim": start_times})
    else:
        xarray_dset = xarrays[0]

    return {"abi_l2_data": xarray_dset, "METADATA": meta_dataset}
