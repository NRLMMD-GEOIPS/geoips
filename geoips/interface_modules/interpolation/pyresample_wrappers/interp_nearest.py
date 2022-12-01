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


def get_final_roi(xarray_obj, area_def):
    roi = None
    if 'interpolation_radius_of_influence' in xarray_obj.attrs.keys():
        roi = xarray_obj.interpolation_radius_of_influence
        LOG.info('    USING XARRAY ROI of %s', roi)
    if not roi or area_def.pixel_size_x > roi:
        roi = area_def.pixel_size_x
        LOG.info('    USING AREA_DEF X ROI of %s', roi)
    if area_def.pixel_size_y > roi:
        roi = area_def.pixel_size_y
        LOG.info('    USING AREA_DEF Y ROI of %s', roi)
    return roi


def interp_nearest(area_def, input_xarray, output_xarray, varlist, array_num=None):
    ''' Set up the call to interp_kd_tree using standard attributes and variables in a given xarray object.
        Returns:
            list of numpy.ma.MaskedArray'''

    LOG.info('Interpolating nearest using standard scifile register method: kd_tree nearest')

    roi = get_final_roi(input_xarray, area_def)

    vars_to_interp = []
    if array_num is not None:
        if len(input_xarray[varlist[0]].shape) == 2:
            if len(input_xarray['latitude'].shape) == 2:
                lons = input_xarray['longitude'].to_masked_array()[:, array_num]
                lats = input_xarray['latitude'].to_masked_array()[:, array_num]
            else:
                lons = input_xarray['longitude'].to_masked_array()
                lats = input_xarray['latitude'].to_masked_array()
            for varname in varlist:
                vars_to_interp += [input_xarray[varname].to_masked_array()[:, array_num]]
        else:
            if len(input_xarray['latitude'].shape) == 2:
                lons = input_xarray['longitude'].to_masked_array()
                lats = input_xarray['latitude'].to_masked_array()
            else:
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

    interp_data = interp_kd_tree(vars_to_interp,
                                 area_def,
                                 data_box_definition,
                                 float(roi),
                                 interp_type='nearest')

    from geoips.data_manipulations.info import percent_unmasked

    for arr, orig, varname in zip(interp_data, vars_to_interp, varlist):
        LOG.info('%s min/max before: %s to %s', varname, orig.min(), orig.max())
        LOG.info('%s min/max after:  %s to %s', varname, arr.min(), arr.max())
        LOG.info('%s Percent unmasked before %s', varname, percent_unmasked(orig))
        LOG.info('%s Percent unmasked after  %s', varname, percent_unmasked(arr))

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
