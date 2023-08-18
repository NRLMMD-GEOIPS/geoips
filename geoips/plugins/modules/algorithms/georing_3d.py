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

"""Data manipulation steps for standard "georing_3d" algorithm.

Generalized algorithm to apply data manipulation steps in a standard order
to apply corrections to a single channel output product.
"""
import logging
import numpy as np
import xarray

LOG = logging.getLogger(__name__)

interface = "algorithms"
family = "xarray_dict_to_xarray"
name = "georing_3d"


def between(data, min, max, lvl=None, type=None):
    """Return masked data where data is between (inclusive) min/max, otherwise zero.

    Parameters
    ----------
    data: 2D numpy ndarray
        Contains integers relating to cloud type, where cloud is between (1,4)
    min: int
        Minimum value (inclusive)
    max: int
        Maximum value (inclusive)
    lvl: int
        If not None, return the level in km where data is between (1,4) else a fill val
    type: string
        If not None, depict the type of algorithm being computed.
        Options: ["cloud_top_height", "cloud_base_height", "cloud_depth", "layered"]
    """
    if lvl is None and type is None:
        between_mask = np.where((data <= max) & (data >= min), data, 0)
    elif lvl is None:
        between_mask = np.where((data <= max) & (data >= min), 1, 0)
    else:
        fill_val = -999 if "top" in type else 999
        lvl_km = (lvl * 0.25) + 0.25
        between_mask = np.where((data <= max) & (data >= min), lvl_km, fill_val)
    return between_mask


def binary_cloud_mask(data):
    """Create a binary mask on data where clouds exist (1) else (0)."""
    bin_mask = np.zeros_like(data)
    bin_mask[(data >= 1) & (data <= 4)] = 1
    return bin_mask


def diff_layer(prev_layer, curr_layer):
    """Return binary mask representing whether there is a new cloud layer."""
    new_layer = np.where((prev_layer == 0) & (curr_layer == 1), 1, 0)
    return new_layer


def collapse(data, cld_height=None):
    """Collapse a 3D matrix into a 2D matrix, based on cloud type.

    Parameters
    ----------
    data: 3D numpy ndarray
        Contains integers relating to cloud_type, where cloud is between (1,4)
    cld_height: string
        If not None, return collapsed matrix with cloud top, cloud base,
        cloud depth, or layered.
    """
    rows = np.shape(data)[1]
    cols = np.shape(data)[2]
    bin_mask = binary_cloud_mask(data)
    if "cloud_layers" == cld_height:
        collapsed_data = np.zeros((rows, cols), dtype="int")
    elif "cloud_depth" == cld_height:
        collapsed_data_top = np.empty((rows, cols), dtype="int")
        collapsed_data_base = np.empty((rows, cols), dtype="int")
        collapsed_data_top.fill(-999)
        collapsed_data_base.fill(999)
    else:
        collapsed_data = np.empty((rows, cols), dtype="int")
        if "top" in cld_height:
            collapsed_data.fill(-999)
        elif "base" in cld_height:
            collapsed_data.fill(999)
    for lvl in range(np.shape(data)[0]):
        if "cloud_layers" == cld_height:
            if lvl == 0:
                prev_layer = collapsed_data
                lvl_data = None
            else:
                prev_layer = lvl_data
            lvl_data = bin_mask[lvl]
            layer_mask = diff_layer(prev_layer, lvl_data)
            collapsed_data[layer_mask == 1] += 1
        else:
            lvl_km = (lvl * 0.25) + 0.25
            poss_idxs = np.where(bin_mask[lvl] == 1)
            if "cloud_top_height" == cld_height:
                # lvl_data = between(data[lvl], 1, 4, lvl, cld_height)
                # lvl_data[bin_mask[lvl] == 1] = (lvl * 0.25) + 0.25
                collapsed_data[(poss_idxs) & (lvl_km > collapsed_data[poss_idxs])] = lvl_km
                # collapsed_data[poss_idxs] = np.where(lvl_km > collapsed_data[poss_idxs],
                #                                      lvl_km, collapsed_data[poss_idxs])
                # collapsed_data[(lvl_km > collapsed_data[poss_idxs])] = lvl_km
            # elif "base" in cld_height:
            #     lvl_data = between(data[lvl], 1, 4, lvl, cld_height)
            #     collapsed_data = np.where(lvl_data < collapsed_data,
            #                             lvl_data, collapsed_data)
            # elif "depth" in cld_height:
            #     lvl_data_top = between(data[lvl], 1, 4, lvl, "cloud_top_height")
            #     lvl_data_base = np.copy(lvl_data_top)
            #     lvl_data_base[lvl_data_base == -999] = 999
            #     collapsed_data_top = np.where(lvl_data_top > collapsed_data_top,
            #                                 lvl_data_top, collapsed_data_top)
            #     collapsed_data_base = np.where(lvl_data_base < collapsed_data_base,
            #                                 lvl_data_base, collapsed_data_base)
    if "depth" in cld_height:
        return collapsed_data_top - collapsed_data_base
    else:
        return collapsed_data


