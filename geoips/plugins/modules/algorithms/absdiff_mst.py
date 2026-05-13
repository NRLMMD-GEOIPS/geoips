# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Data manipulation steps for standard absolute difference algorithm.

Generalized algorithm to calculate the difference between 1 or 2 variables taken from
multiple scan times over the same sector.
"""

import logging

import numpy as np
import xarray as xr

from geoips.data_manipulations.corrections import apply_data_range
from geoips.errors import PluginError

LOG = logging.getLogger(__name__)

interface = "algorithms"
family = "xarray_to_xarray"
name = "absdiff_mst"


def call(
    xobj,
    variables,
    product_name,
    output_data_range=None,
    input_units=None,
    output_units=None,
    min_outbounds="crop",
    max_outbounds="crop",
    norm=False,
    inverse=False,
    sun_zen_correction=False,
    mask_night=False,
    max_day_zen=None,
    mask_day=False,
    min_night_zen=None,
    gamma_list=None,
    scale_factor=None,
):
    """Apply data range and requested corrections to an absdiff product.

    Data manipulation steps for applying a data range and requested corrections
    to a single channel productn absdiff product.

    Parameters
    ----------
    xobj : xarray.Dataset
        * input xarray.Dataset used for data manipulation.
    variables : list of str
        * list of strings representing the variables used to produce 'product_name'
    product_name : str
        * String representing the product produced by this algorithm, using variables
          from 'xobj'
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
    sun_zenith_correction : bool, default=False
        * Boolean flag indicating whether to apply solar zenith correction
          (True) or not (False)

            * If True, returned data will have solar zenith correction applied
              (see data_manipulations.corrections.apply_solar_zenith_correction)
            * If False, returned data will not be modified based on solar zenith
              angle

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
    # Take the first lon / lat values as they should be the same for all time steps
    lon = np.asarray(xobj.longitude[0])  # Take the first longitude value
    lat = np.asarray(xobj.latitude[0])  # Take the first latitude value

    # Get the input variable from timestep 1 and 2
    if len(variables) == 1:
        data1 = np.asarray(xobj[variables[0]][0])
        data2 = np.asarray(xobj[variables[0]][1])
    # Otherwise get variable 1 from timestep 1 and variable 2 from timestep 2
    elif len(variables) == 2:
        data1 = np.asarray(xobj[variables[0]][0])
        data2 = np.asarray(xobj[variables[1]][1])
    else:
        raise PluginError(
            "Error: more than 2 variables were provided to absdiff_mst algorithm plugin"
            f".\n Variables = {variables}. Cannot take the absolute difference between "
            "more than two variables from two different time steps. Please provide only"
            f" 1-2 variable names for product: {product_name}."
        )
    # Take the absolute difference between these variables, such as cth - cbh
    data = np.abs(data2 - data1)

    data = apply_data_range(
        data,
        min_val=output_data_range[0],
        max_val=output_data_range[1],
        min_outbounds=min_outbounds,
        max_outbounds=max_outbounds,
        norm=norm,
        inverse=inverse,
    )

    final_xobj = xr.Dataset(
        data_vars={product_name: (["y", "x"], data)},
        coords={
            "longitude": (["y", "x"], lon),
            "latitude": (["y", "x"], lat),
        },
        attrs=xobj.attrs,
    )

    return final_xobj
