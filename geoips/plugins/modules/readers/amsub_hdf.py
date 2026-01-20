# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Read AMSU-B and MHS passive microwave data files.

This reader is desgined for importing NOAA Advanced Microwave Sounding Unit
(AMSU)-B/Microwave Humidity Sounder (HMS) and EUMETSAQT MHS data files in hdf
format, such as

* NPR.MHOP.NP.D20153.S2046.E2230.B5832021.NS (N19),
* NPR.MHOP.NN.D20153.S1927.E2105.B7748081.NS (N18),
* NPR.MHOP.M1.D20153.S2229.E2318.B3998282.NS (METOP).

 V1.0:  Initial version, NRL-MRY, June 1, 2020

Basic information on AMSU-B product file::

    Input SD Variables
    (nscan, npix):
        npix=90 pixels per scan;
        nscan: vary with orbit
    chan-1 AT:  89 GHz as ch16 anttenna temperature at V-pol   FOV 16km at nadir
    chan-2 AT:  150 (157) GHz as ch17 the number in bracket is for MHS from
                                      metops at V-pol, 16km at nadir
    chan-3 AT:  183.31 +-1 GHz as ch18    at H-pol, 16km
    chan-4 AT:  183.31 +-3 GHz as ch19    at H-pol, 16km
    chan-5 AT:  183.31 +-7 (190.3) GHz as ch20    at V-pol, 16km
    lat:     -90, 90     deg
    lon:     -180, 180   deg
    RR:  surface rainrate (mm/hr)
    Snow: surafce snow cover
    IWP:  ice water path (unit?)
    SWE:  snow water equvelent  (unit)
    Sfc_type:  surface type
    Orbit_mode:   -1: ascending, 1: decending, 2: both
    SFR:  snowfall rate (unit?)
    LZ_angle:  local zinath angle (deg)
    SZ_angle:  solar zinath angle (deg)

    Vdata info (definition of AMSU-B date):
    ScanTime_year
    ScanTime_month
    ScanTime_day
    ScanTime_hour
    ScanTime_minute
    ScanTime_second
    ScanTime_Jday
    Time
