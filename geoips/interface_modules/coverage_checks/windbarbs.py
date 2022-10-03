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

''' Coverage check routine for windbarb xarrays
'''

import logging

LOG = logging.getLogger(__name__)


def windbarbs(xarray_obj, variable_name, area_def, alt_varname_for_covg=None):
    ''' Coverage check routine for wind barb xarray object.

    This algorithm expects input windspeed with units "kts" and returns in "kts"

    Args:
        xarray_obj (xarray.Dataset) :  xarray object containing variable "variable_name" for registering to
        variable_name (str) : variable name to register to 

    Returns:
        float : Percent coverage of variable_name over area_def
    '''

    varname_for_covg = variable_name
    if variable_name not in xarray_obj.variables.keys() and alt_varname_for_covg is not None:
        LOG.info('    UPDATING variable "%s" does not exist, using alternate "%s"', variable_name, alt_varname_for_covg)
        varname_for_covg = alt_varname_for_covg

    from geoips.interfaces import interpoloators
    interp_func = interpoloators.get('pyresample_wrappers.interp_nearest')
    output_xarray = interp_func(area_def, xarray_obj, None, [varname_for_covg], array_num=0)

    from geoips.data_manipulations.info import percent_unmasked
    return percent_unmasked(output_xarray[varname_for_covg].to_masked_array())
