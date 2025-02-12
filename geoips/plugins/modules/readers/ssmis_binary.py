# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""SSMIS Binary reader.

This code is converted from geoips v1 into geoipd v2 framework. This new version
of reader is indepent from the GEOIPS system whose environmental parametrs must
be used in V1.  Now, only python functipns are used with geoips framework
and xarray is utilized to process datasets for product applications.

Version Histopry:
     V1: initial code, July 24, 2020, NRL-MRY

Input File
     SSMIS SDR data

Output Fields
     XARRAY onjectives to hold variables
"""
# Python Standard Libraries
from datetime import datetime, timedelta
import logging
from os.path import basename

# Third-Party Libraries
import numpy as np
import pandas as pd
import xarray as xr

LOG = logging.getLogger(__name__)

interface = "readers"
family = "standard"
name = "ssmis_binary"
source_names = ["ssmis"]

# NOTE: Anytime you see a # NOQA comment, this is for flake8 formatting. Unused
# variables are needed in this for moving through the binary file correctly.


def call(fnames, metadata_only=False, chans=False, area_def=None, self_register=False):
    """Read SSMIS binary data products.

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
    LOG.info("Reading files %s", fnames)

    # checking for right input SSMIS SDR file

    xobjs_list = []
    # NOTE chans, area_def, and self_register NOT implemented.
    for fname in fnames:
        xobjs_list += [read_ssmis_data_file(fname, metadata_only=metadata_only)]

    final_xobjs = append_xarray_dicts(xobjs_list)

    return final_xobjs


def append_xarray_dicts(xobjs_list):
    """Append two dictionaries of xarray objects."""
    final_xobjs = {}
    # Loop through all the datasets in the first
    # xarray object - these should be the same in all
    min_start_dt = xobjs_list[0]["METADATA"].attrs["start_datetime"]
    max_end_dt = xobjs_list[0]["METADATA"].attrs["end_datetime"]
    final_xobjs["METADATA"] = xobjs_list[0]["METADATA"][[]]
    for dsname in xobjs_list[0]:
        xobjs_ds_list = []
        for xobjs in xobjs_list:
            xobjs_ds_list += [xobjs[dsname]]
            curr_start_dt = xobjs[dsname].attrs["start_datetime"]
            curr_end_dt = xobjs[dsname].attrs["end_datetime"]
            if curr_start_dt < min_start_dt:
                min_start_dt = curr_start_dt
            if curr_end_dt > max_end_dt:
                max_end_dt = curr_end_dt
        if dsname != "METADATA":
            final_xobjs[dsname] = xr.concat(xobjs_ds_list, dim="dim_0")
        final_xobjs[dsname].attrs["start_datetime"] = min_start_dt
        final_xobjs[dsname].attrs["end_datetime"] = max_end_dt
    final_xobjs["METADATA"].attrs["start_datetime"] = min_start_dt
    final_xobjs["METADATA"].attrs["end_datetime"] = max_end_dt
    return final_xobjs


