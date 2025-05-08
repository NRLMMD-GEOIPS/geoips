# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""VIIRS Level 2 NetCDF reader."""

import logging
from datetime import datetime
import os

from collections import OrderedDict
import numpy as np
import xarray

LOG = logging.getLogger(__name__)

interface = "readers"
family = "standard"
name = "viirs_l2_netcdf"


def merge_xarrays(src_xobj, dst_xobj):
    """Merge one xarray into another.

    Parameters
    ----------
    src_xobj : xarray.Dataset
        Input dataset to merge
    dst_xobj : xarray.Dataset
        Dataset where src_xobj will be merged

    Returns
    -------
    xarray.Dataset
        Merged xarray dataset
    """
    tmp_xobj = xarray.Dataset()
    for dvar in src_xobj.data_vars.keys():
        dset = src_xobj[dvar]
        if dvar not in dst_xobj:
            dst_xobj[dvar] = dset
        else:
            tmp_xobj[dvar] = xarray.concat(
                [dst_xobj[dvar], dset], dim=dst_xobj[dvar].dims[0]
            )
            dst_xobj = dst_xobj.drop(dvar)
    try:
        merged_xobj = xarray.merge([tmp_xobj, dst_xobj])
    except ValueError:
        tmp_dims = {x: tmp_xobj[x].size for x in tmp_xobj.dims}
        dst_dims = {x: dst_xobj[x].size for x in dst_xobj.dims}
        mismatching_dims = [x for x in dst_dims if tmp_dims[x] != dst_dims[x]]
        merged_xobj = xarray.combine_nested(
            [tmp_xobj, dst_xobj], concat_dim=mismatching_dims
        )
    return merged_xobj


def get_geoips_platform_name(meta_platform_name):
    """Map source file platform name to standard GeoIPS names.

    Parameters
    ----------
    meta_platform_name : str
        Name of platform in source file

    Returns
    -------
    str
        Standard GeoIPS platform name
    """
    geoips_pform_name = {"NPP": "npp", "NPP_OPS": "npp", "JPSS": "noaa20"}
    return geoips_pform_name[meta_platform_name]


def pair_file_names(file_list):
    """Attempt to group VIIRS NASA LANCE/LAADS files together by scan time.

    Parameters
    ----------
    file_list : list
        list of file names passed to reader

    Returns
    -------
    dict
        Dictionary of scan times with each key holding list of files per time.
    """
    basenames = [os.path.basename(x) for x in file_list]
    gran_times = [".".join(x.split(".")[1:3]) for x in basenames]
    unique_gran_times = sorted(np.unique(gran_times))
    paired_granules = OrderedDict()
    for gtimes in unique_gran_times:
        paired_granules[gtimes] = sorted([x for x in file_list if gtimes in x])
    return paired_granules


