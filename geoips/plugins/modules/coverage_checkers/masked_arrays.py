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

    varname_for_covg = variable_name
    if variable_name not in xarray_obj.variables.keys():
        LOG.info(
            '    UPDATING variable "%s" does not exist, using product name "%s"',
            variable_name,
            name,
        )
        varname_for_covg = name

    return percent_unmasked(xarray_obj[varname_for_covg].to_masked_array())
