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

''' Xarray wrapper for driving the interpolation routines with basic Python inputs and outputs'''
import logging
LOG = logging.getLogger(__name__)

interp_type = '2d'


def interp_gauss(area_def, input_xarray, output_xarray, varlist, array_num=None, sigmaval=None):
    ''' Use pyresample gaussian interpolation from interp_kd_tree:  return of list of numpy.ma.MaskedArray '''
    LOG.info('Interpolating using standard scifile register method: kd_tree gauss sigmaval %s', sigmaval)

    vars_to_interp = []
    if array_num is not None:
        lons = input_xarray['longitude'].to_masked_array()[:, :, array_num]
        lats = input_xarray['latitude'].to_masked_array()[:, :, array_num]
        for varname in varlist:
            vars_to_interp += [input_xarray[varname].to_masked_array()[:, :, array_num]]
    else:
        lons = input_xarray['longitude'].to_masked_array()
        lats = input_xarray['latitude'].to_masked_array()
        for varname in varlist:
            vars_to_interp += [input_xarray[varname].to_masked_array()]

    # Use standard scifile / pyresample registration
    from geoips.interface_modules.interpolation.utils.interp_pyresample import interp_kd_tree, get_data_box_definition
    data_box_definition = get_data_box_definition(input_xarray.source_name,
                                                  lons,
                                                  lats)

    # Set s default value of igmaval as 10000

    if sigmaval is None:
        sigmaval = 10000

    interp_data = interp_kd_tree(vars_to_interp,
                                 area_def,
                                 data_box_definition,
                                 input_xarray.interpolation_radius_of_influence,
                                 interp_type='gauss',
                                 sigmas=sigmaval)
    import xarray
    if output_xarray is None:
        from geoips.dev.utils import copy_standard_metadata
        interp_lons, interp_lats = area_def.get_lonlats()
        output_xarray = xarray.Dataset()
        copy_standard_metadata(input_xarray, output_xarray)
        output_xarray['latitude'] = xarray.DataArray(interp_lats)
        output_xarray['longitude'] = xarray.DataArray(interp_lons)
        output_xarray.attrs['registered_dataset'] = True
        output_xarray.attrs['area_definition'] = area_def

    for ind in range(len(varlist)):
        output_xarray[varlist[ind]] = xarray.DataArray(interp_data[ind])

    return output_xarray
