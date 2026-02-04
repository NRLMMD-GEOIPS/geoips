# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""SSMI binary reader.

This SSMI reader is desgined for importing SSMI sdr data files (such as
ssmi_orbital_sdrmi_f15_d20200427_s104500_e123100_r05323_cfnoc.def). This reader
is created to read in TBs at 19 (V,H),22V, 37(V,H) and 85 (V,H) GHz channels.
There are A/B scans for 85 GHz.  The combined A/B scans will be used for
TC imagery products at 85 GHz.

This GEOIPS python code is based on a SSMI SDR reader in C.

Convert SSMI_HIRES_AB for 85GHz and SSMI_LORES for 19-37GHz into xarray for
GEOIPS framework

V1.0:  Initial version, NRL-MRY, May 19, 2020

SSMI input data info::

    pixels per scan:
    LORES=64 for 19, 22, and 37 GHz channels;
    HIRES=128 for 85 GHz channels
        19V[LORES]                                    FOV:   69km x 43km
        19H[LORES]
        22V[LORES]                                           50km x 40km
        37V[LORES]                                           37km x 28km
        37H[LORES]
        85V[HIRES][2]    [][0]: A scans; [][1]: B scans      15km x 13km
        85H[HIRES][2]

           -----header info-----
    int32
        cyr, cmon, cday,       /* file creation date */
        chr, cmin,             /* file creation time */
        scans,                 /* number of scans in file (from DataSeq) */
        scid,                  /* spacecraft ID */
        rev,                   /* nominal rev  */
        bjld, bhr, bmin, bsec, /* begin day of year (julian day), time=hr,min,sec */
        ejld, ehr, emin, esec, /* ending day of year, time */
        ajld, ahr, amin, asec, /* ascending node DOY, time */
        lsat;                  /* logical satellite ID */

       -----scan data-----
    int32 scann;                 /* scan number (from ScanHdr1) */
    int32 bst;                   /* B-scan start time (sec) scaled by 10000 */
    double xtime;                /* bst as seconds since 0z 1 Jan 1987 */
    uint16
        v19[LORES],              /* TBs */
        h19[LORES],
        v22[LORES],
        v37[LORES],
        h37[LORES],
        v85[HIRES][2],
        h85[HIRES][2],
        lon[HIRES][2];           /* longitudes */
    int16 lat[HIRES][2];         /* latitudes */
    char sft[HIRES][2];          /* surface types */
