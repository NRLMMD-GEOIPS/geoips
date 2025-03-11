# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Read AMSU-B and MHS MIRS NetCDF data files.

This reader is desgined for importing the Advanced Microwave Sounding Unit
(AMSU)-B/Microwave Humidity Sounder (HMS) and EUMETSAQT MHS data files in
hdf5 from NOAA MIRS. These new data files have a different file name convention
and and data structure from previous MSPPS.  Example of MIRIS files:

* NPR-MIRS-IMG_v11r4_ma1_s202101111916000_e202101112012000_c202101112047200.nc

    * (ma1 is for metop-B)
* NPR-MIRS-IMG_v11r4_ma2_s202101111715000_e202101111857000_c202101111941370.nc

    * (ma2 is for metop-A)
* NPR-MIRS-IMG_v11r4_n19_s202101111730000_e202101111916000_c202101112001590.nc

    * (NOAA-19)

AMSU-A channel information::

    Chan# / Freq(GHz) / bands / Bandwidth(MHz) / Beamwidth(deg) / NE#T(K) /
                               (Spec.) Polarization at nadir / Instrument Component
    1	23.800	1	270	3.3	0.30	V	A2
    2	31.400	1	180	3.3	0.30	V	A2
    3	50.300	1	180	3.3	0.40	V	A1-2
    4	52.800	1	400	3.3	0.25	V	A1-2
    5	53.596 +-115	2	170	3.3	0.25	H	A1-2
    6	54.400	1	400	3.3	0.25	H	A1-1
    7	54.940	1	400	3.3	0.25	V	A1-1
    8	55.500	1	330	3.3	0.25	H	A1-2
    9	f0=57,290.344	1	330	3.3	0.25	H	A1-1
    10	f0+-217	2	78	3.3	0.40	H	A1-1
    11	f0+-322.2+-48	4	36	3.3	0.40	H	A1-1
    12	f0+-322.2+-22	4	16	3.3	0.60	H	A1-1
    13	f0+-322.2+-10	4	8	3.3	0.80	H	A1-1
    14	f0+-322.2+-4.5	4	3	3.3	1.20	H	A1-1
    15	89,000	1	<6,000	3.3	0.50	V	A1-1

AMSU-B/MHS channel information::

    Channel / Centre Frequency (GHz) / Bandwidth (MHz) / NeDT (K) /
                                     Calibration Accuracy (K) / pol. angle (degree)
    16	89.0	<6000	1.0	1.0	90-q                  (Vertical pol)
    17	150	<4000	1.0	1.0	90-q                  (Vertical)
    18	183.31+-1.00	500	1.1	1.0	nospec        (Horizontal)
    19	183.31+-3.00	1000	1.0	1.0	nospec        (Horizontal)
    20	190.31+17.00	2000	1.2	1.0	90-q          (Vertical)

Since AMSU-A sensor is no longer available, we select only the AMSU-B/MHS
channels. We decide to use the same names of the five channels used for previous
NOAA MSPPS data files. i.e., select frequench index 15-19 (start from 0).

V1.0:  Initial version, NRL-MRY, January 26, 2021

