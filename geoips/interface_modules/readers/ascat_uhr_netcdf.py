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

'''Read derived surface winds from SAR, SMAP, SMOS, and AMSR netcdf data.'''
import logging
from os.path import basename
LOG = logging.getLogger(__name__)

MS_TO_KTS = 1.94384
DEG_TO_KM = 111.321

reader_type = 'standard'


def read_byu_data(wind_xarray):
    ''' Reformat ascat xarray object appropriately
            variables: latitude, longitude, timestamp, wind_speed_kts, wind_dir_deg_met
            attributes: source_name, platform_name, data_provider, interpolation_radius_of_influence'''

    if 'L2B_filename' in wind_xarray.attrs and 'metopa' in wind_xarray.L2B_filename:
        wind_xarray.attrs['source_name'] = 'ascatuhr'
        wind_xarray.attrs['platform_name'] = 'metop-a'
    elif 'L2B_filename' in wind_xarray.attrs and 'metopb' in wind_xarray.L2B_filename:
        wind_xarray.attrs['source_name'] = 'ascatuhr'
        wind_xarray.attrs['platform_name'] = 'metop-b'
    elif 'L2B_filename' in wind_xarray.attrs and 'metopc' in wind_xarray.L2B_filename:
        wind_xarray.attrs['source_name'] = 'ascatuhr'
        wind_xarray.attrs['platform_name'] = 'metop-c'
    elif 'SZF_filenames' in wind_xarray.attrs and 'M02' in wind_xarray.SZF_filenames:
        wind_xarray.attrs['source_name'] = 'ascatuhr'
        wind_xarray.attrs['platform_name'] = 'metop-a'
    elif 'SZF_filenames' in wind_xarray.attrs and 'M01' in wind_xarray.SZF_filenames:
        wind_xarray.attrs['source_name'] = 'ascatuhr'
        wind_xarray.attrs['platform_name'] = 'metop-b'
    elif 'SZF_filenames' in wind_xarray.attrs and 'M03' in wind_xarray.SZF_filenames:
        wind_xarray.attrs['source_name'] = 'ascatuhr'
        wind_xarray.attrs['platform_name'] = 'metop-c'

    import os
    # Store the storm names lower case - only reference to it is in the filename..
    storm_name = os.path.basename(wind_xarray.original_source_filenames[0]).split('_')[3].lower()
    expected_yymmdd = os.path.basename(wind_xarray.original_source_filenames[0]).split('_')[4]
    expected_hhmn = os.path.basename(wind_xarray.original_source_filenames[0].replace('.WRave3.nc',
                                                                                      '').replace('.avewr.nc',
                                                                                                  '')).split('_')[5]
    # from IPython import embed as shell; shell()
    wind_xarray.attrs['storms_with_coverage'] = [storm_name]
    from datetime import datetime
    wind_xarray.attrs['expected_synoptic_time'] = datetime.strptime(expected_yymmdd + expected_hhmn, '%y%m%d%H%M')

    import numpy
    import xarray

    dsname = 'DATA'
    if 'wspeeds' in wind_xarray.variables:
        wind_xarray['wind_speed_kts'] = xarray.where(wind_xarray.ambiguity_select == 1,
                                                     wind_xarray.wspeeds[:, :, 0],
                                                     numpy.nan)
        wind_xarray['wind_speed_kts'] = xarray.where(wind_xarray.ambiguity_select == 2,
                                                     wind_xarray.wspeeds[:, :, 1],
                                                     wind_xarray.wind_speed_kts)
        wind_xarray['wind_speed_kts'] = xarray.where(wind_xarray.ambiguity_select == 3,
                                                     wind_xarray.wspeeds[:, :, 2],
                                                     wind_xarray.wind_speed_kts)
        wind_xarray['wind_speed_kts'] = xarray.where(wind_xarray.ambiguity_select == 4,
                                                     wind_xarray.wspeeds[:, :, 3],
                                                     wind_xarray.wind_speed_kts)
        wind_xarray['wind_speed_kts'] = wind_xarray['wind_speed_kts'] * MS_TO_KTS

        wind_xarray['wind_dir_deg_met'] = xarray.where(wind_xarray.ambiguity_select == 1,
                                                       wind_xarray.wdirs[:, :, 0],
                                                       numpy.nan)
        wind_xarray['wind_dir_deg_met'] = xarray.where(wind_xarray.ambiguity_select == 2,
                                                       wind_xarray.wdirs[:, :, 1],
                                                       wind_xarray.wind_dir_deg_met)
        wind_xarray['wind_dir_deg_met'] = xarray.where(wind_xarray.ambiguity_select == 3,
                                                       wind_xarray.wdirs[:, :, 2],
                                                       wind_xarray.wind_dir_deg_met)
        wind_xarray['wind_dir_deg_met'] = xarray.where(wind_xarray.ambiguity_select == 4,
                                                       wind_xarray.wdirs[:, :, 3],
                                                       wind_xarray.wind_dir_deg_met)
        # Set wind_speed_kts appropriately
        wind_xarray['wind_speed_kts'].attrs = wind_xarray['wspeeds'].attrs.copy()
        wind_xarray['wind_speed_kts'].attrs['units'] = 'kts'
        wind_xarray['wind_speed_kts'].attrs['long_name'] = wind_xarray['wspeeds'].attrs['long_name'].replace(
            'ambiguities', 'ambiguity selection')

        wind_xarray['wind_dir_deg_met'].attrs = wind_xarray['wdirs'].attrs.copy()

        # Set lat/lons/timestamp appropriately
        wind_xarray = wind_xarray.rename({'wspeeds': 'wind_speed_ambiguities_kts',
                                          'wdirs': 'wind_dir_ambiguities_deg_met'})
        wind_xarray['wind_speed_ambiguities_kts'] = wind_xarray['wind_speed_ambiguities_kts'] * MS_TO_KTS

        wind_xarray['latitude'] = xarray.where(wind_xarray.ambiguity_select == 0,
                                               numpy.nan,
                                               wind_xarray.latitude) - 90

        wind_xarray['longitude'] = xarray.where(wind_xarray.ambiguity_select == 0,
                                                numpy.nan,
                                                wind_xarray.longitude)
        dsname = 'WINDSPEED'
    else:
        # bad vals where sigma 0 is -99.0
        wind_xarray['latitude'] = xarray.where(wind_xarray.sig_fore < -98.0,
                                               numpy.nan,
                                               wind_xarray.latitude) - 90

        wind_xarray['latitude'] = xarray.where(wind_xarray.latitude < -90.0,
                                               numpy.nan,
                                               wind_xarray.latitude)

        wind_xarray['longitude'] = xarray.where(wind_xarray.sig_fore < -98.0,
                                                numpy.nan,
                                                wind_xarray.longitude)
        dsname = 'SIGMA'
        wind_xarray['sigma0_mean'] = (wind_xarray['sig_fore'] + wind_xarray['sig_aft'] + wind_xarray['sig_mid']) / 3

    from datetime import datetime
    from numpy import datetime64
    startdt = datetime.strptime(wind_xarray.SZF_start_time[:-1], '%Y%m%d%H%M%S')
    enddt = datetime.strptime(wind_xarray.SZF_stop_time[:-1], '%Y%m%d%H%M%S')
    middt = startdt + (enddt - startdt) / 2
    timearray = numpy.ma.array(numpy.zeros(shape=wind_xarray.latitude.shape).astype(int) + datetime64(middt))
    wind_xarray['timestamp'] = xarray.DataArray(timearray,
                                                name='timestamp',
                                                coords=wind_xarray['latitude'].coords)
    wind_xarray = wind_xarray.set_coords(['timestamp'])

    return {dsname: wind_xarray}


