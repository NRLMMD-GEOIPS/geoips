# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Arctic Weather Satellite (aws) MWR Level 1B NetCDF reader.

Channel information is from the ESA webpage:
https://www.esa.int/Applications/Observing_the_Earth/Meteorological_missions/

Arctic_Weather_Satellite/The_instrument
All channels have a same array size (nscan,nfov).

Chan        Freq(GHz)        FOV(km)        Utilisation

Band 1:
1           50.3             <= 40          Temp sounding
2           52.8             <= 40          Temp sounding
3           53.246           <= 40          Temp sounding
4           53.956           <= 40          Temp sounding
5           54.4             <= 40          Temp sounding
6           54.94            <= 40          Temp sounding
7           55.5             <= 40          Temp sounding
8           57.290           <= 40          Temp sounding

Band 2:
9           89               <= 20          Window and cloud detection

Band 3:
10          165.5            <= 10          Window and humidity sounding
11          176.31           <= 10          Humidity sounding
12          178.81           <= 10          Humidity sounding
13          180.31           <= 10          Humidity sounding
14          181.51           <= 10          Humidity sounding
15          182.31           <= 10          Humidity sounding

Band 4:
16          325.15 +- 1.2    <= 10          Humidity sounding/cloud detection
17          325.15 +- 2.4    <= 10          Humidity sounding/cloud detection
18          325.15 +- 4.1    <= 10          Humidity sounding/cloud detection
19          325.15 +- 6.6    <= 10          Humidity sounding/cloud detection

Note:  We do not know actual assignments of channels to the four groups, due to lack of
official documentation on Arctic Weather Satellite data. Thus, we select current
channels for each band based on internal discussions and our experience.
We will make adjustments once there are any differences from official document is
available.