"""

# Python Standard Libraries
from datetime import datetime
import logging
import os

# Third-Party Libraries
import matplotlib
import numpy as np
import pandas as pd
import xarray as xr

matplotlib.use("agg")

LOG = logging.getLogger(__name__)

interface = "readers"
family = "standard"
name = "ssmi_binary"
source_names = ["ssmi"]

# NOTE: Anytime you see a # NOQA comment, this is for flake8 formatting. Unused
# variables are needed in this for moving through the binary file correctly.


def call(fnames, metadata_only=False, chans=None, area_def=None, self_register=False):
    """Read SSMI FNMOC Binary Data.

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
    # from IPython import embed as shell
    fname = fnames[0]

    LOG.info("Reading file %s", fname)

    #     check for right nput SSMI SDR data file

    data_name = os.path.basename(fname).split("_")[-1].split(".")[-1]

    if data_name != "def":
        LOG.info("Warning: wrong SSMI SDR data type:  data_type={0}".format(data_name))
        raise

    if "cfnoc" in os.path.basename(fname) and "sdrmi" in os.path.basename(fname):
        LOG.info("found a SSMI SDR file")
    else:
        LOG.info("not a SSMI SDR file: skip it")
        raise IOError("Not an SSMI SDR file: skip it")

    """    ------  Notes  ------
       Read in SSMI SDR files for 19v-h,22v,37v-h,85v-h(A and B scans) in binary data
            Then, transform these variables (TBs) into xarray framework for GEOIPS

       Input Parameters:
           fname (str): input file name.  require a full path
       Returns:
           xarray.Dataset with required Variables and Attributes:
               Variables:
                        LORES Channels:
                          'latitude', 'longitude', '19V', '19H',
                          '22V', '37V','37H','time_scan'
                        HIRES Channels (combined A-B scans):
                          'latitude', 'longitude', '85V', '85H', 'sfcType', 'time_scan'
               Attibutes:
                        'source_name', 'platform_name', 'data_provider',
                        'interpolation_radius_of_influence',
                        'start_datetime', 'end_datetime'
               Optional Attrs:
                        'source_file_names', 'source_file_datetimes'
    """

    #    *********  Decode Formula for SSMI SDR Data  *************
    # V1 evaluates a 1-byte binary value as an unsigned number
    # V2 evaluates a 2-byte binary value as an unsigned number
    # V4 evaluates a 4-byte binary value as an unsigned number
    # VLat gets latitude and converts its range to [-90:+90]
    # VLon gets longitude

    def V1(p):
        return buf[p]

    def V2(p):
        # With numpy 2.x upgrade, these buffers were uint8, which overflowed.
        # This made it work.
        return 256 * np.uint16(buf[p]) + np.uint16(buf[p + 1])

    def V4(p):
        return 256 * (256 * (256 * buf[p] + buf[p + 1]) + buf[p + 2]) + buf[p + 3]

    def VLat(p):
        return V2(p) - 9000

    def VLon(p):
        return V2(p)

    # Define a function to extract values of parameters from a scan data block

    def fill_arrays():
        v19 = {}
        h19 = {}
        v22 = {}
        v37 = {}
        h37 = {}

        lat = {}
        lon = {}
        v85 = {}
        h85 = {}
        sft = {}

        LORES = 64
        unit_scale = 100.0  # convert integer TBs into actual values

        for spotL in range(LORES):
            bb = spotL * 52
            spotH = spotL * 2

            v19[spotL] = V2(bb + 10) / unit_scale
            h19[spotL] = V2(bb + 12) / unit_scale
            v22[spotL] = V2(bb + 14) / unit_scale
            v37[spotL] = V2(bb + 16) / unit_scale
            h37[spotL] = V2(bb + 18) / unit_scale

            # Initilize variable for A and B scans [0] - A scan; [1] - B scan

            # for LORES pixel positions
            lat[spotH] = np.zeros(2)
            lon[spotH] = np.zeros(2)
            v85[spotH] = np.zeros(2)
            h85[spotH] = np.zeros(2)
            sft[spotH] = np.zeros(2)  # surface type

            # for HIRES pixel positions (not at LORES positions)
            lat[spotH + 1] = np.zeros(2)
            lon[spotH + 1] = np.zeros(2)
            v85[spotH + 1] = np.zeros(2)
            h85[spotH + 1] = np.zeros(2)
            sft[spotH + 1] = np.zeros(2)

            # for A scan at LORES pixel positions
            lat[spotH][0] = VLat(bb + 6) / unit_scale
            lon[spotH][0] = VLon(bb + 8) / unit_scale
            v85[spotH][0] = V2(bb + 20) / unit_scale
            h85[spotH][0] = V2(bb + 22) / unit_scale
            sft[spotH][0] = V1(bb + 24)

            # for B scan at LORES pixel positions
            lat[spotH][1] = VLat(bb + 26) / unit_scale
            lon[spotH][1] = VLon(bb + 28) / unit_scale
            v85[spotH][1] = V2(bb + 30) / unit_scale
            h85[spotH][1] = V2(bb + 32) / unit_scale
            sft[spotH][1] = V1(bb + 34)

            # for A scan at HIRES pixel positions
            lat[spotH + 1][0] = VLat(bb + 36) / unit_scale
            lon[spotH + 1][0] = VLon(bb + 38) / unit_scale
            v85[spotH + 1][0] = V2(bb + 40) / unit_scale
            h85[spotH + 1][0] = V2(bb + 42) / unit_scale
            sft[spotH + 1][0] = V1(bb + 44)

            # for B scan at HIRES pixel positions
            lat[spotH + 1][1] = VLat(bb + 46) / unit_scale
            lon[spotH + 1][1] = VLon(bb + 48) / unit_scale
            v85[spotH + 1][1] = V2(bb + 50) / unit_scale
            h85[spotH + 1][1] = V2(bb + 52) / unit_scale
            sft[spotH + 1][1] = V1(bb + 54)

        data = {
            "v19": v19,
            "h19": h19,
            "v22": v22,
            "v37": v37,
            "h37": h37,
            "lat": lat,
            "lon": lon,
            "v85": v85,
            "h85": h85,
            "sft": sft,
        }
        return data

    # Main section of processing SSMI SDR data

    # define some parameters
    LORES = 64  # pixels per lo-res scan
    HIRES = 128  # pixels per gi-res scan
    MAXSCANS = 3000  # max lo-res scans per file
    # SCANTIME = 3.798  # approximate A-B scan interval

    # TRUE = 1
    # FALSE = 0
    # BUFSIZE = 4444
    # FRAMESIZE = 12798
    # FILLER = 0xA5
    EOF_LEN = 6

    # Return Codes
    # OK = 0
    # BAD_HDRS = 3
    # BAD_EOF = 4
    BAD_LEN = 5
    # WRITE_ERR = 6
    # END_FILE = 7
    # FATAL_ERR = 8
    # CANT_OPEN = 9

    # Header Info
    blocks = {
        "ProdID": 28,  # Product ID hdr
        "DataSeq": 26,  # DataSeq hdr  (scan line info, total scans))
        "RevHdrDD": 190,  # Rev info
        "ScanHdrDD": 34,  # Scan hdr
        "ScanDD": 370,  #
        "RevHdr": 30,
        "ScanHdr": 12,
        "Scan": 3334,
    }

    f1 = open(fname, "rb")  # open inform ssmi sdr file

    data = {}  # define a dictionary array for parameters (TBs, etc)

    year = {}  # define arrays for scan ime info
    month = {}
    day = {}
    hour = {}
    minute = {}
    second = {}

    #    Process of READ HEARDERs

    #    Product ID Block
    buf = np.frombuffer(f1.read(blocks["ProdID"]), dtype="uint8")
    satid0 = 10 * (V1(18) - 48) + V1(19) - 48
    fcyr = V2(20)  # date of this input file createed
    # fcmon = V1(22)
    # fcday = V1(23)
    # fchr = V1(24)
    # fcmin = V1(25)

    #    Data Sequence Block
    buf = np.frombuffer(f1.read(blocks["DataSeq"]), dtype="uint8")
    # scans = V2(14)  # number of total scans of this orbital file

    #    Data Description Blocks
    buf = np.frombuffer(f1.read(blocks["RevHdrDD"]), dtype="uint8")
    buf = np.frombuffer(f1.read(blocks["ScanHdrDD"]), dtype="uint8")
    buf = np.frombuffer(f1.read(blocks["ScanDD"]), dtype="uint8")

    #     Rev Header Block
    buf = np.frombuffer(f1.read(blocks["RevHdr"]), dtype="uint8")
    # scid = V4(4)  # spcaecraft ID, i.e., 15 for F15
    # rev = V4(8)
    bjld = V2(12)  # start date info: julian day
    bhr = V1(14)  # -                 hour
    bmin = V1(15)
    # bsec = V1(16)
    ejld = V2(17)  # end date info: Julian day
    ehr = V1(19)
    emin = V1(20)
    # esec = V1(21)
    # ajld = V2(22)  # julian day for ascending node
    # ahr = V1(24)
    # amin = V1(25)
    # asec = V1(26)
    # lsat = V1(27)  # logical satellite ID

    # setup year and julian day for this input file
    year_info = str(fcyr)
    jDay_info = str(bjld)

    #   --------  Start processes of reading and extraction of scans  -------------

    scan_read = 0  # initilization of scan count

    while f1:  # loop scans of this file
        # Read Scan Header Block
        while True:
            buf = np.frombuffer(
                f1.read(2), dtype="uint8"
            )  # read in block length from  two-byte words
            if list(buf) == [0, 0] and len(buf) > 0:
                continue
            elif list(buf)[0] != 165:  # not a FILLER, so get the length of this block
                length = V2(0) * 2
            if length != 0:  # find good block with length-bytes data
                break

        length2 = length - 2  # bytes of the rest block

        buf0 = np.frombuffer(
            f1.read(length2), dtype="uint8"
        )  # read length2 bytes of this block
        buf = np.append([0, 0], buf0)  # shift two bytes so buf will have "length" bytes

        if length == BAD_LEN:
            LOG.info("fatal error:  Ban_length")
            raise  # fatal error stop
        elif length == EOF_LEN or length == 0:
            break
        elif length != blocks["ScanHdr"]:
            LOG.info("block length= {0} {1}".format(blocks["ScanHdr"], length))
            continue  # unexpected block length, go to next block

        # extraction of parameters from scan header block
        # scann = V2(4)  # not used      (first scan, i.e., scan header)
        bst = V4(6)  # B-scan start time (sec): second of the day

        # conver time to seconds from beggining of 1987 (do we need this info?)

        scan_hr = bst / 3600  # hour of the scan
        scan_min = (bst - scan_hr * 3600) / 60  # minute of scan
        scan_sec = bst - scan_hr * 3600 - scan_min * 60  # second of the scan

        date_info = datetime.strptime(year_info + jDay_info, "%Y%j")

        scan_yr = date_info.year
        scan_mon = date_info.month
        # scan_day = date_info.day

        # set up time info for each B scan  (will set: A scantime = B scantime later)
        year[scan_read] = scan_yr
        month[scan_read] = scan_mon
        day[scan_read] = scan_hr
        hour[scan_read] = scan_hr
        minute[scan_read] = scan_min
        second[scan_read] = scan_sec

        # read Scan Data Block

        while True:
            buf = np.frombuffer(
                f1.read(2), dtype="uint8"
            )  # read in block length from  two-byte words
            if list(buf) == [0, 0] and len(buf) > 0:
                continue
            elif list(buf)[0] != 165:  # not a FILLER, so get the length of this block
                length = V2(0) * 2
            if length != 0:  # find good block with length-bytes data
                break

        length2 = length - 2  # bytes of the rest block

        buf0 = np.frombuffer(
            f1.read(length2), dtype="uint8"
        )  # read length2 bytes of this block
        buf = np.append([0, 0], buf0)  # shift two bytes so buf will have "length" bytes

        if length == BAD_LEN:
            raise  # fatal error stop
        elif length == EOF_LEN or length == 0:
            break
        elif length != blocks["Scan"]:
            LOG.info("block length= {0} {1}".format(blocks["Scan"], length))
            continue  # unexpected block lengthi, go to next block

        # check of max scans
        if scan_read > MAXSCANS:
            LOG.info("Reached max scans, break!")
            break

        # extract parameters from the scan block
        data[scan_read] = fill_arrays()

        scan_read += 1  # accumulation of scans

    f1.close()  # close input file

    #  -------- Apply the GEOIPS framework in XARRAY data frame ----------

    LOG.info("Making full dataframe")

    # bad_value = -999

    # initilization of variables
    lat_lo = np.zeros((scan_read, 64))  # LORES channels: lat
    lon_lo = np.zeros((scan_read, 64))  # lon
    V19 = np.zeros((scan_read, 64))
    H19 = np.zeros((scan_read, 64))
    V22 = np.zeros((scan_read, 64))
    V37 = np.zeros((scan_read, 64))
    H37 = np.zeros((scan_read, 64))
    time_scan_lo = np.zeros((scan_read, 64))  # same for every pixel of this scan

    lat_hia = np.zeros((scan_read, 128))  # A scan HIRES channels: lat
    lon_hia = np.zeros((scan_read, 128))  # -                      lon
    lat_hib = np.zeros((scan_read, 128))  # B scan HIRES channels: lat
    lon_hib = np.zeros((scan_read, 128))  # -                      lon
    V85a = np.zeros((scan_read, 128))
    V85b = np.zeros((scan_read, 128))
    H85a = np.zeros((scan_read, 128))
    H85b = np.zeros((scan_read, 128))

    lat_ab = np.zeros((scan_read * 2, 128))  # combined A-B scans: lat
    lon_ab = np.zeros((scan_read * 2, 128))  # -                   lon
    V85 = np.zeros((scan_read * 2, 128))
    H85 = np.zeros((scan_read * 2, 128))
    sfcType = np.zeros((scan_read * 2, 128))
    time_scan = np.zeros((scan_read * 2, 128))  # same for every pixel of this scan

    # assignment of data for variables

    for ii in range(scan_read):  # loop of scans
        ii2 = ii * 2  # for combined A-B scans

        for jj in range(LORES):  # loop of pixels per scan for LORES channels
            jj2 = jj * 2
            try:
                lat_lo[ii][jj] = data[ii]["lat"][jj2][0]
                lon_lo[ii][jj] = data[ii]["lon"][jj2][0]
                V19[ii][jj] = data[ii]["v19"][jj]
                H19[ii][jj] = data[ii]["h19"][jj]
                V22[ii][jj] = data[ii]["v22"][jj]
                V37[ii][jj] = data[ii]["v37"][jj]
                H37[ii][jj] = data[ii]["h37"][jj]
                time_scan_lo[ii][jj] = "%04d%03d%02d%02d" % (
                    fcyr,
                    bjld,
                    hour[ii],
                    minute[ii],
                )
            except KeyError:
                LOG.info(
                    "Failed setting arrays in LORES channels {0} {1} {2}".format(
                        ii, jj, jj2
                    )
                )

        for jj in range(HIRES):  # loop of pixels per scan for HIRES channels
            try:
                lat_hia[ii][jj] = data[ii]["lat"][jj][0]  # A scan
                lon_hia[ii][jj] = data[ii]["lon"][jj][0]
                lat_hib[ii][jj] = data[ii]["lat"][jj][1]  # B scan
                lon_hib[ii][jj] = data[ii]["lon"][jj][1]
                V85a[ii][jj] = data[ii]["v85"][jj][0]  # A scan
                V85b[ii][jj] = data[ii]["v85"][jj][1]  # B scan
                H85a[ii][jj] = data[ii]["h85"][jj][0]  # A scan
                H85b[ii][jj] = data[ii]["h85"][jj][1]  # B scan

                # combined A-B scans
                lat_ab[ii2][jj] = lat_hia[ii][jj]  # put A scan values
                lon_ab[ii2][jj] = lon_hia[ii][jj]
                V85[ii2][jj] = V85a[ii][jj]
                H85[ii2][jj] = H85a[ii][jj]
                sfcType[ii2][jj] = data[ii]["sft"][jj][0]
                time_scan[ii2][jj] = "%04d%03d%02d%02d" % (
                    fcyr,
                    bjld,
                    hour[ii],
                    minute[ii],
                )

                lat_ab[ii2 + 1][jj] = lat_hib[ii][jj]  # put B scan values
                lon_ab[ii2 + 1][jj] = lon_hib[ii][jj]
                V85[ii2 + 1][jj] = V85b[ii][jj]
                H85[ii2 + 1][jj] = H85b[ii][jj]
                sfcType[ii2 + 1][jj] = data[ii]["sft"][jj][1]
                time_scan[ii2 + 1][jj] = time_scan[ii2][
                    jj
                ]  # same time for A and B scan
            except KeyError:
                LOG.info("Failed setting arrays in HIRES channels")

    #          ------  setup xarray variables   ------
    # namelist_lores = [
    #     "latitude",
    #     "longitude",
    #     "V19",
    #     "H19",
    #     "V22",
    #     "V37",
    #     "H37",
    #     "time_scan_lo",
    # ]
    # namelist_85ab = ["latitude", "longitude", "V85", "H85", "sfcType", "time"]

    # for LORES channels
    xarray_lores = xr.Dataset()
    xarray_lores["latitude"] = xr.DataArray(lat_lo)
    xarray_lores["longitude"] = xr.DataArray(lon_lo)
    xarray_lores["V19"] = xr.DataArray(V19)
    xarray_lores["H19"] = xr.DataArray(H19)
    xarray_lores["V22"] = xr.DataArray(V22)
    xarray_lores["V37"] = xr.DataArray(V37)
    xarray_lores["H37"] = xr.DataArray(H37)
    xarray_lores["time"] = xr.DataArray(
        pd.DataFrame(time_scan_lo).astype(int).apply(pd.to_datetime, format="%Y%j%H%M")
    )

    # for combined 85GHz A-B channels
    xarray_85ab = xr.Dataset()
    xarray_85ab["latitude"] = xr.DataArray(lat_ab)
    xarray_85ab["longitude"] = xr.DataArray(lon_ab)
    xarray_85ab["V85"] = xr.DataArray(V85)
    xarray_85ab["H85"] = xr.DataArray(H85)
    xarray_85ab["sfcType"] = xr.DataArray(sfcType)
    xarray_85ab["time"] = xr.DataArray(
        pd.DataFrame(time_scan).astype(int).apply(pd.to_datetime, format="%Y%j%H%M")
    )

    # setup attributes

    # ch:       19   22   37  85    GHz
    # FOV_list=['43','40','28',13']  km

    # satID string
    satid = "F" + str(satid0)

    start_time = "%04d%03d%02d%02d" % (fcyr, bjld, bhr, bmin)
    end_time = "%04d%03d%02d%02d" % (fcyr, ejld, ehr, emin)

    # for LORES
    xarray_lores.attrs["start_datetime"] = datetime.strptime(start_time, "%Y%j%H%M")
    xarray_lores.attrs["end_datetime"] = datetime.strptime(end_time, "%Y%j%H%M")
    xarray_lores.attrs["source_name"] = "ssmi"
    xarray_lores.attrs["platform_name"] = satid
    xarray_lores.attrs["data_provider"] = "DMSP"
    xarray_lores.attrs["source_file_names"] = [os.path.basename(fname)]

    # MTIFs need to be "prettier" for PMW products, so 2km resolution for final image
    # xarray_lores.attrs['sample_distance_km'] = 25
    xarray_lores.attrs["sample_distance_km"] = 2
    xarray_lores.attrs["interpolation_radius_of_influence"] = 50000

    # for 85GHz A-B combined
    xarray_85ab.attrs["start_datetime"] = datetime.strptime(start_time, "%Y%j%H%M")
    xarray_85ab.attrs["end_datetime"] = datetime.strptime(end_time, "%Y%j%H%M")
    xarray_85ab.attrs["source_file_datetimes"] = [xarray_85ab.start_datetime]
    xarray_85ab.attrs["source_name"] = "ssmi"
    xarray_85ab.attrs["platform_name"] = satid
    xarray_85ab.attrs["data_provider"] = "DMSP"
    xarray_85ab.attrs["source_file_names"] = [os.path.basename(fname)]

    # MTIFs need to be "prettier" for PMW products, so 2km resolution for final image
    # xarray_85ab.attrs['sample_distance_km'] = 13
    xarray_85ab.attrs["sample_distance_km"] = 2
    xarray_85ab.attrs["interpolation_radius_of_influence"] = 15000

    LOG.info("  Start time %s", start_time)
    LOG.info("  End time %s", end_time)
    LOG.info("  Min lat %s", lat_ab.min())
    LOG.info("  Max lat %s", lat_ab.max())

    return {"HIRES": xarray_85ab, "LORES": xarray_lores, "METADATA": xarray_85ab[[]]}
