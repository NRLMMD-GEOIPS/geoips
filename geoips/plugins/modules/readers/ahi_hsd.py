# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Advanced Himawari Imager Data Reader."""

# cspell:ignore BADVALS, FLDK, GEOLL, GSICS, adname, calib, cfac, currchan, dsname
# cspell:ignore sclunit, nprocs, gvars, nseg, segs

# Python Standard Libraries
from datetime import datetime, timedelta
from glob import glob
import logging
import os
import re
from struct import unpack

# Third-Party Libraries
import numpy as np
import xarray
from scipy.ndimage import zoom

# GeoIPS Libraries
from geoips.interfaces import readers
from geoips.utils.memusg import print_mem_usage
from geoips.utils.context_managers import import_optional_dependencies
from geoips.plugins.modules.readers.utils.geostationary_geolocation import (
    get_geolocation_cache_filename,
    get_geolocation,
)

LOG = logging.getLogger(__name__)

with import_optional_dependencies(loglevel="info"):
    """Attempt to import a package and print to LOG.info if the import fails."""
    import numexpr as ne

try:
    nprocs = 6
    ne.set_num_threads(nprocs)
except Exception:
    LOG.info(
        "Failed numexpr.set_num_threads in %s. If numexpr is not installed and you"
        " need it, install it.",
        __file__,
    )

DONT_AUTOGEN_GEOLOCATION = False
if os.getenv("DONT_AUTOGEN_GEOLOCATION"):
    DONT_AUTOGEN_GEOLOCATION = True

# These should be added to the data file object
BADVALS = {
    "Off_Of_Disk": -999.9,
    "Error": -999.8,
    "Out_Of_Valid_Range": -999.7,
    "Root_Test": -999.6,
    "Unitialized": -9999.9,
}

DATASET_INFO = {
    "LOW": [
        "B05",
        "B06",
        "B07",
        "B08",
        "B09",
        "B10",
        "B11",
        "B12",
        "B13",
        "B14",
        "B15",
        "B16",
    ],
    "MED": ["B01", "B02", "B04"],
    "HIGH": ["B03"],
}
ROIS = {"LOW": 3000, "MED": 2000, "HIGH": 1000}
SAMPLE_DISTANCE_KM = {"LOW": 2, "MED": 1, "HIGH": 0.5}
ALL_CHANS = {
    "LOW": [
        "B05Rad",
        "B05Ref",  # 1.61um
        "B06Rad",
        "B06Ref",  # 2.267um
        "B07Rad",
        "B07BT",  # 3.8853um
        "B08Rad",
        "B08BT",  # 6.2429um
        "B09Rad",
        "B09BT",  # 6.9410um
        "B10Rad",
        "B10BT",  # 7.3467um
        "B11Rad",
        "B11BT",  # 8.5926um
        "B12Rad",
        "B12BT",  # 9.6372um
        "B13Rad",
        "B13BT",  # 10.4073um
        "B14Rad",
        "B14BT",  # 11.2395um
        "B15Rad",
        "B15BT",  # 12.3806um
        "B16Rad",
        "B16BT",
    ],  # 13.2807um
    "MED": [
        "B01Rad",
        "B01Ref",  # 0.47063um
        "B02Rad",
        "B02Ref",  # 0.51000um
        "B04Rad",
        "B04Ref",
    ],  # 0.85670um
    "HIGH": ["B03Rad", "B03Ref"],  # 0.63914um
}

ALL_GVARS = {
    "LOW": [
        "latitude",
        "longitude",
        "solar_zenith_angle",
        "solar_azimuth_angle",
        "satellite_zenith_angle",
        "satellite_azimuth_angle",
    ],
    "MED": [
        "latitude",
        "longitude",
        "solar_zenith_angle",
        "solar_azimuth_angle",
        "satellite_zenith_angle",
        "satellite_azimuth_angle",
    ],
    "HIGH": [
        "latitude",
        "longitude",
        "solar_zenith_angle",
        "solar_azimuth_angle",
        "satellite_zenith_angle",
        "satellite_azimuth_angle",
    ],
}

interface = "readers"
family = "standard"
name = "ahi_hsd"
source_names = ["ahi"]


class AutoGenError(Exception):
    """Raise exception on geolocation autogeneration error."""

    pass


def findDiff(d1, d2, path=""):
    """Find diff."""
    for k in d1.keys():
        if k not in d2:
            LOG.info(path, ":")
            LOG.info(k + " as key not in d2", "\n")
        else:
            if type(d1[k]) is dict:
                if path == "":
                    path = k
                else:
                    path = path + "->" + k
                findDiff(d1[k], d2[k], path)
            else:
                if np.all(d1[k] != d2[k]):
                    LOG.info(path, ":")
                    LOG.info(" - ", k, " : ", d1[k])
                    LOG.info(" + ", k, " : ", d2[k])


