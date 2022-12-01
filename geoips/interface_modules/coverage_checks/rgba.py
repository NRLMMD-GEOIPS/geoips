# # # Distribution Statement A. Approved for public release. Distribution unlimited.
# # #
# # # Author:
# # # Naval Research Laboratory, Marine Meteorology Division
# # #
# # # This program is free software:
# # # you can redistribute it and/or modify it under the terms
# # # of the NRLMMD License included with this program.
# # #
# # # If you did not receive the license, see
# # # https://github.com/U-S-NRL-Marine-Meteorology-Division/
# # # for more information.
# # #
# # # This program is distributed WITHOUT ANY WARRANTY;
# # # without even the implied warranty of MERCHANTABILITY
# # # or FITNESS FOR A PARTICULAR PURPOSE.
# # # See the included license for more details.

''' Coverage check routine for masked arrays
'''

import logging

LOG = logging.getLogger(__name__)


def rgba(xarray_obj, variable_name, area_def=None, alt_varname_for_covg=None):
    ''' Coverage check routine for xarray objects with masked projected arrays.

    Args:
        xarray_obj (xarray.Dataset) :  xarray object containing variable "variable_name"
        variable_name (str) : variable name to check percent unmasked

    Returns:
        float : Percent coverage of variable_name
    '''

    from geoips.image_utils.mpl_utils import percent_unmasked_rgba

    varname_for_covg = variable_name
    if variable_name not in xarray_obj.variables.keys() and alt_varname_for_covg is not None:
        LOG.info('    UPDATING variable "%s" does not exist, using alternate "%s"', variable_name, alt_varname_for_covg)
        varname_for_covg = alt_varname_for_covg

    return percent_unmasked_rgba(xarray_obj[varname_for_covg].to_masked_array())
