# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Read IMERG rainfall data.

A reader is designed to import IMERG rainfall data for GeoIPS using only
python libraries

Aug 17, 2020

for a IMERG 30min data file, the time is the start time of a 30min interval:
    0000-0030-0100-0130-0200 ....

Dataset information::

    Spatial resolution is 0.1 deg.
    1st grid is at (-179.95, -89.95).
    Last grid is at (175.95, 89.95)
    variable array is (3600,1800)

     metadata['top']['dataprovider'] = 'NASA-GPM'

     dataset_info = { 'Grid': {'MWtime': 'HQobservationTime',
                               'MWid': 'HQprecipSource',
                               'MWrr': 'HQprecipitation',
                               'IRweight': 'IRkalmanFilterWeight',
                               'IRrr': 'IRprecipitation',
                               'rain': 'precipitationCal',
                               'rrQC': 'precipitationQualityIndex',
                               'rrUncal': 'precipitationUncal',
                               'rrProb': 'probabilityLiquidPrecipitation',
                               'rrErr': 'randomError',},
              }
"""
# Python Standard Libraries
from datetime import datetime, timedelta
import logging
from os.path import basename

# Third-Party Libraries
import h5py
import matplotlib
import numpy as np
import xarray as xr

matplotlib.use("agg")

LOG = logging.getLogger(__name__)

interface = "readers"
family = "standard"
name = "imerg_hdf5"
source_names = ["imerg"]


def call(fnames, metadata_only=False, chans=None, area_def=None, self_register=False):
    """Read IMERG hdf5 rain rate data products.

    Parameters
    ----------
    fnames : list
        * List of strings, full paths to files
    metadata_only : bool, default=False
        * NOT YET IMPLEMENTED
        * Return before actually reading data if True
    chans : list of str, default=None
        * NOT YET IMPLEMENTED
        * List of desired channels (skip unneeded variables as needed).
        * Include all channels if None.
    area_def : pyresample.AreaDefinition, default=None
        * NOT YET IMPLEMENTED
        * Specify region to read
        * Read all data if None.
    self_register : str or bool, default=False
        * NOT YET IMPLEMENTED
        * register all data to the specified dataset id (as specified in the
          return dictionary keys).
        * Read multiple resolutions of data if False.

    Returns
    -------
    dict of xarray.Datasets
        * dictionary of xarray.Dataset objects with required Variables and
          Attributes.
        * Dictionary keys can be any descriptive dataset ids.

    See Also
    --------
    :ref:`xarray_standards`
        Additional information regarding required attributes and variables
        for GeoIPS-formatted xarray Datasets.
    """
    fname = fnames[0]

    LOG.info("Reading file %s", fname)

    def get_header_info(header, field):
        head = header.split(";\n")
        for ii in head:
            if field in ii:
                fld, val = ii.split("=")
                return val
        return None

    # open one input imerg hdf5 file

    fileobj = h5py.File(str(fname), mode="r")

    # header = fileobj.attrs['FileHeader']
    # start_time =get_header_info(header,'StartGranuleDateTime')
    #             '2011-07-18T01:00:00.000Z'
    # end_time   =get_header_info(header,'StopGranuleDateTime')
    #             '2011-07-18T01:29:59.999Z'

    # get the time info from inport file name
    # date_yrmody       = os.path.basename(fname).split('-')[1].split('.')[-1]
    # date_hhmmse_start = os.path.basename(fname).split('-')[2][1:7]
    # date_hhmmse_end   = os.path.basename(fname).split('-')[3][1:7]

    # start_time = date_yrmody + date_hhmmse_start
    # end_time   = date_yrmody + date_hhmmse_end

    # get imerg variables
    if hasattr(fileobj["Grid"]["lat"], "value"):
        # Older versions of h5py - 2.10.0
        lat = fileobj["Grid"]["lat"].value  # (1800)
        lon = fileobj["Grid"]["lon"].value  # (3600)

        rain = fileobj["Grid"]["precipitationCal"].value  # (1,3600,1800)
        rrProb = fileobj["Grid"][
            "probabilityLiquidPrecipitation"
        ].value  # (1,3600,1800)
        rrErr = fileobj["Grid"]["randomError"].value  # (1,3600,1800)
        IRrr = fileobj["Grid"]["IRprecipitation"].value  # (1,3600,1800)
    else:
        # Newer versions of h5py - 3.2.1
        lat = fileobj["Grid"]["lat"][:]  # (1800)
        lon = fileobj["Grid"]["lon"][:]  # (3600)

        rain = fileobj["Grid"]["precipitationCal"][:]  # (1,3600,1800)
        rrProb = fileobj["Grid"]["probabilityLiquidPrecipitation"][:]  # (1,3600,1800)
        rrErr = fileobj["Grid"]["randomError"][:]  # (1,3600,1800)
        IRrr = fileobj["Grid"]["IRprecipitation"][:]  # (1,3600,1800)

    lat_2d, lon_2d = np.meshgrid(lat, lon)  # (3600,1800)

    # take out the fake additional array of 3d_array (actually 2D array),
    # i.e., delete the "1" array of above variables
    rain = np.squeeze(rain)
    rrProb = np.squeeze(rrProb)
    rrErr = np.squeeze(rrErr)
    IRrr = np.squeeze(IRrr)

    start_dt = datetime.utcfromtimestamp(fileobj["Grid"]["time"][...][0])
    end_dt = start_dt + timedelta(
        minutes=int(fileobj["Grid"]["HQobservationTime"][...].max())
    )

    # close the h5 object
    fileobj.close()

    #          ------  setup xarray variables   ------
    # since IMERG time is fixed for 30 minutes, time is not needed. only
    # start_time and end_time needed.

    # namelist_gmi  = ['latitude', 'longitude', 'rain', 'rrProb', 'rrErr','IRrr']

    # setup xarray for IMERG fields
    xarray_imerg = xr.Dataset()
    xarray_imerg["latitude"] = xr.DataArray(lat_2d)
    xarray_imerg["longitude"] = xr.DataArray(lon_2d)
    xarray_imerg["rain"] = xr.DataArray(rain)
    xarray_imerg["rrProb"] = xr.DataArray(rrProb)
    xarray_imerg["rrErr"] = xr.DataArray(rrErr)
    xarray_imerg["IRrr"] = xr.DataArray(IRrr)

    # setup attributors
    # xarray_imerg.attrs['start_datetime'] = datetime.strptime(start_time,
    #                                                          '%Y%m%d%H%M%S')
    xarray_imerg.attrs["start_datetime"] = start_dt
    # xarray_imerg.attrs['end_datetime']   = datetime.strptime(end_time,'%Y%m%d%H%M%S')
    xarray_imerg.attrs["end_datetime"] = end_dt
    xarray_imerg.attrs["source_name"] = "imerg"
    xarray_imerg.attrs["platform_name"] = "GPM"
    xarray_imerg.attrs["data_provider"] = "NASA"
    xarray_imerg.attrs["source_file_names"] = [basename(fname)]

    # MTIFs need to be "prettier" for PMW products, so 2km resolution for final image
    xarray_imerg.attrs["sample_distance_km"] = 2
    xarray_imerg.attrs["interpolation_radius_of_influence"] = 15000

    return {"IMERG": xarray_imerg, "METADATA": xarray_imerg[[]]}
