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

"""Coverage check routine for RGBA arrays."""
import logging

LOG = logging.getLogger(__name__)

interface = "coverage_checkers"
family = "standard"
name = "rgba"


def call(
    xarray_obj,
    variable_name,
    area_def=None,
    alt_varname=None,
    force_alt_varname=False,
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
    from geoips.image_utils.mpl_utils import percent_unmasked_rgba

    varname_for_covg = variable_name
    if (
        variable_name not in xarray_obj.variables.keys()
        and alt_varname_for_covg is not None
    ):
        LOG.info(
            '    UPDATING variable "%s" does not exist, using alternate "%s"',
            variable_name,
            alt_varname_for_covg,
        )
        varname_for_covg = alt_varname_for_covg
    if force_alt_varname and alt_varname_for_covg is not None:
        LOG.info(
            "    UPDATING force_alt_varname set, "
            'using alternate "%s" rather than variable "%s"',
            alt_varname_for_covg,
            variable_name,
        )
        varname_for_covg = alt_varname_for_covg

    return percent_unmasked_rgba(xarray_obj[varname_for_covg].to_masked_array())
