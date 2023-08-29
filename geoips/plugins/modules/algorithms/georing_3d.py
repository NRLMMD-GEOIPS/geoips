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
import multiprocessing as mp

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


def get_cloud_height(bin_mask, alg_type):
    """Return a 2D matrix of cloud heights determined by alg_type.

    Parameters
    ----------
    bin_mask: 3D numpy ndarray
        Values are 0 or 1, 1 being where a cloud exists
    alg_type: String
        The algorithm type to be applied to cloud height.
        One of ["cloud_top_height", "cloud_base_height", "cloud_depth"]
    """
    rows = np.shape(bin_mask)[1]
    cols = np.shape(bin_mask)[2]
    if "cloud_depth" == alg_type:
        data_top = np.empty((rows, cols), dtype="float32")
        data_top.fill(-999)
        data_base = np.empty((rows, cols), dtype="float32")
        data_base.fill(999)
    else:
        data = np.empty((rows, cols), dtype="float32")
        if "cloud_top_height" == alg_type:
            data.fill(-999)
        elif "cloud_base_height" == alg_type:
            data.fill(999)
    for lvl in range(np.shape(bin_mask)[0]):
        lvl_km = (lvl * 0.25)
        bin_mask_km = bin_mask[lvl] * lvl_km
        if "cloud_depth" == alg_type:
            data_top[bin_mask_km > data_top] = lvl_km
            bin_mask_km[bin_mask_km == 0] = 999
            data_base[bin_mask_km < data_base] = lvl_km
        elif "cloud_top_height" == alg_type:
            data[bin_mask_km > data] = lvl_km
        elif "cloud_base_height" == alg_type:
            bin_mask_km[bin_mask_km == 0] = 999
            data[bin_mask_km < data] = lvl_km
    if "cloud_depth" == alg_type:
        return data_top - data_base
    else:
        return data


def get_cloud_layers(data):
    """Collapse a 3D matrix into a 2D matrix, calculating cloud layers.

    Parameters
    ----------
    data: 3D numpy ndarray
        Contains integers relating to cloud_type, where cloud is between (1,4)
    """
    rows = np.shape(data)[1]
    cols = np.shape(data)[2]
    bin_mask = binary_cloud_mask(data)
    collapsed_data = np.zeros((rows, cols), dtype="int")
    for lvl in range(np.shape(data)[0]):
        if lvl == 0:
            prev_layer = collapsed_data
            lvl_data = None
        else:
            prev_layer = lvl_data
        lvl_data = bin_mask[lvl]
        layer_mask = diff_layer(prev_layer, lvl_data)
        collapsed_data[layer_mask == 1] += 1
    return collapsed_data


def mp_by_function(function, data, alg_type=None):
    """Return manipulated data in a multiprocess manner, provided function and data."""
    num_processes = mp.cpu_count()
    chunk_size = 1000

    pool = mp.Pool(processes=num_processes)
    if alg_type is not None:
        data = pool.starmap(function, [(data, alg_type)], chunksize=chunk_size)
    else:
        data = pool.starmap(function, [(data)], chunksize=chunk_size)
    return data[0]


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
    """Apply data range and requested corrections to a GEOring_3d product.

    Data manipulation steps for applying a data range and requested corrections
    to a GEOring_3d product

    Parameters
    ----------
    xarray_dict : Dictionary of xarray.dataset
        * contains metadata and cloud type data
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

    Returns
    -------
    xarray.Dataset
    """
    data = xarray_dict["GEORING"].variables["cloud3d"].data
    lat = xarray_dict["GEORING"].variables["latitude"].data
    lon = xarray_dict["GEORING"].variables["longitude"].data

    if output_data_range is None:
        output_data_range = [data.min(), data.max()]

    if "cloud_type" == alg_type:
        data = data[level]
        data[data > 4] = 0
        # masks the slice to only include clouds, otherwise the value is -999
    elif "binary_cloud_mask" == alg_type:  # implement binary masking on the dataset
        data = np.max(binary_cloud_mask(data), axis=0)
    elif "layered" == alg_type:
        data = get_cloud_layers(data)
    else:
        bin_mask = binary_cloud_mask(data)
        data = get_cloud_height(bin_mask, alg_type)
        # data = mp_by_function(get_cloud_height, binary_cloud_mask(data), alg_type)
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
