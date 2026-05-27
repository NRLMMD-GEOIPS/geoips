# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Coverage check routine for RGBA arrays."""

# Python Standard Libraries
import logging

# GeoIPS imports
from geoips.image_utils.mpl_utils import percent_unmasked_rgba

LOG = logging.getLogger(__name__)

interface = "coverage_checkers"
family = "standard"
name = "rgba"


def call(
    xarray_obj,
    variable_name,
    area_def=None,
):
    """Coverage check routine for xarray objects with projected RGBA arrays.

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
    if variable_name not in xarray_obj:
        raise KeyError(
            f"Variable {variable_name} did not exist. Can not calculate coverage."
        )
    return percent_unmasked_rgba(xarray_obj[variable_name].to_masked_array())