"""

# Python Standard Libraries
from datetime import datetime
import logging
import os

# Third-Party Libraries
import matplotlib
import numpy as np
import pandas as pd

# library for hdf files
from pyhdf.SD import SD, SDC
from pyhdf.VS import HC

# from pyhdf.VS import *
from pyhdf.HDF import HDF
import xarray as xr

matplotlib.use("agg")

LOG = logging.getLogger(__name__)

interface = "readers"
family = "standard"
name = "amsub_hdf"
source_names = ["amsu-b"]


def call(fnames, metadata_only=False, chans=None, area_def=None, self_register=False):
    """Read AMSU-B hdf data products.

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
    # fname='NPR.MHOP.NP.D20154.S1406.E1553.B5833031.NS'
    fname = fnames[0]

    LOG.info("Reading file %s", fname)

    #     check for right input AMSU-B/MHS data file

    data_name = os.path.basename(fname).split("_")[-1].split(".")[-1]

    if data_name != "NS":
        LOG.info("Warning: wrong AMSU-B/MHS data type:  data_type=", data_name)
        raise

    if ("NRP" and "MHOP") in os.path.basename(fname):
        LOG.info("found a AMSU-B/MHS hdf file")
    else:
        LOG.info("not a AMSU-B/MHS hdf file: skip it")
        raise

    """    ------  Notes  ------
       Read AMSU-B hdf files for 5 chan antenna temperature (AT) and asscoaited EDRs
         Then, transform these ATs and fields into xarray framework for GEOIPS
         ( AT will be corrected into brightness temperature (TB) later)

       Input Parameters:
           fname (str): input file name.  require a full path
       Returns:
           xarray.Dataset with required Variables and Attributes:
               Variables:
                        AMSUB vars:
                          'latitude', 'longitude', 'Ch1', 'Ch2', 'Ch3', 'Ch4','Ch4',
                          'RR', 'Snow','SWE','IWP','SFR' 'sfcType', 'time_scan'
               Attibutes:
                        'source_name', 'platform_name', 'data_provider',
                        'interpolation_radius_of_influence', 'start_datetime',
                        'end_datetime'
    """

    SData_ID = SD(fname, SDC.READ)
    VData_ID = HDF(fname, HC.READ).vstart()

    # get scan time info
    year = VData_ID.attach("ScanTime_year")[:]
    # month = VData_ID.attach("ScanTime_month")[:]
    # day = VData_ID.attach("ScanTime_dom")[:]
    hour = VData_ID.attach("ScanTime_hour")[:]
    minute = VData_ID.attach("ScanTime_minute")[:]
    # second = VData_ID.attach("ScanTime_second")[:]
    jday = VData_ID.attach("ScanTime_doy")[:]

    # get EDRs
    lat = SData_ID.select("Latitude").get()
    lon = SData_ID.select("Longitude").get()
    RR = SData_ID.select("RR").get()
    Snow = SData_ID.select("Snow").get()
    IWP = SData_ID.select("IWP").get()
    SWE = SData_ID.select("SWE").get()
    SFR = SData_ID.select("SFR").get()
    Sfc_type = SData_ID.select("Sfc_type").get()
    Chan1_AT = SData_ID.select("Chan1_AT").get()
    Chan2_AT = SData_ID.select("Chan2_AT").get()
    Chan3_AT = SData_ID.select("Chan3_AT").get()
    Chan4_AT = SData_ID.select("Chan4_AT").get()
    Chan5_AT = SData_ID.select("Chan5_AT").get()
    # SZ_angle = SData_ID.select("SZ_angle").get()
    # LZ_angle = SData_ID.select("LZ_angle").get()

    # Min, Max, and scale factors (using hdfview)
    # AT_min = 75.0
    # AT_max = 325.0
    # RR_min = 0.0
    # RR_max = 30.0
    # Snow_min = 0.0
    # Snow_max = 100.0
    # IWP_min = 0.0
    # IWP_max = 3.0
    # SWE_min = 0.0
    # SWE_max = 30.0
    # SFR_min = 0.03
    # SFR_max = 5.0

    AT_scale = 100.0
    RR_scale = 10.0
    Snow_scale = 1.0
    IWP_scale = 100.0
    SWE_scale = 100.0
    SFR_scale = 100.0

    # Adjust the values with scale factors

    RR = RR * RR_scale
    Snow = Snow / Snow_scale
    IWP = IWP / IWP_scale
    SWE = SWE / SWE_scale
    SFR = SFR / SFR_scale
    Chan1_AT = Chan1_AT / AT_scale
    Chan2_AT = Chan2_AT / AT_scale
    Chan3_AT = Chan3_AT / AT_scale
    Chan4_AT = Chan4_AT / AT_scale
    Chan5_AT = Chan5_AT / AT_scale

    SData_ID.end()  # close input file
    VData_ID.end()  # close input file

    #  -------- Apply the GEOIPS framework in XARRAY data frame ----------

    LOG.info("Making full dataframe")

    # setup the time in datetime64 format
    npix = RR.shape[1]  # pixels per scan
    nscan = RR.shape[0]  # total scans of this file

    time_scan = np.zeros((nscan, npix))

    for i in range(nscan):
        time_scan[i:] = "%04d%03d%02d%02d" % (
            year[i][0],
            jday[i][0],
            hour[i][0],
            minute[i][0],
        )

    #          ------  setup xarray variables   ------

    # namelist_amsub  = ['latitude', 'longitude', 'Chan1_AT', 'Chan2_AT', 'Chan3_AT',
    #                    'Chan4_AT','Chan5_AT', 'RR','Snow','IWP','SWE','SFR',
    #                    'Sfc_type','time']

    # setup amsub xarray
    xarray_amsub = xr.Dataset()
    xarray_amsub["latitude"] = xr.DataArray(lat)
    xarray_amsub["longitude"] = xr.DataArray(lon)
    xarray_amsub["Chan1_AT"] = xr.DataArray(Chan1_AT)
    xarray_amsub["Chan2_AT"] = xr.DataArray(Chan2_AT)
    xarray_amsub["Chan3_AT"] = xr.DataArray(Chan3_AT)
    xarray_amsub["Chan4_AT"] = xr.DataArray(Chan4_AT)
    xarray_amsub["Chan5_AT"] = xr.DataArray(Chan5_AT)
    xarray_amsub["RR"] = xr.DataArray(RR)
    xarray_amsub["Snow"] = xr.DataArray(Snow)
    xarray_amsub["IWP"] = xr.DataArray(IWP)
    xarray_amsub["SWE"] = xr.DataArray(SWE)
    xarray_amsub["SFR"] = xr.DataArray(SFR)
    xarray_amsub["sfcType"] = xr.DataArray(Sfc_type)
    xarray_amsub["time"] = xr.DataArray(
        pd.DataFrame(time_scan).astype(int).apply(pd.to_datetime, format="%Y%j%H%M")
    )

    # setup attributes

    # satID and start_end time from input filename (M3  --> METOP-3 ???)
    sat_id = os.path.basename(fname).split(".")[2]
    if sat_id == "NP":
        satid = "noaa-19"
    elif sat_id == "NN":
        satid = "noaa-18"
    elif sat_id == "M1":
        satid = "metop-b"
    elif sat_id == "M2":
        satid = "metop-a"
    elif sat_id == "M3":
        satid = "metop-c"

    yr = os.path.basename(fname).split(".")[3][1:3]
    jd = os.path.basename(fname).split(".")[3][3:6]
    hr = os.path.basename(fname).split(".")[4][1:3]
    mi = os.path.basename(fname).split(".")[4][3:6]
    start_time = "%02d%03d%02d%02d" % (int(yr), int(jd), int(hr), int(mi))
    hr = os.path.basename(fname).split(".")[5][1:3]
    mi = os.path.basename(fname).split(".")[5][3:6]
    end_time = "%02d%03d%02d%02d" % (int(yr), int(jd), int(hr), int(mi))

    # add attributes to xarray
    xarray_amsub.attrs["start_datetime"] = datetime.strptime(start_time, "%y%j%H%M")
    xarray_amsub.attrs["end_datetime"] = datetime.strptime(end_time, "%y%j%H%M")
    xarray_amsub.attrs["source_name"] = "amsu-b"
    xarray_amsub.attrs["platform_name"] = satid
    xarray_amsub.attrs["data_provider"] = "nesdis"

    # MTIFs need to be "prettier" for PMW products, so 2km resolution for final image
    # xarray_amsub.attrs['sample_distance_km'] = 15
    xarray_amsub.attrs["sample_distance_km"] = 2
    xarray_amsub.attrs["interpolation_radius_of_influence"] = 30000

    return {"AMSUB": xarray_amsub, "METADATA": xarray_amsub[[]]}
