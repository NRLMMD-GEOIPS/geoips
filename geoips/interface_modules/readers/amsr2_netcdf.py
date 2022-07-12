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

'''Read AMSR2 data products'''
import logging
from os.path import basename
LOG = logging.getLogger(__name__)

varnames = {'Brightness_Temperature_10_GHzH': 'tb10h',
            'Brightness_Temperature_10_GHzV': 'tb10v',
            'Brightness_Temperature_18_GHzH': 'tb18h',
            'Brightness_Temperature_18_GHzV': 'tb18v',
            'Brightness_Temperature_23_GHzH': 'tb23h',
            'Brightness_Temperature_23_GHzV': 'tb23v',
            'Brightness_Temperature_36_GHzH': 'tb36h',
            'Brightness_Temperature_36_GHzV': 'tb36v',
            'Brightness_Temperature_6_GHzH': 'tb6h',
            'Brightness_Temperature_6_GHzV': 'tb6v',
            'Brightness_Temperature_7_GHzH': 'tb7h',
            'Brightness_Temperature_7_GHzV': 'tb7v',
            'Brightness_Temperature_89_GHz_AH': 'tb89hA',
            'Brightness_Temperature_89_GHz_AV': 'tb89vA',
            'Brightness_Temperature_89_GHz_BH': 'tb89hB',
            'Brightness_Temperature_89_GHz_BV': 'tb89hB',
            }
land_num = {'6': 0,
            '7': 1,
            '10': 2,
            '18': 3,
            '23': 4,
            '36': 5,
            '89A': 0,
            '89B': 1}
land_var = {'6':   'Land_Ocean_Flag_6_to_36',
            '7':   'Land_Ocean_Flag_6_to_36',
            '10':  'Land_Ocean_Flag_6_to_36',
            '18':  'Land_Ocean_Flag_6_to_36',
            '23':  'Land_Ocean_Flag_6_to_36',
            '36':  'Land_Ocean_Flag_6_to_36',
            '89A': 'Land_Ocean_Flag_89',
            '89B': 'Land_Ocean_Flag_89'}
chan_nums = {'Brightness_Temperature_6_GHzV': 1,
             'Brightness_Temperature_6_GHzH': 2,
             'Brightness_Temperature_7_GHzV': 3,
             'Brightness_Temperature_7_GHzH': 4,
             'Brightness_Temperature_10_GHzV': 5,
             'Brightness_Temperature_10_GHzH': 6,
             'Brightness_Temperature_18_GHzV': 7,
             'Brightness_Temperature_18_GHzH': 8,
             'Brightness_Temperature_23_GHzV': 9,
             'Brightness_Temperature_23_GHzH': 10,
             'Brightness_Temperature_36_GHzV': 11,
             'Brightness_Temperature_36_GHzH': 12,
             'Brightness_Temperature_89_GHz_AV': 13,
             'Brightness_Temperature_89_GHz_AH': 14,
             'Brightness_Temperature_89_GHz_BV': 13,
             'Brightness_Temperature_89_GHz_BH': 14,}
reader_type = 'standard'


