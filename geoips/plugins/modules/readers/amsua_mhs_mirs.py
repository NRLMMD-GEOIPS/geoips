# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Read AMSU-A and MHS MIRS NetCDF data files.

This reader is desgined for importing the Advanced Microwave Sounding Unit
(AMSU)-A and Microwave Humidity Sounder (HMS) files made available from NOAA MIRS.
These data files have a different file name convention
and and data structure from previous MSPPS.  Example of MIRIS files:

* NPR-MIRS-IMG_v11r4_ma1_s202101111916000_e202101112012000_c202101112047200.nc

    * (ma1 is for metop-B)
* NPR-MIRS-IMG_v11r4_ma2_s202101111715000_e202101111857000_c202101111941370.nc

    * (ma2 is for metop-A)
* NPR-MIRS-IMG_v11r4_n19_s202101111730000_e202101111916000_c202101112001590.nc

    * (NOAA-19)

AMSU-B was replaced with MHS in 2005, and now AMSU-A / MHS fly on newer NOAA birds (>17)
and METOP-A/B/C (METOP-A dead now).  AMSU-A channels are still channels 1-15, and MHS
channels (1-5) live in the same 16-20 slots that previously contained AMSU-B.

More information on the AMSU and MHS instruments may be found here
https://en.wikipedia.org/wiki/Advanced_microwave_sounding_unit
https://en.wikipedia.org/wiki/Microwave_humidity_sounder

AMSU-A channel information:

Chan  Frequency                 Polarization  #Bands  Sensitivity  Primary Function
Num   (GHz)                     (at nadir)            NEDT (K)
1     23.8                      vertical      1       0.30         Water Vapor Burden
2     31.4                      vertical      1       0.30         Water Vapor Burden
3     50.3                      vertical      1       0.40         Water Vapor Burden
4     52.8                      vertical      1       0.25         Water Vapor Burden
5     53.596 ± 0.115            horizontal    2       0.25         Tropospheric Temp
6     54.4                      horizontal    1       0.25         Tropospheric Temp
7     54.94                     vertical      1       0.25         Tropospheric Temp
8     55.5                      horizontal    1       0.25         Tropospheric Temp
9     57.290                    horizontal    1       0.25         Stratospheric Temp
10    57.290 ± 0.217            horizontal    2       0.40         Stratospheric Temp
11    57.290 ± 0.3222 ± 0.048   horizontal    4       0.40         Stratospheric Temp
12    57.290 ± 0.3222 ± 0.022   horizontal    4       0.60         Stratospheric Temp
13    57.290 ± 0.3222 ± 0.010   horizontal    4       0.80         Stratospheric Temp
14    57.290 ± 0.3222 ± 0.0045  horizontal    4       1.20         Stratospheric Temp
15    89.0                      vertical      1       0.50         Cloud Top/Snow

MHS channel information:

Chan  AMSU-B  Frequency       AMSU-B         Bandwidth  Sensitivity  Polarization
Num   Chan#  (GHz)            Freq(GHz)      (MHz)      NEDT (K)     (at nadir)
1     16      89.0            89.0 ± 0.9     2800       0.22         Vertical
2     17      157.0           150 ± 0.9      2800       0.34         Vertical
3     18      183.311 ± 1.00  183.31 ± 1.00  2 x 500    0.51         Horizontal
4     19      183.311 ± 3.00  183.31 ± 3.00  2 x 1000   0.40         Horizontal
5     20      190.311         183.31 ± 7.00  2200       0.46         Vertical

V1.0:  Initial version, NRL-MRY, January 26, 2021

Dataset information::

    Basic information on AMSU-A MHS MIRS product file
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
from collections import defaultdict
import h5py
import numpy as np
import pandas as pd
import xarray as xr

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
name = "amsua_mhs_mirs"
source_names = ["amsu-a_mhs"]

# Basic information on AMSU-B product file
# index: 1     2    3    4      5      6    7
# freq: 23.8,31.4,50.3,52.799,53.595,54.4,54.941,
# 55.499,57.29,57.29,57.29,57.29,57.29,57.29,
# index:   8     9      10    11   12   13     14
# freq: 55.499,57.29,57.29,57.29,57.29,57.29,57.29,
# index: 15  16  17    18      19     20
# freq: 89.,89.,157.,183.311,183.311,190.311

AMSUA_CHANS = [f"AMSUA_CHAN{x+1}" for x in range(15)]
MHS_CHANS = [f"Chan{x+1}_AT" for x in range(5)]

