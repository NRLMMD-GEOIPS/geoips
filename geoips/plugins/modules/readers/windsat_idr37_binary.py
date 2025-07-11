# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

# cspell:ignore dcnum, plon, slon, jday, rrflag, fsurface, ftime, fasc, alat, alon, aasc

"""Windsat binary data reader.

This code is designed to read windsat sdr binary data (idr37) file for windsat
37 GHz products in GEOIPS environments. the input file name is something alike
US058SORB-BINspp.wndmi_fws_d20191126_s134102_e153244_r87467_cfnmoc.idr37.

V1.0: initial version.  Song Yang, NRL-MRY, 01/08/2020

errflag is the important parameter of the windsat edr dataset.  It is a 32-bit
integer which describes what is the current data point status.  Here are the
meaning of each bit::

    0-7: Wilheit rain flag
      8: forward/aft scan (bit set to 1 for forward part of scan, 0 for aft scan )
      9: ascending/descending pass flag (1 for ascending, 0 for descending)
     10: Warm load flag
     11: Warm load gains applied (1 = gains applied, 0 = gains not applied)
     12: Glare angle invalid because no 1 vector or LOS doesn't pierce earth
     13-18: Glare angle (0 to 30 represents angles of 0 to 60 degree in increments
            of 2 deg; 31 represents angles .gt. 60 deg; 32 represents invalid
            glare angle)
     19: Cold load flag. If set to 1 the VH channel data had to be corrected due
         to interference in the cold load signal, such as the moon or a
         geostationary satellite.
     20: Gain Saturation flag. Set to 1 when strong RFI causes the gain to change.
         This is set if any TDR saturation flag is set at this frequency
     23: used to hold the rfi flag so that it may be passed on to other structures
         such as the resampling and intermediate structures. Finally RFI is placed
         in the sdr structure.
     other bits are spare

Here is the original sdr record in Fortran::

    type IDRRecord_short
       real(double) :: JD2000           8 bytes
       real, dimension(4)::  stokes     16 bytes
       real :: latitude                 4 bytes
       real :: longitude                4 bytes
       real :: EIA                      4 bytes: earth incidence angle, the angle
                                                 on the ground between vertical and
                                                 the satellite look vector
       real :: PRA                      4 bytes: rotation of the polarization plane
                                                 from true
       real :: CAA                      4 bytes: compass azimuth angle on the ground
       real :: tI45, tIcp, pra45        12 bytes
       integer :: errflag               4 bytes (32-bits integer):a set of bit
                                                flags for data quality and
                                                conditions (above explanation)
       integer :: Scan                  4 bytes: scan line number in the orbit.
                                                 WindSat scans every 1.9 seconds
       integer(int16) :: dcnum          2 bytes: pixel number along the scan,
                                                 called 'downcount number',
                                                 because the highest pixel number
                                                 is measured first.
       integer(int16) :: SurfaceType    2 bytes: legacy SSMI surface type
       integer(int16) :: scanAngle      2 bytes: angle on the ground between the
                                                 flight direction and the look
                                                 direction
       integer(int8) :: water2land ! copied from IDRL record   1 byte:
       integer(int8) :: land2water ! copied from IDRL record   1 byte:
    end type IDRRecord_short

* Gain saturation is when a sudden, large signal causes the gain to change
  quickly and make averaged gain unreliable.
* Forward/Aft is for sensor view position
* The warm load flag indicates that calibration may be unreliable due to solar
  intrusion into the warm load.
* Cold load flags do not mean calibration is unreliable. It's a way for us to
  check the cold load correction algorithm.
* Sun glare is not something to worry about.
* The RFI flag is never set at 37 GHz.
* tI45, tIcp, pra45, scanAngleI, water2land, and land2water aren't commanly used.

   * The first four are for recreating the 6-element pre-Stokes polarization
     vector, and the last two measure coastal contamination

The actual idr37 data record (idr_record) in C::

    typedef struct {
       double jd2000;
       float stokes[4];
       float plat;     lat of earth observation
       float plon;     lon of earth observation
       float eia;      radiance= ~53deg
       float pra;
       float caa;
       float slat;  latitude of satellite position?  not
       float slon;  longitude of satellite position? not
       float salt;  altitude of satellite (meter? km?) not
       int errflag;
       int scan;
       short dcnum;
       short surf;
       float spare;
    idr_record;

    Its total length of idr_record is 72 bytes
"""
# Python Standard Libraries
from datetime import datetime, timezone
import logging
import os

