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

# Python Standard Libraries
import logging
import os
from datetime import datetime

LOG = logging.getLogger(__name__)

reader_type = 'standard'


def mimic_netcdf(fnames, metadata_only=False, chans=None, area_def=None, self_register=False):
    ''' Read TPW MIMIC data from a list of filenames.

    All GeoIPS 2.0 readers read data into xarray Datasets - a separate
    dataset for each shape/resolution of data - and contain standard metadata information.

    <xarray.Dataset>
    Dimensions:             (lat: 721, lon: 1440)
    Dimensions without coordinates: lat, lon
    Data variables:
        lonArr              (lon) float32 ...
        latArr              (lat) float32 ...
        tpwGrid             (lat, lon) float32 ...
        tpwGridPrior        (lat, lon) float32 ...
        tpwGridSubseq       (lat, lon) float32 ...
        timeAwayGridPrior   (lat, lon) timedelta64[ns] ...
        timeAwayGridSubseq  (lat, lon) timedelta64[ns] ...
        footGridPrior       (lat, lon) float32 ...
        footGridSubseq      (lat, lon) float32 ...
        satGridPrior        (lat, lon) uint8 ...
        satGridSubseq       (lat, lon) uint8 ...


    Args:
        fnames (list): List of strings, full paths to files
        metadata_only (Optional[bool]):
            * DEFAULT False
            * return before actually reading data if True
        chans (Optional[list of str]):
            * NOT IMPLEMENTED
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

    fname = fnames[0]

    import xarray
    xobj = xarray.open_dataset(fname)

    [date,time,ext] = os.path.basename(fname).split('.')
    dt = datetime.strptime(date+time,'comp%Y%m%d%H%M%S')
    xobj.attrs['data_provider'] = 'cimss'

    xobj.attrs['start_datetime'] = dt
    xobj.attrs['end_datetime'] = dt
    xobj.attrs['platform_name'] = 'tpw'
    xobj.attrs['filename_datetimes'] = [dt]
    xobj.attrs['source_name'] = 'mimic'
    # ~2km for data_fine
    xobj.attrs['sample_distance_km'] = 110.0 * abs(xobj.variables['latArr'][1].data - xobj.variables['latArr'][0].data)
    xobj.attrs['interpolation_radius_of_influence'] = xobj.attrs['sample_distance_km'] * 1000.0 * 1.5
    if metadata_only is True:
        return {'METADATA': xobj}

    LOG.info('Obtaining lat/lon from xarray')
    # Meshgrid requires Latitude and Longitude at once, so don't put in loop
    lat = xobj.variables['latArr'][...]
    lon = xobj.variables['lonArr'][...]

    LOG.info('Calculating full lat/lon grid')
    import numpy
    lon_final, lat_final = numpy.meshgrid(lon,lat)

    LOG.info('Adding lat grid to xarray')
    xobj['latitude'] = xarray.DataArray(numpy.ma.array(lat_final), dims=('lat', 'lon'))
    LOG.info('Adding lon grid to xarray')
    xobj['longitude'] =  xarray.DataArray(numpy.ma.array(lon_final), dims=('lat', 'lon'))
    xobj = xobj.drop('latArr')
    xobj = xobj.drop('lonArr')
    xobj['tpw'] = xobj['tpwGrid']

    return {'MIMIC': xobj,
            'METADATA': xobj[[]]}