CHAN_INDEX_MAP = {x: i for i, x in enumerate(AMSUA_CHANS + MHS_CHANS)}


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
    ingested_xarrays = defaultdict(list)
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

        xarray_metadata = xr.Dataset()

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
        xarray_metadata.attrs["start_datetime"] = start_datetime
        xarray_metadata.attrs["end_datetime"] = end_datetime
        xarray_metadata.attrs["source_name"] = "amsu-a_mhs"
        xarray_metadata.attrs["platform_name"] = satid
        xarray_metadata.attrs["crtm_name"] = crtm_name
        xarray_metadata.attrs["data_provider"] = "NOAA-nesdis"

        # MTIFs need to be "prettier" for PMW products, so 2km resolution for
        # final image.
        # xarray_amsub.attrs['sample_distance_km'] = 15
        xarray_metadata.attrs["sample_distance_km"] = 2
        xarray_metadata.attrs["interpolation_radius_of_influence"] = 30000

        if metadata_only:
            LOG.info("metadata_only requested, returning without reading data")
            return {"METADATA": xarray_metadata}

            # Select 5 AMSU-B/MHS Channels
        xarray_amsua = xr.Dataset()
        xarray_mhs = xr.Dataset()
        xarray_amsua_mhs = xr.Dataset()
        for chan in chans:
            if chan in AMSUA_CHANS or chan in MHS_CHANS:
                chan_ind = CHAN_INDEX_MAP[chan]
                chan_num = chan_ind + 1
                if chan in AMSUA_CHANS:
                    xarray_amsua[chan] = xr.DataArray(
                        var_all["BT"][:, :, chan_ind],
                        attrs={"channel_number": chan_num},
                    )
                    xarray_amsua.attrs["source_name_override"] = "amsu-a"
                else:
                    xarray_mhs[chan] = xr.DataArray(
                        var_all["BT"][:, :, chan_ind],
                        attrs={"channel_number": chan_num},
                    )
                    xarray_mhs.attrs["source_name_override"] = "mhs"
            else:
                xarray_amsua_mhs[chan] = xr.DataArray(var_all[chan][()])
                xarray_amsua_mhs.attrs["source_name_override"] = "amsu-a_mhs"

        # Add time and geolocation variables
        beam_pos = np.broadcast_to(
            np.arange(fileobj["Field_of_view"].size) + 1, var_all["LZ_angle"][()].shape
        )
        scan_angle = xr.DataArray((beam_pos - 45.5) * 10.0 / 9.0)
        for ingest_xr in [xarray_amsua, xarray_mhs, xarray_amsua_mhs]:
            if not ingest_xr:
                continue
            source_name_override = ingest_xr.attrs["source_name_override"]
            ingest_xr.attrs = xarray_metadata.attrs
            ingest_xr.attrs["source_name"] = source_name_override
            ingest_xr["time"] = xr.DataArray(
                pd.DataFrame(time_scan)
                .astype(int)
                .apply(pd.to_datetime, format="%Y%j%H%M")
            )
            ingest_xr["latitude"] = xr.DataArray(var_all["Latitude"][()])
            ingest_xr["longitude"] = xr.DataArray(var_all["Longitude"][()])
            ingest_xr["satellite_zenith_angle"] = xr.DataArray(var_all["LZ_angle"][()])
            ingest_xr["SZ_angle"] = xr.DataArray(var_all["SZ_angle"][()])
            ingest_xr["RAzi_angle"] = xr.DataArray(var_all["RAzi_angle"][()])
            ingest_xr["sensor_scan_angle"] = scan_angle
            # These variables were previously always read in... leaving them commented
            # out as an reminder for what is in the file....
            # ingest_xr["Snow"] = xr.DataArray(var_all["Snow"][()])
            # ingest_xr["IWP"] = xr.DataArray(var_all["IWP"][()])
            # ingest_xr["SWE"] = xr.DataArray(var_all["SWE"][()])
            # ingest_xr["SFR"] = xr.DataArray(var_all["SFR"][()])
            # ingest_xr["sfcType"] = xr.DataArray(var_all["Sfc_type"][()])
            # ingest_xr["TPW"] = xr.DataArray(var_all["TPW"][()])
            # ingest_xr["CLW"] = xr.DataArray(var_all["CLW"][()])
            # ingest_xr["RWP"] = xr.DataArray(var_all["RWP"][()])
            # ingest_xr["GWP"] = xr.DataArray(var_all["GWP"][()])
            # ingest_xr["SIce"] = xr.DataArray(var_all["SIce"][()])
            # ingest_xr["SIce_MY"] = xr.DataArray(var_all["SIce_MY"][()])
            # ingest_xr["SIce_FY"] = xr.DataArray(var_all["SIce_FY"][()])
            # ingest_xr["TSkin"] = xr.DataArray(var_all["TSkin"][()])
            # ingest_xr["SurfP"] = xr.DataArray(var_all["SurfP"][()])
            # ingest_xr["CldTop"] = xr.DataArray(var_all["CldTop"][()])
            # ingest_xr["CldBase"] = xr.DataArray(var_all["CldBase"][()])
            # ingest_xr["CldThick"] = xr.DataArray(var_all["CldThick"][()])
            # ingest_xr["WindSp"] = xr.DataArray(var_all["WindSp"][()])
            # ingest_xr["WindDir"] = xr.DataArray(var_all["WindDir"][()])
            # ingest_xr["WindU"] = xr.DataArray(var_all["WindU"][()])
            # ingest_xr["WindV"] = xr.DataArray(var_all["WindV"][()])

        fileobj.close()
        if xarray_amsua:
            ingested_xarrays["AMSUA"].append(xarray_amsua)
        if xarray_mhs:
            ingested_xarrays["MHS"].append(xarray_mhs)
        if xarray_amsua_mhs:
            ingested_xarrays["AMSUA-MHS"].append(xarray_amsua_mhs)

    xarray_dict = {"METADATA": xarray_metadata}
    for dtype, xarray_list in ingested_xarrays.items():
        if xarray_list:
            final_xarray = xr.concat(xarray_list, dim="dim_0")
            final_xarray.attrs["start_datetime"] = pd.to_datetime(
                np.min(final_xarray["time"].data)
            ).to_pydatetime()
            final_xarray.attrs["end_datetime"] = pd.to_datetime(
                np.max(final_xarray["time"].data)
            ).to_pydatetime()
            xarray_dict[dtype] = final_xarray

    return xarray_dict