def metadata_to_datetime(metadata, time_var="ob_start_time"):
    """Use information from block_01 to get the image datetime."""
    ost = metadata["block_01"][time_var]
    otl = metadata["block_01"]["ob_timeline"]
    dt = datetime(1858, 11, 17, 00, 00, 00)
    dt += timedelta(days=np.floor(ost))
    dt += timedelta(hours=int(otl // 100), minutes=int(otl % 100))
    return dt


def _get_geolocation_metadata(metadata):
    """
    Gather all of the metadata used in creating geolocation data for input file.

    This is split out so we can easily create a hash of the data for creation
    of a unique filename. This allows us to avoid recalculation of angles that
    have already been calculated.
    """
    geomet = {}
    # Used for cached file paths
    geomet["platform_name"] = metadata["block_01"]["satellite_name"].lower()
    geomet["ob_area"] = metadata["block_01"]["ob_area"]
    # Used for cached filenames
    geomet["scene"] = geomet["ob_area"]
    geomet["num_lines"] = int(
        metadata["block_02"]["num_lines"] * metadata["block_07"]["num_segments"]
    )
    geomet["num_samples"] = int(metadata["block_02"]["num_samples"])
    geomet["lfac"] = float(metadata["block_03"]["LFAC"])
    geomet["loff"] = float(metadata["block_03"]["LOFF"])
    geomet["cfac"] = float(metadata["block_03"]["CFAC"])
    geomet["res_km"] = np.ceil(2.0 * 40000000.0 / geomet["cfac"]) / 2.0
    geomet["roi_factor"] = 5  # roi = res * roi_factor, was 10
    geomet["coff"] = float(metadata["block_03"]["COFF"])
    geomet["Rs"] = float(metadata["block_03"]["earth_to_sat_radius"])
    geomet["H_m"] = float(geomet["Rs"] * 1000.0)
    geomet["Sd_coeff"] = float(metadata["block_03"]["Sd_coeff"])
    geomet["ecc"] = float(metadata["block_03"]["r3"])
    geomet["sub_lon"] = float(metadata["block_03"]["sub_lon"])
    geomet["lon0"] = geomet["sub_lon"]
    return geomet


def get_latitude_longitude(metadata, BADVALS, area_def=None):
    """
    Get latitudes and longitudes.

    This routine accepts a dictionary containing metadata as read from an HSD
    format file and returns latitudes and longitudes for a full disk image.

    Note: This code has been adapted from Dan Lindsey's Fortran90 code.
    This was done in three steps that ultimately culminated in faster, but more
    difficult to understand code.  If you plan to edit this, I recommend that
    you return to Dan's original code, then explore the commented code here,
    then finally, look at the single-command statements that are currently being
    used.
    """
    # If the filename format needs to change for the pre-generated geolocation
    # files, please discuss prior to changing.  It will force recreation of all
    # files, which can be problematic for large numbers of sectors
    fname = get_geolocation_cache_filename("GEOLL", metadata)
    if not os.path.isfile(fname):
        if (
            area_def is not None
            and DONT_AUTOGEN_GEOLOCATION
            and "tc2019" not in area_def.area_id
        ):
            msg = (
                "GETGEO Requested NO AUTOGEN GEOLOCATION. "
                + "Could not create latlonfile for ad {}: {}"
            ).format(metadata["ob_area"], fname)
            LOG.error(msg)
            raise AutoGenError(msg)

        LOG.debug("Calculating latitudes and longitudes.")

        sclunit = 1.525878906250000e-05  # NOQA

        # Constants
        LOG.info("    LATLONCALC Building constants.")
        pi = np.pi
        rad2deg = 180.0 / pi  # NOQA
        deg2rad = pi / 180.0  # NOQA
        num_lines = metadata["num_lines"]
        num_samples = metadata["num_samples"]
        lfac = metadata["lfac"]  # NOQA
        loff = metadata["loff"]  # NOQA
        cfac = metadata["cfac"]  # NOQA
        coff = metadata["coff"]  # NOQA
        Rs = metadata["Rs"]  # NOQA
        Sd_coeff = metadata["Sd_coeff"]  # NOQA
        ecc = metadata["ecc"]  # NOQA
        sub_lon = metadata["sub_lon"]  # NOQA

        # first_line = df.metadata['block_07']['segment_first_line'][0]
        first_line = 0
        # last_line = first_line + num_lines
        last_line = num_lines
        line_step = 1

        first_sample = 0
        last_sample = num_samples
        sample_step = 1

        # Create cartesian grid
        LOG.info("    LATLONCALC Creating cartesian grid")
        x, y = np.meshgrid(
            np.arange(first_sample, last_sample, sample_step),
            np.arange(first_line, last_line, line_step),
        )
        # Changing to use numexpr rather than numpy.  Appears to speed up each statement
        # by about five times.
        #
        # In [8]: timeit -n100 deg2rad *
        # (np.array(x, dtype=np.float) - coff)/(sclunit * cfac)
        # 100 loops, best of 3: 96.6 ms per loop
        #
        # In [9]: timeit -n100 ne.evaluate('deg2rad*(x-coff)/(sclunit*cfac)')
        # 100 loops, best of 3: 20 ms per loop
        x = ne.evaluate("deg2rad * (x - coff) / (sclunit * cfac)")  # NOQA
        y = ne.evaluate("deg2rad*(y - loff)/(sclunit * lfac)")  # NOQA
        # # Improvement here is from 132ms for np.sin(x) to 23.5ms for
        # ne.evaluate('sin(x)')
        LOG.info("    LATLONCALC Calculating sines and cosines")
        # sin_x = ne.evaluate('sin(x)')  # NOQA
        # sin_y = ne.evaluate('sin(y)')  # NOQA
        # cos_x = ne.evaluate('cos(x)')  # NOQA
        # cos_y = ne.evaluate('cos(y)')  # NOQA

        # Calculate surface distance (I think)
        # Improvement here is from 200ms for numpy to 16.9ms for ne
        LOG.debug("Calculating Sd")
        Sd = ne.evaluate(
            "(Rs * cos(x) * cos(y))**2 - (cos(y)**2 + ecc * sin(y)**2) * Sd_coeff"
        )
        # No real savings on these lines.  Leave alone.
        Sd[Sd < 0.0] = 0.0
        Sd **= 0.5

        # # Good data mask
        # good = Sd != 0

        # # Now I'm lost, but it seems to work.  Comes from the Himawari-8 users's guide
        # # Original version with excess calculations
        LOG.debug("Calculating Sn")
        # Sn = ne.evaluate('(Rs * cos_x * cos_y-Sd)/(cos_y**2 + ecc * sin_y**2)')
        # # NOQA
        LOG.debug("Calculating S1")
        # S1 = ne.evaluate('Rs - (Sn * cos_x * cos_y)')  # NOQA
        LOG.debug("Calculating S2")
        # S2 = ne.evaluate('Sn * sin_x * cos_y')  # NOQA
        LOG.debug("Calculating S3")
        # S3 = ne.evaluate('-Sn * sin_y')  # NOQA
        LOG.debug("Calculating Sxy")
        # Sxy = ne.evaluate('(S1**2 + S2**2)**0.5')  # NOQA

        # # if hasattr(self, '_temp_latitudes_arr'):
        # #     lats = self._temp_latitudes_arr
        # # else:
        LOG.debug("    LATLONCALC Allocating latitudes")
        # lats = np.full((num_lines, num_samples), df.BADVALS['Off_Of_Disk'])
        # # if hasattr(self, '_temp_longitudes_arr'):
        # #     lons = self._temp_longitudes_arr
        # # else:
        LOG.debug("    LATLONCALC Allocating longitudes")
        # lons = np.full((num_lines, num_samples), df.BADVALS['Off_Of_Disk'])

        # # It may help to figure out how to index into an array in numeval
        # # Improves from 663ms for numpy to 329ms for numeval
        # LOG.debug('Calculating latitudes')
        # lats[good] = ne.evaluate('rad2deg*arctan(ecc*S3/Sxy)')[good]
        # # Improves from 669ms for numpy to 301ms for numeval
        # LOG.debug('Calculating longitudes')
        # lons[good] = ne.evaluate('rad2deg*arctan(S2/S1)+sub_lon')[good]
        # # No real savings on these lines.  Leave alone.
        # lons[lons > 180.0] -= 360
        # # self._latitudes = lats
        # # self._longitudes = lons

        # The following equations have been combined from above.
        # The more we can fit into a single equation, the faster things will be.
        # I know this makes things ugly, but hopefully this will never have to be
        # edited.
        LOG.info("    LATLONCALC Calculating latitudes")
        bad = Sd == 0
        lats = ne.evaluate(
            "rad2deg*arctan(-ecc*(Rs*cos(x)*cos(y)-Sd)"
            "/ (cos(y)**2+ecc*sin(y)**2) * sin(y)"
            "/ ((Rs-(Rs*cos(x)*cos(y)-Sd)/(cos(y)**2+ecc*sin(y)**2)*cos(x)*cos(y))**2"
            "+ ((Rs*cos(x)*cos(y)-Sd)"
            "/(cos(y)**2+ecc*sin(y)**2)*sin(x)*cos(y))**2)**0.5)"
        )
        lats[bad] = BADVALS["Off_Of_Disk"]
        LOG.info("    LATLONCALC Calculating longitudes")
        lons = ne.evaluate(
            "rad2deg*arctan(((Rs*cos(x)*cos(y)-Sd)"
            "/ (cos(y)**2 + ecc*sin(y)**2))*sin(x)*cos(y)"
            "/ (Rs-((Rs*cos(x)*cos(y)-Sd)"
            "/ (cos(y)**2 + ecc*sin(y)**2))*cos(x)*cos(y))) + sub_lon"
        )
        lons[bad] = BADVALS["Off_Of_Disk"]
        lons[lons > 180.0] -= 360
        LOG.debug("Done calculating latitudes and longitudes")

        with open(fname, "w") as df:
            lats.tofile(df)
            lons.tofile(df)
        # Switch to xarray based geolocation files
        # ds = xarray.Dataset({'latitude':(['x','y'],lats),
        #                      'longitude':(['x','y'],lons)})
        # ds.to_netcdf(fname)

    # Create a memmap to the lat/lon file
    # Nothing will be read until explicitly requested
    # We are mapping this here so that the lats and lons are available when
    # calculating satellite angles
    LOG.info(
        "GETGEO memmap to {} : lat/lon file for {}".format(fname, metadata["ob_area"])
    )

    shape = (metadata["num_lines"], metadata["num_samples"])
    offset = 8 * metadata["num_samples"] * metadata["num_lines"]
    lats = np.memmap(fname, mode="r", dtype=np.float64, offset=0, shape=shape)
    lons = np.memmap(fname, mode="r", dtype=np.float64, offset=offset, shape=shape)
    # Switch to xarray based geolocation files
    # saved_xarray = xarray.load_dataset(fname)
    # lons = saved_xarray['longitude'].to_masked_array()
    # lats = saved_xarray['latitude'].to_masked_array()

    return lats, lons


def _get_metadata_block_info(df):
    """
    Get metadata block info.

    Returns a dictionary whose keys represent metadata block numbers and whose
    values are tuples containing the block's starting byte number and the
    block's length in bytes.
    """
    # Initialize the first block's data
    block_info = {1: (0, 0)}
    # print(df.name)

    # Loop over blocks and determine their sizes
    for blockind in range(1, 12):
        # Make sure we are at the start of the block
        block_start = block_info[blockind][0]
        df.seek(block_start)

        # Read the block number and block length
        block_num = unpack("B", df.read(1))[0]
        if block_num != blockind:
            raise IOError(
                "Unexpected block number encountered. "
                f"Expected {blockind}, but got {block_num}. File {df.name}"
            )
        block_length = unpack("H", df.read(2))[0]

        # Add block_length for the current block
        block_info[blockind] = (block_start, block_length)

        # Add entry for the NEXT block
        if blockind < 11:
            block_info[blockind + 1] = (block_start + block_length, 0)

    return block_info


def _get_metadata_block_01(df, block_info):
    """
    Get metadata block 01.

    Parse the first metadata block from an AHI data file and return a dictionary
    containing that metadata.
    """
    # Get the block start and length in bytes
    block_start, block_length = block_info[1]

    # Seek to the start of the block and read the block in its entirety
    df.seek(block_start)
    data = df.read(block_length)

    # Create dictionary for this block
    block_data = {}
    block_data["block_name"] = "basic_information"
    block_data["block_num"] = np.fromstring(data[0:1], dtype="uint8")[0]
    block_data["block_length"] = np.fromstring(data[1:3], dtype="uint16")[0]
    block_data["num_headers"] = np.fromstring(data[3:5], dtype="uint16")[0]
    block_data["byte_order"] = np.fromstring(data[5:6], dtype="uint8")[0]
    block_data["satellite_name"] = data[6:22].decode("ascii").replace("\x00", "")
    block_data["processing_center"] = data[22:38].decode("ascii").replace("\x00", "")
    block_data["ob_area"] = data[38:42].decode("ascii").replace("\x00", "")
    block_data["other_ob_info"] = data[42:44].decode("ascii").replace("\x00", "")
    block_data["ob_timeline"] = np.fromstring(data[44:46], dtype="uint16")[0]
    block_data["ob_start_time"] = np.fromstring(data[46:54], dtype="float64")[0]
    block_data["ob_end_time"] = np.fromstring(data[54:62], dtype="float64")[0]
    block_data["creation_time"] = np.fromstring(data[62:70], dtype="float64")[0]
    block_data["total_header_length"] = np.fromstring(data[70:74], dtype="uint32")[0]
    block_data["total_data_length"] = np.fromstring(data[74:78], dtype="uint32")[0]
    block_data["quality_flag_1"] = np.fromstring(data[78:79], dtype="uint8")[0]
    block_data["quality_flag_2"] = np.fromstring(data[79:80], dtype="uint8")[0]
    block_data["quality_flag_3"] = np.fromstring(data[80:81], dtype="uint8")[0]
    block_data["quality_flag_4"] = np.fromstring(data[81:82], dtype="uint8")[0]
    block_data["file_format_version"] = data[82:114].decode("ascii").replace("\x00", "")
    block_data["file_name"] = data[114:242].decode("ascii").replace("\x00", "")
    block_data["spare"] = data[242:282].decode("ascii").replace("\x00", "")

    return block_data


def _get_metadata_block_02(df, block_info):
    """
    Get metadata block 02.

    Parse the second metadata block from an AHI data file and return a
    dictionary containing that metadata.
    """
    # Get the block start and length in bytes
    block_start, block_length = block_info[2]

    # Seek to the start of the block and read the block in its entirety
    df.seek(block_start)
    data = df.read(block_length)

    # Create dictionary for this block
    block_data = {}
    block_data["block_name"] = "data_information"
    block_data["block_num"] = np.fromstring(data[0:1], dtype="uint8")[0]
    block_data["block_length"] = np.fromstring(data[1:3], dtype="uint16")[0]
    block_data["bits_per_pixel"] = np.fromstring(data[3:5], dtype="uint16")[0]
    block_data["num_samples"] = np.fromstring(data[5:7], dtype="uint16")[0]
    block_data["num_lines"] = np.fromstring(data[7:9], dtype="uint16")[0]
    block_data["compression_flag"] = np.fromstring(data[9:10], dtype="uint8")[0]
    block_data["spare"] = data[10:50].decode("ascii").replace("\x00", "")

    return block_data


def _get_metadata_block_03(df, block_info):
    """
    Get metadata block 03.

    Parse the third metadata block from an AHI data file and return a
    dictionary containing that metadata.
    """
    # Get the block start and length in bytes
    block_start, block_length = block_info[3]

    # Seek to the start of the block and read the block in its entirety
    df.seek(block_start)
    data = df.read(block_length)

    # Create dictionary for this block
    block_data = {}
    block_data["block_name"] = "projection_information"
    block_data["block_num"] = np.fromstring(data[0:1], dtype="uint8")[0]
    block_data["block_length"] = np.fromstring(data[1:3], dtype="uint16")[0]
    block_data["sub_lon"] = np.fromstring(data[3:11], dtype="float64")[0]
    # Column scaling factor
    block_data["CFAC"] = np.fromstring(data[11:15], dtype="uint32")[0]
    # Line scaling factor
    block_data["LFAC"] = np.fromstring(data[15:19], dtype="uint32")[0]
    # Column offset
    block_data["COFF"] = np.fromstring(data[19:23], dtype="float32")[0]
    # Line offset
    block_data["LOFF"] = np.fromstring(data[23:27], dtype="float32")[0]
    # Distance to earth's center
    block_data["earth_to_sat_radius"] = np.fromstring(data[27:35], dtype="float64")[0]
    # Radius of earth at equator
    block_data["equator_radius"] = np.fromstring(data[35:43], dtype="float64")[0]
    # Radius of earth at pole
    block_data["pole_radius"] = np.fromstring(data[43:51], dtype="float64")[0]
    # (R_eq**2 - R_pol**2)/R_eq**2
    block_data["r1"] = np.fromstring(data[51:59], dtype="float64")[0]
    # R_pol**2/R_eq**2
    block_data["r2"] = np.fromstring(data[59:67], dtype="float64")[0]
    # R_eq**2/R_pol**2
    block_data["r3"] = np.fromstring(data[67:75], dtype="float64")[0]
    # Coefficient for S_d(R_s**2 - R_eq**2)
    block_data["Sd_coeff"] = np.fromstring(data[75:83], dtype="float64")[0]
    block_data["resampling_types"] = np.fromstring(data[83:85], dtype="uint16")[0]
    block_data["resampling_size"] = np.fromstring(data[85:87], dtype="uint16")[0]
    block_data["spare"] = np.fromstring(data[87:127], dtype="uint16")

    return block_data


def _get_metadata_block_04(df, block_info):
    """
    Get metadata block 04.

    Parse the 4th metadata block from an AHI data file and return a
    dictionary containing that metadata.
    """
    # Get the block start and length in bytes
    block_start, block_length = block_info[4]

    # Seek to the start of the block and read the block in its entirety
    df.seek(block_start)
    data = df.read(block_length)

    # Create dictionary for this block
    block_data = {}
    block_data["block_name"] = "navigation_information"
    block_data["block_num"] = np.fromstring(data[0:1], dtype="uint8")[0]
    block_data["block_length"] = np.fromstring(data[1:3], dtype="uint16")[0]
    block_data["nav_info_time"] = np.fromstring(data[3:11], dtype="float64")[0]
    block_data["SSP_lon"] = np.fromstring(data[11:19], dtype="float64")[0]
    block_data["SSP_lat"] = np.fromstring(data[19:27], dtype="float64")[0]
    block_data["earthcenter_to_sat_dist"] = np.fromstring(data[27:35], dtype="float64")[
        0
    ]
    block_data["nadir_lon"] = np.fromstring(data[35:43], dtype="float64")[0]
    block_data["nadir_lat"] = np.fromstring(data[43:51], dtype="float64")[0]
    block_data["sun_pos"] = np.fromstring(data[51:75], dtype="float64")
    block_data["moon_pos"] = np.fromstring(data[75:99], dtype="float64")
    block_data["spare"] = np.fromstring(data[99:139], dtype="float64")

    return block_data


def _get_metadata_block_05(df, block_info):
    """
    Get metadata block 05.

    Parse the 5th metadata block from an AHI data file and return a
    dictionary containing that metadata.
    """
    # Get the block start and length in bytes
    block_start, block_length = block_info[5]

    # Seek to the start of the block and read the block in its entirety
    df.seek(block_start)
    data = df.read(block_length)

    # Create dictionary for this block
    block_data = {}
    block_data["block_name"] = "calibration_information"
    block_data["block_num"] = np.fromstring(data[0:1], dtype="uint8")[0]
    block_data["block_length"] = np.fromstring(data[1:3], dtype="uint16")[0]
    block_data["band_number"] = np.fromstring(data[3:5], dtype="uint16")[0]
    block_data["cent_wavelenth"] = np.fromstring(data[5:13], dtype="float64")[0]
    block_data["valid_bits_per_pixel"] = np.fromstring(data[13:15], dtype="uint16")[0]
    block_data["count_badval"] = np.fromstring(data[15:17], dtype="uint16")[0]
    block_data["count_outside_scan"] = np.fromstring(data[17:19], dtype="uint16")[0]
    block_data["gain"] = np.fromstring(data[19:27], dtype="float64")[0]
    block_data["offset"] = np.fromstring(data[27:35], dtype="float64")[0]
    if block_data["band_number"] in range(7, 17):
        block_data["c0"] = np.fromstring(data[35:43], dtype="float64")[0]
        block_data["c1"] = np.fromstring(data[43:51], dtype="float64")[0]
        block_data["c2"] = np.fromstring(data[51:59], dtype="float64")[0]
        block_data["C0"] = np.fromstring(data[59:67], dtype="float64")[0]
        block_data["C1"] = np.fromstring(data[67:75], dtype="float64")[0]
        block_data["C2"] = np.fromstring(data[75:83], dtype="float64")[0]
        block_data["speed_of_light"] = np.fromstring(data[83:91], dtype="float64")[0]
        block_data["planck_const"] = np.fromstring(data[91:99], dtype="float64")[0]
        block_data["boltz_const"] = np.fromstring(data[99:107], dtype="float64")[0]
        # block_data['spare'] = np.fromstring(data[107:147], dtype='float64')
    else:
        block_data["c_prime"] = np.fromstring(data[35:43], dtype="float64")[0]
        block_data["spare"] = np.fromstring(data[43:147], dtype="float64")

    return block_data


def _get_metadata_block_06(df, block_info):
    """
    Get metadata block 06.

    Parse the 6th metadata block from an AHI data file and return a
    dictionary containing that metadata.
    """
    # Get the block start and length in bytes
    block_start, block_length = block_info[6]

    # Seek to the start of the block and read the block in its entirety
    df.seek(block_start)
    data = df.read(block_length)

    # Create dictionary for this block
    block_data = {}
    block_data["block_name"] = "intercalibration_information"
    block_data["block_num"] = np.fromstring(data[0:1], dtype="uint8")[0]
    block_data["block_length"] = np.fromstring(data[1:3], dtype="uint16")[0]
    # Global Space-based Inter-Calibration System (GSICS) calibration coefficients
    block_data["GSICS_intercept"] = np.fromstring(data[3:11], dtype="float64")[0]
    block_data["GSICS_slope"] = np.fromstring(data[11:19], dtype="float64")[0]
    block_data["GSICS_quadratic"] = np.fromstring(data[19:27], dtype="float64")[0]
    block_data["radiance_bias"] = np.fromstring(data[27:35], dtype="float64")[0]
    block_data["bias_uncert"] = np.fromstring(data[35:43], dtype="float64")[0]
    block_data["standard_radiance"] = np.fromstring(data[43:51], dtype="float64")[0]
    block_data["GSICS_valid_start"] = np.fromstring(data[51:59], dtype="float64")[0]
    block_data["GSICS_valid_end"] = np.fromstring(data[59:67], dtype="float64")[0]
    block_data["GSICS_upper_limit"] = np.fromstring(data[67:71], dtype="float32")[0]
    block_data["GSICS_lower_limit"] = np.fromstring(data[71:75], dtype="float32")[0]
    block_data["GSICS_filename"] = data[75:203].decode("ascii").replace("\x00", "")
    block_data["spare"] = data[203:259].decode("ascii").replace("\x00", "")

    return block_data


def _get_metadata_block_07(df, block_info):
    """
    Get metadata block 07.

    Parse the 7th metadata block from an AHI data file and return a
    dictionary containing that metadata.
    """
    # Get the block start and length in bytes
    block_start, block_length = block_info[7]

    # Seek to the start of the block and read the block in its entirety
    df.seek(block_start)
    data = df.read(block_length)

    # Create dictionary for this block
    block_data = {}
    block_data["block_name"] = "segment_information"
    block_data["block_num"] = np.fromstring(data[0:1], dtype="uint8")[0]
    block_data["block_length"] = np.fromstring(data[1:3], dtype="uint16")[0]
    block_data["num_segments"] = np.fromstring(data[3:4], dtype="uint8")[0]
    block_data["segment_number"] = np.fromstring(data[4:5], dtype="uint8")[0]
    block_data["segment_first_line"] = np.fromstring(data[5:7], dtype="uint16")[0]
    block_data["spare"] = data[7:47].decode("ascii").replace("\x00", "")

    return block_data


def _get_metadata_block_08(df, block_info):
    """
    Get metadata block 08.

    Parse the 8th metadata block from an AHI data file and return a
    dictionary containing that metadata.
    """
    # Get the block start and length in bytes
    block_start, block_length = block_info[8]

    # Seek to the start of the block and read the block in its entirety
    df.seek(block_start)
    data = df.read(block_length)

    # Create dictionary for this block
    block_data = {}
    block_data["block_name"] = "navigation_correction_information"
    block_data["block_num"] = np.fromstring(data[0:1], dtype="uint8")[0]
    block_data["block_length"] = np.fromstring(data[1:3], dtype="uint16")[0]
    block_data["center_scan_of_rotation"] = np.fromstring(data[3:7], dtype="float32")[0]
    block_data["center_line_of_rotation"] = np.fromstring(data[7:11], dtype="float32")[
        0
    ]
    block_data["rotation_correction"] = np.fromstring(data[11:19], dtype="float64")[0]
    block_data["num_correction_info"] = np.fromstring(data[19:21], dtype="uint16")[0]

    start = 21
    block_data["line_num_after_rotation"] = np.empty(block_data["num_correction_info"])
    block_data["scan_shift_amount"] = np.empty(block_data["num_correction_info"])
    block_data["line_shift_amount"] = np.empty(block_data["num_correction_info"])
    for info_ind in range(0, block_data["num_correction_info"]):
        block_data["line_num_after_rotation"][info_ind] = np.fromstring(
            data[start : start + 2], dtype="uint16"
        )
        block_data["scan_shift_amount"][info_ind] = np.fromstring(
            data[start + 2 : start + 6], dtype="float32"
        )
        block_data["line_shift_amount"][info_ind] = np.fromstring(
            data[start + 6 : start + 10], dtype="float32"
        )
        start += 10
    block_data["spare"] = data[start : start + 40].decode("ascii").replace("\x00", "")

    return block_data


def _get_metadata_block_09(df, block_info):
    """
    Get metadata block 09.

    Parse the 9th metadata block from an AHI data file and return a
    dictionary containing that metadata.
    """
    # Get the block start and length in bytes
    block_start, block_length = block_info[9]

    # Seek to the start of the block and read the block in its entirety
    df.seek(block_start)
    data = df.read(block_length)

    # Create dictionary for this block
    block_data = {}
    block_data["block_name"] = "observation_time_information"
    block_data["block_num"] = np.fromstring(data[0:1], dtype="uint8")[0]
    block_data["block_length"] = np.fromstring(data[1:3], dtype="uint16")[0]
    block_data["num_ob_times"] = np.fromstring(data[3:5], dtype="uint16")[0]

    start = 5
    block_data["ob_time_line_number"] = np.empty(block_data["num_ob_times"])
    block_data["ob_time"] = np.empty(block_data["num_ob_times"])
    for info_ind in range(0, block_data["num_ob_times"]):
        block_data["ob_time_line_number"][info_ind] = np.fromstring(
            data[start : start + 2], dtype="uint16"
        )
        block_data["ob_time"][info_ind] = np.fromstring(
            data[start + 2 : start + 10], dtype="float64"
        )
        start += 10
    block_data["spare"] = data[start : start + 40].decode("ascii").replace("\x00", "")

    return block_data


def _get_metadata_block_10(df, block_info):
    """
    Get metadata block 10.

    Parse the 10th metadata block from an AHI data file and return a
    dictionary containing that metadata.
    """
    # Get the block start and length in bytes
    block_start, block_length = block_info[10]

    # Seek to the start of the block and read the block in its entirety
    df.seek(block_start)
    data = df.read(block_length)

    # Create dictionary for this block
    block_data = {}
    block_data["block_name"] = "error_information"
    block_data["block_num"] = np.fromstring(data[0:1], dtype="uint8")[0]
    block_data["block_length"] = np.fromstring(data[1:3], dtype="uint16")[0]
    block_data["num_err_info_data"] = np.fromstring(data[3:5], dtype="uint16")[0]

    start = 5
    block_data["err_line_number"] = np.array([])
    block_data["num_err_per_line"] = np.array([])
    for info_ind in range(0, block_data["num_err_info_data"]):
        block_data["err_line_number"].append(
            np.fromstring(data[start : start + 2], dtype="uint16")
        )
        block_data["num_err_per_line"].append(
            np.fromstring(data[start + 2 : start + 4], dtype="uint16")
        )
        start += 4
    block_data["spare"] = data[start : start + 40].decode("ascii").replace("\x00", "")

    return block_data


def _get_metadata_block_11(df, block_info):
    """
    Get metadata block 11.

    Parse the 11th metadata block from an AHI data file and return a
    dictionary containing that metadata.
    """
    # Get the block start and length in bytes
    block_start, block_length = block_info[11]

    # Seek to the start of the block and read the block in its entirety
    df.seek(block_start)
    data = df.read(block_length)

    # Create dictionary for this block
    block_data = {}
    block_data["block_name"] = "spare"
    block_data["block_num"] = np.fromstring(data[0:1], dtype="uint8")[0]
    block_data["block_length"] = np.fromstring(data[1:3], dtype="uint16")[0]
    block_data["spare"] = data[3:259].decode("ascii").replace("\x00", "")

    return block_data


def _get_metadata(df, **kwargs):
    """Gather metadata for the data file and return as a dictionary."""
    metadata = {}
    # Get metadata block info
    try:
        block_info = _get_metadata_block_info(df)
    except IOError as resp:
        raise IOError(resp)

    # Read all 12 blocks
    metadata["block_01"] = _get_metadata_block_01(df, block_info)
    metadata["block_02"] = _get_metadata_block_02(df, block_info)
    metadata["block_03"] = _get_metadata_block_03(df, block_info)
    metadata["block_04"] = _get_metadata_block_04(df, block_info)
    metadata["block_05"] = _get_metadata_block_05(df, block_info)
    metadata["block_06"] = _get_metadata_block_06(df, block_info)
    metadata["block_07"] = _get_metadata_block_07(df, block_info)
    metadata["block_08"] = _get_metadata_block_08(df, block_info)
    metadata["block_09"] = _get_metadata_block_09(df, block_info)
    metadata["block_10"] = _get_metadata_block_10(df, block_info)
    metadata["block_11"] = _get_metadata_block_11(df, block_info)
    # Gather some useful info to the top level
    metadata["path"] = df.name
    # metadata['satellite'] = metadata['block_01']['satellite_name']
    metadata["satellite"] = metadata["block_01"]["satellite_name"]
    # Can this be gotten from the data?
    metadata["sensor"] = "AHI"
    # Make accessable to parent classes that don't know the structure of our metadata
    metadata["num_lines"] = metadata["block_02"]["num_lines"]
    metadata["num_samples"] = metadata["block_02"]["num_samples"]
    return metadata


def _get_files(path):
    """Get a list of file names from the input path."""
    if os.path.isfile(path):
        fnames = [path]
    elif os.path.isdir(path):
        # Temporarily only looking for full disk images.
        # Should change later.
        fnames = glob(path + "/*.DAT")
    else:
        raise IOError("No such file or directory: {0}".format(path))
    return fnames


def _check_file_consistency(metadata):
    """
    Check file consistency.

    Checks to be sure that all input metadata are from the same image time.
    Performs checks on ob_start_time (date only), ob_timeline, ob_area, and
    sub_lon.
    If these are all equal, returns True.
    If any differ, returns False.
    """
    # Checks start dates without comparing times.
    # Times are incomparable using this field, but are compared below using ob_timeline.
    start_dates = [
        int(metadata[fname]["block_01"]["ob_start_time"]) for fname in metadata.keys()
    ]
    if start_dates[1:] != start_dates[:-1]:
        return False

    # Check the following fields for exact equality.
    #   satellite_name: Must make sure this isn't Himawari-8 and 9 mixed.
    #   ob_timeline: Provides HHMM for each image, so should be the same for all files
    #   from thes same image.
    #   ob_area: Provides the four letter code of the observation area
    #   (e.g. FLDK or JP01).
    #   sub_lon: Just a dummy check to be sure nothing REALLY weird is going on.
    members_to_check = {
        "block_01": {"satellite_name": None, "ob_timeline": None, "ob_area": None},
        "block_03": {"sub_lon": None},
    }

    for block in members_to_check.keys():
        for field in members_to_check[block].keys():
            member_vals = [metadata[fname][block][field] for fname in metadata.keys()]
            # This tests to be sure that all elements in member_vals are equal
            # If they aren't all equal, then return False
            if member_vals[1:] != member_vals[:-1]:
                return False
    return True


def sort_by_band_and_seg(metadata):
    """Sort by band and segment."""
    # cfac = metadata['block_03']['CFAC']
    band_number = metadata["block_05"]["band_number"]
    segment_number = metadata["block_07"]["segment_number"]
    # return '{0}_{1:02d}_{2:02d}'.format(cfac, band_number, segment_number)
    return "{0:02d}_{1:02d}".format(band_number, segment_number)


def call(
    fnames,
    metadata_only=False,
    chans=None,
    area_def=None,
    self_register=False,
    test_arg="AHI Default Test Arg",
):
    """
    Read AHI HSD data data from a list of filenames.

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
    return readers.read_data_to_xarray_dict(
        fnames,
        call_single_time,
        metadata_only,
        chans,
        area_def,
        self_register,
    )


def call_single_time(
    fnames,
    metadata_only=False,
    chans=None,
    area_def=None,
    self_register=False,
    test_arg="AHI Default Test Arg",
):
    """
    Read AHI HSD data data from a list of filenames.

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
    process_datetimes = {}
    LOG.debug("AHI reader test_arg: %s", test_arg)
    print_mem_usage("MEMUSG", verbose=False)
    process_datetimes["overall_start"] = datetime.utcnow()
    gvars = {}
    datavars = {}
    adname = "undefined"
    if area_def and self_register:
        raise ValueError("area_def and self_register are mutually exclusive keywords")
    elif area_def:
        adname = area_def.area_id
    elif self_register:
        if self_register not in DATASET_INFO:
            raise ValueError(
                "Unrecognized resolution name requested for self registration: "
                f"{self_register}",
            )
        adname = "FULL_DISK"

    # Get metadata for all input data files
    all_metadata = {}
    for fname in fnames:
        if chans:
            gotone = False
            for chan in chans:
                currchan = chan.replace("BT", "").replace("Ref", "").replace("Rad", "")
                if currchan in fname:
                    gotone = True
            if not gotone:
                LOG.info(
                    "SKIPPING file %s, not needed from channel list %s", fname, chans
                )
                continue
        try:
            with open(fname, "rb") as file_stream:
                all_metadata[fname] = _get_metadata(file_stream)
        except IOError as resp:
            LOG.exception("BAD FILE %s skipping", resp)
            if ".bz2" in fname:
                LOG.exception("BAD FILE %s must be bunzip2ed prior to processing", resp)
            continue
        if metadata_only:
            LOG.info("Only need metadata from first file, skipping rest of files")
            break

    # Check to be sure that all input files are from the same image time
    if not _check_file_consistency(all_metadata):
        raise ValueError("Input files inconsistent.")

    # Now put together a dict that shows what we actually got
    # This is largely to help us read in order and only create arrays of the minimum
    # required size. Dict structure is channel{segment{file}}
    # Also build sets containing all segments and channels passed
    file_info = {}
    file_segs = set()
    file_chans = set()

    xarray_obj = xarray.Dataset()
    for md in all_metadata.values():
        ch = "B{0:02d}".format(md["block_05"]["band_number"])
        sn = md["block_07"]["segment_number"]
        if ch not in file_info:
            file_info[ch] = {}
        file_info[ch][sn] = md
        file_segs.add(sn)
        file_chans.add(ch)

    xarray_obj.attrs["file_metadata"] = file_info.copy()

    # Most of the metadata are the same between files.
    # From here on we will just rely on the metadata from a single data file
    # for each resolution.
    res_md = {}
    for res in ["LOW", "MED", "HIGH"]:
        # Find a file file for this resolution: Any one will do
        res_chans = list(set(DATASET_INFO[res]).intersection(file_info.keys()))
        if res_chans:
            # Gets metadata for all available segments for this channel
            segment_info = file_info[res_chans[0]]
            # Get the metadata for any of the segments (doesn't matter which)
            res_md[res] = segment_info[list(segment_info.keys())[0]]

    # If we plan to self register, make sure we requested a resolution that we
    # actually plan to read
    if self_register and self_register not in res_md:
        raise ValueError(
            "Resolution requested for self registration has not been read."
        )

    if len(list(res_md.keys())) == 0:
        raise ValueError(
            "No valid files found in list, make sure .DAT.bz2 are bunzip2-ed: "
            f"{fnames}"
        )

    # Gather metadata
    # Assume the same for all resolutions.   Not true, but close enough.
    highest_md = res_md[list(res_md.keys())[0]]
    start_dt = metadata_to_datetime(
        highest_md, time_var="ob_start_time"
    )  # Assume same for all
    end_dt = metadata_to_datetime(
        highest_md, time_var="ob_end_time"
    )  # Assume same for all
    # mid_dt = start_dt + (end_dt - start_dt)/2
    ob_area = highest_md["block_01"]["ob_area"]
    if ob_area == "FLDK":
        xarray_obj.attrs["sector_name"] = "Full-Disk"
    elif ob_area[0:2] == "JP":
        xarray_obj.attrs["sector_name"] = "Japan-{}".format(ob_area[2:])
    elif ob_area[0] == "R":
        xarray_obj.attrs["sector_name"] = "Regional-{}-{}".format(
            ob_area[1], ob_area[2:]
        )
    else:
        raise ValueError("Unregognized ob_area {}".format(ob_area))
    xarray_obj.attrs["start_datetime"] = start_dt
    xarray_obj.attrs["end_datetime"] = end_dt
    xarray_obj.attrs["source_name"] = "ahi"
    xarray_obj.attrs["data_provider"] = "jma"
    xarray_obj.attrs["platform_name"] = highest_md["block_01"]["satellite_name"].lower()
    xarray_obj.attrs["area_definition"] = area_def
    xarray_obj.attrs["source_file_names"] = [
        os.path.basename(fname) for fname in fnames
    ]

    # If metadata_only requested, return here.
    if metadata_only:
        LOG.info("Only need metadata from first file, returning")
        return {"METADATA": xarray_obj}

    # If one or more channels are missing a segment that other channels have, add it in
    # as "None". This will be set to bad values in the output data
    for ch, segs in file_info.items():
        diff = file_segs.difference(segs.keys())
        if diff:
            segs.update({(sn, None) for sn in diff})

    all_chans_list = []
    for chl in list(ALL_CHANS.values()) + list(ALL_GVARS.values()):
        all_chans_list += chl

    # If specific channels were requested, check them against input data
    # If specific channels were requested, but no files exist for one of the
    # channels, then error
    if chans:
        for chan in chans:
            if chan not in all_chans_list:
                raise ValueError("Requested channel {0} not recognized.".format(chan))
            if chan[0:3] not in file_chans:
                # raise ValueError('Requested channel {0} not found in input data'.
                # format(chan))
                LOG.warning("Requested channel %s not found in input data", chan)

    # If no specific channels were requested, get everything
    if not chans:
        chans = all_chans_list
    # Creates dict whose keys are band numbers in the form B## and whose values are
    # lists containing the data type(s) requested for the band (e.g. Rad, Ref, BT).
    chan_info = {}
    for ch in chans:
        chn = ch[0:3]
        typ = ch[3:]
        if chn not in chan_info:
            chan_info[chn] = []
        chan_info[chn].append(typ)

    # Gather geolocation data
    # Assume datetime the same for all resolutions.  Not true, but close enough.
    # This saves us from having very slightly different solar angles for each channel.
    # Loop over resolutions and get metadata as needed
    # for res in ['HIGH', 'MED', 'LOW']:
    if self_register:
        LOG.info("")
        LOG.info("Getting geolocation information for adname %s.", adname)
        gmd = _get_geolocation_metadata(res_md[self_register])
        fldk_lats, fldk_lons = get_latitude_longitude(gmd, BADVALS, area_def)
        gvars[adname] = get_geolocation(
            start_dt, gmd, fldk_lats, fldk_lons, BADVALS, area_def
        )
        if not gvars[adname]:
            LOG.error(
                "GEOLOCATION FAILED for adname %s DONT_AUTOGEN_GEOLOCATION is: %s",
                adname,
                DONT_AUTOGEN_GEOLOCATION,
            )
            gvars[adname] = {}
    else:
        for res in ["LOW", "MED", "HIGH"]:
            try:
                res_md[res]
            except KeyError:
                continue
            LOG.info("")
            LOG.info(
                "Getting geolocation information for resolution %s for %s", res, adname
            )
            try:
                gmd = _get_geolocation_metadata(res_md[res])
                fldk_lats, fldk_lons = get_latitude_longitude(gmd, BADVALS, area_def)
                gvars[res] = get_geolocation(
                    start_dt, gmd, fldk_lats, fldk_lons, BADVALS, area_def
                )
            except IndexError as resp:
                LOG.exception("SKIPPING apparently no coverage or bad geolocation file")
                raise IndexError(resp)

    LOG.info("Done with geolocation for %s", adname)
    LOG.info("")
    # Read the data
    # Will read all data if area_def is None
    # Will only read required data if an area_def is provided
    for chan, types in chan_info.items():
        if chan not in file_info.keys():
            continue
        LOG.info("Reading %s", chan)
        chan_md = file_info[chan]
        for res, res_chans in DATASET_INFO.items():
            if chan in res_chans:
                break
        if (not self_register) and (res not in gvars.keys() or not gvars[res]):
            LOG.info(
                "We don't have geolocation information for %s for %s skipping %s",
                res,
                adname,
                chan,
            )
            continue
        if not area_def:
            dsname = res
        else:
            dsname = adname

        rad = ref = bt = False
        if "Rad" in types:
            rad = True
        if "Ref" in types:
            ref = True
        if "BT" in types:
            bt = True
        # zoom = 1
        # if self_register:
        #     if self_register == 'HIGH':
        #         if res == 'MED':
        #             zoom = 2
        #         if res == 'LOW':
        #             zoom = 4
        #     elif self_register == 'MED':
        #         if res == 'HIGH':
        #             zoom = 0.5
        #         if res == 'LOW':
        #             zoom = 2
        #     else:
        #         if res == 'HIGH':
        #             zoom = 0.25
        #         if res == 'MID':
        #             zoom = 0.5

        # Need to think about how to implement "zoom" to read only what is needed.
        # This is more complicated than I thought initially.
        # Mostly due to problems with ensuring that zoom produces integer dimensions
        #   and is an integer itself when inverted.
        # data = self.get_data(chan_md, gvars[res], rad, ref, bt, zoom=zoom)
        data = get_data(chan_md, gvars[res], rad, ref, bt)
        for typ, val in data.items():
            if dsname not in datavars:
                datavars[dsname] = {}
            datavars[dsname][chan + typ] = val

    # This needs to be fixed:
    #   remove any unneeded datasets from datavars and gvars
    #   also mask any values below -999.0
    if area_def:
        for res in ["HIGH", "MED", "LOW"]:
            if res not in gvars.keys():
                continue
            if adname not in gvars and "latitude" in gvars[res]:
                gvars[adname] = gvars[res]
            gvars.pop(res)

    if self_register:
        adname = "FULL_DISK"

        # Determine which resolution has geolocation
        LOG.info("Registering to %s", self_register)
        if self_register == "HIGH":
            datavars["FULL_DISK"] = datavars.pop("HIGH")
            for varname, var in datavars["LOW"].items():
                datavars["FULL_DISK"][varname] = zoom(var, 4, order=0)
            datavars.pop("LOW")
            for varname, var in datavars["MED"].items():
                datavars["FULL_DISK"][varname] = zoom(var, 2, order=0)
            datavars.pop("MED")

        elif self_register == "MED":
            datavars["FULL_DISK"] = datavars.pop("MED")
            for varname, var in datavars["LOW"].items():
                datavars["FULL_DISK"][varname] = zoom(var, 2, order=0)
            datavars.pop("LOW")
            for varname, var in datavars["HIGH"].items():
                datavars["FULL_DISK"][varname] = var[::2, ::2]
            datavars.pop("HIGH")

        elif self_register == "LOW":
            datavars["FULL_DISK"] = datavars.pop("LOW")
            for varname, var in datavars["MED"].items():
                datavars["FULL_DISK"][varname] = var[::2, ::2]
            datavars.pop("MED")
            for varname, var in datavars["HIGH"].items():
                datavars["FULL_DISK"][varname] = var[::4, ::4]
            datavars.pop("HIGH")

        else:
            raise ValueError("No geolocation data found.")
    print_mem_usage("MEMUSG", verbose=False)

    # basically just reformat the all_metadata dictionary to
    # reference channel names as opposed to file names..
    band_metadata = get_band_metadata(all_metadata)
    print_mem_usage("MEMUSG", verbose=False)

    # Remove lines and samples arrays.  Not needed.
    for res in gvars.keys():
        try:
            gvars[res].pop("Lines")
            gvars[res].pop("Samples")
            for varname, var in gvars[res].items():
                gvars[res][varname] = np.ma.array(
                    var, mask=gvars[res]["satellite_zenith_angle"].mask
                )
                gvars[res][varname] = np.ma.masked_where(
                    gvars[res]["satellite_zenith_angle"] > 85, gvars[res][varname]
                )
        except KeyError:
            pass
    for ds in datavars.keys():
        if not datavars[ds]:
            datavars.pop(ds)
        else:
            for varname in datavars[ds].keys():
                set_variable_metadata(xarray_obj.attrs, band_metadata, ds, varname)
                datavars[ds][varname] = np.ma.masked_less(datavars[ds][varname], -999.1)
                if "satellite_zenith_angle" in gvars[ds].keys():
                    datavars[ds][varname] = np.ma.masked_where(
                        gvars[ds]["satellite_zenith_angle"] > 85, datavars[ds][varname]
                    )

    print_mem_usage("MEMUSG", verbose=False)
    xarray_objs = {}

    for dsname in datavars.keys():
        xobj = xarray.Dataset()
        xobj.attrs = xarray_obj.attrs.copy()
        for varname in datavars[dsname].keys():
            xobj[varname] = xarray.DataArray(datavars[dsname][varname])
            if re.match(r"B[0-9][0-9]", varname):
                xobj[varname].attrs["channel_number"] = int(varname[1:3])
        for varname in gvars[dsname].keys():
            xobj[varname] = xarray.DataArray(gvars[dsname][varname])
        # if hasattr(xobj, 'area_definition') and xobj.area_definition is not None:
        #     xobj.attrs['interpolation_radius_of_influence'] =
        #     max(xobj.area_definition.pixel_size_x, xobj.area_definition.pixel_size_y)
        # else:
        #     xobj.attrs['interpolation_radius_of_influence'] = 2000
        # Make this a fixed 3000 (1.5 * lowest resolution data) - may want to
        # adjust for different channels.
        xobj.attrs["interpolation_radius_of_influence"] = 3000
        xarray_objs[dsname] = xobj
        # May need to deconflict / combine at some point, but for now just use
        # attributes from any one of the datasets as the METADATA dataset
        xarray_objs["METADATA"] = xobj[[]]
    LOG.info("Done reading AHI data for {}".format(adname))
    LOG.info("")

    print_mem_usage("MEMUSG", verbose=False)
    process_datetimes["overall_end"] = datetime.utcnow()
    from geoips.geoips_utils import output_process_times

    output_process_times(process_datetimes, job_str="AHI HSD Reader")
    return xarray_objs


def set_variable_metadata(xobj_attrs, band_metadata, dsname, varname):
    """
    Set variable metadata.

    MLS 20180914
    Setting xobj_attrs at the variable level for the associated
    channel metadata pulled from the actual netcdf file.
    This will now be accessible from the scifile object.
    Additionally, pull out specifically the band_wavelength and
    attach it to the _varinfo at the variable level - this is
    automatically pulled from the xobj_attrs dictionary
    and set in the variable._varinfo dictionary in scifile/scifile.py
    and scifile/containers.py (see empty_varinfo at the beginning
    of containers.py for dictionary fields that are automatically
    pulled from the appropriate location in the  xobj_attrs
    dictionary and set on the _varinfo dictionary)
    """
    if dsname not in xobj_attrs.keys():
        xobj_attrs[dsname] = {}
    bandname = varname.replace("Rad", "").replace("Ref", "").replace("BT", "")
    if varname not in xobj_attrs[dsname].keys():
        if bandname in band_metadata.keys():
            xobj_attrs[dsname][varname] = {}
            # Store the full metadata dictionary in the scifile metadata
            xobj_attrs[dsname][varname]["all"] = band_metadata[bandname]
            # Set the actual wavelength property on the variable itself
            if (
                "calibration_information" in band_metadata[bandname].keys()
                and "cent_wavelenth"
                in band_metadata[bandname]["calibration_information"].keys()
            ):
                xobj_attrs[dsname][varname]["wavelength"] = band_metadata[bandname][
                    "calibration_information"
                ]["cent_wavelenth"]


def get_band_metadata(all_metadata):
    """
    Get band metadata.

    This method basically just reformats the all_metadata
    dictionary that is set based on the metadata found
    in the netcdf object itself to reference channel
    names as opposed to filenames as the dictionary keys.
    """
    bandmetadata = {}
    for fname in all_metadata.keys():
        bandnum = all_metadata[fname]["block_05"]["band_number"]
        bandmetadata["B%02d" % bandnum] = {}
        for blockname in all_metadata[fname].keys():
            newkey = blockname
            if (
                "block" in blockname
                and "block_name" in all_metadata[fname][blockname].keys()
            ):
                newkey = all_metadata[fname][blockname]["block_name"]
            bandmetadata["B%02d" % bandnum][newkey] = all_metadata[fname][blockname]
    return bandmetadata


def get_data(md, gvars, rad=False, ref=False, bt=False, zoom=1.0):
    """Read data for a full channel's worth of files."""
    # Coordinate arrays for reading
    # Unsure if Lines can ever be None, but the test below was causing an error due to
    # testing the truth value of an entire array.  May need to implement test again here
    # to ensure that gvars['Lines'] is actually something, but testing this method for
    # now.
    # Test against full-disk.  Works for sectors...
    # if ('Lines' in gvars and 'Samples' in gvars) and gvars['Lines'].any()
    # and gvars['Samples'].any():
    if "Lines" in gvars and "Samples" in gvars:
        full_disk = False
        line_inds = gvars["Lines"]
        sample_inds = gvars["Samples"]
        shape = line_inds.shape

        # All required line numbers (used for determining which files to even look at)
        req_lines = set(line_inds.flatten())
    else:
        full_disk = True
        # Assume we are going to make a full-disk image
        smd = md[list(md.keys())[0]]
        nseg = smd["block_07"]["num_segments"]
        lines = smd["num_lines"] * nseg
        samples = smd["num_samples"]
        # sample_inds, line_inds = np.meshgrid(np.arange(samples), np.arange(lines))
        shape = (lines, samples)

        # # Determine dimension sizes
        # lines = []
        # samples = []
        # shell()
        # for seg, smd in md.items():
        #     lines.append(smd['num_lines'])
        #     samples.append(smd['num_samples'])
        # # Sum the nubmer of lines per segment
        # lines = np.sum(lines)
        # # Samples must be the same for all segments
        # samples = set(samples)
        # if len(samples) != 1:
        #     raise ValueError('Number of samples per segment do not match.')
        # samples = list(samples)[0]

        # sample_inds, line_inds = np.meshgrid(np.arange(samples), np.arange(lines))
        # line_inds = line_inds.astype('int32')
        # sample_inds = sample_inds.astype('int32')

        req_lines = set(range(lines))

    # Initialize empty array for channel
    valid_bits = md[list(md.keys())[0]]["block_05"]["valid_bits_per_pixel"]
    # # Ensure zoom produces an integer result
    # zoom_mod = np.mod(np.array(shape), 1/zoom)
    # if np.any(zoom_mod):
    #     raise ValueError('Zoom level does not produce integer dimensions.')
    # counts = np.full(np.int(np.array(shape) * zoom),
    #                  1 + 2**valid_bits, dtype=np.uint16)
    LOG.debug("Making counts array")
    counts = np.full(shape, 1 + 2**valid_bits, dtype=np.uint16)

    # Loop over segments
    for seg, smd in md.items():
        LOG.info("Reading segment {}".format(seg))
        # Skip if we don't have a file for this segment
        if not smd:
            continue

        # Get calibration info
        LOG.debug("Getting calibration info")
        calib = smd["block_05"]
        gain = calib["gain"]
        offset = calib["offset"]
        count_badval = calib["count_badval"]
        count_outbounds = calib["count_outside_scan"]
        valid_bits = smd["block_05"]["valid_bits_per_pixel"]

        # Get info for current file
        LOG.debug("Getting lines and samples")
        path = smd["path"]
        nl = smd["num_lines"]
        ns = smd["num_samples"]
        first_line = smd["block_07"]["segment_first_line"]
        lines = range(first_line, first_line + nl)

        # If required lines and file lines don't intersect, move on to the next file
        if not req_lines.intersection(lines):
            continue

        LOG.debug("Determining indicies in data array.")
        header_len = smd["block_01"]["total_header_length"]
        if not full_disk:
            data_inds = np.where(
                (line_inds >= first_line) & (line_inds < first_line + nl)
            )
            data_lines = line_inds[data_inds] - first_line
            data_samples = sample_inds[data_inds]
            counts[data_inds] = np.memmap(
                path, mode="r", dtype=np.uint16, offset=header_len, shape=(nl, ns)
            )[data_lines, data_samples]
        else:
            first_line -= 1
            last_line = first_line + nl
            counts[first_line:last_line, :] = np.memmap(
                path, mode="r", dtype=np.uint16, offset=header_len, shape=(nl, ns)
            )[:, :]

        LOG.info("Doing the actual read for segment {}".format(seg))

    # It appears that there are values that appear to be good outside the allowable
    # range.  The allowable range is set by the number of valid bits per pixel
    # This number can be 11, 12, or 14
    # These correspond to valid ranges of [0:2048], [0:4096], [0:16384]
    # Here we find all invalid pixels so we can mask later
    outrange_inds = np.where(((counts < 0) | (counts > 2**valid_bits)))
    error_inds = np.where(counts == count_badval)
    offdisk_inds = np.where(counts == count_outbounds)

    # It appears that some AHI data does not correctly set erroneous pixels to
    # count_badval. To fis this, we can find the count value at which radiances become
    # less than or equal to zero. Any counts above that value are bad.
    # Note: This is only for use when calculating brightness temperatures
    # (i.e. when gain is negative)
    if gain < 0:
        root = -offset / gain
        root_inds = np.where(counts > root)
    else:
        root_inds = []

    # Create mask for good values in order to suppress warning from log of negative
    # values.
    # Note: This is only for use when calculating brightness temperatures
    good = np.ones(counts.shape, dtype=bool)
    good[root_inds] = 0
    good[outrange_inds] = 0
    good[error_inds] = 0
    good[offdisk_inds] = 0

    # Create data dict
    data = {}

    # Convert to radiances
    data["Rad"] = counts * gain + offset

    # If reflectance is requested
    # Note the weird memory manipulation to save memory when radiances are not requested
    band_num = calib["band_number"]
    if ref:
        LOG.info("Converting to Reflectance")
        if band_num not in range(1, 7):
            raise ValueError(
                "Unable to calculate reflectances for band #{0}".format(band_num)
            )

        # Get the radiance data
        # Have to do this when using ne
        rad_data = data["Rad"]  # NOQA

        # If we don't need radiances, then reuse the memory
        if not rad:
            data["Ref"] = data.pop("Rad")
        else:
            data["Ref"] = np.empty_like(data["Rad"])

        c_prime = calib["c_prime"]  # NOQA
        ne.evaluate("rad_data * c_prime", out=data["Ref"])

    # If brightness temperature is requested
    # Note the weird memory manipulation to save memory when radiances are not requested
    if bt:
        LOG.info("Converting to Brightness Temperature")
        if band_num not in range(7, 17):
            raise ValueError(
                f"Unable to calculate brightness temperatures for band #{band_num}"
            )

        # Get the radiance data
        # Have to do this when using ne
        rad_data = data["Rad"]  # NOQA

        # If we don't need radiances, then reuse the memory
        if not rad:
            data["BT"] = data.pop("Rad")
        else:
            data["BT"] = np.empty_like(data["Rad"])

        h = calib["planck_const"]
        k = calib["boltz_const"]
        wl = calib["cent_wavelenth"] / 1000000.0  # Initially in microns
        c = calib["speed_of_light"]
        c0 = calib["c0"]  # NOQA
        c1 = calib["c1"]  # NOQA
        c2 = calib["c2"]  # NOQA

        # Make this as in-place as possible
        # Note, rad_data are in units of W/(m**2 sr um)
        log_coeff = (2.0 * h * c**2) / (wl**5)  # NOQA
        dividend = (h * c) / (k * wl)  # NOQA
        ne.evaluate(
            "dividend/log( (log_coeff/(rad_data*1000000.0))+1 )", out=data["BT"]
        )

    for val in data.values():
        LOG.info("Setting badvals")
        val[root_inds] = BADVALS["Root_Test"]
        val[outrange_inds] = BADVALS["Out_Of_Valid_Range"]
        val[offdisk_inds] = BADVALS["Off_Of_Disk"]
        val[error_inds] = BADVALS["Error"]

    return data