Dataset information::

    Basic information on AMSU-B product file
    index: 1     2    3    4      5      6    7
    freq: 23.8,31.4,50.3,52.799,53.595,54.4,54.941,
    55.499,57.29,57.29,57.29,57.29,57.29,57.29,
    index:   8     9      10    11   12   13     14
    freq: 55.499,57.29,57.29,57.29,57.29,57.29,57.29,
    index: 15  16  17    18      19     20
    freq: 89.,89.,157.,183.311,183.311,190.311

    dimensions:
          Scanline = 2370 ;
          Field_of_view = 90 ;
          P_Layer = 100 ;
          Channel = 20 ;
          Qc_dim = 4 ;
    variables:
          Freq(Channel): Central Frequencies (GHz)
          Polo(Channel): Polarizations
          ScanTime_year(Scanline): Calendar Year 20XX
          ScanTime_doy(Scanline: julian day 1-366
          ScanTime_month(Scanline): Calendar month 1-12
          ScanTime_dom(Scanline): Calendar day of the month 1-31
          ScanTime_hour(Scanline: hour of the day 0-23
          ScanTime_minute(Scanline): minute of the hour 0-59
          ScanTime_second(Scanline): second of the minute 0-59
          ScanTime_UTC(Scanline): Number of seconds since 00:00:00 UTC
          Orb_mode(Scanline): 0-ascending,1-descending
          Latitude(Scanline, Field_of_view):Latitude of the view (-90,90),
                                            unit: degree
          Longitude(Scanline, Field_of_view):Longitude of the view (-180,180),
                                             unit: degree
          Sfc_type(Scanline, Field_of_view):type of surface:0-ocean,1-sea ice,
                                            2-land,3-snow
          Atm_type(Scanline, Field_of_view): type of atmosphere:currently missing
                                          ( note: not needed for geoips products)
          Qc(Scanline, Field_of_view, Qc_dim): Qc: 0-good, 1-usable with problem,
                                                   2-bad
          ChiSqr(Scanline, Field_of_view): Convergence rate: <3-good,>10-bad
          LZ_angle(Scanline, Field_of_view): Local Zenith Angle degree
          RAzi_angle(Scanline, Field_of_view):Relative Azimuth Angle 0-360 degree
          SZ_angle(Scanline, Field_of_view):Solar Zenith Angle (-90,90) degree
          BT(Scanline, Field_of_view, Channel): Channel Temperature (K)
          YM(Scanline, Field_of_view, Channel): UnCorrected Channel Temperature(K)
          ChanSel(Scanline, Field_of_view, Channel):Channels Selection Used in
                                                    Retrieval
          TPW(Scanline, Field_of_view): Total Precipitable Water (mm)
          CLW(Scanline, Field_of_view):Cloud liquid Water (mm)
          RWP(Scanline, Field_of_view): Rain Water Path (mm)
          LWP(Scanline, Field_of_view): Liquid Water Path (mm)
          SWP(Scanline, Field_of_view): Snow Water Path (mm)
          IWP(Scanline, Field_of_view): Ice Water Path (mm)
          GWP(Scanline, Field_of_view): Graupel Water Path (mm)
          RR(Scanline, Field_of_view): Rain Rate (mm/hr)
          Snow(Scanline, Field_of_view): Snow Cover (range: 0-1) i.e., 1 -> 100%
          SWE(Scanline, Field_of_view): Snow Water Equivalent (cm)
          SnowGS(Scanline, Field_of_view):Snow Grain Size (mm)
          SIce(Scanline, Field_of_view):Sea Ice Concentration (%)
          SIce_MY(Scanline, Field_of_view): Multi-Year Sea Ice Concentration (%)
          SIce_FY(Scanline, Field_of_view): First-Year Sea Ice Concentration (%)
          TSkin(Scanline, Field_of_view): Skin Temperature (K)
          SurfP(Scanline, Field_of_view): Surface Pressure (mb)
          Emis(Scanline, Field_of_view, Channel):Channel Emissivity
                                          (unit:1,  Emis:scale_factor = 0.0001)
          SFR(Scanline, Field_of_view): Snow Fall Rate in mm/hr
          CldTop(Scanline, Field_of_view): Cloud Top Pressure (scale_factor = 0.1)
          CldBase(Scanline, Field_of_view): Cloud Base Pressure
                                            (scale_factor = 0.1)
          CldThick(Scanline, Field_of_view): Cloud Thickness (scale_factor = 0.1)
          PrecipType(Scanline, Field_of_view): Precipitation Type (Frozen/Liquid)
          RFlag(Scanline, Field_of_view): Rain Flag
          SurfM(Scanline, Field_of_view): Surface Moisture (scale_factor = 0.1)
          WindSp(Scanline, Field_of_view): Wind Speed (m/s) (scale_factor = 0.01
          WindDir(Scanline, Field_of_view: Wind Direction (scale_factor = 0.01)
          WindU(Scanline, Field_of_view):U-direction Wind Speed (m/s)
                                        (scale_factor = 0.01)
          WindV(Scanline, Field_of_view: V-direction Wind Speed (m/s)
                                        (scale_factor = 0.01)
          Prob_SF(Scanline, Field_of_view): Probability of falling snow (%)

Additional info::

    Variables (nscan, npix):  npix=90 pixels per scan; nscan: vary with orbit
    chan-1 AT:  89 GHz              as ch16    anttenna temperature at V-pol
                                               FOV 16km at nadir
    chan-2 AT:  150 (157) GHz       as ch17 the number in bracket is for MHS
                                           from metops at V-pol, 16km at nadir
    chan-3 AT:  183.31 +-1 GHz          as ch18    at H-pol, 16km
    chan-4 AT:  183.31 +-3 GHz          as ch19    at H-pol, 16km
    chan-5 AT:  183.31 +-7 (190.3) GHz  as ch20    at V-pol, 16km
    lat:     -90, 90     deg
    lon:     -180, 180   deg
    RR:  surface rainrate (mm/hr)
    Snow: surafce snow cover
    IWP:  ice water path
    SWE:  snow water equvelent
    Sfc_type:  surface type
    Orbit_mode:   -1: ascending, 1: decending, 2: both
    SFR:  snowfall rate (unit?)
    LZ_angle:  local zinath angle (deg)
    SZ_angle:  solar zinath angle (deg)
"""
# Python Standard Libraries
from datetime import datetime
import logging
import os

# Third-Party Libraries
import h5py
import matplotlib
import numpy as np
import pandas as pd
import xarray as xr


matplotlib.use("agg")

LOG = logging.getLogger(__name__)

# Selected variables for TC products (add more if needed)
VARLIST = [
    "BT",
    "Latitude",
    "Longitude",
    "Freq",
    "RR",
    "TPW",
    "CLW",
    "RWP",
    "LWP",
    "SWP",
    "IWP",
    "GWP",
    "Snow",
    "SWE",
    "SIce",
    "SIce_MY",
    "SIce_FY",
    "TSkin",
    "SurfP",
    "Emis",
    "Sfc_type",
    "SFR",
    "CldTop",
    "CldBase",
    "CldThick",
    "WindSp",
    "WindDir",
    "WindU",
    "WindV",
    "LZ_angle",
    "RAzi_angle",
    "SZ_angle",
    "ScanTime_UTC",
    "ScanTime_second",
    "Orb_mode",
    "ScanTime_year",
    "ScanTime_doy",
    "ScanTime_month",
    "ScanTime_dom",
    "ScanTime_hour",
    "ScanTime_minute",
]

interface = "readers"
family = "standard"
name = "amsub_mirs"
source_names = ["amsu-b"]


def call(fnames, metadata_only=False, chans=None, area_def=None, self_register=False):
    """Read AMSU/MHS MIRS data products.

    Parameters
    ----------
    fnames : list
        * List of strings, full paths to files
    metadata_only : bool, default=False
        * Return before actually reading data if True
    chans : list of str, default=None
        * List of desired channels (skip unneeded variables as needed).
        * Include all channels if None.
    area_def : pyresample.AreaDefinition, default=None
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
    xarrays = []
    for fname in fnames:
        LOG.info("Reading file %s", fname)

        #     check for right input AMSU-B/MHS data file
        data_name = os.path.basename(fname).split("_")[-1].split(".")[-1]

        if data_name != "nc":
            LOG.info("Warning: wrong AMSU-B/MHS data type:  data_type=", data_name)
            raise

        if "NPR-MIRS-IMG" in os.path.basename(fname):
            LOG.info("found a NOAA MIRS AMSU-B/MHS file")
        else:
            LOG.info("not a NOAA MIRS AMSU-B/MHS file: skip it")
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

        # import all data contents
        fileobj = h5py.File(fname, mode="r")

        var_all = {}

        # read-in selected variables
        for var in VARLIST:
            var_all[var] = fileobj[var]

        # values adjustment with scale_factor if there is a "scale_factor'

        for var in VARLIST:
            var_attrs = var_all[var].attrs.items()  # get attribute info
            for attrs in var_attrs:  # loop attribute tuples
                if "scale_factor" in attrs[0]:
                    factor = attrs[1][0]
                    var_all[var] = var_all[var] * factor

        # Select 5 AMSU-B/MHS Channels

        Chan1_AT = var_all["BT"][:, :, 15]
        Chan2_AT = var_all["BT"][:, :, 16]
        Chan3_AT = var_all["BT"][:, :, 17]
        Chan4_AT = var_all["BT"][:, :, 18]
        Chan5_AT = var_all["BT"][:, :, 19]

        # start_time=os.path.basename(fname).split('_')[3][1:13]
        # end_time=os.path.basename(fname).split('_')[4][1:13]
        # Collect start_time and end_time of input file (one orbit) from
        # attributes - filename wrong!
        start_datetime = datetime.strptime(
            fileobj.attrs["time_coverage_start"].astype(str), "%Y-%m-%dT%H:%M:%SZ"
        )
        end_datetime = datetime.strptime(
            fileobj.attrs["time_coverage_end"].astype(str), "%Y-%m-%dT%H:%M:%SZ"
        )

        #  -------- Apply the GEOIPS framework in XARRAY data frame ----------

        LOG.info("Making full dataframe")

        # setup the time in datetime64 format
        npix = var_all["RR"].shape[1]  # pixels per scan
        nscan = var_all["RR"].shape[0]  # total scans of this file

        time_scan = np.zeros((nscan, npix))
        # take time of each scan
        for i in range(nscan):
            yr = var_all["ScanTime_year"][i]
            dy = var_all["ScanTime_doy"][i]
            hr = var_all["ScanTime_hour"][i]
            mn = var_all["ScanTime_minute"][i]
            try:
                time_scan[i:] = "%04d%03d%02d%02d" % (yr, dy, hr, mn)
            except ValueError:
                LOG.info(
                    "Could not parse time for scan line %s: YEAR=%s, DOY=%s, "
                    "HOUR=%s, MINUTE=%s",
                    i,
                    yr,
                    dy,
                    hr,
                    mn,
                )
                continue
        #          ------  setup xarray variables   ------

        # namelist_amsub  = ['latitude', 'longitude', 'Chan1_AT', 'Chan2_AT', 'Chan3_AT'
        #                    ,'Chan4_AT','Chan5_AT', 'RR','Snow','IWP','SWE','SFR',
        #                    'Sfc_type','time']

        xarray_amsub = xr.Dataset()

        # setup attributes

        # satID and start_end time from input filename (ma3 --> METOP-c?) - TBD:
        # depending on data file )
        sat_id = os.path.basename(fname).split("_")[2]
        if sat_id == "n19":
            satid = "noaa-19"
            crtm_name = "mhs_n19"
        elif sat_id == "n18":
            satid = "noaa-18"
            crtm_name = "mhs_n18"
        elif sat_id == "n20":
            satid = "noaa-20"
            crtm_name = "mhs_n20"
        elif sat_id == "ma1":
            satid = "metop-b"
            crtm_name = "mhs_metob-b"
        elif sat_id == "ma2":
            satid = "metop-a"
            crtm_name = "mhs_metop-a"
        elif sat_id == "ma3":
            satid = "metop-c"
            crtm_name = "mhs_metop-c"

        # add attributes to xarray
        xarray_amsub.attrs["start_datetime"] = start_datetime
        xarray_amsub.attrs["end_datetime"] = end_datetime
        xarray_amsub.attrs["source_name"] = "amsu-b"
        xarray_amsub.attrs["platform_name"] = satid
        xarray_amsub.attrs["crtm_name"] = crtm_name
        xarray_amsub.attrs["data_provider"] = "NOAA-nesdis"

        # MTIFs need to be "prettier" for PMW products, so 2km resolution for
        # final image.
        # xarray_amsub.attrs['sample_distance_km'] = 15
        xarray_amsub.attrs["sample_distance_km"] = 2
        xarray_amsub.attrs["interpolation_radius_of_influence"] = 30000

        if metadata_only:
            LOG.info("metadata_only requested, returning without reading data")
            return {"METADATA": xarray_amsub}

        # keep same variables from previous version of amsub reader for files from MSPPS
        xarray_amsub["latitude"] = xr.DataArray(var_all["Latitude"][()])
        xarray_amsub["longitude"] = xr.DataArray(var_all["Longitude"][()])
        xarray_amsub["Chan1_AT"] = xr.DataArray(Chan1_AT, attrs={"channel_number": 1})
        xarray_amsub["Chan2_AT"] = xr.DataArray(Chan2_AT, attrs={"channel_number": 2})
        xarray_amsub["Chan3_AT"] = xr.DataArray(Chan3_AT, attrs={"channel_number": 3})
        xarray_amsub["Chan4_AT"] = xr.DataArray(Chan4_AT, attrs={"channel_number": 4})
        xarray_amsub["Chan5_AT"] = xr.DataArray(Chan5_AT, attrs={"channel_number": 5})
        xarray_amsub["RR"] = xr.DataArray(var_all["RR"][()])
        xarray_amsub["Snow"] = xr.DataArray(var_all["Snow"][()])
        xarray_amsub["IWP"] = xr.DataArray(var_all["IWP"][()])
        xarray_amsub["SWE"] = xr.DataArray(var_all["SWE"][()])
        xarray_amsub["SFR"] = xr.DataArray(var_all["SFR"][()])
        xarray_amsub["sfcType"] = xr.DataArray(var_all["Sfc_type"][()])
        xarray_amsub["time"] = xr.DataArray(
            pd.DataFrame(time_scan).astype(int).apply(pd.to_datetime, format="%Y%j%H%M")
        )

        # add variables from MIRS file
        xarray_amsub["TPW"] = xr.DataArray(var_all["TPW"][()])
        xarray_amsub["CLW"] = xr.DataArray(var_all["CLW"][()])
        xarray_amsub["RWP"] = xr.DataArray(var_all["RWP"][()])
        xarray_amsub["GWP"] = xr.DataArray(var_all["GWP"][()])
        xarray_amsub["SIce"] = xr.DataArray(var_all["SIce"][()])
        xarray_amsub["SIce_MY"] = xr.DataArray(var_all["SIce_MY"][()])
        xarray_amsub["SIce_FY"] = xr.DataArray(var_all["SIce_FY"][()])
        xarray_amsub["TSkin"] = xr.DataArray(var_all["TSkin"][()])
        xarray_amsub["SurfP"] = xr.DataArray(var_all["SurfP"][()])
        xarray_amsub["CldTop"] = xr.DataArray(var_all["CldTop"][()])
        xarray_amsub["CldBase"] = xr.DataArray(var_all["CldBase"][()])
        xarray_amsub["CldThick"] = xr.DataArray(var_all["CldThick"][()])
        xarray_amsub["WindSp"] = xr.DataArray(var_all["WindSp"][()])
        xarray_amsub["WindDir"] = xr.DataArray(var_all["WindDir"][()])
        xarray_amsub["WindU"] = xr.DataArray(var_all["WindU"][()])
        xarray_amsub["WindV"] = xr.DataArray(var_all["WindV"][()])
        xarray_amsub["satellite_zenith_angle"] = xr.DataArray(var_all["LZ_angle"][()])
        xarray_amsub["SZ_angle"] = xr.DataArray(var_all["SZ_angle"][()])
        xarray_amsub["RAzi_angle"] = xr.DataArray(var_all["RAzi_angle"][()])
        # from amsub_mhs_prep/oned_innov.f90:
        beam_pos = np.broadcast_to(
            np.arange(fileobj["Field_of_view"].size) + 1, var_all["LZ_angle"][()].shape
        )
        xarray_amsub["sensor_scan_angle"] = xr.DataArray((beam_pos - 45.5) * 10.0 / 9.0)

        xarrays.append(xarray_amsub)

    final_xarray = xr.concat(xarrays, dim="dim_0")

    return {"AMSUB": final_xarray, "METADATA": final_xarray[[]]}
