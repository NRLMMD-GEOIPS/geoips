# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""ABI Level 2 NetCDF reader."""

# Python Standard Libraries
from datetime import datetime
import logging

# Third-Party Libraries
import netCDF4 as ncdf
from numpy import isnan
import satpy
import xarray as xr

log = logging.getLogger(__name__)

interface = "readers"
family = "standard"
name = "abi_l2_netcdf"
source_names = ["abi"]


def get_metadata(fname):
    """Get metadata."""
    from geoips.plugins.modules.readers.abi_netcdf import (
        _get_metadata as get_metadata,
    )

    with ncdf.Dataset(fname, "r") as df:
        metadata = get_metadata(df, fname)
    return metadata


def calculate_abi_geolocation(
    metadata,
    area_def,
    geolocation_cache_backend="memmap",
    cache_chunk_size=None,
    resource_tracker=None,
):
    """Calculate ABI geolocation."""
    from geoips.plugins.modules.readers import abi_netcdf

    geometa = abi_netcdf._get_geolocation_metadata(metadata)
    sdt = datetime.strptime(
        metadata["file_info"]["time_coverage_start"], "%Y-%m-%dT%H:%M:%S.%fZ"
    )
    fldk_lats, fldk_lons = abi_netcdf.get_latitude_longitude(
        geometa,
        abi_netcdf.BADVALS,
        area_def,
        geolocation_cache_backend=geolocation_cache_backend,
        chunk_size=cache_chunk_size,
        resource_tracker=resource_tracker,
    )
    geo = abi_netcdf.get_geolocation(
        sdt,
        geometa,
        fldk_lats,
        fldk_lons,
        abi_netcdf.BADVALS,
        area_def,
        geolocation_cache_backend=geolocation_cache_backend,
        chunk_size=cache_chunk_size,
        resource_tracker=resource_tracker,
    )
    geo["fldk_lats"] = fldk_lats
    geo["fldk_lons"] = fldk_lons
    return geo


def satpy_read(fname, chans):
    """Ingest data using satpy.Scene.

    satpy.Scene object converted to xarray dataset at the end

    Parameters
    ----------
    fname : str
        Full file path
    chans : list, optional
        List of variables to load from file, by default None
        All variables are loaded in None

    Returns
    -------
    xarray.dataset
        Dataset holding either requested or all variables from file
    """
    scene = satpy.Scene([fname], reader="abi_l2_nc")
    available_vars = scene.available_dataset_names()
    if not chans:
        load_chans = available_vars
    else:
        load_chans = set(chans).intersection(set(available_vars))
    scene.load(load_chans)
    xarray = scene.to_xarray_dataset()
    return xarray


def xr_read(fname, chans=None):
    """Ingest data using xarray.open_dataset.

    Parameters
    ----------
    fname : str
        Full file path
    chans : list, optional
        List of variables to load from file, by default None
        All variables are loaded in None

    Returns
    -------
    xarray.dataset
        Dataset holding either requested or all variables from file.
    """
    ds = xr.open_dataset(fname)
    ds.attrs["start_datetime"] = datetime.strptime(
        ds.attrs["time_coverage_start"], "%Y-%m-%dT%H:%M:%S.%fZ"
    )
    ds.attrs["end_datetime"] = datetime.strptime(
        ds.attrs["time_coverage_end"], "%Y-%m-%dT%H:%M:%S.%fZ"
    )
    if chans:
        ds_vars = list(ds.variables)
        drop_vars = [x for x in ds_vars if x not in chans and x not in ["lat", "lon"]]
        ds = ds.drop_vars(drop_vars)
    return ds


