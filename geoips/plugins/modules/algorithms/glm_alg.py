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

"""Data manipulation steps for standard "single_channel" algorithm.

Generalized algorithm to apply data manipulation steps in a standard order
to apply corrections to a single channel output product.
"""
import logging

LOG = logging.getLogger(__name__)

interface = "algorithms"
family = "xarray_dict_to_xarray"
name = "glm_alg"


def call(
    xarray_dict, # Dictionary containing xarray dictionaries
    output_data_range=[0, 10000],  # Range of values that your algorithm will output
    scale_factor=1,  # Adding a scale factor here for use in converting input meters to output kilometers
    min_outbounds="crop",
    max_outbounds="crop",
    norm=False,
    inverse=False,
):
    """Apply data range and requested corrections to a single channel product.

    Data manipulation steps for applying a data range and requested corrections
    to a single channel product

    Parameters
    ----------
    xarray_dict : Dictionary of xarray.Dataset
        * dictionary of xarray.Dataset Channel Data
    output_data_range : list of float, default=None
        * list of min and max value for output data product.
        * This is applied LAST after all other corrections/adjustments
        * If None, use data min and max.
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
    Returns
    -------
    xarray.Dataset.
    """
    import xarray

    chan = "group_area"
    for var_name in xarray_dict["GLM"].variables.keys():
        if "area" in var_name:
            chan = var_name

    channel_vars = {
        "longitude": xarray_dict["GLM"]["lon"],
        "latitude": xarray_dict["GLM"]["lat"],
        "quality_flag": xarray_dict["GLM"]["quality_flag"],
        f"{chan}": xarray_dict["GLM"][f"{chan}"],
    }

    final_xarray = xarray.Dataset(
        data_vars=channel_vars,
        coords=xarray_dict["GLM"].coords,
        attrs=xarray_dict["METADATA"].attrs,
    )

    return final_xarray