def read_ssmis_data_file(fname, metadata_only=False):
    """Read a single SSMIS data file."""
    data_name = basename(fname).split("_")[-1].split(".")[-1]

    if data_name != "raw":
        LOG.warning("Warning: wrong SSMI SDR data type:  data_type=%s", data_name)
        raise

    if "cfnoc" in basename(fname) and "sdris" in basename(fname):
        LOG.info("found a SSMIS SDR file")
    else:
        LOG.info("not a SSMIS SDR file: skip it")
        raise

    # ------------------------  Process of dataset ---------------------------

    f1 = open(fname, "rb")

    # READ HEARDER
    sw_rev = np.fromstring(f1.read(2), dtype=np.dtype("short")).byteswap()[0]  # NOQA
    endian, fileid = np.fromstring(
        f1.read(2), dtype=np.dtype("int8")
    ).byteswap()  # NOQA
    rev = np.fromstring(f1.read(4), dtype=np.dtype("int32")).byteswap()
    year = np.fromstring(f1.read(4), dtype=np.dtype("int32")).byteswap()
    jday = np.fromstring(f1.read(2), dtype=np.dtype("short")).byteswap()
    hour, minu = np.fromstring(f1.read(2), dtype=np.dtype("int8")).byteswap()
    satid, nsdr = np.fromstring(f1.read(4), dtype=np.dtype("short")).byteswap()
    spare1, spare2, spare3 = np.fromstring(  # NOQA
        f1.read(3), dtype=np.dtype("int8")
    ).byteswap()
    proc_stat_flags = np.fromstring(  # NOQA
        f1.read(1), dtype=np.dtype("int8")
    ).byteswap()  # NOQA
    spare4 = np.fromstring(f1.read(4), dtype=np.dtype("int32")).byteswap()  # NOQA
    # Need to set up time to be read in by the metadata (year and jday are arrays)
    time = "%04d%03d%02d%02d" % (year[0], jday[0], hour, minu)  # NOQA
    nbytes = 28  # bytes that have been read in
    # Read scan records at 512-byte boundaries
    nfiller = 512 - (
        nbytes % 512
    )  # skip nfiller bytes so that the scan header will start at the 513th byte of
    # the data records,
    filler_bytes = np.fromstring(
        f1.read(nfiller), dtype=np.dtype("int8")
    ).byteswap()  # NOQA

    # Rev 6A of the SSMIS SDR software changed the scalling of channel 12-16 to 100
    # (it was 10 before this change) effective with orbit rev 12216 for F-16 and
    # thereafter for all future satellites
    rev6a = 1
    # When revs wrapped back to 0, the rev[0] < 12216 was no longer valid.
    # Check that rev < 12216, AND year < 2023 (revs wrapped on 7 March 2023)
    if satid == 1 and rev[0] < 12216 and year < 2023:
        rev6a = 0

    if satid == 1:
        satid = "F16"
    elif satid == 2:
        satid = "F17"
    elif satid == 3:
        satid = "F18"
    elif satid == 4:
        satid = "F19"

    satellite_zenith_angle = 53.1
    sensor_scan_angle = 45.0
    satellite_altitude = 859

    # bad_value = -999

    for nn in range(nsdr):  # loop number of sdr data records
        nbytes = 0

        # SCAN HEADER
        syncword = np.fromstring(f1.read(4), dtype=np.dtype("int32")).byteswap()  # NOQA
        scan_year = np.fromstring(f1.read(4), dtype=np.dtype("int32")).byteswap()
        scan_jday = np.fromstring(f1.read(2), dtype=np.dtype("short")).byteswap()
        scan_hour, scan_minu = np.fromstring(
            f1.read(2), dtype=np.dtype("int8")
        ).byteswap()
        scan = np.fromstring(f1.read(4), dtype=np.dtype("int32")).byteswap()  # NOQA
        nscan_imager, nscan_enviro, nscan_las, nscan_uas = np.fromstring(
            f1.read(4), dtype=np.dtype("int8")
        ).byteswap()
        start_scantime_imager = np.fromstring(
            f1.read(112), dtype=np.dtype("int32")
        ).byteswap()
        scenecounts_imager = np.fromstring(
            f1.read(28), dtype=np.dtype("uint8")
        ).byteswap()
        start_scantime_enviro = np.fromstring(
            f1.read(96), dtype=np.dtype("int32")
        ).byteswap()
        scenecounts_enviro = np.fromstring(
            f1.read(24), dtype=np.dtype("uint8")
        ).byteswap()
        start_scantime_las = np.fromstring(
            f1.read(32), dtype=np.dtype("int32")
        ).byteswap()
        scenecounts_las = np.fromstring(f1.read(8), dtype=np.dtype("uint8")).byteswap()
        start_scantime_uas = np.fromstring(
            f1.read(16), dtype=np.dtype("int32")
        ).byteswap()
        scenecounts_uas = np.fromstring(f1.read(4), dtype=np.dtype("uint8")).byteswap()
        spare = np.fromstring(f1.read(20), dtype=np.dtype("int32")).byteswap()  # NOQA
        nbytes += 360  # total bytes of the scan header
        # nscan0 = scan - 1  # number of scans

        # not use geoips functions for time variables
        yyyyjjjhhmn = "{0:4d}{1:03d}{2:02d}{3:02d}".format(
            scan_year[0], scan_jday[0], scan_hour, scan_minu
        )

        # set up start and end toem of this data

        if nn == 0:
            start_time = yyyyjjjhhmn
        # if nn == nsdr - 1:
        #     end_time = yyyyjjjhhmn

        try:
            # The start end time in the standard file name seems to be a bit more
            # reliable, so try parsing the file name first before falling back
            # on the header information in the binary file

            # Grab only the file name
            bfname = basename(fname)

            # Standard SSMIS file names are the following format:
            # <FILE_ID>_<SATELLITE>_<DATE>_<START>_<END>_<REV>_<EXTENSION>
            split_fname = bfname.split("_")
            date = split_fname[2]
            start = split_fname[3]
            end = split_fname[4]
            start_datetime = datetime.strptime(date + start, "d%Y%m%ds%H%M%S")
            end_datetime = datetime.strptime(date + end, "d%Y%m%de%H%M%S")
            if end_datetime < start_datetime:
                # Rolled over to new day
                end_datetime += timedelta(days=1)
        except ValueError:
            # Could not parse the start/end time from the file name
            # Fall back on using info in header
            start_datetime = datetime.strptime(start_time, "%Y%j%H%M")

            # Estimate end time just for metadata purposes
            # To my knowledge, the file end time is not included in the binary header
            # The following offset was determined by taking the start/end time
            # listed in the file name, then dividing the total number of seconds by the
            # number of sensor data records, which came out to 45.5 seconds
            estimated_seconds_per_sensor_data_record = 45.5
            seconds_offset = estimated_seconds_per_sensor_data_record * nsdr
            end_datetime = start_datetime + timedelta(seconds=seconds_offset)

        try:
            # The start end time in the standard file name seems to be a bit more
            # reliable, so try parsing the file name first before falling back
            # on the header information in the binary file

            # Grab only the file name
            bfname = basename(fname)

            # Standard SSMIS file names are the following format:
            # <FILE_ID>_<SATELLITE>_<DATE>_<START>_<END>_<REV>_<EXTENSION>
            split_fname = bfname.split("_")
            date = split_fname[2]
            start = split_fname[3]
            end = split_fname[4]
            start_datetime = datetime.strptime(date + start, "d%Y%m%ds%H%M%S")
            end_datetime = datetime.strptime(date + end, "d%Y%m%de%H%M%S")
            if end_datetime < start_datetime:
                # Rolled over to new day
                end_datetime += timedelta(days=1)
        except ValueError:
            # Could not parse the start/end time from the file name
            # Fall back on using info in header
            start_datetime = datetime.strptime(start_time, "%Y%j%H%M")

            # Estimate end time just for metadata purposes
            # To my knowledge, the file end time is not included in the binary header
            # The following offset was determined by taking the start/end time
            # listed in the file name, then dividing the total number of seconds by the
            # number of sensor data records, which came out to 45.5 seconds
            estimated_seconds_per_sensor_data_record = 45.5
            seconds_offset = estimated_seconds_per_sensor_data_record * nsdr
            end_datetime = start_datetime + timedelta(seconds=seconds_offset)

        try:
            # The start end time in the standard file name seems to be a bit more
            # reliable, so try parsing the file name first before falling back
            # on the header information in the binary file

            # Grab only the file name
            bfname = basename(fname)

            # Standard SSMIS file names are the following format:
            # <FILE_ID>_<SATELLITE>_<DATE>_<START>_<END>_<REV>_<EXTENSION>
            split_fname = bfname.split("_")
            date = split_fname[2]
            start = split_fname[3]
            end = split_fname[4]
            start_datetime = datetime.strptime(date + start, "d%Y%m%ds%H%M%S")
            end_datetime = datetime.strptime(date + end, "d%Y%m%de%H%M%S")
            if end_datetime < start_datetime:
                # Rolled over to new day
                end_datetime += timedelta(days=1)
        except ValueError:
            # Could not parse the start/end time from the file name
            # Fall back on using info in header
            start_datetime = datetime.strptime(start_time, "%Y%j%H%M")

            # Estimate end time just for metadata purposes
            # To my knowledge, the file end time is not included in the binary header
            # The following offset was determined by taking the start/end time
            # listed in the file name, then dividing the total number of seconds by the
            # number of sensor data records, which came out to 45.5 seconds
            estimated_seconds_per_sensor_data_record = 45.5
            seconds_offset = estimated_seconds_per_sensor_data_record * nsdr
            end_datetime = start_datetime + timedelta(seconds=seconds_offset)

        if metadata_only:
            xarray_imager = xr.Dataset()
            xarray_imager.attrs["start_datetime"] = start_datetime
            xarray_imager.attrs["end_datetime"] = end_datetime
            xarray_imager.attrs["source_name"] = "ssmis"
            xarray_imager.attrs["platform_name"] = satid
            xarray_imager.attrs["data_provider"] = "DMSP"
            xarray_imager.attrs["source_file_names"] = [basename(fname)]
            xarray_imager.attrs["satellite_zenith_angle"] = satellite_zenith_angle
            xarray_imager.attrs["sensor_scan_angle"] = sensor_scan_angle
            xarray_imager.attrs["satellite_altitude"] = satellite_altitude
            LOG.info(
                "approximate start_time, end_time= %s, %s",
                xarray_imager.start_datetime,
                xarray_imager.end_datetime,
            )
            return {"METADATA": xarray_imager}

        # -----------------------------------------------------------------------------------------

        #       -------- Apply the GEOIPS framework in XARRAY data frame ----------

        if scenecounts_imager[0] < 0:
            LOG.info("IMAGER is negative")

        # initilization of imager variables

        lt_img = np.zeros((nscan_imager, 180))
        lg_img = np.zeros((nscan_imager, 180))
        ch08 = np.zeros((nscan_imager, 180))
        ch09 = np.zeros((nscan_imager, 180))
        ch10 = np.zeros((nscan_imager, 180))
        ch11 = np.zeros((nscan_imager, 180))
        ch17 = np.zeros((nscan_imager, 180))
        ch18 = np.zeros((nscan_imager, 180))
        surf = np.zeros((nscan_imager, 180))
        rain = np.zeros((nscan_imager, 180))
        time_imager = np.zeros((nscan_imager, 180))

        # IMAGER READ DATA
        for ii in range(nscan_imager):
            if start_scantime_imager[ii] == -999:
                LOG.info("value of imager scan is %s", ii)
                continue
            for jj in range(scenecounts_imager[ii]):
                imager_lat, imager_lon, imager_scene = np.fromstring(
                    f1.read(6), dtype=np.dtype("short")
                ).byteswap()
                imager_surf, imager_rain = np.fromstring(
                    f1.read(2), dtype=np.dtype("int8")
                ).byteswap()
                (
                    imager_ch08,
                    imager_ch09,
                    imager_ch10,
                    imager_ch11,
                    imager_ch17,
                    imager_ch18,
                ) = np.fromstring(f1.read(12), dtype=np.dtype("short")).byteswap()
                nbytes += 20
                # k = 180 * (nscan0 + ii) + jj
                lat = 0.01 * imager_lat
                lon = 0.01 * imager_lon
                try:
                    lt_img[ii][jj] = lat
                    lg_img[ii][jj] = lon
                    ch08[ii][jj] = imager_ch08  # 150    Ghz
                    ch09[ii][jj] = imager_ch09  # 183+-7
                    ch10[ii][jj] = imager_ch10  # 183+-3
                    ch11[ii][jj] = imager_ch11  # 183+-1
                    ch17[ii][jj] = imager_ch17  # 91V
                    ch18[ii][jj] = imager_ch18  # 91H
                    surf[ii][jj] = imager_surf
                    rain[ii][jj] = imager_rain
                except ValueError:
                    LOG.info("Failed setting arrays in scan_imager")

        time_imager[:][
            :
        ] = yyyyjjjhhmn  # set same time for this data record and must use the
        # datetime64 format

        # catenation of data records
        if nn == 0:
            lt_img_pre = lt_img
            lg_img_pre = lg_img
            ch08_pre = ch08
            ch09_pre = ch09
            ch10_pre = ch10
            ch11_pre = ch11
            ch17_pre = ch17
            ch18_pre = ch18
            surf_pre = surf
            rain_pre = rain
            time_imager_pre = time_imager
        else:
            lt_img = np.vstack((lt_img_pre, lt_img))
            lg_img = np.vstack((lg_img_pre, lg_img))
            ch08 = np.vstack((ch08_pre, ch08))
            ch09 = np.vstack((ch09_pre, ch09))
            ch10 = np.vstack((ch10_pre, ch10))
            ch11 = np.vstack((ch11_pre, ch11))
            ch17 = np.vstack((ch17_pre, ch17))
            ch18 = np.vstack((ch18_pre, ch18))
            surf = np.vstack((surf_pre, surf))
            rain = np.vstack((rain_pre, rain))
            time_imager = np.vstack((time_imager_pre, time_imager))

        # reset pre_catinated arrays
        lt_img_pre = lt_img
        lg_img_pre = lg_img
        ch08_pre = ch08
        ch09_pre = ch09
        ch10_pre = ch10
        ch11_pre = ch11
        ch17_pre = ch17
        ch18_pre = ch18
        surf_pre = surf
        rain_pre = rain
        time_imager_pre = time_imager

        # -----------------------------------------------------------------------------------------
        #
        #       for ENVIRONMENTAL Variables

        if scenecounts_enviro[0] < 0:
            LOG.info("ENVIRO is negative")

        # initilization of imager variables

        lt_env = np.zeros((nscan_enviro, 90))
        lg_env = np.zeros((nscan_enviro, 90))
        ch12 = np.zeros((nscan_enviro, 90))
        ch13 = np.zeros((nscan_enviro, 90))
        ch14 = np.zeros((nscan_enviro, 90))
        ch15 = np.zeros((nscan_enviro, 90))
        ch16 = np.zeros((nscan_enviro, 90))
        ch15_5x5 = np.zeros((nscan_enviro, 90))
        ch16_5x5 = np.zeros((nscan_enviro, 90))
        ch17_5x5 = np.zeros((nscan_enviro, 90))
        ch18_5x5 = np.zeros((nscan_enviro, 90))
        ch17_5x4 = np.zeros((nscan_enviro, 90))
        ch18_5x4 = np.zeros((nscan_enviro, 90))
        time_enviro = np.zeros((nscan_enviro, 90))

        # ENVIRO READ DATA
        for ii in range(nscan_enviro):
            if ii % 2 == 0:  # for odd scan numbers
                if start_scantime_enviro[ii] == -999:
                    LOG.info("value of enviro odd scan is %s", ii)
                    continue
                for jj in range(scenecounts_enviro[ii]):
                    enviroodd_lat, enviroodd_lon, enviroodd_scene = np.fromstring(
                        f1.read(6), dtype=np.dtype("short")
                    ).byteswap()
                    enviroodd_seaice, enviroodd_surf = np.fromstring(
                        f1.read(2), dtype=np.dtype("int8")
                    ).byteswap()
                    (
                        enviroodd_ch12,
                        enviroodd_ch13,
                        enviroodd_ch14,
                        enviroodd_ch15,
                        enviroodd_ch16,
                        enviroodd_ch15_5x5,
                        enviroodd_ch16_5x5,
                        enviroodd_ch17_5x5,
                        enviroodd_ch18_5x5,
                        enviroodd_ch17_5x4,
                        enviroodd_ch18_5x4,
                    ) = np.fromstring(f1.read(22), dtype=np.dtype("short")).byteswap()
                    enviroodd_rain1, enviroodd_rain2 = np.fromstring(
                        f1.read(2), dtype=np.dtype("int8")
                    ).byteswap()
                    edr_bitflags = np.fromstring(  # NOQA
                        f1.read(4), dtype=np.dtype("int32")
                    ).byteswap()
                    nbytes += 36
                    lat = 0.01 * enviroodd_lat
                    lon = 0.01 * enviroodd_lon
                    lt_env[ii][jj] = lat
                    lg_env[ii][jj] = lon
                    if rev6a == 1:
                        ch12[ii][jj] = enviroodd_ch12  # 19H
                        ch13[ii][jj] = enviroodd_ch13  # 19V
                        ch14[ii][jj] = enviroodd_ch14  # 22V
                        ch15[ii][jj] = enviroodd_ch15  # 37H
                        ch16[ii][jj] = enviroodd_ch16  # 37V
                        ch15_5x5[ii][jj] = enviroodd_ch15_5x5
                        ch16_5x5[ii][jj] = enviroodd_ch16_5x5
                        ch17_5x5[ii][jj] = enviroodd_ch17_5x5
                        ch18_5x5[ii][jj] = enviroodd_ch18_5x5
                        ch17_5x4[ii][jj] = enviroodd_ch17_5x4
                        ch18_5x4[ii][jj] = enviroodd_ch18_5x4
                    else:
                        ch12[ii][jj] = 10 * enviroodd_ch12
                        ch13[ii][jj] = 10 * enviroodd_ch13
                        ch14[ii][jj] = 10 * enviroodd_ch14
                        ch15[ii][jj] = 10 * enviroodd_ch15
                        ch16[ii][jj] = 10 * enviroodd_ch16
                        ch15_5x5[ii][jj] = 10 * enviroodd_ch15_5x5
                        ch16_5x5[ii][jj] = 10 * enviroodd_ch16_5x5
                        ch17_5x5[ii][jj] = 10 * enviroodd_ch17_5x5
                        ch18_5x5[ii][jj] = 10 * enviroodd_ch18_5x5
                        ch17_5x4[ii][jj] = 10 * enviroodd_ch17_5x4
                        ch18_5x4[ii][jj] = 10 * enviroodd_ch18_5x4

            if (
                ii % 2 == 1
            ):  # for even scan numbers (ch15_5x5, ch16_5x5, ch17_5x5, ch18_5x5,
                # ch17_5x4, ch18_5x4 ??? need a review)
                if start_scantime_enviro[ii] == -999:
                    LOG.info("value of enviro even scan is %s", ii)
                    continue
                for jj in range(scenecounts_enviro[ii]):
                    enviroeven_lat, enviroeven_lon, enviroeven_scene = np.fromstring(
                        f1.read(6), dtype=np.dtype("short")
                    ).byteswap()
                    enviroeven_seaice, enviroeven_surf = np.fromstring(
                        f1.read(2), dtype=np.dtype("int8")
                    ).byteswap()
                    (
                        enviroeven_ch12,
                        enviroeven_ch13,
                        enviroeven_ch14,
                        enviroeven_ch15,
                        enviroeven_ch16,
                    ) = np.fromstring(f1.read(10), dtype=np.dtype("short")).byteswap()
                    nbytes += 18
                    lat = 0.01 * enviroeven_lat
                    lon = 0.01 * enviroeven_lon
                    lt_env[ii][jj] = lat
                    lg_env[ii][jj] = lon
                    if rev6a == 1:
                        ch12[ii][jj] = enviroeven_ch12
                        ch13[ii][jj] = enviroeven_ch13
                        ch14[ii][jj] = enviroeven_ch14
                        ch15[ii][jj] = enviroeven_ch15
                        ch16[ii][jj] = enviroeven_ch16
                    else:
                        ch12[ii][jj] = 10 * enviroeven_ch12
                        ch13[ii][jj] = 10 * enviroeven_ch13
                        ch14[ii][jj] = 10 * enviroeven_ch14
                        ch15[ii][jj] = 10 * enviroeven_ch15
                        ch16[ii][jj] = 10 * enviroeven_ch16

        time_enviro[:][:] = yyyyjjjhhmn

        # catenation of data records
        if nn == 0:
            lt_env_pre = lt_env
            lg_env_pre = lg_env
            ch12_pre = ch12
            ch13_pre = ch13
            ch14_pre = ch14
            ch15_pre = ch15
            ch16_pre = ch16
            time_enviro_pre = time_enviro

            ch15_5x5_pre = ch15_5x5
            ch16_5x5_pre = ch16_5x5
            ch17_5x5_pre = ch17_5x5
            ch18_5x5_pre = ch18_5x5
            ch17_5x4_pre = ch17_5x4
            ch18_5x4_pre = ch18_5x4
        else:
            lt_env = np.vstack((lt_env_pre, lt_env))
            lg_env = np.vstack((lg_env_pre, lg_env))
            ch12 = np.vstack((ch12_pre, ch12))
            ch13 = np.vstack((ch13_pre, ch13))
            ch14 = np.vstack((ch14_pre, ch14))
            ch15 = np.vstack((ch15_pre, ch15))
            ch16 = np.vstack((ch16_pre, ch16))
            time_enviro = np.vstack((time_enviro_pre, time_enviro))

            ch15_5x5 = np.vstack((ch15_5x5_pre, ch15_5x5))
            ch16_5x5 = np.vstack((ch16_5x5_pre, ch16_5x5))
            ch17_5x5 = np.vstack((ch17_5x5_pre, ch17_5x5))
            ch18_5x5 = np.vstack((ch18_5x5_pre, ch18_5x5))
            ch17_5x4 = np.vstack((ch17_5x4_pre, ch17_5x4))
            ch18_5x4 = np.vstack((ch18_5x4_pre, ch18_5x4))

        # reset pre_catinated arrays
        lt_env_pre = lt_env
        lg_env_pre = lg_env
        ch12_pre = ch12
        ch13_pre = ch13
        ch14_pre = ch14
        ch15_pre = ch15
        ch16_pre = ch16
        time_enviro_pre = time_enviro

        ch15_5x5_pre = ch15_5x5
        ch16_5x5_pre = ch16_5x5
        ch17_5x5_pre = ch17_5x5
        ch18_5x5_pre = ch18_5x5
        ch17_5x4_pre = ch17_5x4
        ch18_5x4_pre = ch18_5x4

        # -----------------------------------------------------------------------------------------
        #           Process LAS data record

        if scenecounts_las[0] < 0:
            LOG.info("LAS is negative")

        lt_las = np.zeros((nscan_las, 60))
        lg_las = np.zeros((nscan_las, 60))
        ch01_3x3 = np.zeros((nscan_las, 60))
        ch02_3x3 = np.zeros((nscan_las, 60))
        ch03_3x3 = np.zeros((nscan_las, 60))
        ch04_3x3 = np.zeros((nscan_las, 60))
        ch05_3x3 = np.zeros((nscan_las, 60))
        ch06_3x3 = np.zeros((nscan_las, 60))
        ch07_3x3 = np.zeros((nscan_las, 60))
        ch08_5x5 = np.zeros((nscan_las, 60))
        ch09_5x5 = np.zeros((nscan_las, 60))
        ch10_5x5 = np.zeros((nscan_las, 60))
        ch11_5x5 = np.zeros((nscan_las, 60))
        ch18_5x5_las = np.zeros((nscan_las, 60))
        ch24_3x3 = np.zeros((nscan_las, 60))
        surf_las = np.zeros((nscan_las, 60))
        time_las = np.zeros((nscan_las, 60))
        height_1000mb = np.zeros((nscan_las, 60))

        # LAS READ DATA
        for ii in range(nscan_las):
            if start_scantime_las[ii] == -999:
                LOG.info("value of las scan is %s", ii)
                continue
            for jj in range(scenecounts_las[ii]):
                try:
                    (
                        las_lat,
                        las_lon,
                        las_ch01_3x3,
                        las_ch02_3x3,
                        las_ch03_3x3,
                        las_ch04_3x3,
                        las_ch05_3x3,
                        las_ch06_3x3,
                        las_ch07_3x3,
                        las_ch08_5x5,
                        las_ch09_5x5,
                        las_ch10_5x5,
                        las_ch11_5x5,
                        las_ch18_5x5,
                        las_ch24_3x3,
                        las_height_1000mb,
                        las_surf,
                    ) = np.fromstring(f1.read(34), dtype=np.dtype("short")).byteswap()
                    las_tqflag, las_hqflag = np.fromstring(
                        f1.read(2), dtype=np.dtype("int8")
                    ).byteswap()
                    las_terrain, las_scene = np.fromstring(
                        f1.read(4), dtype=np.dtype("short")
                    ).byteswap()
                except Exception as resp:
                    LOG.info(
                        "Poorly formatted scene # %s, skipping. resp: %s",
                        str(jj),
                        str(resp),
                    )
                    continue

                lat = 0.01 * las_lat
                lon = 0.01 * las_lon
                nbytes += 40
                lt_las[ii][jj] = lat
                lg_las[ii][jj] = lon
                ch01_3x3[ii][jj] = las_ch01_3x3  # 50.3 V
                ch02_3x3[ii][jj] = las_ch02_3x3  # 52.8 V
                ch03_3x3[ii][jj] = las_ch03_3x3  # 53.60V
                ch04_3x3[ii][jj] = las_ch04_3x3  # 54.4 V
                ch05_3x3[ii][jj] = las_ch05_3x3  # 55.5 V
                ch06_3x3[ii][jj] = las_ch06_3x3  # 57.3 RCP
                ch07_3x3[ii][jj] = las_ch07_3x3  # 59.4 RCP
                ch08_5x5[ii][jj] = las_ch08_5x5  # 150 H
                ch09_5x5[ii][jj] = las_ch09_5x5  # 183.31+-7 H
                ch10_5x5[ii][jj] = las_ch10_5x5  # 183.31+-3 H
                ch11_5x5[ii][jj] = las_ch11_5x5  # 183.31+-1 H
                ch18_5x5[ii][jj] = las_ch18_5x5  # 91 H
                ch24_3x3[ii][jj] = las_ch24_3x3  # 60.79+-36+-0.05 RCP
                surf_las[ii][jj] = las_surf
                height_1000mb[ii][jj] = las_height_1000mb

        time_las[:][:] = yyyyjjjhhmn

        # catenation of data records
        if nn == 0:
            lt_las_pre = lt_las
            lg_las_pre = lg_las
            ch01_3x3_pre = ch01_3x3
            ch02_3x3_pre = ch02_3x3
            ch03_3x3_pre = ch03_3x3
            ch04_3x3_pre = ch04_3x3
            ch05_3x3_pre = ch05_3x3
            ch06_3x3_pre = ch06_3x3
            ch07_3x3_pre = ch07_3x3
            ch08_5x5_pre = ch08_5x5
            ch09_5x5_pre = ch09_5x5
            ch10_5x5_pre = ch10_5x5
            ch11_5x5_pre = ch11_5x5
            ch18_5x5_las_pre = ch18_5x5_las
            ch24_3x3_pre = ch24_3x3
            surf_las_pre = surf_las
            height_1000mb_pre = height_1000mb
            time_las_pre = time_las
        else:
            lt_las = np.vstack((lt_las_pre, lt_las))
            lg_las = np.vstack((lg_las_pre, lg_las))
            ch01_3x3 = np.vstack((ch01_3x3_pre, ch01_3x3))
            ch02_3x3 = np.vstack((ch02_3x3_pre, ch02_3x3))
            ch03_3x3 = np.vstack((ch03_3x3_pre, ch03_3x3))
            ch04_3x3 = np.vstack((ch04_3x3_pre, ch04_3x3))
            ch05_3x3 = np.vstack((ch05_3x3_pre, ch05_3x3))
            ch06_3x3 = np.vstack((ch06_3x3_pre, ch06_3x3))
            ch07_3x3 = np.vstack((ch07_3x3_pre, ch07_3x3))
            ch08_5x5 = np.vstack((ch08_5x5_pre, ch08_5x5))
            ch09_5x5 = np.vstack((ch09_5x5_pre, ch09_5x5))
            ch10_5x5 = np.vstack((ch10_5x5_pre, ch10_5x5))
            ch11_5x5 = np.vstack((ch11_5x5_pre, ch11_5x5))
            ch18_5x5_las = np.vstack((ch18_5x5_las_pre, ch18_5x5_las))
            ch24_3x3 = np.vstack((ch24_3x3_pre, ch24_3x3))
            surf_las = np.vstack((surf_las_pre, surf_las))
            height_1000mb = np.vstack((height_1000mb_pre, height_1000mb))
            time_las = np.vstack((time_las_pre, time_las))

        # reset pre_catinated arrays
        lt_las_pre = lt_las
        lg_las_pre = lg_las
        ch01_3x3_pre = ch01_3x3
        ch02_3x3_pre = ch02_3x3
        ch03_3x3_pre = ch03_3x3
        ch04_3x3_pre = ch04_3x3
        ch05_3x3_pre = ch05_3x3
        ch06_3x3_pre = ch06_3x3
        ch07_3x3_pre = ch07_3x3
        ch08_5x5_pre = ch08_5x5
        ch09_5x5_pre = ch09_5x5
        ch10_5x5_pre = ch10_5x5
        ch11_5x5_pre = ch11_5x5
        ch18_5x5_las_pre = ch18_5x5_las
        ch24_3x3_pre = ch24_3x3
        surf_las_pre = surf_las
        height_1000mb_pre = height_1000mb
        time_las_pre = time_las

        # ---------------------------------------------------------------------------------
        #          Process UAS data record

        if scenecounts_uas[0] < 0:
            LOG.info("UAS is negative")

        lt_uas = np.zeros((nscan_uas, 30))
        lg_uas = np.zeros((nscan_uas, 30))
        ch19_6x6 = np.zeros((nscan_uas, 30))
        ch20_6x6 = np.zeros((nscan_uas, 30))
        ch21_6x6 = np.zeros((nscan_uas, 30))
        ch22_6x6 = np.zeros((nscan_uas, 30))
        ch23_6x6 = np.zeros((nscan_uas, 30))
        ch24_6x6 = np.zeros((nscan_uas, 30))
        scene = np.zeros((nscan_uas, 30))
        tqflag = np.zeros((nscan_uas, 30))
        time_uas = np.zeros((nscan_uas, 30))

        # UAS READ DATA
        for ii in range(nscan_uas):
            if start_scantime_uas[ii] == -999:
                LOG.info("value of uas scan is %s", ii)
                continue
            for jj in range(scenecounts_uas[ii]):
                (
                    uas_lat,
                    uas_lon,
                    uas_ch19_6x6,
                    uas_ch20_6x6,
                    uas_ch21_6x6,
                    uas_ch22_6x6,
                    uas_ch23_6x6,
                    uas_ch24_6x6,
                    uas_scene,
                    uas_tqflag,
                ) = np.fromstring(f1.read(20), dtype=np.dtype("short")).byteswap()
                uas_field, uas_bdotk2 = np.fromstring(
                    f1.read(8), dtype=np.dtype("int32")
                ).byteswap()
                nbytes += 28
                lat = 0.01 * uas_lat
                lon = 0.01 * uas_lon
                lt_uas[ii][jj] = lat
                lg_uas[ii][jj] = lon
                ch19_6x6[ii][jj] = uas_ch19_6x6  # 63.28+-0.28 RCP GHz
                ch20_6x6[ii][jj] = uas_ch20_6x6  # 60.79+-0.36 RCP
                ch21_6x6[ii][jj] = uas_ch21_6x6  # 60.79+-0.36+-0.002 RCP
                ch22_6x6[ii][jj] = uas_ch22_6x6  # 60.79+-0.36+-0.0055 RCP
                ch23_6x6[ii][jj] = uas_ch23_6x6  # 60.79+-0.36+-0.0016 RCP
                ch24_6x6[ii][jj] = uas_ch24_6x6  # 60.79+-0.36+-0.050 RCP
                scene[ii][jj] = uas_scene
                tqflag[ii][jj] = uas_tqflag

        time_uas[:][:] = yyyyjjjhhmn

        # catenation of data records
        if nn == 0:
            lt_uas_pre = lt_uas
            lg_uas_pre = lg_uas
            ch19_6x6_pre = ch19_6x6
            ch20_6x6_pre = ch20_6x6
            ch21_6x6_pre = ch21_6x6
            ch22_6x6_pre = ch22_6x6
            ch23_6x6_pre = ch23_6x6
            ch24_6x6_pre = ch24_6x6
            scene_pre = scene
            tqflag_pre = tqflag
            time_uas_pre = time_uas
        else:
            lt_uas = np.vstack((lt_uas_pre, lt_uas))
            lg_uas = np.vstack((lg_uas_pre, lg_uas))
            ch19_6x6 = np.vstack((ch19_6x6_pre, ch19_6x6))
            ch20_6x6 = np.vstack((ch20_6x6_pre, ch20_6x6))
            ch21_6x6 = np.vstack((ch21_6x6_pre, ch21_6x6))
            ch22_6x6 = np.vstack((ch22_6x6_pre, ch22_6x6))
            ch23_6x6 = np.vstack((ch23_6x6_pre, ch23_6x6))
            ch24_6x6 = np.vstack((ch24_6x6_pre, ch24_6x6))
            scene = np.vstack((scene_pre, scene))
            tqflag = np.vstack((tqflag_pre, tqflag))
            time_uas = np.vstack((time_uas_pre, time_uas))

        # reset pre_catinated arrays
        lt_uas_pre = lt_uas
        lg_uas_pre = lg_uas
        ch19_6x6_pre = ch19_6x6
        ch20_6x6_pre = ch20_6x6
        ch21_6x6_pre = ch21_6x6
        ch22_6x6_pre = ch22_6x6
        ch23_6x6_pre = ch23_6x6
        ch24_6x6_pre = ch24_6x6
        scene_pre = scene
        tqflag_pre = tqflag
        time_uas_pre = time_uas

        # -------------------------------------------------------------------------------------------------------
        #       fill up space
        nfiller = 512 - (
            nbytes % 512
        )  # nfiller bytes to be skipped so that the next scan header will start at
        # the 513th byte.
        try:
            filler_bytes = np.fromstring(  # NOQA
                f1.read(nfiller), dtype=np.dtype("int8")
            ).byteswap()[0]
        except Exception as resp:
            LOG.info("Poorly formatted filler_bytes, skipping. resp: %s", str(resp))
            continue

    f1.close()

    LOG.info("start_time, end_time= %s, %s", start_datetime, end_datetime)

    # --------------------- Xarray Objects for Processing Datasets------------
    #   conversion of TBs to K
    #             TBs/100 + 273.15   (K)
    #             setup xarray objects
    namelist_imager = [  # NOQA
        "latitude",
        "longitude",
        "H150",
        "H183-7",
        "H183-3",
        "H183-1",
        "V91",
        "H91",
        "sfcType",
        "rain",
        "time",
    ]
    # namelist_enviro = [
    #     "latitude",
    #     "longitude",
    #     "H19",
    #     "V19",
    #     "V22",
    #     "H37",
    #     "V37",
    #     "ch15_5x5",
    #     "ch16_5x5",
    #     "ch17_5x5",
    #     "ch18_5x5",
    #     "ch17_5x4",
    #     "ch18_5x4",
    #     "time",
    # ]
    # namelist_las = [
    #     "latitude",
    #     "longitude",
    #     "ch01_3x3",
    #     "ch02_3x3",
    #     "ch03_3x3",
    #     "ch04_3x3",
    #     "ch05_3x3",
    #     "ch06_3x3",
    #     "ch07_3x3",
    #     "ch08_5x5",
    #     "ch09_5x5",
    #     "ch10_5x5",
    #     "ch11_5x5",
    #     "ch18_5x5_las",
    #     "ch24_3x3",
    #     "height_1000mb",
    #     "surf_las",
    #     "time",
    # ]
    # namelist_uas = [
    #     "latitude",
    #     "longitude",
    #     "ch19_6x6",
    #     "ch20_6x6",
    #     "ch21_6x6",
    #     "ch22_6x6",
    #     "ch23_6x6",
    #     "ch24_6x6",
    #     "scene",
    #     "tqflag",
    #     "time",
    # ]

    # set xarray object for imager variables
    xarray_imager = xr.Dataset()
    xarray_imager["latitude"] = xr.DataArray(lt_img)
    xarray_imager["longitude"] = xr.DataArray(lg_img)
    # xarray_imager['V150']     = xr.DataArray(ch08/100+273.15)
    # xarray_imager['V150'].attrs['channel_number'] = 8
    xarray_imager["H150"] = xr.DataArray(
        ch08 / 100 + 273.15
    )  # ch08 is 150GHz-H, not 150GHz-V
    xarray_imager["H150"].attrs["channel_number"] = 8
    xarray_imager["H183-7"] = xr.DataArray(ch09 / 100 + 273.15)
    xarray_imager["H183-7"].attrs["channel_number"] = 9
    xarray_imager["H183-3"] = xr.DataArray(ch10 / 100 + 273.15)
    xarray_imager["H183-3"].attrs["channel_number"] = 10
    xarray_imager["H183-1"] = xr.DataArray(ch11 / 100 + 273.15)
    xarray_imager["H183-1"].attrs["channel_number"] = 11
    xarray_imager["V91"] = xr.DataArray(ch17 / 100 + 273.15)
    xarray_imager["V91"].attrs["channel_number"] = 17
    xarray_imager["H91"] = xr.DataArray(ch18 / 100 + 273.15)
    xarray_imager["H91"].attrs["channel_number"] = 18
    xarray_imager["sfcType"] = xr.DataArray(surf)
    xarray_imager["rain"] = xr.DataArray(rain)
    xarray_imager["time"] = xr.DataArray(
        pd.DataFrame(time_imager).astype(int).apply(pd.to_datetime, format="%Y%j%H%M")
    )

    # set xarray object for enviro  variables
    xarray_enviro = xr.Dataset()
    xarray_enviro["latitude"] = xr.DataArray(lt_env)
    xarray_enviro["longitude"] = xr.DataArray(lg_env)
    xarray_enviro["H19"] = xr.DataArray(ch12 / 100 + 273.15)
    xarray_enviro["H19"].attrs["channel_number"] = 12
    xarray_enviro["V19"] = xr.DataArray(ch13 / 100 + 273.15)
    xarray_enviro["V19"].attrs["channel_number"] = 13
    xarray_enviro["V22"] = xr.DataArray(ch14 / 100 + 273.15)
    xarray_enviro["V22"].attrs["channel_number"] = 14
    xarray_enviro["H37"] = xr.DataArray(ch15 / 100 + 273.15)
    xarray_enviro["H37"].attrs["channel_number"] = 15
    xarray_enviro["V37"] = xr.DataArray(ch16 / 100 + 273.15)
    xarray_enviro["V37"].attrs["channel_number"] = 16
    xarray_enviro["Ch15_5x5"] = xr.DataArray(ch15_5x5 / 100 + 273.15)
    xarray_enviro["Ch15_5x5"].attrs["channel_number"] = 15
    xarray_enviro["Ch16_5x5"] = xr.DataArray(ch16_5x5 / 100 + 273.15)
    xarray_enviro["Ch16_5x5"].attrs["channel_number"] = 16
    xarray_enviro["Ch17_5x5"] = xr.DataArray(ch17_5x5 / 100 + 273.15)
    xarray_enviro["Ch17_5x5"].attrs["channel_number"] = 17
    xarray_enviro["Ch18_5x5"] = xr.DataArray(ch18_5x5 / 100 + 273.15)
    xarray_enviro["Ch18_5x5"].attrs["channel_number"] = 18
    xarray_enviro["Ch17_5x4"] = xr.DataArray(ch17_5x4 / 100 + 273.15)
    xarray_enviro["Ch17_5x4"].attrs["channel_number"] = 17
    xarray_enviro["Ch18_5x4"] = xr.DataArray(ch18_5x4 / 100 + 273.15)
    xarray_enviro["Ch18_5x4"].attrs["channel_number"] = 18
    xarray_enviro["time"] = xr.DataArray(
        pd.DataFrame(time_enviro).astype(int).apply(pd.to_datetime, format="%Y%j%H%M")
    )

    # set xarray object for LAS  variables
    xarray_las = xr.Dataset()
    xarray_las["latitude"] = xr.DataArray(lt_las)
    xarray_las["longitude"] = xr.DataArray(lg_las)
    xarray_las["Ch01_3x3"] = xr.DataArray(ch01_3x3 / 100 + 273.15)
    xarray_las["Ch01_3x3"].attrs["channel_number"] = 1
    xarray_las["Ch02_3x3"] = xr.DataArray(ch02_3x3 / 100 + 273.15)
    xarray_las["Ch02_3x3"].attrs["channel_number"] = 2
    xarray_las["Ch03_3x3"] = xr.DataArray(ch03_3x3 / 100 + 273.15)
    xarray_las["Ch03_3x3"].attrs["channel_number"] = 3
    xarray_las["Ch04_3x3"] = xr.DataArray(ch04_3x3 / 100 + 273.15)
    xarray_las["Ch04_3x3"].attrs["channel_number"] = 4
    xarray_las["Ch05_3x3"] = xr.DataArray(ch05_3x3 / 100 + 273.15)
    xarray_las["Ch05_3x3"].attrs["channel_number"] = 5
    xarray_las["Ch06_3x3"] = xr.DataArray(ch06_3x3 / 100 + 273.15)
    xarray_las["Ch06_3x3"].attrs["channel_number"] = 6
    xarray_las["Ch07_3x3"] = xr.DataArray(ch07_3x3 / 100 + 273.15)
    xarray_las["Ch07_3x3"].attrs["channel_number"] = 7
    xarray_las["Ch08_5x5"] = xr.DataArray(ch08_5x5 / 100 + 273.15)
    xarray_las["Ch08_5x5"].attrs["channel_number"] = 8
    xarray_las["Ch09_5x5"] = xr.DataArray(ch09_5x5 / 100 + 273.15)
    xarray_las["Ch09_5x5"].attrs["channel_number"] = 9
    xarray_las["Ch10_5x5"] = xr.DataArray(ch10_5x5 / 100 + 273.15)
    xarray_las["Ch10_5x5"].attrs["channel_number"] = 10
    xarray_las["Ch11_5x5"] = xr.DataArray(ch11_5x5 / 100 + 273.15)
    xarray_las["Ch11_5x5"].attrs["channel_number"] = 11
    xarray_las["Ch18_5x5_las"] = xr.DataArray(ch18_5x5_las / 100 + 273.15)
    xarray_las["Ch18_5x5_las"].attrs["channel_number"] = 18
    xarray_las["Ch24_3x3"] = xr.DataArray(ch24_3x3 / 100 + 273.15)
    xarray_las["Ch24_3x3"].attrs["channel_number"] = 24
    xarray_las["Height_1000mb"] = xr.DataArray(height_1000mb)
    xarray_las["Surf_las"] = xr.DataArray(surf_las)
    xarray_las["time"] = xr.DataArray(
        pd.DataFrame(time_las).astype(int).apply(pd.to_datetime, format="%Y%j%H%M")
    )

    # set xarray object for UAS  variables
    xarray_uas = xr.Dataset()
    xarray_uas["latitude"] = xr.DataArray(lt_uas)
    xarray_uas["longitude"] = xr.DataArray(lg_uas)
    xarray_uas["Ch19_6x6"] = xr.DataArray(ch19_6x6 / 100 + 273.15)
    xarray_uas["Ch19_6x6"].attrs["channel_number"] = 19
    xarray_uas["Ch20_6x6"] = xr.DataArray(ch20_6x6 / 100 + 273.15)
    xarray_uas["Ch20_6x6"].attrs["channel_number"] = 20
    xarray_uas["Ch21_6x6"] = xr.DataArray(ch21_6x6 / 100 + 273.15)
    xarray_uas["Ch21_6x6"].attrs["channel_number"] = 21
    xarray_uas["Ch22_6x6"] = xr.DataArray(ch22_6x6 / 100 + 273.15)
    xarray_uas["Ch22_6x6"].attrs["channel_number"] = 22
    xarray_uas["Ch23_6x6"] = xr.DataArray(ch23_6x6 / 100 + 273.15)
    xarray_uas["Ch23_6x6"].attrs["channel_number"] = 23
    xarray_uas["Ch24_6x6"] = xr.DataArray(ch24_6x6 / 100 + 273.15)
    xarray_uas["Ch24_6x6"].attrs["channel_number"] = 24
    xarray_uas["Scene"] = xr.DataArray(scene)
    xarray_uas["tqFlag"] = xr.DataArray(tqflag)
    xarray_uas["time"] = xr.DataArray(
        pd.DataFrame(time_uas).astype(int).apply(pd.to_datetime, format="%Y%j%H%M")
    )

    # Setup attributes

    # for Imager
    xarray_imager.attrs["start_datetime"] = start_datetime
    xarray_imager.attrs["end_datetime"] = end_datetime
    xarray_imager.attrs["source_name"] = "ssmis"
    xarray_imager.attrs["platform_name"] = satid
    xarray_imager.attrs["data_provider"] = "DMSP"
    xarray_imager.attrs["source_file_names"] = [basename(fname)]
    xarray_imager.attrs["satellite_zenith_angle"] = satellite_zenith_angle
    xarray_imager.attrs["sensor_scan_angle"] = sensor_scan_angle
    xarray_imager.attrs["satellite_altitude"] = satellite_altitude

    # MTIFs need to be "prettier" for PMW products, so 2km resolution for final image
    xarray_imager.attrs["sample_distance_km"] = 2
    xarray_imager.attrs["interpolation_radius_of_influence"] = 15000

    # for Enviro
    xarray_enviro.attrs["start_datetime"] = start_datetime
    xarray_enviro.attrs["end_datetime"] = end_datetime
    xarray_enviro.attrs["source_name"] = "ssmis"
    xarray_enviro.attrs["platform_name"] = satid
    xarray_enviro.attrs["data_provider"] = "DMSP"
    xarray_enviro.attrs["source_file_names"] = [basename(fname)]
    xarray_enviro.attrs["satellite_zenith_angle"] = satellite_zenith_angle
    xarray_enviro.attrs["sensor_scan_angle"] = sensor_scan_angle
    xarray_enviro.attrs["satellite_altitude"] = satellite_altitude

    # MTIFs need to be "prettier" for PMW products, so 2km resolution for final image
    xarray_enviro.attrs["sample_distance_km"] = 2
    xarray_enviro.attrs["interpolation_radius_of_influence"] = 50000

    # for LAS
    xarray_las.attrs["start_datetime"] = start_datetime
    xarray_las.attrs["end_datetime"] = end_datetime
    xarray_las.attrs["source_name"] = "ssmis"
    xarray_las.attrs["platform_name"] = satid
    xarray_las.attrs["data_provider"] = "DMSP"
    xarray_las.attrs["source_file_names"] = [basename(fname)]
    xarray_las.attrs["satellite_zenith_angle"] = satellite_zenith_angle
    xarray_las.attrs["sensor_scan_angle"] = sensor_scan_angle
    xarray_las.attrs["satellite_altitude"] = satellite_altitude

    # MTIFs need to be "prettier" for PMW products, so 2km resolution for final image
    xarray_las.attrs["sample_distance_km"] = 2
    xarray_las.attrs["interpolation_radius_of_influence"] = 50000

    # for UAS
    xarray_uas.attrs["start_datetime"] = start_datetime
    xarray_uas.attrs["end_datetime"] = end_datetime
    xarray_uas.attrs["source_name"] = "ssmis"
    xarray_uas.attrs["platform_name"] = satid
    xarray_uas.attrs["data_provider"] = "DMSP"
    xarray_uas.attrs["source_file_names"] = [basename(fname)]
    xarray_uas.attrs["satellite_zenith_angle"] = satellite_zenith_angle
    xarray_uas.attrs["sensor_scan_angle"] = sensor_scan_angle
    xarray_uas.attrs["satellite_altitude"] = satellite_altitude

    # MTIFs need to be "prettier" for PMW products, so 2km resolution for final image
    xarray_uas.attrs["sample_distance_km"] = 2
    xarray_uas.attrs["interpolation_radius_of_influence"] = 50000

    return {
        "IMAGER": xarray_imager,
        "ENVIRO": xarray_enviro,
        "LAS": xarray_las,
        "UAS": xarray_uas,
        "METADATA": xarray_imager[[]],
    }
