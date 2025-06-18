# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Read SEVIRI hrit data.

Notes
-----
   1) At present, this reader does not work for High Resolution Visible data,
      which is ignored. Additionally, to ease generation of geolocation fields,
      datasets are assumed to be square and centered at their sub longitude.

20170330 MLS Try to only decompress what we need (VERY filename dependent),
  make scifile and hrit channel names match (more filename dependence),
  don't try to decompress/open file for import_metadata (more filename
  dependence for time). satpy requires time to open file, and requires standard
  (decompressed) filenames, so built in filename dependence by using satpy.
"""
# Python Standard Libraries
import os
import logging
import numpy as np
from geoips.plugins.modules.readers.utils.hrit_reader import HritFile, HritError

# GeoIPS Libraries
from geoips.errors import NoValidFilesError
from geoips.interfaces import readers
from geoips.filenames.base_paths import PATHS as gpaths
from geoips.utils.context_managers import import_optional_dependencies
from geoips.plugins.modules.readers.utils.geostationary_geolocation import (
    get_geolocation,
)

LOG = logging.getLogger(__name__)

with import_optional_dependencies(loglevel="info"):
    """Attempt to import a package and print to LOG.info if the import fails."""
    import numexpr as ne

try:
    NPROC = 6
    ne.set_num_threads(NPROC)
except NameError:
    err_str = "Failed ne.set_num_threads in seviri_hrit.py. "
    err_str += "If you need numexpr, install it."
    LOG.info(err_str)


# These should be added to the data file object
BADVALS = {
    "Off_Of_Disk": -999.9,
}

VIS_CALIB = {
    "msg1": {"B01": 65.2296, "B02": 73.0127, "B03": 62.3715, "B12": 78.7599},
    "msg2": {"B01": 65.2065, "B02": 73.1869, "B03": 61.9923, "B12": 79.0113},
    "msg3": {"B01": 65.5148, "B02": 73.1807, "B03": 62.0208, "B12": 78.9416},
    "msg4": {"B01": 65.2656, "B02": 73.1692, "B03": 61.9416, "B12": 79.0035},
}

IR_CALIB = {
    "msg1": {
        "B04": {"wn": 2567.330, "a": 0.9956, "b": 3.410},  # IR3.9 Water vapour channel
        "B05": {"wn": 1598.103, "a": 0.9962, "b": 2.218},  # IR6.2 Water vapour channel
        "B06": {"wn": 1362.081, "a": 0.9991, "b": 0.478},  # IR7.3 Water vapour channel
        "B07": {"wn": 1149.069, "a": 0.9996, "b": 0.179},  # IR8.7 Atmospheric window
        "B08": {"wn": 1034.343, "a": 0.9999, "b": 0.060},  # IR9.7 Ozone channel
        "B09": {"wn": 930.647, "a": 0.9983, "b": 0.625},  # IR10.8 Atmospheric window
        "B10": {"wn": 839.660, "a": 0.9988, "b": 0.397},  # IR12.0 Atmospheric window
        "B11": {"wn": 752.387, "a": 0.9981, "b": 0.578},
    },  # IR13.4 Carbon dioxide channel
    "msg2": {
        "B04": {"wn": 2568.832, "a": 0.9954, "b": 3.438},  # IR3.9 Water vapour channel
        "B05": {"wn": 1600.548, "a": 0.9963, "b": 2.185},  # IR6.2 Water vapour channel
        "B06": {"wn": 1360.330, "a": 0.9991, "b": 0.470},  # IR7.3 Water vapour channel
        "B07": {"wn": 1148.620, "a": 0.9996, "b": 0.179},  # IR8.7 Atmospheric window
        "B08": {"wn": 1035.289, "a": 0.9999, "b": 0.056},  # IR9.7 Ozone channel
        "B09": {"wn": 931.700, "a": 0.9983, "b": 0.640},  # IR10.8 Atmospheric window
        "B10": {"wn": 836.445, "a": 0.9988, "b": 0.408},  # IR12.0 Atmospheric window
        "B11": {"wn": 751.792, "a": 0.9981, "b": 0.561},
    },  # IR13.4 Carbon dioxide channel
    "msg3": {
        "B04": {"wn": 2547.771, "a": 0.9915, "b": 2.9002},  # IR3.9 Water vapour channel
        "B05": {"wn": 1595.621, "a": 0.9960, "b": 2.0337},  # IR6.2 Water vapour channel
        "B06": {"wn": 1360.377, "a": 0.9991, "b": 0.4340},  # IR7.3 Water vapour channel
        "B07": {"wn": 1148.130, "a": 0.9996, "b": 0.1714},  # IR8.7 Atmospheric window
        "B08": {"wn": 1034.715, "a": 0.9999, "b": 0.0527},  # IR9.7 Ozone channel
        "B09": {"wn": 929.842, "a": 0.9983, "b": 0.6084},  # IR10.8 Atmospheric window
        "B10": {"wn": 838.659, "a": 0.9988, "b": 0.3882},  # IR12.0 Atmospheric window
        "B11": {"wn": 750.653, "a": 0.9982, "b": 0.5390},
    },  # IR13.4 Carbon dioxide channel
    "msg4": {
        "B04": {"wn": 2555.280, "a": 0.9916, "b": 2.9438},  # IR3.9 Water vapour channel
        "B05": {"wn": 1596.080, "a": 0.9959, "b": 2.0780},  # IR6.2 Water vapour channel
        "B06": {"wn": 1361.748, "a": 0.9990, "b": 0.4929},  # IR7.3 Water vapour channel
        "B07": {"wn": 1148.130, "a": 0.9996, "b": 0.1731},  # IR8.7 Atmospheric window
        "B08": {"wn": 1034.851, "a": 0.9998, "b": 0.0597},  # IR9.7 Ozone channel
        "B09": {"wn": 931.122, "a": 0.9983, "b": 0.6256},  # IR10.8 Atmospheric window
        "B10": {"wn": 839.113, "a": 0.9988, "b": 0.4002},  # IR12.0 Atmospheric window
        "B11": {"wn": 748.585, "a": 0.9981, "b": 0.5635},
    },
}  # IR13.4 Carbon dioxide channel

geolocation_variable_names = [
    "latitude",
    "longitude",
    "solar_zenith_angle",
    "satellite_zenith_angle",
    "solar_azimuth_angle",
    "satellite_azimuth_angle",
]

interface = "readers"
family = "standard"
name = "seviri_hrit"


def calculate_chebyshev_polynomial(coefs, start_dt, end_dt, dt):
    """Calculate Chebyshev Polynomial."""
    start_to_end = (end_dt - start_dt).seconds
    # dt_to_end = (end_dt - dt).seconds
    start_to_dt = (dt - start_dt).seconds
    t = (start_to_dt - 0.5 * (start_to_end)) / (0.5 * (start_to_end))
    t2 = 2 * t

    # I think this is what was in the documentation
    # MSG_Level_1_5_Image_Data_Format_Description.pdf
    # p 87 earth fixed coordinate frame
    # p 124 decoding chebychev polynomial function
    d = 0
    dd = 0
    for j in range(7, 1, -1):
        save = d
        d = t2 * d - dd + coefs[j]
        dd = save
    d = t * d - dd + 0.5 * coefs[0]

    # f = -0.5 * coefs[0] # First term of Chebyshev polynomial
    # f = f + coefs[0] # second term of Chebyshev polynomial
    # f = f + coefs[1]*t # third term
    # T_k_minus_3 = 1
    # T_k_minus_2 = t
    # T_k_minus_1 = t2*T_k_minus_2 - T_k_minus_3
    # remaining terms recursively defined
    # for xcoef in coefs[3:]:
    #    f = f + xcoef * T_k_minus_1
    #    T_k_minus_3 = T_k_minus_2
    #    T_k_minus_2 = T_k_minus_1
    #    T_k_minus_1 = t2*T_k_minus_2 - T_k_minus_3

    return d


class XritError(Exception):
    """Raise exception on XritError."""

    def __init__(self, msg, code=None):
        """Initialize XritError."""
        self.code = code
        self.value = msg

    def __str__(self):
        """Return XritError string."""
        if self.code:
            return "{}: {}".format(self.code, self.value)
        else:
            return self.value


def compare_dicts(d1, d2, skip=None):
    """Compare the values in two dictionaries.

    If they are equal, return True, otherwise False
    If skip is set and contains one of the keys, skip that key
    """
    if d1.keys() != d2.keys():
        return False

    for key in d1.keys():
        if skip and key in skip:
            continue
        if d1[key] != d2[key]:
            return False
    return True


def get_top_level_metadata(fnames, sect):
    """Get top level metadata."""
    md = {}
    for fname in fnames:
        df = HritFile(fname)
        if "block_2" in df.metadata.keys():
            break
    if "GEOS" in df.metadata.get("block_2", {}).get("projection", {}):
        md["sector_name"] = "Full-Disk"
    else:
        projection = df.metadata.get("block_2", {}).get("projection", {})
        st = df.start_datetime.isoformat()
        et = df.start_datetime.isoformat()
        raise HritError(
            f"Unknown projection encountered: {projection}.\n"
            f"start_datetime={st}\n"
            f"end_datetime={et}"
        )
    md["start_datetime"] = df.start_datetime
    md["end_datetime"] = df.start_datetime
    md["data_provider"] = "nesdisstar"
    # MLS Check platform_name
    # Turn msg4_iodc into msg4.  Then pull geoips satname (meteoEU/meteoIO)
    # from utils/satellite_info.py
    msg_satname = df.annotation_metadata["platform"].lower().replace("_iodc", "")
    # Save actual satellite name (msg1 / msg4) for the coefficient tables above.
    # geoips specific platform_name should be msg-1 or msg-4
    md["satellite_name"] = msg_satname
    # from geoips.utils.satellite_info import open_satinfo
    # try:
    #     satinfo = open_satinfo(msg_satname)
    #     if hasattr(satinfo, 'geoips_satname'):
    #         msg_satname = satinfo.geoips_satname
    # except KeyError:
    #     raise HritError('Unknown satname encountered: {}'.format(msg_satname))
    md["platform_name"] = msg_satname[0:3] + "-" + msg_satname[-1]  # msg-1 or msg-4
    md["source_name"] = "seviri"
    md["source_file_names"] = [os.path.basename(fname) for fname in fnames]
    md["area_definition"] = sect
    md["sample_distance_km"] = 3.0

    return md


def get_latitude_longitude(gmd, BADVALS, area_def):
    """Generate full-disk latitudes and longitudes."""
    # Anywhere you see NOQA or noqa: F841, this is added since the variables are used
    # however they are not recognized by flake8 linter under numexpr.evaluate()
    # Constants
    pi = np.pi
    # Must include rad2deg variable, because it is used within the
    # numexpr command below.  flake8 does not recognize it as being
    # used, so must include # NOQA flag
    rad2deg = 180.0 / pi  # NOQA
    deg2rad = pi / 180.0
    Rs = 42164  # Satellite altitude (km)  # noqa: F841
    Re = 6378.1690  # Earth equatorial radius (km)
    Rp = 6356.5838  # Earth polar radius (km)
    r3 = Re**2 / Rp**2  # noqa: F841
    sd_coeff = 1737122264  # If there is a problem for MSG use 1737121856  # noqa: F841
    lon0 = gmd["lon0"]  # noqa: F841

    deg2rad = np.pi / 180.0
    x, y = np.meshgrid(
        np.arange(0, gmd["num_samples"], 1), np.arange(0, gmd["num_lines"], 1)
    )
    x = np.fliplr(x)
    y = np.fliplr(y)
    x = deg2rad * (x - gmd["sample_offset"]) / (2**-16 * gmd["sample_scale"])
    y = deg2rad * (y - gmd["line_offset"]) / (2**-16 * gmd["line_scale"])

    cos_x = np.cos(x)
    sin_x = np.sin(x)  # noqa: F841
    cos_y = np.cos(y)
    sin_y = np.sin(y)  # noqa: F841

    sd = ne.evaluate("(Rs * cos_x * cos_y)**2 - (cos_y**2 + r3 * sin_y**2) * sd_coeff")
    bad_mask = sd < 0.0
    sd[bad_mask] = 0.0
    sd **= 0.5

    # Doing inplace operations when variables are no longer needed

    # sd no longer needed
    sn = sd
    ne.evaluate("(Rs * cos_x * cos_y - sd) / (cos_y**2 + r3 * sin_y**2)", out=sn)

    # cos_x no longer needed
    s1 = cos_x
    ne.evaluate("Rs - (sn * cos_x * cos_y)", out=s1)

    # Nothing unneed
    s2 = ne.evaluate("sn * sin_x * cos_y")  # noqa: F841

    # sin_y no longer needed
    s3 = cos_y
    ne.evaluate("-sn * sin_y", out=s3)

    # sn no longer needed
    sxy = sn
    ne.evaluate("sqrt(s1**2 + s2**2)", out=sxy)

    # s3 no longer needed
    lats = s3
    ne.evaluate("rad2deg * arctan(r3 * s3 / sxy)", out=lats)

    # s1 no longer needed
    lons = s1
    ne.evaluate("rad2deg * arctan(s2 / s1) + lon0", out=lons)
    lons[lons > 180.0] -= 360

    # Set bad values
    lats[bad_mask] = BADVALS["Off_Of_Disk"]
    lons[bad_mask] = BADVALS["Off_Of_Disk"]

    return lats, lons


# def get_low_res_geolocation_args(prologue):
def _get_geolocation_metadata(prologue, file_metadata):
    """Get geolocation metadata."""
    geomet = {}
    geomet["platform_name"] = file_metadata["platform_name"]
    geomet["source_name"] = file_metadata["source_name"]
    geomet["scan_mode"] = prologue["imageDescription"]["projectionDescription"][
        "typeOfProjection"
    ]
    # Used for cached filenames
    geomet["scene"] = geomet["scan_mode"]
    geomet["lon0"] = prologue["imageDescription"]["projectionDescription"][
        "longitudeOfSSP"
    ]
    geomet["num_lines"] = prologue["imageDescription"]["referenceGridVIS_IR"][
        "numberOfLines"
    ]
    geomet["num_samples"] = prologue["imageDescription"]["referenceGridVIS_IR"][
        "numberOfColumns"
    ]
    geomet["line_scale"] = -13642337  # This will only work for low resolution data
    geomet["sample_scale"] = -13642337
    geomet["line_offset"] = geomet["num_lines"] / 2
    geomet["sample_offset"] = geomet["num_samples"] / 2
    geomet["start_datetime"] = prologue["imageAcquisition"]["plannedAcquisitionTime"][
        "trueRepeatCycleStart"
    ]
    geomet["H_m"] = 42164 * 1000.0  # Satellite altitude (m)
    geomet["roi_factor"] = 10  # roi = res_km * 1000 * roi_factor
    return geomet


def countsToRad(counts, slope, offset):
    """Convert counts to rad."""
    rad = np.full_like(counts, -999.0)
    rad[counts > 0] = offset + (slope * counts[counts > 0])
    return rad


def radToRef(rad, sun_zen, platform, band):
    """Convert Rad to Ref."""
    irrad = VIS_CALIB[platform][band]
    ref = np.full_like(rad, -999.0)
    # 0 to 1 rather than 0 to 100
    ref[rad > 0] = rad[rad > 0] / irrad
    # DO NOT REMOVE THIS STEP ALTOGETHER!!!!  Just take out the solar zenith correction
    # part. Previously, solar zenith correction was being applied twice, then we were
    # off by factor of pi/irrad. Now we should be good!
    # ref[rad > 0] = np.pi * rad[rad > 0] /
    #                                 (irrad * np.cos((np.pi / 180) * sun_zen[rad > 0]))
    ref[rad > 0] = np.pi * rad[rad > 0] / irrad
    ref[ref < 0] = 0
    ref[ref > 1] = 1
    ref[sun_zen > 95] = -999.0
    ref[sun_zen <= -999] = -999.0
    return ref


def radToBT(rad, platform, band):
    """Convert rad to BT."""
    c1 = 1.19104e-05
    c2 = 1.43877
    wn = IR_CALIB[platform][band]["wn"]
    a = IR_CALIB[platform][band]["a"]
    b = IR_CALIB[platform][band]["b"]
    temp = np.full_like(rad, -999.0)
    temp[rad > 0] = ((c2 * wn) / np.log(1 + wn**3 * c1 / rad[rad > 0]) - b) / a
    return temp


class Chan(object):
    """Channel class."""

    _good_names = [
        "B01Rad",
        "B01Ref",  # VIS0.6 Cloud mapping
        "B02Rad",
        "B02Ref",  # VIS0.8 Vegetation index
        "B03Rad",
        "B03Ref",  # NIR1.6 Cloud / snow discrimination
        "B04Rad",
        "B04BT",  # IR3.9  Atmospheric window
        "B05Rad",
        "B05BT",  # IR6.2  Water vapour channel (Upper atmosphere)
        "B06Rad",
        "B06BT",  # IR7.3  Water vapour channel (Lower atmosphere)
        "B07Rad",
        "B07BT",  # IR8.7  Atmospheric window
        "B08Rad",
        "B08BT",  # IR9.7  Ozone channel
        "B09Rad",
        "B09BT",  # IR10.8 Atmospheric window
        "B10Rad",
        "B10BT",  # IR12.0 Atmospheric window
        "B11Rad",
        "B11BT",
    ]  # IR13.4 Carbon dioxide channel

    def __init__(self, name):
        """Initialize Chan object."""
        if "B12" in name:
            raise HritError(
                "Channel 12 (High Resolution Visible) currently not handled."
            )
        if name not in self._good_names:
            raise ValueError("Unknown channel name: {}".format(name))
        self._name = name
        self._band = name[0:3]
        self._type = name[3:]

    @property
    def name(self):
        """Name property."""
        return self._name

    @property
    def band(self):
        """Band property."""
        return self._band

    @property
    def band_num(self):
        """Band number property."""
        return int(self._band[1:])

    @property
    def type(self):
        """Type property."""
        return self._type


class ChanList(object):
    """ChanList Class."""

    def __init__(self, chans):
        """Initialize ChanList object."""
        chans = set(chans)
        self._info = {"chans": [Chan(chan) for chan in chans]}
        self._info["names"] = list(set([chan.name for chan in self.chans]))
        self._info["bands"] = list(set([chan.band for chan in self.chans]))
        self._info["types"] = list(set([chan.type for chan in self.chans]))

    @property
    def chans(self):
        """Chans property."""
        return self._info["chans"]

    @property
    def names(self):
        """Names property."""
        return self._info["names"]

    @property
    def bands(self):
        """Bands property."""
        return self._info["bands"]

    @classmethod
    def _all_types_for_bands(cls, bands):
        """List all types for bands."""
        good_names = Chan._good_names
        chans = set()
        for chan in good_names:
            for band in bands:
                if band in chan:
                    chans.add(chan)
        return cls(chans)


def call_single_time(
    fnames, metadata_only=False, chans=None, area_def=None, self_register=False
):
    """Read SEVIRI hrit data products.

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
    gvars = {}
    datavars = {}
    adname = "undefined"
    # Remove any HRV files from file list
    # See note 1 at top of module

    fnames = [fname for fname in fnames if not any(val in fname for val in ["HRV"])]
    if not fnames:
        raise NoValidFilesError("No files found in list, skipping")

    # Check inputs
    if self_register and self_register != "LOW":
        raise XritError(
            "Unknown resolution supplied to self_register: {}".format(self_register)
        )
    if area_def:
        try:
            adname = area_def.description
        except AttributeError:
            TypeError("Keyword area_def must be of type Sector.")
    else:
        adname = "FULL_DISK"

    import xarray

    xarray_obj = xarray.Dataset()

    # Gather top-level metadata. MUst pass ALL fnames to make sure we
    # use a datafile, and not pro or epi (they do not contain projection
    # information)
    xarray_obj.attrs = get_top_level_metadata(fnames, area_def)

    # chans == [] specifies we don't want to read ANY data, just metadata.
    # chans == None specifies that we are not specifying a channel list,
    #               and thus want ALL channels.
    if metadata_only:
        # If NO CHANNELS were specifically requested, just return at this
        # point with the metadata fields populated. A dummy SciFile dataset
        # will be created with only metadata. This is for checking what
        # platform/source combination we are using, etc.
        return {"METADATA": xarray_obj}

    # Create file objects for each input file and organize
    dfs = {}
    pro = None
    epi = None
    sdt = None
    imgf = None
    all_segs = set()
    from struct import error as structerror

    for fname in fnames:
        try:
            df = HritFile(fname)
        except structerror:
            # Don't fail altogether if there is one bad file
            LOG.exception("FAILED reader %s, skipping", fname)
            continue
        # Ensure all files have same start datetime
        if not sdt:
            sdt = df.start_datetime
        if df.start_datetime != sdt:
            raise HritError(
                "Start date time does not match for all files: {}".format(fnames)
            )
        # Get prologue
        if df.file_type == "prologue":
            pro = df.prologue
            dt = xarray_obj.attrs["start_datetime"]
            # xarray_obj.attrs['prologue'] = pro
            for poly in df.prologue["satelliteStatus"]["orbit"]["orbitPolynomial"]:
                if dt <= poly["endTime"] and dt >= poly["startTime"]:
                    LOG.info("Calculating x/y/z satellite location")

                    st = poly["startTime"]
                    et = poly["endTime"]
                    xcoef = poly["X"]
                    ycoef = poly["Y"]
                    zcoef = poly["Z"]
                    x = calculate_chebyshev_polynomial(xcoef, st, et, dt)
                    y = calculate_chebyshev_polynomial(ycoef, st, et, dt)
                    z = calculate_chebyshev_polynomial(zcoef, st, et, dt)
                    xarray_obj.attrs["satECF_m"] = {}
                    xarray_obj.attrs["satECF_m"]["x"] = x * 1000
                    xarray_obj.attrs["satECF_m"]["y"] = y * 1000
                    xarray_obj.attrs["satECF_m"]["z"] = z * 1000

        # Get epilogue
        elif df.file_type == "epilogue":
            epi = df.epilogue
            xarray_obj.attrs["epilogue"] = epi
        # Store data files, organized by band, then segment
        elif df.file_type == "image":
            # Ensure all files have the same geolocation information
            if not imgf:
                imgf = df
            if not compare_dicts(
                imgf.geolocation_metadata,
                df.geolocation_metadata,
                skip=["line_offset", "sample_offset"],
            ):
                raise HritError(
                    "Geolocation metadata do not match for image files: {}".format(
                        fnames
                    )
                )
            # Initialize band info with None for eight segments
            if df.band not in dfs:
                dfs[df.band] = {num: None for num in range(1, 9)}
            dfs[df.band][df.segment] = df
            all_segs.add(df.segment)
        else:
            LOG.warning("Unhandled file type encountered: {}".format(df.file_type))
    if not pro:
        raise HritError("No prologue file found")

    # If specific channels were requested, check them against the input data
    if chans:
        chlist = ChanList(list(set(chans) - set(geolocation_variable_names)))
        for chan in chlist.chans:
            if chan.band not in dfs.keys():
                raise ValueError(
                    "Requested channel {} not found in input data.".format(chan.name)
                )
    # If no specific channels were requested, get everything
    else:
        chlist = ChanList._all_types_for_bands(dfs.keys())

    xarray_obj.attrs["datavars"] = {}
    # Gather geolocation data
    # Assume the datetime is the same for all resolution.  Not true, but close enough.
    # This saves us from having slightly different solar angles for each channel.
    gmd = _get_geolocation_metadata(pro, xarray_obj.attrs)
    fldk_lats, fldk_lons = get_latitude_longitude(gmd, BADVALS, area_def)
    gvars[adname] = get_geolocation(sdt, gmd, fldk_lats, fldk_lons, BADVALS, area_def)

    # Drop files for channels other than those requested and decompress
    outdir = os.path.join(
        gpaths["LOCALSCRATCH"],
        xarray_obj.attrs["source_name"],
        xarray_obj.attrs["platform_name"],
        xarray_obj.attrs["start_datetime"].strftime("%Y%m%d%H%M"),
    )

    from geoips.filenames.base_paths import make_dirs

    make_dirs(outdir)

    # Can not change dictionary size during iteration for Python 3
    skip_bands = []
    for band in dfs.keys():
        if band not in chlist.bands:
            skip_bands += [band]
            # dfs.pop(band)
            continue
        else:
            # dfs[band] = {seg: df.decompress(outdir) for seg, df in dfs[band].items()}
            skip_segs = []
            for seg, df in dfs[band].items():
                if df is None:
                    LOG.error(
                        "FAILED READ ABOVE, SKIPPING TRYING TO DECOMPRESS FILE %s %s",
                        band,
                        seg,
                    )
                    skip_segs += [seg]
                    # dfs[band].pop(seg)
                    continue
                try:
                    dfs[band][seg] = df.decompress(outdir)
                except HritError as resp:
                    skip_segs += [seg]
                    LOG.error(
                        "FAILED DECOMPRESSING, %s, SKIPPING FILE %s", str(resp), df.name
                    )
            for skip_seg in skip_segs:
                dfs[band].pop(skip_seg)
    for skip_band in skip_bands:
        dfs.pop(skip_band)

    # Create data arrays for requested data and read count data
    num_lines = pro["imageDescription"]["referenceGridVIS_IR"]["numberOfLines"]
    num_samples = pro["imageDescription"]["referenceGridVIS_IR"]["numberOfColumns"]
    count_data = {}
    annotation_metadata = {}
    for band in chlist.bands:
        if len(dfs[band].items()) == 0:
            LOG.error("No data in band %s, SKIPPING", band)
            continue
        # Create empty full-disk array for this channel
        data = np.full((num_lines, num_samples), -999.9, dtype=float)
        # Read data into data array
        for seg, df in dfs[band].items():
            seg_num_lines = df.metadata["block_1"]["num_lines"]
            start_line = seg_num_lines * (seg - 1)
            end_line = seg_num_lines * seg
            try:
                data[start_line:end_line, 0:] = df._read_image_data()
            except ValueError as resp:
                LOG.error("FAILED READING SEGMENT, SKIPPING %s" % (resp))
        LOG.info("Read band %s %s" % (band, df.annotation_metadata["band"]))
        if "Lines" in gvars[adname]:
            count_data[band] = data[gvars[adname]["Lines"], gvars[adname]["Samples"]]
        else:
            count_data[band] = data
        annotation_metadata[band] = df.annotation_metadata

    datavars[adname] = {}
    radiances = {}
    image_cal = pro["radiometricProcessing"]["level15ImageCalibration"]
    for chan in chlist.chans:
        counts = count_data[chan.band]
        if chan.band not in radiances:
            band_cal = image_cal[chan.band_num - 1]
            offset = band_cal["offset"]
            slope = band_cal["slope"]
            radiances[chan.band] = countsToRad(counts, slope, offset)
        if chan.type == "Rad":
            datavars[adname][chan.name] = radiances[chan.band]
        if chan.type == "Ref":
            LOG.info(
                "Calculating reflectances for %s, data range %f to %f",
                chan.band,
                radiances[chan.band].min(),
                radiances[chan.band].max(),
            )
            datavars[adname][chan.name] = radToRef(
                radiances[chan.band],
                gvars[adname]["solar_zenith_angle"],
                xarray_obj.attrs["satellite_name"],
                chan.band,
            )
            LOG.info(
                "Final reflectances for %s, data range %f to %f",
                chan.band,
                datavars[adname][chan.name].min(),
                datavars[adname][chan.name].max(),
            )
        if chan.type == "BT":
            LOG.info(
                "Calculating brightness temperatures for %s, data range %f to %f",
                chan.band,
                radiances[chan.band].min(),
                radiances[chan.band].max(),
            )
            datavars[adname][chan.name] = radToBT(
                radiances[chan.band], xarray_obj.attrs["satellite_name"], chan.band
            )
            LOG.info(
                "Final brightness temperatures for %s, data range %f to %f",
                chan.band,
                datavars[adname][chan.name].min(),
                datavars[adname][chan.name].max(),
            )
        if adname not in xarray_obj.attrs["datavars"].keys():
            xarray_obj.attrs["datavars"][adname] = {}
        if chan.name not in xarray_obj.attrs["datavars"].keys():
            xarray_obj.attrs["datavars"][adname][chan.name] = {}

        xarray_obj.attrs["datavars"][adname][chan.name]["wavelength"] = float(
            annotation_metadata[chan.band]["band"][3:5]
            + "."
            + annotation_metadata[chan.band]["band"][5:]
        )

    gvars[adname]["latitude"] = np.ma.masked_less_equal(gvars[adname]["latitude"], -999)
    toplat = gvars[adname]["latitude"][np.ma.where(gvars[adname]["latitude"])][0]
    bottomlat = gvars[adname]["latitude"][np.ma.where(gvars[adname]["latitude"])][-1]

    for var in gvars[adname].keys():
        if toplat < bottomlat:
            gvars[adname][var] = np.ma.masked_less_equal(
                np.flipud(gvars[adname][var]), -999
            )
        else:
            gvars[adname][var] = np.ma.masked_less_equal(gvars[adname][var], -999)

        if "satellite_zenith_angle" in gvars[adname].keys():
            gvars[adname][var] = np.ma.masked_where(
                gvars[adname]["satellite_zenith_angle"] > 75, gvars[adname][var]
            )

    for var in datavars[adname].keys():
        if toplat < bottomlat:
            datavars[adname][var] = np.ma.masked_less_equal(
                np.flipud(datavars[adname][var]), -999
            )
        else:
            datavars[adname][var] = np.ma.masked_less_equal(datavars[adname][var], -999)

        if "satellite_zenith_angle" in gvars[adname].keys():
            datavars[adname][var] = np.ma.masked_where(
                gvars[adname]["satellite_zenith_angle"] > 75, datavars[adname][var]
            )

    xarray_objs = {}
    for dsname in datavars.keys():
        xobj = xarray.Dataset()
        xobj.attrs = xarray_obj.attrs.copy()
        for varname in datavars[dsname].keys():
            xobj[varname] = xarray.DataArray(datavars[dsname][varname])
        for varname in gvars[dsname].keys():
            xobj[varname] = xarray.DataArray(gvars[dsname][varname])
        if hasattr(xobj.attrs, "area_definition") and xobj.area_definition is not None:
            xobj.attrs["interpolation_radius_of_influence"] = max(
                xobj.area_definition.pixel_size_x, xobj.area_definition.pixel_size_y
            )
        else:
            xobj.attrs["interpolation_radius_of_influence"] = 10000
        xarray_objs[dsname] = xobj

    xarray_objs["METADATA"] = list(xarray_objs.values())[0][[]]
    LOG.info("Done reading SEVIRI data for {}".format(adname))
    LOG.info("")

    return xarray_objs


def call(fnames, metadata_only=False, chans=None, area_def=None, self_register=False):
    """Read SEVIRI hrit data products.

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
    # Remove any HRV files from file list. Need to do this here instead of in
    # 'call_single_time' as that will initially be fed one file at a time. If that file
    # is a HRV file, then this will result in an empty list and an error thrown in
    # 'get_top_level_metadata'.
    # See note 1 at top of module
    fnames = [fname for fname in fnames if not any(val in fname for val in ["HRV"])]

    return readers.read_data_to_xarray_dict(
        fnames,
        call_single_time,
        metadata_only,
        chans,
        area_def,
        self_register,
    )