def read_amsr_winds(wind_xarray):
    ''' Reformat AMSR xarray object appropriately
            variables: latitude, longitude, timestamp, wind_speed_kts
            attributes: source_name, platform_name, data_provider, interpolation_radius_of_influence'''
    MS_TO_KTS = 1.94384
    LOG.info('Reading AMSR data')
    # Set attributes appropriately
    wind_xarray.attrs['source_name'] = 'amsr2'
    wind_xarray.attrs['platform_name'] = 'gcom-w1'
    wind_xarray.attrs['interpolation_radius_of_influence'] = 10000
    # AMSR is one text file per datafile, so don't append
    wind_xarray.attrs['overwrite_text_file'] = True
    wind_xarray.attrs['append_text_file'] = False
    # https://www.ospo.noaa.gov/Products/atmosphere/gpds/about_amsr2.html
    # OCEAN Winds based on 37GHz, which is 7km x 12km ground resolution
    wind_xarray.attrs['sample_distance_km'] = 7.0
    if 'creator_name' in wind_xarray.attrs and 'NOAA' in wind_xarray.creator_name:
        wind_xarray.attrs['data_provider'] = 'star'

    # Set lat/lons appropriately
    wind_xarray = wind_xarray.rename({'Latitude_for_Low_Resolution': 'latitude',
                                      'Longitude_for_Low_Resolution': 'longitude'})
    wind_xarray = wind_xarray.set_coords(['latitude', 'longitude'])
    wind_xarray = wind_xarray.reset_coords(['Latitude_for_High_Resolution',
                                            'Longitude_for_High_Resolution'])

    # Set wind_speed_kts appropriately
    import numpy
    import xarray

    # convert to kts
    wind_xarray['wind_speed_kts'] = wind_xarray['WSPD'] * MS_TO_KTS

    # # Only keep the good wind speeds
    # wind_xarray['wind_speed_kts'] = xarray.where(wind_xarray['WSPD_QC'] == 0,
    #                                              wind_xarray['wind_speed_kts'], numpy.nan)

    wind_xarray['wind_speed_kts'].attrs = wind_xarray['WSPD'].attrs
    wind_xarray['wind_speed_kts'].attrs['units'] = 'kts'
    wind_xarray['wind_speed_kts'] = wind_xarray['wind_speed_kts'].assign_coords(latitude=wind_xarray.latitude,
                                                                                longitude=wind_xarray.longitude)

    # Set timestamp appropriately
    import pandas
    dtstrs = []
    LOG.info('Reading scan_times')
    for scan_time in wind_xarray['Scan_Time']:
        dtstrs += ['{0:04.0f}{1:02.0f}{2:02.0f}T{3:02.0f}{4:02.0f}{5:02.0f}'.format(
            *tuple([xx for xx in scan_time.values]))]
    # Have to set it on the actual xarray so it becomes a xarray format time series (otherwise if you set it
    # directly to ts, it is a pandas format time series, and expand_dims doesn't exist).
    timestamps = pandas.to_datetime(dtstrs, format='%Y%m%dT%H%M%S', errors='coerce').tolist()
    LOG.info('Setting list of times')
    tss = [timestamps for ii in range(0, wind_xarray['wind_speed_kts'].shape[1])]
    LOG.info('Setting timestamp DataArray')
    wind_xarray['timestamp'] = xarray.DataArray(data=numpy.array(tss).transpose(),
                                                coords=wind_xarray.wind_speed_kts.coords,
                                                name='timestamp')
    wind_xarray = wind_xarray.set_coords(['timestamp'])
    return {'WINDS': wind_xarray}