# Third-Party Libraries
import numpy as np

# import pandas as pd
import xarray


LOG = logging.getLogger(__name__)

dataset_info = {
    "WINDSAT_SDR_FWD": {
        "ftime_jd2000": "ftime_jd2000",
        "ftb37v": "ftb37v",
        "ftb37h": "ftb37h",
        "flat": "flat",
        "flon": "flon",
        "fsurfaceType": "fsurfaceType",
        "frainFlag": "frainFlag",
        "fasc_des_pass": "fasc_des_pass",
    },
    "WINDSAT_SDR_AFT": {
        "atime_jd2000": "atime_jd2000",
        "atb37v": "atb37v",
        "atb37h": "atb37h",
        "alat": "alat",
        "alon": "alon",
        "asurfaceType": "asurfaceType",
        "arainFlag": "arainFlag",
        "aasc_des_pass": "aasc_des_pass",
    },
}
gvar_info = {
    "WINDSAT_SDR_FWD": {"Latitude": "latitude", "Longitude": "longitude"},
    "WINDSAT_SDR_AFT": {"Latitude": "latitude", "Longitude": "longitude"},
}

interface = "readers"
family = "standard"
name = "windsat_idr37_binary"
source_names = ["windsat"]

# NOTE: Anytime you see a # NOQA comment, this is for flake8 formatting. Unused
# variables are needed in this for moving through the binary file correctly. There is
# fmt: off and fmt: on comments, which prevent black from moving the # NOQA comments.