def call(fnames, metadata_only=False, chans=None, area_def=None, self_register=False):
    """Read VIIRS L2 netCDF data.

    Parameters
    ----------
    fci_files : list
        list of files for a given scan time
    metadata_only : bool, optional
        Only return metadata, by default False
    chans : list, optional
        List of channels/variables to load, by default None
    area_def : pyresample area definition, optional
        Read in data for specific area definition, by default None
        (currently unsupported)
    self_register : bool, optional
        Self register data to given resolution, by default False
        (currently unsupported)

    Returns
    -------
    dict
        dictionary of xarray datasets

    Raises
    ------
    AttributeError
        Encountered unknown platform name in source file
    """
    xobj = xarray.Dataset()
    # for fname in pair_file_names(fnames):
    for gran_time, gran_files in pair_file_names(fnames).items():
        gran_xobj = xarray.Dataset()
        for fname in gran_files:
            LOG.info(f"Opening: {fname}")
            # First grab metadata
            with xarray.open_dataset(fname) as ds:
                available_vars = list(ds.data_vars.keys())
                meta = xarray.Dataset(attrs=ds.attrs)
                try:
                    if "." in meta.attrs["time_coverage_start"]:
                        tformat = "%Y-%m-%dT%H:%M:%S.%fZ"
                    else:
                        tformat = "%Y-%m-%dT%H:%M:%SZ"
                    start_datetime = datetime.strptime(
                        meta.attrs["time_coverage_start"], tformat
                    )
                    end_datetime = datetime.strptime(
                        meta.attrs["time_coverage_end"], tformat
                    )
                except KeyError:
                    start_datetime = datetime.strptime(
                        meta.attrs["PGE_StartTime"], "%Y-%m-%d %H:%M:%S.%f"
                    )
                    end_datetime = datetime.strptime(
                        meta.attrs["PGE_EndTime"], "%Y-%m-%d %H:%M:%S.%f"
                    )
                if hasattr(meta, "SatelliteInstrument"):
                    pform = meta.attrs["SatelliteInstrument"]
                elif hasattr(meta, "satellite_name"):
                    pform = meta.attrs["satellite_name"]
                else:
                    raise AttributeError("Cannot identify platform name")
                geoips_attrs = {
                    "area_definition": area_def,
                    "start_datetime": start_datetime,
                    "end_datetime": end_datetime,
                    "vertical_data_type": "surface",
                    "source_name": "viirs",
                    "platform_name": get_geoips_platform_name(pform),
                    "data_provider": "nasa",
                    "interpolation_radius_of_influence": 2000,
                }
                meta.attrs = dict(meta.attrs, **geoips_attrs)

            if metadata_only is True:
                LOG.info(
                    "metadata_only is True, reading only first"
                    + "file for metadata information and returning"
                )
                return {"METADATA": meta}

            group = None
            if "Geolocation" in meta.title:
                # This is a geolocation file, need to open the group to
                # find the available datasets
                group = "geolocation_data"
                with xarray.open_dataset(fname, group=group) as ds:
                    available_vars = list(ds.data_vars.keys())

            if not chans:
                # Load all datasets if no chans are requested
                default_chans = available_vars
            else:
                default_chans = chans

            # Only load the requested variables
            drop_vars = list(set(available_vars).difference(set(default_chans)))

            # Use xarray to open the file
            xr = xarray.load_dataset(fname, group=group, drop_variables=drop_vars)

            empty_vars = []

            for xr_dim_name, xr_dim_val in xr.dims.items():
                for gr_dim_name, gr_dim_val in gran_xobj.dims.items():
                    if (xr_dim_name != gr_dim_name) & (xr_dim_val == gr_dim_val):
                        LOG.info(
                            "Detected %s shares the same dim size as %s",
                            xr_dim_name,
                            gr_dim_name,
                        )
                        LOG.info(
                            "Renaming to share same dimension name: %s", gr_dim_name
                        )
                        xr = xr.rename({xr_dim_name: gr_dim_name})

            for var, data in xr.variables.items():
                if data.size == 0:
                    LOG.info("Empty variable: %s. Dropping", var)
                    empty_vars.append(var)
                    continue
                # Check if time array exists
                time_key = "datetime_" + "_".join(data.dims)
                if (time_key not in gran_xobj) & (time_key not in xr):
                    LOG.info("Creating time key: %s", time_key)
                    time_array = np.empty(data.shape).astype(datetime)
                    time_array[:] = start_datetime
                    xr[time_key] = (data.dims, time_array)
            xr = xr.drop_vars(empty_vars)

            gran_xobj = merge_xarrays(xr, gran_xobj)

        if "Latitude" in list(gran_xobj.variables.keys()):
            gran_xobj = gran_xobj.rename({"Latitude": "latitude"})
            gran_xobj = gran_xobj.rename({"Longitude": "longitude"})

        loaded_vars = list(gran_xobj.variables.keys())
        if not all(x in loaded_vars for x in chans):
            # sorted(loaded_vars) != sorted(chans):
            LOG.info(
                "Not all variables available for %s. "
                + "Not appending to final xarray Dataset",
                gran_time,
            )
            continue
        # Merge xarrays together
        xobj = merge_xarrays(gran_xobj, xobj)

    for key in xobj.data_vars.keys():
        xobj[key].data = xobj[key].to_masked_array()
    xobj.attrs = meta.attrs

    vars_2d = []
    vars_1d = []
    for key in xobj.data_vars.keys():
        dims = list(xobj[key].dims)
        if "time" in dims:
            dims.remove("time")
        if len(dims) == 1:
            vars_1d.append(key)
        elif len(dims) == 2:
            vars_2d.append(key)

    xobj_1d = xobj.drop_vars(vars_2d)
    xobj_2d = xobj.drop_vars(vars_1d)

    rename_vars = {}
    for geo_var in ["longitude", "latitude"]:
        if geo_var not in xobj_1d.data_vars.keys():
            for key in xobj_1d.data_vars.keys():
                if geo_var in key:
                    print(f"Renaming {key} to latitude")
                    rename_vars[key] = geo_var
                    xobj_1d[geo_var] = xobj_1d[key]

    return {"viirs_data_2d": xobj_2d, "viirs_data_1d": xobj_1d, "METADATA": meta}
