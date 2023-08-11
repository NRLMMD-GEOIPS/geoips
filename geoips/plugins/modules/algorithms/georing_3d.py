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
from datetime import datetime

LOG = logging.getLogger(__name__)

KtoC_conversion = -273.15

interface = "algorithms"
family = "xarray_dict_to_xarray"
name = "georing_3d"

def between(data, min, max):
    le_max = np.where(data <= max, 1, 0)
    ge_min = np.where(data >= min, 1, 0)
    return np.where(ge_min + le_max == 2, data, 0)

def collapse(data):
    rows = np.shape(data)[1]
    cols = np.shape(data)[2]
    collapsed_data = np.zeros((rows, cols), dtype="int")
    for lvl in range(np.shape(data)[0]):
        lvl_data = between(data[lvl], 1, 4)
        collapsed_data += lvl_data
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
    cloud_type=True,
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

    if cloud_type:
        data = data[level]
        data = between(data, 1, 4) # masks the slice to only include clouds, otherwise the value is -999
    else: # implement binary masking on the entire dataset
        data = collapse(data)
        data = np.where(data > 0, 1, 0)
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
    source_file_datetimes = xarray_dict["GEORING"].attrs["source_file_datetimes"]
    source_name = xarray_dict["GEORING"].attrs["source_name"]
    data_provider = xarray_dict["GEORING"].attrs["data_provider"]
    data_dict = dict(Cloud_Type=(["x", "y"], data)) if cloud_type else dict(Binary_Cloud_Mask=(["x", "y"], data))
    final_xarray = xarray.Dataset(data_vars=data_dict, 
                                  coords=dict(latitude=(["x","y"], lat_final),
                                              longitude=(["x","y"], lon_final)),
                                  attrs=dict(source_name=source_name,
                                                  platform_name=platform_name,
                                                  start_datetime=start_dt,
                                                  end_datetime=end_dt,
                                                  source_file_datetimes=source_file_datetimes,
                                                  data_provider=data_provider)
                                 )
    return final_xarray
