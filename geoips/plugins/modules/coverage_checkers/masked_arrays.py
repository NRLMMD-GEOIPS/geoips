# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Coverage check routine for masked arrays."""

import logging

LOG = logging.getLogger(__name__)

interface = "coverage_checkers"
family = "standard"
name = "masked_arrays"


def call(
    xarray_obj,
    variable_name,
    area_def=None,
):
    """Coverage check routine for xarray objects with masked projected arrays.

    Parameters
    ----------
    xarray_obj : xarray.Dataset
        xarray object containing variable "variable_name"
    variable_name : str
        variable name to check percent unmasked

    Returns
    -------
    float
        Percent coverage of variable_name
    """
    from geoips.data_manipulations.info import percent_unmasked

    if variable_name not in xarray_obj:
        raise KeyError(
            f"Variable {variable_name} did not exist. Can not calculate coverage."
        )

    return percent_unmasked(xarray_obj[variable_name].to_masked_array())