Also, variables (L1B_quality_flag and degraded_channels) are space holders for QC
purposes. They are not used for now, but will be applied later.
"""

import logging
from datetime import datetime, timezone

# import os
# from collections import OrderedDict
# import numpy as np
import xarray

# from IPython import embed as shell
LOG = logging.getLogger(__name__)

#                            AWS sensor info
# setup variables
ROIs = {"Band1": 45000, "Band2": 25000, "Band3": 20000, "Band4": 20000}
group_names = ["/data/navigation", "/data/calibration", "/quality"]
list_vars = [
    "aws_lat",
    "aws_lon",
    "aws_solar_zenith_angle",
    "aws_solar_azimuth_angle",
    "aws_satellite_zenith_angle",
    "aws_satellite_azimuth_angle",
    "L1B_quality_flag",
    "degraded_channels",
    "aws_toa_brightness_temperature",
]

interface = "readers"
family = "standard"
name = "aws_netcdf"


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
    geoips_pform_name = {"AWS1": "aws"}
    return geoips_pform_name[meta_platform_name]


def call(fnames, metadata_only=False, chans=None, area_def=None, self_register=False):
    """Read aws L1 netCDF data.

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

    Notes
    -----
    data : grouped file
        stored in groups (status, data, quality) and sub-groups
        open_groups to open and decode a file for required fields
        global attributes in home group '/'
        '/'  is an important character to access data
        process only one orbit file
    """
    xobj_group = xarray.Dataset()
    for fname in fnames:  # loop input files (only one for now)
        LOG.info(f"Opening: {fname}")
        # First grab metadata
        ds = xarray.open_groups(fname)
        available_groups = list(ds)

        meta = xarray.Dataset(attrs=ds["/"].attrs)
        try:
            if "." in meta.attrs["sensing_start_time_utc"]:
                tformat = "%Y-%m-%d %H:%M:%S.%f"
            else:
                tformat = "%Y-%m-%d %H:%M:%S"
            start_datetime = datetime.strptime(
                meta.attrs["sensing_start_time_utc"], tformat
            )
            start_datetime = start_datetime.replace(tzinfo=timezone.utc)
            end_datetime = datetime.strptime(
                meta.attrs["sensing_end_time_utc"], tformat
            )
            end_datetime = end_datetime.replace(tzinfo=timezone.utc)
        except KeyError:
            LOG.info("error in orbit data start and end time")
        if hasattr(meta, "Spacecraft"):
            pform = meta.attrs["Spacecraft"]
        else:
            raise AttributeError("Cannot identify platform name")
        geoips_attrs = {
            "area_definition": area_def,
            "start_datetime": start_datetime,
            "end_datetime": end_datetime,
            "vertical_data_type": "surface",
            "source_name": "mwr",
            "platform_name": get_geoips_platform_name(pform),
            "data_provider": "noaa",
            "interpolation_radius_of_influence": 20000,
        }
        meta.attrs = dict(meta.attrs, **geoips_attrs)

        if metadata_only is True:
            LOG.info(
                "metadata_only is True, reading only first"
                + "file for metadata information and returning"
            )
            return {"METADATA": meta}
        # load data for list_vars from these groups
        for group in group_names:
            if group in available_groups:
                available_vars_group = list(ds[group].data_vars.keys())
                # Only load the requested variables from this group
                drop_vars = list(set(available_vars_group).difference(set(list_vars)))
                xr = xarray.load_dataset(fname, group=group, drop_variables=drop_vars)
            # merge xarray
            xobj_group = merge_xarrays(xr, xobj_group)

    # setup 4-band xarrays
    # Channel assignments for each band are based on internal discussions and
    # our experience.  They could be adjusted later once data documentations are
    # available.
    # quality_flag and degraded_channels are spare variables for QC purposes. They
    # are not used now, but will be applied later.
    xobj_band1 = xarray.Dataset()
    xobj_band2 = xarray.Dataset()
    xobj_band3 = xarray.Dataset()
    xobj_band4 = xarray.Dataset()

    xobj_band1["chan1"] = xobj_group["aws_toa_brightness_temperature"][:, :, 0]
    xobj_band1["chan2"] = xobj_group["aws_toa_brightness_temperature"][:, :, 1]
    xobj_band1["chan3"] = xobj_group["aws_toa_brightness_temperature"][:, :, 2]
    xobj_band1["chan4"] = xobj_group["aws_toa_brightness_temperature"][:, :, 3]
    xobj_band1["chan5"] = xobj_group["aws_toa_brightness_temperature"][:, :, 4]
    xobj_band1["chan6"] = xobj_group["aws_toa_brightness_temperature"][:, :, 5]
    xobj_band1["chan7"] = xobj_group["aws_toa_brightness_temperature"][:, :, 6]
    xobj_band1["chan8"] = xobj_group["aws_toa_brightness_temperature"][:, :, 7]
    xobj_band2["chan9"] = xobj_group["aws_toa_brightness_temperature"][:, :, 8]
    xobj_band3["chan10"] = xobj_group["aws_toa_brightness_temperature"][:, :, 9]
    xobj_band3["chan11"] = xobj_group["aws_toa_brightness_temperature"][:, :, 10]
    xobj_band3["chan12"] = xobj_group["aws_toa_brightness_temperature"][:, :, 11]
    xobj_band3["chan13"] = xobj_group["aws_toa_brightness_temperature"][:, :, 12]
    xobj_band3["chan14"] = xobj_group["aws_toa_brightness_temperature"][:, :, 13]
    xobj_band3["chan15"] = xobj_group["aws_toa_brightness_temperature"][:, :, 14]
    xobj_band4["chan16"] = xobj_group["aws_toa_brightness_temperature"][:, :, 15]
    xobj_band4["chan17"] = xobj_group["aws_toa_brightness_temperature"][:, :, 16]
    xobj_band4["chan18"] = xobj_group["aws_toa_brightness_temperature"][:, :, 17]
    xobj_band4["chan19"] = xobj_group["aws_toa_brightness_temperature"][:, :, 18]

    xobj_band1["latitude"] = xobj_group["aws_lat"][:, :, 0]
    xobj_band1["latitude"] = xobj_group["aws_lat"][:, :, 0]
    xobj_band1["longitude"] = xobj_group["aws_lon"][:, :, 0]
    xobj_band1["solar_zenith_angle"] = xobj_group["aws_solar_zenith_angle"][:, :, 0]
    xobj_band1["solar_azimuth_angle"] = xobj_group["aws_solar_azimuth_angle"][:, :, 0]
    xobj_band1["satellite_zenith_angle"] = xobj_group["aws_satellite_zenith_angle"][
        :, :, 0
    ]
    xobj_band1["satellite_azimuth_angle"] = xobj_group["aws_satellite_azimuth_angle"][
        :, :, 0
    ]
    xobj_band1["quality_flag"] = xobj_group["L1B_quality_flag"]
    xobj_band1["degraded_channels"] = xobj_group["degraded_channels"]

    xobj_band2["latitude"] = xobj_group["aws_lat"][:, :, 1]
    xobj_band2["latitude"] = xobj_group["aws_lat"][:, :, 1]
    xobj_band2["longitude"] = xobj_group["aws_lon"][:, :, 1]
    xobj_band2["solar_zenith_angle"] = xobj_group["aws_solar_zenith_angle"][:, :, 1]
    xobj_band2["solar_azimuth_angle"] = xobj_group["aws_solar_azimuth_angle"][:, :, 1]
    xobj_band2["satellite_zenith_angle"] = xobj_group["aws_satellite_zenith_angle"][
        :, :, 1
    ]
    xobj_band2["satellite_azimuth_angle"] = xobj_group["aws_satellite_azimuth_angle"][
        :, :, 1
    ]
    xobj_band2["quality_flag"] = xobj_group["L1B_quality_flag"]
    xobj_band2["degraded_channels"] = xobj_group["degraded_channels"]

    xobj_band3["latitude"] = xobj_group["aws_lat"][:, :, 2]
    xobj_band3["latitude"] = xobj_group["aws_lat"][:, :, 2]
    xobj_band3["longitude"] = xobj_group["aws_lon"][:, :, 2]
    xobj_band3["solar_zenith_angle"] = xobj_group["aws_solar_zenith_angle"][:, :, 2]
    xobj_band3["solar_azimuth_angle"] = xobj_group["aws_solar_azimuth_angle"][:, :, 2]
    xobj_band3["satellite_zenith_angle"] = xobj_group["aws_satellite_zenith_angle"][
        :, :, 2
    ]
    xobj_band3["satellite_azimuth_angle"] = xobj_group["aws_satellite_azimuth_angle"][
        :, :, 2
    ]
    xobj_band3["quality_flag"] = xobj_group["L1B_quality_flag"]
    xobj_band3["degraded_channels"] = xobj_group["degraded_channels"]

    xobj_band4["latitude"] = xobj_group["aws_lat"][:, :, 3]
    xobj_band4["latitude"] = xobj_group["aws_lat"][:, :, 3]
    xobj_band4["longitude"] = xobj_group["aws_lon"][:, :, 3]
    xobj_band4["solar_zenith_angle"] = xobj_group["aws_solar_zenith_angle"][:, :, 3]
    xobj_band4["solar_azimuth_angle"] = xobj_group["aws_solar_azimuth_angle"][:, :, 3]
    xobj_band4["satellite_zenith_angle"] = xobj_group["aws_satellite_zenith_angle"][
        :, :, 3
    ]
    xobj_band4["satellite_azimuth_angle"] = xobj_group["aws_satellite_azimuth_angle"][
        :, :, 3
    ]
    xobj_band4["quality_flag"] = xobj_group["L1B_quality_flag"]
    xobj_band4["degraded_channels"] = xobj_group["degraded_channels"]

    # add attributes to each band (will make adjustments on roi etc later)
    geoips_attrs["interpolation_radius_of_influence"] = ROIs["Band1"]
    xobj_band1.attrs = geoips_attrs.copy()
    geoips_attrs["interpolation_radius_of_influence"] = ROIs["Band2"]
    xobj_band2.attrs = geoips_attrs.copy()
    geoips_attrs["interpolation_radius_of_influence"] = ROIs["Band3"]
    xobj_band3.attrs = geoips_attrs.copy()
    geoips_attrs["interpolation_radius_of_influence"] = ROIs["Band4"]
    xobj_band4.attrs = geoips_attrs.copy()

    return {
        "AWS_Band1": xobj_band1,
        "AWS_Band2": xobj_band2,
        "AWS_Band3": xobj_band3,
        "AWS_Band4": xobj_band4,
        "METADATA": meta,
    }