def call(
    xarray_dict,
    output_data_range=None,
    input_units=None,
    output_units=None,
    min_outbounds="crop",
    max_outbounds="crop",
    norm=False,
    inverse=False,
    alg_type="cloud_type",
    level=35
):
    """Apply data range and requested corrections to a single channel product.

    Data manipulation steps for applying a data range and requested corrections
    to a single channel product

    Parameters
    ----------
    arrays : list of numpy.ndarray
        * list of numpy.ndarray or numpy.MaskedArray of channel data
        * MUST be length one for single_channel algorithm.
    output_data_range : list of float, default=None
        * list of min and max value for output data product.
        * This is applied LAST after all other corrections/adjustments
        * If None, use data min and max.
    input_units : str, default=None
        * Units of input data, for applying necessary conversions
        * If None, no conversion
    output_units : str, default=None
        * Units of output data, for applying necessary conversions
        * If None, no conversion
    min_outbounds : str, default='crop'
        * Method to use when applying bounds.  Valid values are:

            * retain: keep all pixels as is
            * mask: mask all pixels that are out of range
            * crop: set all out of range values to either min_val or max_val
              as appropriate
    max_outbounds : str, default='crop'
        * Method to use when applying bounds.  Valid values are:

            * retain: keep all pixels as is
            * mask: mask all pixels that are out of range
            * crop: set all out of range values to either min_val or max_val
              as appropriate
    norm : bool, default=False
        * Boolean flag indicating whether to normalize (True) or not (False)

            * If True, returned data will be in the range from 0 to 1
            * If False, returned data will be in the range from min_val to max_val
    inverse : bool, default=False
        * Boolean flag indicating whether to inverse (True) or not (False)

            * If True, returned data will be inverted
            * If False, returned data will not be inverted
    cloud_type : boolean, default=True
        * Denotes whether or not cloud_type masking should be done on the data
    level : integer, default=0
        * Denotes which level of the data to do cloud_type masking on

    Notes
    -----
    Order of operations, based on the passed arguments, is:

    1. Mask night
    2. Mask day
    3. Apply solar zenith correction
    4. Apply gamma values
    5. Apply scale factor
    6. Convert units
    7. Apply data range.

    NOTE: If "norm=True" is specified, the "output_data_range" will NOT
    match the actual range of the returned data, since the normalized data
    will be returned between 0 and 1.

    If you require a different order of operations than that specified within
    "single_channel" algorithm, please create a new algorithm for your desired
    order of operations.

    Returns
    -------
    numpy.ndarray
        numpy.ndarray or numpy.MaskedArray of appropriately scaled channel data,
        in units "output_units".
    """
    data = xarray_dict["GEORING"].variables["cloud3d"].data
    lat = xarray_dict["GEORING"].variables["latitude"].data
    lon = xarray_dict["GEORING"].variables["longitude"].data

    if output_data_range is None:
        output_data_range = [data.min(), data.max()]

    if "cloud_type" == alg_type:
        data = data[level]
        data[data > 4] = 0
        # data = between(data, 1, 4)
        # masks the slice to only include clouds, otherwise the value is -999
    elif "binary_cloud_mask" == alg_type:  # implement binary masking on the dataset
        data = np.sum(binary_cloud_mask(data), axis=0)
        data[data > 0] = 1
    else:
        # bin_mask = binary_cloud_mask(data)
        data = collapse(data, cld_height=alg_type)
    lon_final, lat_final = np.meshgrid(lon, lat)

    from geoips.data_manipulations.corrections import apply_data_range

    data = apply_data_range(
        data,
        min_val=output_data_range[0],
        max_val=output_data_range[1],
        min_outbounds=min_outbounds,
        max_outbounds=max_outbounds,
        norm=norm,
        inverse=inverse,
    )

    start_dt = xarray_dict["GEORING"].attrs["start_datetime"]
    end_dt = xarray_dict["GEORING"].attrs["end_datetime"]
    platform_name = xarray_dict["GEORING"].attrs["platform_name"]
    sf_datetimes = xarray_dict["GEORING"].attrs["source_file_datetimes"]
    source_name = xarray_dict["GEORING"].attrs["source_name"]
    data_provider = xarray_dict["GEORING"].attrs["data_provider"]
    if "cloud_type" in alg_type:
        data_dict = dict(Cloud_Type=(["x", "y"], data))
    elif "binary" in alg_type:
        data_dict = dict(Binary_Cloud_Mask=(["x", "y"], data))
    elif "base_height" in alg_type:
        data_dict = dict(Cloud_Base_Height=(["x", "y"], data))
    elif "top_height" in alg_type:
        data_dict = dict(Cloud_Top_Height=(["x", "y"], data))
    elif "depth" in alg_type:
        data_dict = dict(Cloud_Depth=(["x", "y"], data))
    elif "layered" in alg_type:
        data_dict = dict(Cloud_Layers=(["x", "y"], data))
    final_xarray = xarray.Dataset(data_vars=data_dict,
                                  coords=dict(latitude=(["x", "y"], lat_final),
                                              longitude=(["x", "y"], lon_final)),
                                  attrs=dict(source_name=source_name,
                                             platform_name=platform_name,
                                             start_datetime=start_dt,
                                             end_datetime=end_dt,
                                             source_file_datetimes=sf_datetimes,
                                             data_provider=data_provider))
    return final_xarray
