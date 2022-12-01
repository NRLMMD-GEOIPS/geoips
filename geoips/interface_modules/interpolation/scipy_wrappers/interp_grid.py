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

interp_type = 'grid'


def interp_grid(area_def, input_xarray, output_xarray, varlist, array_num=None, method=None):
    ''' Set imgkey as 'Griddata<method>' where <method> is one of 'cubic', 'linear' or 'nearest' '''
    LOG.info('Interpolating using scipy.interpolate.griddata %s', method)

    interp_datas = []
    for varname in varlist:
        if array_num is not None:
            lons = input_xarray['longitude'].to_masked_array()[:, :, array_num]
            lats = input_xarray['latitude'].to_masked_array()[:, :, array_num]
            var_to_interp = input_xarray[varname].to_masked_array()[:, :, array_num]
        else:
            lons = input_xarray['longitude'].to_masked_array()
            lats = input_xarray['latitude'].to_masked_array()
            var_to_interp = input_xarray[varname].to_masked_array()

        from geoips.interface_modules.interpolation.utils.interp_scipy import interp_griddata
        min_gridlon = area_def.area_extent_ll[0]
        max_gridlon = area_def.area_extent_ll[2]
        min_gridlat = area_def.area_extent_ll[1]
        max_gridlat = area_def.area_extent_ll[3]
        numx_grid = area_def.pixel_size_x
        numy_grid = area_def.pixel_size_y

        interp_datas += [interp_griddata(var_to_interp,
                                         lons,
                                         lats,
                                         min_gridlon,
                                         max_gridlon,
                                         min_gridlat,
                                         max_gridlat,
                                         numx_grid,
                                         numy_grid,
                                         method)]

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