def read_amsr_mbt(full_xarray, varname, timestamp=None):
    ''' Reformat AMSR xarray object appropriately
            variables: latitude, longitude, timestamp, brightness temperature variables
            attributes: source_name, platform_name, data_provider, interpolation_radius_of_influence'''
    import xarray
    LOG.info('Reading AMSR data %s', varname)
    sub_xarray = xarray.Dataset()
    sub_xarray.attrs = full_xarray.attrs.copy()
    # Set attributes appropriately

    # Mappings are Brightness_Temperature_89_GHz_AH -> Latitude_for_89A, etc
    # Mappings are Brightness_Temperature_10_GHzH -> Latitude_for_10, etc
    chanstr = varname.replace('Brightness_Temperature_', '')
    chanstr = chanstr.replace('_GHz_', '')
    chanstr = chanstr.replace('_GHz', '')
    chanstr = chanstr.replace('H', '')
    chanstr = chanstr.replace('V', '')

    # Set lat/lons appropriately
    sub_xarray['latitude'] = full_xarray['Latitude_for_{0}'.format(chanstr)]
    sub_xarray['longitude'] = full_xarray['Longitude_for_{0}'.format(chanstr)]
    sub_xarray[varnames[varname]] = full_xarray[varname]
    sub_xarray[varnames[varname]].attrs['channel_number'] = chan_nums[varname]
    sub_xarray.set_coords(['latitude', 'longitude'])

    # https://www.ospo.noaa.gov/Products/atmosphere/gpds/about_amsr2.html
    # 37GHz, 7km x 12km ground resolution
    # 89GHz, 3km x 5km ground resolution

    # MTIFs need to be "prettier" for PMW products, so 2km resolution for all channels
    # sub_xarray.attrs['sample_distance_km'] = 3.0
    sub_xarray.attrs['sample_distance_km'] = 2.0
    sub_xarray.attrs['interpolation_radius_of_influence'] = 10000
    for dim in sub_xarray.dims.keys():
        if 'low_rez' in dim:
            # MTIFs need to be "prettier" for PMW products, so 2km resolution for all channels
            # sub_xarray.attrs['sample_distance_km'] = 7.0
            sub_xarray.attrs['sample_distance_km'] = 2.0
            sub_xarray.attrs['interpolation_radius_of_influence'] = 20000

    # See dictionaries above for appropriate land mask array locations for each variable
    full_xarray['LandMask'] = xarray.DataArray(full_xarray[land_var[chanstr]].to_masked_array()[
        land_num[chanstr], :, :],
                                               coords=full_xarray[varname].coords)

    if timestamp is None:
        import numpy
        # Set timestamp appropriately
        import pandas
        dtstrs = []
        LOG.info('Reading scan_times, for dims %s', sub_xarray[varnames[varname]].dims)
        for scan_time in full_xarray['Scan_Time']:
            dtstrs += ['{0:04.0f}{1:02.0f}{2:02.0f}T{3:02.0f}{4:02.0f}{5:02.0f}'.format(
                *tuple([xx for xx in scan_time.values]))]
        # Have to set it on the actual xarray so it becomes a xarray format time series (otherwise if you set it
        # directly to ts, it is a pandas format time series, and expand_dims doesn't exist).
        timestamps = pandas.to_datetime(dtstrs, format='%Y%m%dT%H%M%S', errors='coerce').tolist()
        LOG.info('    Setting list of times')
        tss = [timestamps for ii in range(0, sub_xarray[varnames[varname]].shape[1])]
        LOG.info('    Setting timestamp DataArray')
        sub_xarray['timestamp'] = xarray.DataArray(data=numpy.array(tss).transpose(),
                                                   coords=full_xarray[varname].coords,
                                                   name='timestamp')
        sub_xarray = sub_xarray.set_coords(['timestamp'])
    else:
        LOG.info('Using existing scan_times, for dims %s', sub_xarray[varnames[varname]].dims)
        sub_xarray['timestamp'] = timestamp
    from geoips.xarray_utils.timestamp import get_min_from_xarray_timestamp, get_max_from_xarray_timestamp
    sub_xarray.attrs['start_datetime'] = get_min_from_xarray_timestamp(sub_xarray, 'timestamp')
    sub_xarray.attrs['end_datetime'] = get_max_from_xarray_timestamp(sub_xarray, 'timestamp')
    return sub_xarray


def read_amsr_data(full_xarray, chans):
    full_xarray = full_xarray.reset_coords(full_xarray.coords)

    sunzen = 90 - full_xarray.Sun_Elevation
    satzen = full_xarray.Earth_Incidence_Angle
    satazm = full_xarray.Earth_Azimuth_Angle
    loqf = full_xarray.Pixel_Data_Quality_6_to_36
    hiqf = full_xarray.Pixel_Data_Quality_89
    sunglint_flag = full_xarray.Sun_Glint_Flag
    sensor_scan_angle = full_xarray.Scan_Angle
    xarrays = {}
    # Every single channel has a different set of Lat/Lons!
    for varname in full_xarray.variables:
        if chans is not None and varname not in chans:
            LOG.info('SKIPPING: Variable %s not requested in %s', varname, chans)
        if 'Brightness' in varname:
            usetimestamp = None
            for xra in list(xarrays.values()):
                if xra.timestamp.dims == full_xarray[varname].dims:
                    usetimestamp = xra.timestamp
            new_xarray = read_amsr_mbt(full_xarray, varname, usetimestamp)
            if sunzen.dims == tuple(new_xarray.dims):
                new_xarray['SatAzimuth'] = satazm
                new_xarray['SatZenith'] = satzen
                new_xarray['SunZenith'] = sunzen
                new_xarray['QualityFlag'] = loqf
                new_xarray['SunGlintFlag'] = sunglint_flag
                new_xarray['sensor_scan_angle'] = sensor_scan_angle
            elif hiqf.dims == tuple(new_xarray.dims):
                new_xarray['QualityFlag'] = hiqf
            xarrays[varname] = new_xarray
        else:
            LOG.info('SKIPPING variable %s', varname)

    return xarrays