def ascat_uhr_netcdf(fnames, metadata_only=False, chans=None, area_def=None, self_register=False):
    ''' Read ASCAT UHR derived winds or normalized radar cross section from netcdf data.

    All GeoIPS 2.0 readers read data into xarray Datasets - a separate
    dataset for each shape/resolution of data - and contain standard metadata information.

    Args:
        fnames (list): List of strings, full paths to files
        metadata_only (Optional[bool]):
            * DEFAULT False
            * return before actually reading data if True
        chans (Optional[list of str]):
            * NOT YET IMPLEMENTED
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
        list of xarray.Datasets: list of xarray.Dataset objects with required
            Variables and Attributes: (See geoips/docs :doc:`xarray_standards`)
    '''

    from geoips.xarray_utils.timestamp import get_min_from_xarray_timestamp, get_max_from_xarray_timestamp
    import xarray
    # Only SAR reads multiple files
    fname = fnames[0]
    wind_xarray = xarray.open_dataset(str(fname))
    wind_xarray.attrs['source_name'] = 'unknown'
    wind_xarray.attrs['platform_name'] = 'unknown'

    wind_xarray.attrs['original_source_filenames'] = [basename(fname)]
    wind_xarray.attrs['interpolation_radius_of_influence'] = 20000
    # 1.25km grid, 4km accuracy
    wind_xarray.attrs['sample_distance_km'] = 4
    wind_xarray.attrs['data_provider'] = 'byu'
    wind_xarray.attrs['minimum_coverage'] = 20

    LOG.info('Read data from %s', fname)

    if hasattr(wind_xarray, 'institution') and 'Brigham Young University' in wind_xarray.institution:
        wind_xarrays = read_byu_data(wind_xarray)

    for wind_xarray in wind_xarrays.values():

        LOG.info('Setting standard metadata')
        wind_xarray.attrs['start_datetime'] = get_min_from_xarray_timestamp(wind_xarray, 'timestamp')
        wind_xarray.attrs['end_datetime'] = get_max_from_xarray_timestamp(wind_xarray, 'timestamp')

        if 'wind_speed_kts' in wind_xarray.variables:
            # These text files store wind speeds natively in kts
            wind_xarray['wind_speed_kts'].attrs['units'] = 'kts'

        LOG.info('Read data %s start_dt %s source %s platform %s data_provider %s roi %s native resolution',
                 wind_xarray.attrs['start_datetime'],
                 wind_xarray.attrs['source_name'],
                 wind_xarray.attrs['platform_name'],
                 wind_xarray.attrs['data_provider'],
                 wind_xarray.attrs['interpolation_radius_of_influence'],
                 wind_xarray.attrs['sample_distance_km'])

    wind_xarrays['METADATA'] = wind_xarray[[]]
    if wind_xarrays['METADATA'].start_datetime == wind_xarrays['METADATA'].end_datetime:
        # Use alternate attributes to set start and end datetime
        from datetime import datetime
        wind_xarrays['METADATA'].attrs['start_datetime'] = datetime.strptime(
            wind_xarray.SZF_start_time, '%Y%m%d%H%M%SZ')
        wind_xarrays['METADATA'].attrs['end_datetime'] = datetime.strptime(wind_xarray.SZF_stop_time, '%Y%m%d%H%M%SZ')

    return wind_xarrays