def call(fnames, metadata_only=False, chans=None, area_def=None, self_register=False):
    """Read Windsat binary data products.

    Parameters
    ----------
    fnames : list
        * List of strings, full paths to files
    metadata_only : bool, default=False
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
    # get data time info from input fname
    fname = fnames[0]
    time_s_date = os.path.basename(fname).split("_")[2][1:9]
    time_s_hhmm = os.path.basename(fname).split("_")[3][1:5]
    time_e_hhmm = os.path.basename(fname).split("_")[4][1:5]

    # findout whether this data file crossing boundary of day, month, or year
    time_s_year = time_s_date[0:4]
    time_s_month = time_s_date[4:6]
    time_s_day = time_s_date[6:8]

    # initialization of ending date for this file
    time_e_year = int(time_s_year)
    time_e_month = int(time_s_month)
    time_e_day = int(time_s_day)

    # if time_e_hhmm is less than time_s_hhmm, the data crossed the day
    # boundary and entered the next day

    if (int(time_s_year) % 400 == 0) or (
        (int(time_s_year) % 4 == 0) and (int(time_s_year) % 100 != 0)
    ):
        year_leap = "true"
        LOG.info("%d is a Leap Year" % int(time_s_year))
    else:
        year_leap = "false"
        LOG.info("%d is Not the Leap Year" % int(time_s_year))

    if int(time_e_hhmm) < int(time_s_hhmm):
        time_e_day = int(time_s_day) + 1
        if (
            (int(time_s_month) == 4)
            or (int(time_s_month) == 6)
            or (int(time_s_month) == 9)
        ):  # in Apr, Jun and Sep
            if time_e_day > 30:
                time_e_day == 1  # first day of the next month
                time_e_month == int(time_s_month) + 1
        else:
            if int(time_s_month) == 2:  # in Feb
                if year_leap:  # In a leap year
                    if time_e_day > 29:
                        time_e_day == 1  # first day of the next month
                        time_e_month == int(time_s_month) + 1
                else:  # No leap year
                    if time_e_day > 28:
                        time_e_day == 1  # first day of the next month
                        time_e_month == int(time_s_month) + 1
            else:  # in Jan, Mar, Jul, Aug, Oct, Dec
                if time_e_day > 31:
                    time_e_day == 1  # first day of the next month
                    time_e_month == int(time_s_month) + 1
        if time_e_month > 12:  # in Dec, deterimine whether it crosses the year boundary
            time_e_year == int(time_s_year) + 1

    # convret end_time of the data into strings
    time_e_date = (
        str(time_e_year) + str("%02d" % time_e_month) + str("%02d" % time_e_day)
    )

    # Need to set up time to be read in by the metadata (year and jday are arrays)
    time_start = time_s_date + " " + time_s_hhmm
    time_end = time_e_date + " " + time_e_hhmm

    xarray_obj = xarray.Dataset()

    # Enter metadata
    start_datetime = datetime.strptime(time_start, "%Y%m%d %H%M")
    xarray_obj.attrs["start_datetime"] = start_datetime.replace(tzinfo=timezone.utc)
    end_datetime = datetime.strptime(time_end, "%Y%m%d %H%M")
    xarray_obj.attrs["end_datetime"] = end_datetime.replace(tzinfo=timezone.utc)
    xarray_obj.attrs["source_file_datetimes"] = [xarray_obj.attrs["start_datetime"]]

    xarray_obj.attrs["platform_name"] = "coriolis"
    xarray_obj.attrs["source_name"] = "windsat"
    xarray_obj.attrs["interpolation_radius_of_influence"] = 10000
    xarray_obj.attrs["sample_distance_km"] = 2
    xarray_obj.attrs["data_provider"] = "NRL-NOAA"

    # Passing chans == [] indicates we do not want ANY data, only metadata, so
    # return once metadata is set.
    if metadata_only:
        return {"METADATA": xarray_obj}

    # find out size of the input file (bytes)
    filesize_info = os.stat(fname).st_size
    len_OneRec = 72  # size of record (bytes)?
    rec_tot = filesize_info // len_OneRec  # how many records in the file

    # check for exact data records by mode of the file_size vs data_record
    try:
        good_datafile = filesize_info % len_OneRec
        if good_datafile == 0:
            LOG.info("This is a good windsat idr37 data file")
        else:
            LOG.info("This is not a good windsat idr37 data file:  skipping ....")
            return
    except Exception as resp:
        LOG.info(
            "\tBLANKET EXCEPTION %s: %s >> %s : %s",
            type(resp).__name__,
            str(resp.__doc__),
            str(resp.args),
            "windsat idr37 data does not have even number of data records !! "
            "Skipping...",
        )
        return {"METADATA": xarray_obj}

    bad_value = -999
    # declare data arrays
    try:
        windsat_read = np.ma.zeros(rec_tot)  # initialization of zeros
        np.ma.masked_all_like(windsat_read)
    except Exception as resp:
        LOG.info(
            "\tBLANKET EXCEPTION %s: %s >> %s : %s",
            type(resp).__name__,
            str(resp.__doc__),
            str(resp.args),
            "windsat idr37 data does not have even number of data records !! "
            "Skipping...",
        )
        return {"METADATA": xarray_obj}

    ftime_jd2000 = np.ma.masked_values(windsat_read, bad_value)
    ftb37v = np.ma.masked_values(windsat_read, bad_value)
    ftb37h = np.ma.masked_values(windsat_read, bad_value)
    flat = np.ma.masked_values(windsat_read, bad_value)
    flon = np.ma.masked_values(windsat_read, bad_value)
    fsurfaceType = np.ma.masked_values(windsat_read, bad_value)
    frainFlag = np.ma.masked_values(windsat_read, bad_value)
    fasc_des_pass = np.ma.masked_values(windsat_read, bad_value)

    atime_jd2000 = np.ma.masked_values(windsat_read, bad_value)
    atb37v = np.ma.masked_values(windsat_read, bad_value)
    atb37h = np.ma.masked_values(windsat_read, bad_value)
    alat = np.ma.masked_values(windsat_read, bad_value)
    alon = np.ma.masked_values(windsat_read, bad_value)
    asurfaceType = np.ma.masked_values(windsat_read, bad_value)
    arainFlag = np.ma.masked_values(windsat_read, bad_value)
    aasc_des_pass = np.ma.masked_values(windsat_read, bad_value)

    f1 = open(fname, "rb")

    k = 0
    k2 = 0
    # read in the windsat edr products for all data  points
    for ii in range(rec_tot):  # loop records of this file
        if ii % 10000 == 0:
            LOG.info("Running record number %s of %s", ii, rec_tot)
        try:
            # read in variables using their size (bytes)
            jd2000 = np.frombuffer(f1.read(8), dtype=np.dtype("float64")).byteswap()[
                0
            ]  # sec since 1200Z,01/01/2000
            # get time info for each data point
            # fmt: off
            # timeinfo = pd.datetime(2000, 1, 1, 12) + pd.Timedelta(jd2000, unit="s")
            # time_date = int(
            #     str(timeinfo.year) + str(timeinfo.month) + str(timeinfo.day)
            # )
            # time_hhmm = int(str(timeinfo.hour) + str(timeinfo.minute))
            tb37v, tb37h, tb37info1, tb37info2 = np.frombuffer(
                f1.read(16), dtype=np.dtype("float32")
            ).byteswap()  # K (37v,37h,info1,info2)
            lat = np.frombuffer(f1.read(4), dtype=np.dtype("float32")).byteswap()[
                0
            ]  # deg
            lon = np.frombuffer(f1.read(4), dtype=np.dtype("float32")).byteswap()[
                0
            ]  # deg
            # if lon > 180.0:          # windbarbs needs lon in (-180,180)
            #   lon=lon-360

            eia = np.frombuffer(  # NOQA
                f1.read(4), dtype=np.dtype("float32")
            ).byteswap()[
                0
            ]  # unit in radiance =~53 deg
            pra = np.frombuffer(f1.read(4), dtype=np.dtype("float32")).byteswap()[  # NOQA
                0
            ]
            caa = np.frombuffer(f1.read(4), dtype=np.dtype("float32")).byteswap()[  # NOQA
                0
            ]
            slat = np.frombuffer(  # NOQA
                f1.read(4), dtype=np.dtype("float32")
            ).byteswap()[
                0
            ]  # deg
            slon = np.frombuffer(  # NOQA
                f1.read(4), dtype=np.dtype("float32")
            ).byteswap()[
                0
            ]  # deg
            salt = np.frombuffer(  # NOQA
                f1.read(4), dtype=np.dtype("float32")
            ).byteswap()[
                0
            ]  # meter
            errflag = np.frombuffer(f1.read(4), dtype=np.dtype("int32")).byteswap()[
                0
            ]  # deg
            scanNum = np.frombuffer(f1.read(4), dtype=np.dtype("int32")).byteswap()[  # NOQA
                0
            ]
            downcountNum = np.frombuffer(  # NOQA
                f1.read(2), dtype=np.dtype("int16")
            ).byteswap()[0]
            surfaceType = np.frombuffer(f1.read(2), dtype=np.dtype("int16")).byteswap()[
                0
            ]
            spare = np.frombuffer(  # NOQA
                f1.read(4), dtype=np.dtype("float32")
            ).byteswap()[
                0
            ]  # spare var for space holder

            # fmt: on
            # decode errflag to assign value to approperated variables, i.e.,
            # forward/aft mode, ascending/descending etc
            fore_aft_scan = (
                errflag >> 8 & 1
            )  # =1, foreward scan; =0, aft scan (foreward scan used for image)
            asc_des_pass = errflag >> 9 & 1  # =1, ascending; =0, descending

            # rainflag
            rrflag_tmp = 0
            for j in range(8):
                bit = errflag >> j & 1  # =1, set, =0, not set
                rrflag_tmp += bit * pow(2, j)
            rrflag = rrflag_tmp

            if (
                fore_aft_scan == 1
            ):  # forward scan points  --> will be used for image products
                ftb37v[k] = tb37v
                ftb37h[k] = tb37h
                flat[k] = lat
                flon[k] = lon
                fsurfaceType[k] = surfaceType
                frainFlag[k] = rrflag
                ftime_jd2000[k] = jd2000
                fasc_des_pass[k] = asc_des_pass
                k += 1
            else:  # aft scan points
                atb37v[k2] = tb37v
                atb37h[k2] = tb37h
                alat[k2] = lat
                alon[k2] = lon
                asurfaceType[k2] = surfaceType
                arainFlag[k2] = rrflag
                atime_jd2000[k2] = jd2000
                aasc_des_pass[k2] = asc_des_pass
                k2 += 1

        except Exception as resp:
            LOG.info(
                "\tBLANKET EXCEPTION %s: %s >> %s : %s",
                type(resp).__name__,
                str(resp.__doc__),
                str(resp.args),
                "Failed setting windsat sdr data arrays!! Skipping...",
            )
    f1.close()

    flat = np.ma.masked_values(flat, bad_value)
    flon = np.ma.masked_values(flon, bad_value)
    ftime_jd2000 = np.ma.masked_values(ftime_jd2000, bad_value)
    ftb37v = np.ma.masked_values(ftb37v, bad_value)
    ftb37h = np.ma.masked_values(ftb37h, bad_value)
    fsurfaceType = np.ma.masked_values(fsurfaceType, bad_value)
    frainFlag = np.ma.masked_values(frainFlag, bad_value)
    fasc_des_pass = np.ma.masked_values(fasc_des_pass, bad_value)

    alat = np.ma.masked_values(alat, bad_value)
    alon = np.ma.masked_values(alon, bad_value)
    atime_jd2000 = np.ma.masked_values(atime_jd2000, bad_value)
    atb37v = np.ma.masked_values(atb37v, bad_value)
    atb37h = np.ma.masked_values(atb37h, bad_value)
    asurfaceType = np.ma.masked_values(asurfaceType, bad_value)
    arainFlag = np.ma.masked_values(arainFlag, bad_value)
    aasc_des_pass = np.ma.masked_values(aasc_des_pass, bad_value)

    xarray_sdr_fwd = xarray.Dataset()
    xarray_sdr_aft = xarray.Dataset()
    xarray_sdr_aft = xarray.Dataset()
    xarray_sdr_fwd.attrs = xarray_obj.attrs.copy()
    xarray_sdr_aft.attrs = xarray_obj.attrs.copy()

    timediff = np.datetime64("2000-01-01T12:00:00") - np.datetime64(
        "1970-01-01T00:00:00"
    )
    timestamps = ftime_jd2000.astype("np.datetime64[s]") + timediff
    xarray_sdr_aft["time"] = xarray.DataArray(timestamps)
    xarray_sdr_aft["latitude"] = xarray.DataArray(alat)
    xarray_sdr_aft["longitude"] = xarray.DataArray(alon)
    xarray_sdr_aft["atb37v"] = xarray.DataArray(atb37v)
    xarray_sdr_aft["asurfaceType"] = xarray.DataArray(asurfaceType)
    xarray_sdr_aft["arainFlag"] = xarray.DataArray(arainFlag)
    xarray_sdr_aft["aasc_des_pass"] = xarray.DataArray(aasc_des_pass)

    xarray_sdr_fwd["time"] = xarray.DataArray(timestamps)
    xarray_sdr_fwd["latitude"] = xarray.DataArray(flat)
    xarray_sdr_fwd["longitude"] = xarray.DataArray(flon)
    xarray_sdr_fwd["ftb37v"] = xarray.DataArray(ftb37v)
    xarray_sdr_fwd["fsurfaceType"] = xarray.DataArray(fsurfaceType)
    xarray_sdr_fwd["frainFlag"] = xarray.DataArray(frainFlag)
    xarray_sdr_fwd["fasc_des_pass"] = xarray.DataArray(fasc_des_pass)
    return {"METADATA": xarray_obj, "AFT": xarray_sdr_aft, "FWD": xarray_sdr_fwd}
