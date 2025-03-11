# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Coverage check routine for windbarb xarrays."""

import logging

LOG = logging.getLogger(__name__)

interface = "coverage_checkers"
family = "standard"
name = "windbarbs"


def call(
    xarray_obj,
    variable_name,
    area_def=None,
):
    """Coverage check routine for wind barb xarray object.

    Parameters
    ----------
    xarray_obj : xarray.Dataset
        xarray object containing variable "variable_name"
    variable_name : str
        variable name to check percent unmasked.

    Returns
    -------
    float
        Percent coverage of variable_name over area_def
    """
    if variable_name not in xarray_obj:
        raise KeyError(
            f"Variable {variable_name} did not exist. Can not calculate coverage."
        )

    from geoips.interfaces import interpolators

    interp_plugin = interpolators.get_plugin("interp_nearest")
    output_xarray = interp_plugin(
        area_def, xarray_obj, None, [variable_name], array_num=0
    )

    from geoips.data_manipulations.info import percent_unmasked

    return percent_unmasked(output_xarray[variable_name].to_masked_array())
