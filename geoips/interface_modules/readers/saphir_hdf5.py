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

''' Read SAPHIR hdf files '''

# Python Standard Libraries
import logging
LOG = logging.getLogger(__name__)
from numpy import datetime64

reader_type = 'standard'


def saphir_hdf5(fnames, metadata_only=False, chans=None, area_def=None, self_register=False):
    ''' Read SAPHIR hdf data products.

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

    import os
    from datetime import datetime
    import numpy as np
    import pandas as pd
    import xarray as xr
    import h5py
    fname = fnames[0]
    fileobj = h5py.File(str(fname), mode='r')

    lon_obj = fileobj['ScienceData']['Longitude_Samples']
    londata = float(lon_obj.attrs['scale_factor']) * (lon_obj[...]) + float(lon_obj.attrs['add_offset'])
    lat_obj = fileobj['ScienceData']['Latitude_Samples']
    # Offset is -40.0, scale_factor is 0.01
    latdata = float(lat_obj.attrs['scale_factor']) * (lat_obj[...]) + float(lat_obj.attrs['add_offset'])

    date_time_group = fileobj['ScienceData']['Scan_FirstSampleAcqTime'][...]

    sstart_date_time_group = date_time_group[0, 0]
    # NOTE in Python 3, since h5py returns a binary string, splitting on ' ' failed, but splitting on the default
    # delimeter worked.  This appears to work on Python 2 as well.
    # sstart_date_group, sstart_time_group = sstart_date_time_group.split(' ')
    sstart_date_group, sstart_time_group = sstart_date_time_group.split()
    sstart_group_time = sstart_time_group[0:6]

    start_date_group = int(sstart_date_group)
    start_time_group = int(sstart_group_time)

    edtg = date_time_group.size - 1
    send_date_time_group = date_time_group[0, edtg]
    # NOTE in Python 3, since h5py returns a binary string, splitting on ' ' failed, but splitting on the default
    # delimeter worked.  This appears to work on Python 2 as well.
    send_date_group, send_time_group = send_date_time_group.split()
    send_group_time = send_time_group[0:6]

    end_date_group = int(send_date_group)
    end_time_group = int(send_group_time)

    incidence_angle = 0.01 * np.ma.masked_equal(fileobj['ScienceData']['IncidenceAngle_Samples'], 32767)
    ch1qf = np.ma.masked_equal(np.squeeze((fileobj['ScienceData']['QF_Samples_S1'][...])), 65535)
    ch2qf = np.ma.masked_equal(np.squeeze((fileobj['ScienceData']['QF_Samples_S2'][...])), 65535)
    ch3qf = np.ma.masked_equal(np.squeeze((fileobj['ScienceData']['QF_Samples_S3'][...])), 65535)
    ch4qf = np.ma.masked_equal(np.squeeze((fileobj['ScienceData']['QF_Samples_S4'][...])), 65535)
    ch5qf = np.ma.masked_equal(np.squeeze((fileobj['ScienceData']['QF_Samples_S5'][...])), 65535)
    ch6qf = np.ma.masked_equal(np.squeeze((fileobj['ScienceData']['QF_Samples_S6'][...])), 65535)
    ch1 = np.ma.masked_equal(np.squeeze(0.01*(fileobj['ScienceData']['TB_Samples_S1'][...])), 65535)
    ch2 = np.ma.masked_equal(np.squeeze(0.01*(fileobj['ScienceData']['TB_Samples_S2'][...])), 65535)
    ch3 = np.ma.masked_equal(np.squeeze(0.01*(fileobj['ScienceData']['TB_Samples_S3'][...])), 65535)
    ch4 = np.ma.masked_equal(np.squeeze(0.01*(fileobj['ScienceData']['TB_Samples_S4'][...])), 65535)
    ch5 = np.ma.masked_equal(np.squeeze(0.01*(fileobj['ScienceData']['TB_Samples_S5'][...])), 65535)
    ch6 = np.ma.masked_equal(np.squeeze(0.01*(fileobj['ScienceData']['TB_Samples_S6'][...])), 65535)
    scanqf = np.ma.masked_equal(np.squeeze((fileobj['ScienceData']['SAPHIR_QF_scan'][...])), 65535)

    LOG.info('Reading file %s', fname)

    # setup saphir xarray
    xarray_saphir = xr.Dataset()
    xarray_saphir['latitude'] = xr.DataArray(latdata)
    xarray_saphir['longitude'] = xr.DataArray(londata)
    xarray_saphir['IncidenceAngle'] = xr.DataArray(incidence_angle)
    xarray_saphir['scan_qf'] = xr.DataArray(scanqf)
    xarray_saphir['ch1qf_183.31_0.2'] = xr.DataArray(ch1qf)
    xarray_saphir['ch2qf_183.31_1.1'] = xr.DataArray(ch2qf)
    xarray_saphir['ch3qf_183.31_2.8'] = xr.DataArray(ch3qf)
    xarray_saphir['ch4qf_183.31_4.2'] = xr.DataArray(ch4qf)
    xarray_saphir['ch5qf_183.31_6.8'] = xr.DataArray(ch5qf)
    xarray_saphir['ch6qf_183.31_11.0'] = xr.DataArray(ch6qf)
    xarray_saphir['ch1_183.31_0.2'] = xr.DataArray(np.ma.masked_where(ch1qf > 64, ch1))
    xarray_saphir['ch2_183.31_1.1'] = xr.DataArray(np.ma.masked_where(ch2qf > 64, ch2))
    xarray_saphir['ch3_183.31_2.8'] = xr.DataArray(np.ma.masked_where(ch3qf > 64, ch3))
    xarray_saphir['ch4_183.31_4.2'] = xr.DataArray(np.ma.masked_where(ch4qf > 64, ch4))
    xarray_saphir['ch5_183.31_6.8'] = xr.DataArray(np.ma.masked_where(ch5qf > 64, ch5))
    xarray_saphir['ch6_183.31_11.0'] = xr.DataArray(np.ma.masked_where(ch6qf > 64, ch6))
    # xarray_saphir['timestamp']=xr.DataArray(pd.DataFrame(time_scan).astype(int).apply(pd.to_datetime,format='%Y%j%H%M'))

    # add attributes to xarray 
    xarray_saphir.attrs['start_datetime'] = datetime.strptime("%08d%06d" % (start_date_group, start_time_group),
                                                              '%Y%m%d%H%M%S')
    xarray_saphir.attrs['end_datetime'] = datetime.strptime("%08d%06d" % (end_date_group, end_time_group),
                                                            '%Y%m%d%H%M%S')
    xarray_saphir.attrs['source_name'] = 'saphir'
    xarray_saphir.attrs['platform_name'] = 'meghatropiques'
    xarray_saphir.attrs['data_provider'] = 'GSFC'
    xarray_saphir.attrs['sample_distance_km'] = 10
    xarray_saphir.attrs['interpolation_radius_of_influence'] = 20000

    return {'SAPHIR': xarray_saphir,
            'METADATA': xarray_saphir[[]]}