def amsr2_netcdf(fnames, metadata_only=False, chans=None, area_def=None, self_register=False):
    ''' Read AMSR2 netcdf data products. NOTE AMSR2 OCEAN wind products are in sfc_winds_ncdf.py

    All GeoIPS 2.0 readers read data into xarray Datasets - a separate
    dataset for each shape/resolution of data - and contain standard metadata information.

    Args:
        fnames (list): List of strings, full paths to files
        metadata_only (Optional[bool]):
            * DEFAULT False
            * return before actually reading data if True
        chans (Optional[list of str]):
            * DEFAULT None (include all channels)
            * List of desired channels (skip unneeded variables as needed)
        area_def (Optional[pyresample.AreaDefinition]):
            * NOT YET IMPLEMENTED
                * DEFAULT None (read all data)
                * Specify region to read
        self_register (Optional[str]):
            * NOT YET IMPLEMENTED
                * DEFAULT False (read multiple resolutions of data)
                * register all data to the specified resolution.

    Returns:
        dict of xarray.Datasets: dict of xarray.Dataset objects with required
            Variables and Attributes: (See geoips/docs :doc:`xarray_standards`),
            dict key can be any descriptive dataset id
   '''
    import xarray
    fname = fnames[0]
    full_xarray = xarray.open_dataset(str(fname))
    full_xarray.attrs['data_provider'] = 'unknown'
    full_xarray.attrs['original_source_filenames'] = [basename(fname)]
    full_xarray.attrs['source_name'] = 'amsr2'
    full_xarray.attrs['platform_name'] = 'gcom-w1'
    full_xarray.attrs['interpolation_radius_of_influence'] = 10000
    if 'creator_name' in full_xarray.attrs and 'NOAA' in full_xarray.creator_name:
        full_xarray.attrs['data_provider'] = 'star'
    full_xarray.attrs['minimum_coverage'] = 20
    LOG.info('Read data from %s', fname)
    if metadata_only is True:
        from datetime import datetime
        full_xarray.attrs['start_datetime'] = datetime.strptime(full_xarray.attrs['time_coverage_start'][0:19],
                                                                '%Y-%m-%dT%H:%M:%S')
        full_xarray.attrs['end_datetime'] = datetime.strptime(full_xarray.attrs['time_coverage_end'][0:19],
                                                              '%Y-%m-%dT%H:%M:%S')
        LOG.info('metadata_only requested, returning without readind data')
        return {'METADATA': full_xarray}

    if hasattr(full_xarray, 'title') and 'AMSR2_OCEAN' in full_xarray.title:
        xarrays = read_amsr_winds(full_xarray)

    elif hasattr(full_xarray, 'title') and 'MBT' in full_xarray.title:
        xarrays = read_amsr_data(full_xarray, chans)

    elif hasattr(full_xarray, 'title') and 'PRECIP' in full_xarray.title:
        xarrays = read_amsr_data(full_xarray, chans)

    for dsname, curr_xarray in xarrays.items():
        LOG.info('Setting standard metadata')
        from geoips.xarray_utils.timestamp import get_min_from_xarray_timestamp, get_max_from_xarray_timestamp
        curr_xarray.attrs['start_datetime'] = get_min_from_xarray_timestamp(curr_xarray, 'timestamp')
        curr_xarray.attrs['end_datetime'] = get_max_from_xarray_timestamp(curr_xarray, 'timestamp')
    xarrays['METADATA'] = list(xarrays.values())[0][[]]
    return xarrays