def call(
    fnames,
    area_def=None,
    metadata_only=False,
    chans=False,
    self_register=False,
    geolocation_cache_backend="memmap",
    cache_chunk_size=None,
    resource_tracker=None,
):
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
    try:
        metadata = get_metadata(fnames[0])
        end_metadata = get_metadata(fnames[-1])
    except KeyError:
        metadata = {"file_info": xr.open_dataset(fnames[0]).attrs}
        end_metadata = {"file_info": xr.open_dataset(fnames[-1]).attrs}
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
        "interpolation_radius_of_influence": 50000,
    }
    if (
        "platform_ID" in metadata["file_info"]
        and "platform_name" not in metadata["file_info"]
    ):
        # Some of the level2 data have platform_ID attribute in the form G<NN>,
        # where <NN> = 16, 17, 18
        # Use platform_ID to set the platform_name
        geoips_attrs["platform_name"] = metadata["file_info"]["platform_ID"].replace(
            "G", "goes-"
        )

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
    try:
        geo = calculate_abi_geolocation(
            metadata,
            area_def,
            geolocation_cache_backend=geolocation_cache_backend,
            cache_chunk_size=cache_chunk_size,
            resource_tracker=resource_tracker,
        )
        if area_def:
            lats = geo["latitude"]
            lons = geo["longitude"]
        else:
            lats = geo["fldk_lats"]
            lons = geo["fldk_lons"]
        ll_mask = (isnan(lats)) | (lats < -90) | (lats > 90)
    except KeyError:
        ll_mask = None

    xarrays = []
    # Ensure start_datetime and end_datetime are always tied to the file being read
    geoips_attrs.pop("start_datetime")
    geoips_attrs.pop("end_datetime")
    for fname in fnames:
        log.info("Reading %s" % fname)
        try:
            log.info("Trying with satpy backend")
            xarray = satpy_read(fname, chans)
        except ValueError:
            log.info("Attempting to load with xarray")
            xarray = xr_read(fname, chans)
        if not list(xarray.variables):
            log.info("Requested chans not in file, skipping")
            continue
        if area_def and ll_mask is not None:
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
        if ll_mask is not None:
            xarray["latitude"] = (("y", "x"), lats)
            xarray["longitude"] = (("y", "x"), lons)
            for ll in ["latitude", "longitude"]:
                xarray[ll] = xarray[ll].where(~ll_mask)
        if "lat" in xarray:
            xarray = xarray.rename({"lat": "latitude", "lon": "longitude"})
        # Add metadata needed by downstream GeoIPS utils
        xarray.attrs = dict(xarray.attrs, **geoips_attrs)
        if "start_datetime" not in xarray.attrs:
            xarray.attrs["start_datetime"] = xarray.start_time
            xarray.attrs["end_datetime"] = xarray.end_time
        xarrays.append(xarray)
    # If more than one file is passed, assuming more than one scan was passed.
    # This might not work if multiple L2 product types are passed that are of
    # different resolutions
    if len(xarrays) > 1:
        start_times = [x.attrs["start_datetime"] for x in xarrays]
        if len(set(start_times)) > 1:
            # multiple scan times were passed in
            xarray_dset = xr.concat(xarrays, dim="time_dim")
            xarray_dset.attrs["start_datetime"] = min(start_times)
            xarray_dset = xarray_dset.assign_coords({"time_dim": start_times})
        else:
            # Multiple files for a single scan time were passed in (such as multiple
            # Derived motion winds (DMW) files)
            # We can easily concatenate if these are 1D data, and have the same dim.
            # Check if we can do this, raise an error if not.
            # First check the dim sizes for each variable in the xarray
            xarray_dim_sizes = [len(dset.dims) for dset in xarrays]
            # Now check if each variable
            xarray_dim_names = ["_".join(list(dset.dims)) for dset in xarrays]
            if all([size == 1 for size in xarray_dim_sizes]) and (
                len(set(xarray_dim_names)) == 1
            ):
                xarray_dset = xr.concat(xarrays, dim=xarray_dim_names[0])
            else:
                raise ValueError(
                    "Do not know how to stack xarrays with "
                    "mismatching dim sizes and names"
                )
    else:
        xarray_dset = xarrays[0]

    return {"abi_l2_data": xarray_dset, "METADATA": meta_dataset}
