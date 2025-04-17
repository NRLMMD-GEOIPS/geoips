# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Standard GeoIPS xarray dictionary based ABI NetCDF data reader."""

# Python Standard Libraries
import logging
import os
from glob import glob
from datetime import datetime, timedelta

# Third-Party Libraries
import numpy as np
from scipy.ndimage import zoom
import xarray

from geoips.interfaces import readers
from geoips.utils.context_managers import import_optional_dependencies
from geoips.plugins.modules.readers.utils.geostationary_geolocation import (
    get_geolocation_cache_filename,
    get_geolocation,
    AutoGenError,
)


LOG = logging.getLogger(__name__)
# np.seterr(all='raise')

# Installed Libraries

with import_optional_dependencies(loglevel="info"):
    """Attempt to import a package & print to LOG.info if the import fails."""
    # If this reader is not installed on the system, don't fail alltogether,
    # just skip this import. This reader will not work if the import fails
    # and the package will have to be installed to process data of this type.
    import netCDF4 as ncdf
    import numexpr as ne

interface = "readers"
family = "standard"
name = "abi_netcdf"
source_names = ["abi"]

nprocs = 6

try:
    ne.set_num_threads(nprocs)
except Exception:
    LOG.info(
        f"Failed numexpr.set_num_threads in {__file__}. "
        "If numexpr is not installed and you need it, install it."
    )

DONT_AUTOGEN_GEOLOCATION = False
if os.getenv("DONT_AUTOGEN_GEOLOCATION"):
    DONT_AUTOGEN_GEOLOCATION = True

# These should be added to the data file object
BADVALS = {
    "Off_Of_Disk": -999.9,
    "Conditional": -999.8,
    "Out_Of_Valid_Range": -999.7,
    "No_Value": -999.6,
    "Unitialized": -9999.9,
}

DATASET_INFO = {
    "MED": ["B01", "B03", "B05"],
    "HIGH": ["B02"],
    "LOW": [
        "B04",
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
}
ALL_GEO_VARS = [
    "solar_zenith_angle",
    "satellite_zenith_angle",
    "solar_azimuth_angle",
    "satellite_azimuth_angle",
    "latitude",
    "longitude",
]
ALL_CHANS = {
    "LOW": [
        "B04Rad",
        "B04Ref",  # 1.37um Near-IR Cirrus
        "B06Rad",
        "B06Ref",  # 2.2um  Near-IR Cloud Particle Size
        "B07Rad",
        "B07BT",  # 3.9um  IR      Shortwave Window
        "B08Rad",
        "B08BT",  # 6.2um  IR      Upper-level tropospheric water vapor
        "B09Rad",
        "B09BT",  # 6.9um  IR      Mid-level water vapor
        "B10Rad",
        "B10BT",  # 7.3um  IR      Lower-level Water Vapor
        "B11Rad",
        "B11BT",  # 8.4um  IR      Cloud-top phase
        "B12Rad",
        "B12BT",  # 9.6um  IR      Ozone
        "B13Rad",
        "B13BT",  # 10.3um IR      Clean IR Longwave Window
        "B14Rad",
        "B14BT",  # 11.2um IR      IR Longwave window
        "B15Rad",
        "B15BT",  # 12.3um IR      Dirty Longwave Window
        "B16Rad",
        "B16BT",
    ],  # 13.3um IR      CO2 Longwave infrared
    "MED": [
        "B01Rad",
        "B01Ref",  # 0.47um Vis     Blue
        "B02Rad",
        "B02Ref",  # 0.64um Vis     Red
        "B05Rad",
        "B05Ref",
    ],  # 1.6um  Near-IR Snow/Ice
    "HIGH": ["B03Rad", "B03Ref"],  # 0.86um Near-IR Veggie
}


def metadata_to_datetime(metadata):
    """Use information from the metadata to get the image datetime."""
    times = metadata["var_info"]["time_bounds"]
    epoch = datetime(2000, 1, 1, 12, 0, 0)
    start_time = epoch + timedelta(seconds=times[0])
    end_time = epoch + timedelta(seconds=times[1])
    return start_time, end_time


def _get_files(path):
    """Get a list of file names from the input path."""
    if os.path.isfile(path):
        fnames = [path]
    elif os.path.isdir(path):
        fnames = glob(os.path.join(path, "OR_ABI*.nc"))
    elif os.path.isfile(path[0]):
        fnames = path
    else:
        raise IOError("No such file or directory: {0}".format(path))
    return fnames


def _check_file_consistency(metadata):
    """
    Check that all input metadata are from the same image time.

    Performs cheks on platform_ID, instrument_type, processing_level, and times.
    If these are all equal, returns True.
    If any differ, returns False.
    """
    # Checking file-level metadata for exact equality in the following fields
    # Was failing on processing_level due to extra NASA text sometimes
    # Also fails on time_coverage_end due to deviations on the order of 0.5 seconds
    #   Probably should fashion better checks for these two.
    # checks = ['platform_ID', 'instrument_type', 'processing_level', 'timeline_id',
    #           'scene_id', 'time_coverage_start', 'time_coverage_end']
    checks = [
        "platform_ID",
        "instrument_type",
        "timeline_id",
        "scene_id",
        "time_coverage_start",
    ]
    for name in checks:
        check_set = set(
            [metadata[fname]["file_info"][name] for fname in metadata.keys()]
        )
        if len(check_set) != 1:
            LOG.debug("Failed on {0}. Found: {1}".format(name, check_set))
            return False
    return True


def _get_file_metadata(df):
    """Gather all of the file-level metadata."""
    metadata = {}
    md_names = [
        "id",
        "dataset_name",
        "naming_authority",
        "institution",
        "project",
        "iso_series_metadata_id",
        "Conventions",
        "Metadata_Conventions",
        "keywords_vocabulary",
        "standard_name_vocabulary",
        "title",
        "summary",
        "license",
        "keywords",
        "cdm_data_type",
        "orbital_slot",
        "platform_ID",
        "instrument_type",
        "processing_level",
        "date_created",
        "production_site",
        "production_environment",
        "production_data_source",
        "timeline_id",
        "scene_id",
        "spatial_resolution",
        "time_coverage_start",
        "time_coverage_end",
    ]
    metadata_dict = {"id": "instrument_ID"}
    for name in md_names:
        try:
            if hasattr(df, name):
                metadata[name] = getattr(df, name)
            else:
                metadata[name] = getattr(df, metadata_dict[name])
        except AttributeError:
            LOG.info("Warning! File-level metadata field missing: {0}".format(name))
    return metadata


def _get_variable_metadata(df):
    """
    Gather all required variable level metadata.

    Some are skipped or gathered later as needed.
    """
    metadata = {}
    # Note: We have skipped DQF, Rad, band_wavelength_star_look, num_star_looks,
    #       star_id, t, t_star_look, x_image, x_image_bounds, y_image, y_image_bounds,
    #       geospatial_lat_lon_extent, goes_imager_projection
    md_names = [
        "band_id",
        "band_wavelength",
        "earth_sun_distance_anomaly_in_AU",
        "esun",
        "kappa0",
        "max_radiance_value_of_valid_pixels",
        "min_radiance_value_of_valid_pixels",
        "missing_pixel_count",
        "nominal_satellite_height",
        "nominal_satellite_subpoint_lat",
        "nominal_satellite_subpoint_lon",
        "percent_uncorrectable_L0_errors",
        "planck_bc1",
        "planck_bc2",
        "planck_fk1",
        "planck_fk2",
        "processing_parm_version_container",
        "saturated_pixel_count",
        "std_dev_radiance_value_of_valid_pixels",
        "time_bounds",
        "undersaturated_pixel_count",
        "valid_pixel_count",
        "x",
        "y",
        "yaw_flip_flag",
    ]
    for name in md_names:
        try:
            metadata[name] = df.variables[name][...]
            if metadata[name].size == 1:
                metadata[name] = metadata[name][()]
            if name in ["x", "y"]:
                metadata[f"{name}_add_offset"] = df.variables[name].add_offset
                metadata[f"{name}_scale_factor"] = df.variables[name].scale_factor
        except KeyError:
            LOG.info("Warning! Variable-level metadata field missing: {0}".format(name))
    metadata["num_lines"] = metadata["y"].size
    metadata["num_samples"] = metadata["x"].size
    return metadata


def _get_lat_lon_extent_metadata(df):
    """Get lat lon extent metadata."""
    glle = df.variables["geospatial_lat_lon_extent"]
    metadata = {}
    md_names = [
        "geospatial_eastbound_longitude",
        "geospatial_lat_center",
        "geospatial_lat_nadir",
        "geospatial_lon_center",
        "geospatial_lon_nadir",
        "geospatial_northbound_latitude",
        "geospatial_southbound_latitude",
        "geospatial_westbound_longitude",
    ]
    for name in md_names:
        try:
            metadata[name] = getattr(glle, name)
            if metadata[name].size == 1:
                metadata[name] = metadata[name][()]
        except AttributeError:
            LOG.info("Warning! Lat lon extent metadata field missing: {0}".format(name))
    return metadata


def _get_imager_projection(df):
    """Get imager projection."""
    gip = df.variables["goes_imager_projection"]
    metadata = {}
    md_names = [
        "inverse_flattening",
        "latitude_of_projection_origin",
        "longitude_of_projection_origin",
        "perspective_point_height",
        "semi_major_axis",
        "semi_minor_axis",
    ]
    for name in md_names:
        try:
            metadata[name] = getattr(gip, name)
            if metadata[name].size == 1:
                metadata[name] = metadata[name][()]
        except AttributeError:
            LOG.info("Warning! Lat lon extent metadata field missing: {0}".format(name))
    metadata["grid_mapping"] = getattr(gip, "grid_mapping_name")
    return metadata


def _get_metadata(df, fname, **kwargs):
    """
    Gather metadata for the data file and return as a dictionary.

    Note: We are gathering all of the available metadata in case it is needed at
    some point.
    """
    metadata = {}
    # Gather all file-level metadata
    metadata["file_info"] = _get_file_metadata(df)
    # Gather all variable-level metadata
    metadata["var_info"] = _get_variable_metadata(df)
    # Gather lat lon extent info
    metadata["ll_info"] = _get_lat_lon_extent_metadata(df)
    # Gather projection info
    metadata["projection"] = _get_imager_projection(df)
    # Gather some useful info to the top level
    try:
        metadata["path"] = df.filepath()
    except ValueError:
        # Without cython installed, df.filepath() does not work
        metadata["path"] = fname
    metadata["satellite"] = metadata["file_info"]["platform_ID"]
    metadata["sensor"] = "ABI"
    metadata["num_lines"] = metadata["var_info"]["y"].size
    metadata["num_samples"] = metadata["var_info"]["x"].size
    return metadata


def get_latitude_longitude(metadata, BADVALS, sect=None):
    """
    Get latitudes and longitudes.

    This routine accepts a dictionary containing metadata as read from a NCDF4
    format file, and returns latitudes and longitudes for a full disk.
    """
    # If the filename format needs to change for the pre-generated geolocation
    # files, please discuss prior to changing.  It will force recreation of all
    # files, which can be problematic for large numbers of sectors
    fname = get_geolocation_cache_filename("GEOLL", metadata)
    if not os.path.isfile(fname):
        if sect is not None and DONT_AUTOGEN_GEOLOCATION and "tc2019" not in sect.name:
            msg = (
                f"GETGEO Requested NO AUTOGEN GEOLOCATION. "
                f"Could not create latlonfile for ad {metadata['scene']}: {fname}"
            )
            LOG.error(msg)
            raise AutoGenError(msg)

        LOG.debug("Calculating latitudes and longitudes.")

        r2d = 180.0 / np.pi  # NOQA

        lambda0 = np.radians(metadata["lon0"])  # NOQA
        Re = metadata["Re"]
        # invf = metadata['invf']
        Rp = metadata["Rp"]
        # e = np.sqrt((1 / invf) * (2 - 1 / invf))
        H = metadata["H_m"]
        c = H**2 - Re**2  # NOQA

        # Python 3 netcdf reads create a masked array, while Python 2 netcdf reads
        # create ndarray. These should NOT be masked, so if we have a masked array,
        # fill it.
        if isinstance(metadata["x"], np.ma.core.MaskedArray):
            x = np.float64(metadata["x"].filled())
        else:
            x = np.float64(metadata["x"])
        if isinstance(metadata["y"], np.ma.core.MaskedArray):
            y = np.float64(metadata["y"].filled())
        else:
            y = np.float64(metadata["y"])

        LOG.info("      Making {0} by {1} grid.".format(x.size, y.size))
        # Need to transpose the latline, then repeat lonsize times
        yT = y[np.newaxis].T
        y = np.hstack([yT for num in range(x.size)])
        # Repeat lonline latsize times
        x = np.vstack([x for num in range(yT.size)])

        # Note: In this next section, we will be reusing memory space as much as
        #       possible. To make this as transparent as possible, we will do all
        #       variable assignment first, then fill them
        # This method requires that all lines remain in the SAME ORDER or things
        # will go very badly
        cosx = np.empty_like(x)
        cosy = np.empty_like(x)
        a = np.empty_like(x)
        b = np.empty_like(x)
        sinx = x  # X is not needed after the line that defines sinx
        siny = y  # Y is not needed after the line that defines siny
        rs = a
        sx = b
        sy = cosy  # sinx is not needed after the line that defines sy
        sz = cosx  # cosx is not needed after the line that defines sz
        lats = rs
        lons = sz

        LOG.info("      Calculating intermediate steps")
        Rrat = Re**2 / Rp**2  # NOQA
        ne.evaluate("cos(x)", out=cosx)  # NOQA
        ne.evaluate("cos(y)", out=cosy)  # NOQA
        ne.evaluate("sin(x)", out=sinx)  # NOQA
        ne.evaluate("sin(y)", out=siny)  # NOQA
        ne.evaluate("sinx**2 + cosx**2 * (cosy**2 + siny**2 * Rrat)", out=a)  # NOQA
        ne.evaluate("-2 * H * cosx * cosy", out=b)  # NOQA
        ne.evaluate("(-b - sqrt(b**2 - (4 * a * c))) / (2 * a)", out=rs)  # NOQA
        good_mask = np.isfinite(rs)

        ne.evaluate("rs * cosx * cosy", out=sx)  # NOQA
        ne.evaluate("rs * cosx * siny", out=sz)  # NOQA
        ne.evaluate("rs * sinx", out=sy)  # NOQA

        LOG.info("Calculating Latitudes")
        ne.evaluate("r2d * arctan(Rrat * sz / sqrt((H - sx)**2 + sy**2))", out=lats)
        LOG.info("Calculating Longitudes")
        lons = ne.evaluate("r2d * (lambda0 + arctan(sy / (H - sx)))", out=lons)
        lats[~good_mask] = BADVALS["Off_Of_Disk"]
        lons[~good_mask] = BADVALS["Off_Of_Disk"]
        LOG.info("Done calculating latitudes and longitudes")

        with open(fname, "w") as df:
            lats.tofile(df)
            lons.tofile(df)
        # # Possible switch to xarray based geolocation files, but we lose memmapping.
        # ds = xarray.Dataset(
        #     {
        #         'latitude':(['x','y'],lats),
        #         'longitude':(['x','y'],lons)
        #         }
        #     )
        # ds.to_netcdf(fname)

    # Create memmap to the lat/lon file
    # Nothing will be read until explicitly requested
    # We are mapping this here so that the lats and lons are available when
    # calculating satlelite angles
    LOG.info(
        "GETGEO memmap to {} : lat/lon file for {}".format(fname, metadata["scene"])
    )

    shape = (metadata["num_lines"], metadata["num_samples"])
    offset = 8 * metadata["num_samples"] * metadata["num_lines"]
    lats = np.memmap(fname, mode="r", dtype=np.float64, offset=0, shape=shape)
    lons = np.memmap(fname, mode="r", dtype=np.float64, offset=offset, shape=shape)
    # Possible switch to xarray based geolocation files, but we lose memmapping
    # saved_xarray = xarray.load_dataset(fname)
    # lons = saved_xarray['longitude'].to_masked_array()
    # lats = saved_xarray['latitude'].to_masked_array()

    return lats, lons


def _get_geolocation_metadata(metadata):
    """
    Gather all of the metadata used in creating geolocation data for input file.

    This is split out so we can easily create a chash of the data for creation
    of a unique filename. This allows us to avoid recalculation of angles that
    have already been calculated.
    """
    geomet = {}
    # G16 -> goes-16
    geomet["platform_name"] = metadata["file_info"]["platform_ID"].replace("G", "goes-")
    geomet["Re"] = metadata["projection"]["semi_major_axis"]
    geomet["Rp"] = metadata["projection"]["semi_minor_axis"]
    geomet["invf"] = metadata["projection"]["inverse_flattening"]
    geomet["e"] = 0.0818191910435
    geomet["pphgt"] = metadata["projection"]["perspective_point_height"]
    geomet["H_m"] = geomet["Re"] + geomet["pphgt"]
    geomet["lat0"] = metadata["projection"]["latitude_of_projection_origin"]
    geomet["lon0"] = metadata["projection"]["longitude_of_projection_origin"]
    geomet["scene"] = metadata["file_info"]["scene_id"]
    # Just getting the nadir resolution in kilometers.  Must extract from a string.
    geomet["res_km"] = float(
        metadata["file_info"]["spatial_resolution"].split()[0][0:-2]
    )
    geomet["roi_factor"] = 5  # roi = res * roi_factor, was 10
    geomet["num_lines"] = metadata["var_info"]["num_lines"]
    geomet["num_samples"] = metadata["var_info"]["num_samples"]
    geomet["x"] = metadata["var_info"]["x"]
    geomet["y"] = metadata["var_info"]["y"]
    return geomet


def call(fnames, metadata_only=False, chans=None, area_def=None, self_register=False):
    """
    Read ABI NetCDF data from a list of filenames.

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
    fnames, metadata_only=False, chans=None, area_def=None, self_register=False
):
    """
    Read ABI NetCDF data from a list of filenames.

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
    standard_metadata = {}
    adname = "undefined"
    if area_def and self_register:
        raise ValueError("area_def and self_register are mutually exclusive keywords")
    elif area_def:
        adname = area_def.area_id

    # Test inputs
    if area_def and self_register:
        raise ValueError(
            "sector_definition and self_register are mutually exclusive keywords"
        )

    # Get metadata for all input data files
    # Check to be sure that all input files are form the same image time
    all_metadata = {}
    for fname in fnames:
        if chans:
            gotone = False
            for chan in chans:
                currchan = (
                    chan.replace("BT", "")
                    .replace("Ref", "")
                    .replace("Rad", "")
                    .replace("B", "C")
                )
                if currchan in fname:
                    gotone = True
            if not gotone:
                LOG.info(
                    "SKIPPING file %s, not needed from channel list %s", fname, chans
                )
                continue
        try:
            with ncdf.Dataset(str(fname), "r") as df:
                all_metadata[fname] = _get_metadata(df, fname)
        except IOError as resp:
            LOG.exception("BAD FILE %s skipping", resp)
            continue
        if metadata_only:
            LOG.info("Only need metadata from first file, returning")
            break

    if not _check_file_consistency(all_metadata):
        raise ValueError("Input files inconsistent.")

    # Now put together a dict that shows what we actually got
    # This is largely to help us read in order and only create arrays of the minimum
    # required size.
    # Dict structure is channel{metadata}
    file_info = {}

    xarray_obj = xarray.Dataset()
    for md in all_metadata.values():
        ch = "B{0:02d}".format(int(md["var_info"]["band_id"]))
        if ch not in file_info:
            file_info[ch] = md

    xarray_obj.attrs["file_metadata"] = file_info.copy()

    # Most of the metadata are the same between files.
    # From here on we will just rely on the metadata from a single data file
    # for each resolution
    res_md = {}
    for res in ["LOW", "MED", "HIGH"]:
        # Find a file for this resolution: Any one will do
        res_chans = list(set(DATASET_INFO[res]).intersection(file_info.keys()))
        if res_chans:
            res_md[res] = file_info[res_chans[0]]

    # If we plan to self register, make sure we requested a resolution that we actually
    # plan to read.
    #
    # This could be problematic if we try to self-register to LOW when only
    # reading MED or something
    if self_register and self_register not in res_md:
        raise ValueError(
            "Resolution requested for self registration has not been read."
        )

    # Gather metadata
    # Assume the same for all resolutions.  Not true, but close enough.
    highest_md = res_md[list(res_md.keys())[0]]
    sdt, edt = metadata_to_datetime(highest_md)
    xarray_obj.attrs["start_datetime"] = sdt
    xarray_obj.attrs["end_datetime"] = edt
    xarray_obj.attrs["source_name"] = "abi"
    xarray_obj.attrs["data_provider"] = "noaa"
    xarray_obj.attrs["source_file_names"] = [
        os.path.basename(fname) for fname in fnames
    ]

    # G16 -> goes-16
    xarray_obj.attrs["platform_name"] = highest_md["file_info"]["platform_ID"].replace(
        "G", "goes-"
    )
    xarray_obj.attrs["area_definition"] = area_def

    # Get appropriate sector name
    if area_def:
        xarray_obj.attrs["area_id"] = area_def.area_id
        xarray_obj.attrs["area_definition"] = area_def
    else:
        if self_register and self_register not in DATASET_INFO:
            raise ValueError(
                f"Unrecognized resolution name requested for self "
                f"registration: {self_register}"
            )
        scene_id = highest_md["file_info"]["dataset_name"].split("_")[1].split("-")[2]
        if scene_id == "RadF":
            xarray_obj.attrs["area_id"] = "Full-Disk"
        elif scene_id == "RadM1":
            xarray_obj.attrs["area_id"] = "Mesoscale-1"
        elif scene_id == "RadM2":
            xarray_obj.attrs["area_id"] = "Mesoscale-2"
        elif scene_id == "RadC":
            xarray_obj.attrs["area_id"] = "CONUS"
        xarray_obj.attrs["area_definition"] = None
    adname = xarray_obj.attrs["area_id"]

    if metadata_only:
        LOG.info("Only need metadata from first file, returning")
        return {"METADATA": xarray_obj}

    # Create list of all possible channels for the case where no channels were requested
    all_chans_list = []
    for chl in ALL_CHANS.values():
        all_chans_list += chl

    # If specific channels were requested, check them against the input data
    # If specific channels were requested, but no files exist for one of the
    # channels, then error
    if chans:
        for chan in chans:
            if chan in ALL_GEO_VARS:
                continue
            if chan not in all_chans_list:
                raise ValueError("Requested channel {0} not recognized.".format(chan))
            if chan[0:3] not in file_info.keys():
                continue
                # raise ValueError(
                #     'Requested channel {0} not found in input data.'.format(chan)
                # )

    # If no specific channels were requested, get everything
    if not chans:
        chans = all_chans_list

    # Creates dict whose keys are band numbers in the form B## and whose values are
    # lists containing the data types(s) requested for the band (e.g. Rad, Ref, BT).
    chan_info = {}
    for ch in chans:
        if ch in ALL_GEO_VARS:
            continue
        chn = ch[0:3]
        typ = ch[3:]
        if chn not in chan_info:
            chan_info[chn] = []
        chan_info[chn].append(typ)

    # Gather geolocation data
    # Assume datetime the same for all resolutions.  Not true, but close enough.
    # This save us from having very slightly different solar angles for each channel.
    # Loop over resolutions and get metadata as needed
    if self_register:
        LOG.info("")
        LOG.info(
            "Getting geolocation information for resolution {} for {}.".format(
                self_register, adname
            )
        )
        # Get just the metadata we need
        standard_metadata[adname] = _get_geolocation_metadata(res_md[self_register])
        fldk_lats, fldk_lons = get_latitude_longitude(
            standard_metadata[adname], BADVALS, area_def
        )
        gvars[adname] = get_geolocation(
            sdt, standard_metadata[adname], fldk_lats, fldk_lons, BADVALS, area_def
        )
        if not gvars[adname]:
            LOG.error(
                f"GEOLOCATION FAILED for adname {adname} DONT_AUTOGEN_GEOLOCATION "
                f"is: {DONT_AUTOGEN_GEOLOCATION}"
            )
            gvars[adname] = {}
    else:
        for res in ["LOW", "MED", "HIGH"]:
            try:
                res_md[res]
            except KeyError:
                continue
            try:
                # Get just the metadata we need
                standard_metadata[res] = _get_geolocation_metadata(res_md[res])
                fldk_lats, fldk_lons = get_latitude_longitude(
                    standard_metadata[res], BADVALS, area_def
                )
                gvars[res] = get_geolocation(
                    sdt, standard_metadata[res], fldk_lats, fldk_lons, BADVALS, area_def
                )
            except ValueError as resp:
                LOG.error(
                    "{} GEOLOCATION FAILED FOR {} resolution {}. Skipping.".format(
                        resp, adname, res
                    )
                )
            # Not sure what this does, but it fails if we only pass one resolution
            # worth of data...
            #
            # MLS I think this may be necessary to avoid catastrophic failure if
            # geolocation has not been autogenerated.  I'll see.
            # if not gvars[res]:
            #     LOG.error(
            #         f"GEOLOCATION FAILED for {adname} resolution {res} "
            #         f"DONT_AUTOGEN_GEOLOCATION is: {DONT_AUTOGEN_GEOLOCATION}"
            #     )
            #     gvars[res] = {}

    LOG.interactive("Done with geolocation for {}".format(adname))
    LOG.info("")

    # Read the data
    # Will read all data if sector_definition is None
    # Will only read required data if an sector_definition is provided
    for chan, types in chan_info.items():
        # If we didn't pass all the channel data, skip non-existent data types
        if chan not in file_info:
            continue
        LOG.info("Reading {}".format(chan))
        chan_md = file_info[chan]
        for res, res_chans in DATASET_INFO.items():
            if chan in res_chans:
                break
        if (not self_register) and (
            res not in gvars.keys() or not gvars[res] or "latitude" not in gvars[res]
        ):
            LOG.info(
                f"We don't have geolocation information for {res} for {adname} "
                f"skipping {chan}."
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
        if self_register:
            data = get_data(chan_md, gvars[adname], rad, ref, bt)
        else:
            data = get_data(chan_md, gvars[res], rad, ref, bt)
        for typ, val in data.items():
            if dsname not in datavars:
                datavars[dsname] = {}
            datavars[dsname][chan + typ] = val

    # This needs to be fixed:
    #   remove any unneeded datasets from datavars and gvars
    #   also mask any values below -999.0
    if area_def:
        for res in ["LOW", "MED", "HIGH"]:
            if adname not in gvars and res in gvars and gvars[res]:
                gvars[adname] = gvars[res]
            try:
                gvars.pop(res)
            except KeyError:
                pass

    # NOTE: Moved zoom and subsample to get_data, but still need to move data
    #       to correct dataset and drop extra datasets
    if self_register:
        # Determine which resolution has geolocation
        LOG.info("Registering to {}".format(self_register))
        if self_register == "HIGH":
            datavars[adname] = datavars.pop("HIGH")
            for varname, var in datavars["LOW"].items():
                datavars[adname][varname] = var
                # datavars[adname][varname] = zoom(var, 4, order=0)
            datavars.pop("LOW")
            for varname, var in datavars["MED"].items():
                datavars[adname][varname] = var
                # datavars[adname][varname] = zoom(var, 2, order=0)
            datavars.pop("MED")

        elif self_register == "MED":
            datavars[adname] = datavars.pop("MED")
            for varname, var in datavars["LOW"].items():
                datavars[adname][varname] = var
                # datavars[adname][varname] = zoom(var, 2, order=0)
            datavars.pop("LOW")
            for varname, var in datavars["HIGH"].items():
                datavars[adname][varname] = var
                # datavars[adname][varname] = var[::2, ::2]
            datavars.pop("HIGH")

        elif self_register == "LOW":
            datavars[adname] = datavars.pop("LOW")
            for varname, var in datavars["MED"].items():
                datavars[adname][varname] = var
                # datavars[adname][varname] = var[::2, ::2]
            datavars.pop("MED")
            for varname, var in datavars["HIGH"].items():
                datavars[adname][varname] = var
                # datavars[adname][varname] = var[::4, ::4]
            datavars.pop("HIGH")

        else:
            raise ValueError("No geolocation data found.")

    # basically just reformat the all_metadata dictionary to
    # reference channel names as opposed to file names..
    # band_metadata = get_band_metadata(all_metadata)

    # Remove lines and samples arrays.  Not needed.
    for res in gvars.keys():
        try:
            LOG.info(f"Popping Lines and samples for {res}")
            gvars[res].pop("Lines")
            gvars[res].pop("Samples")
        except KeyError:
            LOG.info(f"Did not find Lines and Samples to pop for {res}")
            pass
        try:
            LOG.info(f"Masking greater than 75 degrees sat zenith angle for {res}")
            for varname, var in gvars[res].items():
                LOG.info(f"Masking {varname} greater than 75 degrees sat zenith angle")
                gvars[res][varname] = np.ma.array(
                    var, mask=gvars[res]["satellite_zenith_angle"].mask
                )
                gvars[res][varname] = np.ma.masked_where(
                    gvars[res]["satellite_zenith_angle"] > 75, gvars[res][varname]
                )
        except KeyError:
            LOG.info(f"Did not find satellite zenith angle to mask for {res}")
            pass
    for ds in datavars.keys():
        if not datavars[ds]:
            datavars.pop(ds)

    xarray_objs = {}
    for dsname in datavars.keys():
        xobj = xarray.Dataset()
        xobj.attrs = xarray_obj.attrs.copy()
        for varname in datavars[dsname].keys():
            xobj[varname] = xarray.DataArray(datavars[dsname][varname])
        for varname in gvars[dsname].keys():
            xobj[varname] = xarray.DataArray(gvars[dsname][varname])

        roi = 500
        roi_factor = 5
        if hasattr(xobj, "area_definition") and xobj.area_definition is not None:
            roi = max(
                xobj.area_definition.pixel_size_x, xobj.area_definition.pixel_size_y
            )
            LOG.info("Trying area_def roi %s", roi)
        for curr_res in standard_metadata.keys():
            if standard_metadata[curr_res]["res_km"] * 1000.0 * roi_factor > roi:
                roi = standard_metadata[curr_res]["res_km"] * 1000.0 * roi_factor
                LOG.info("Trying standard_metadata[%s] %s", curr_res, roi)
        xobj.attrs["interpolation_radius_of_influence"] = roi
        LOG.info(f"Using roi {roi}")
        xarray_objs[dsname] = xobj
        # At some point we may need to deconflict, but for now just use any of the
        # dataset attributes as the METADATA dataset
        xarray_objs["METADATA"] = xobj[[]]

    LOG.info("Done reading ABI data for %s", adname)
    LOG.info("")
    return xarray_objs


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
        bandnum = all_metadata[fname]["var_info"]["band_id"][0]
        bandmetadata["B%02d" % bandnum] = {}
        bandmetadata["B%02d" % bandnum] = all_metadata[fname]
    return bandmetadata


def get_data(md, gvars, rad=False, ref=False, bt=False):
    """Read data for a full channel's worth of files."""
    # Coordinate arrays for reading
    if "Lines" in gvars and "Samples" in gvars:
        full_disk = False
        line_inds = gvars["Lines"]
        sample_inds = gvars["Samples"]
    else:
        full_disk = True

    band_num = md["var_info"]["band_id"]

    # Read radiance data for channel
    # For some reason, netcdf4 does not like it if you pass a bunch of indexes.
    # It is very slow and creates memory errors if there are too many.
    # Have to read ALL of the data, then subset.
    # Need to find a solution for this.
    # Use with to open the data file for reading and automatically close once complete
    with ncdf.Dataset(md["path"], "r") as df:
        if not full_disk:
            rad_data = np.float64(df.variables["Rad"][...][line_inds, sample_inds])
            qf = df.variables["DQF"][...][line_inds, sample_inds]
        else:
            # Here we need to determine which indexes to read based on the size of the
            # input geolocation data.  We assume that the geolocation data and the
            # variable data cover the same domain, just at a different resolution.
            geoloc_shape = np.array(gvars["solar_zenith_angle"].shape, dtype=np.float64)
            data_shape = np.array(df.variables["Rad"].shape, dtype=np.float64)
            # If the geolocation shape matches the data shape, just read the data
            if np.all(geoloc_shape == data_shape):
                rad_data = np.float64(df.variables["Rad"][...])
                qf = df.variables["DQF"][...]
            # Upscaling data to match geolocation shape
            elif np.all(np.maximum(geoloc_shape, data_shape) == geoloc_shape):
                # Data shape is smaller, so it is the denominator
                zoom_factor, remainder = np.divmod(geoloc_shape, data_shape)
                # Ensure that all elements of the zoom factor are whole numbers
                if np.any(remainder):
                    raise ValueError(
                        "Zoom factor is not a whole number.  "
                        "This section of code needs to be reexamined."
                    )
                # Ensure that all elements of the zoom factor are equal
                if not np.all(zoom_factor == zoom_factor[0]):
                    raise ValueError(
                        "Zoom factor must be equal for both dimensions.  "
                        "This section of code needs to be reexamined."
                    )
                # Perform the actual zoom
                zoom_factor = zoom_factor.astype(np.int)
                rad_data = zoom(
                    np.float64(df.variables["Rad"][...]), zoom_factor[0], order=0
                )
                qf = zoom(df.variables["DQF"][...], zoom_factor[0], order=0)
            # Downscaling data to match geolocation shape
            elif np.all(np.maximum(geoloc_shape, data_shape) == data_shape):
                # Geoloc shape is smaller, so it is the denominator
                zoom_factor, remainder = np.divmod(data_shape, geoloc_shape)
                # Ensure that all elements of the zoom factor are whole numbers
                if np.any(remainder):
                    raise ValueError(
                        "Zoom factor is not a whole number.  "
                        "This section of code needs to be reexamined."
                    )
                # Ensure that all elements of the zoom factor are equal
                if not np.all(zoom_factor == zoom_factor[0]):
                    raise ValueError(
                        "Zoom factor must be equal for both dimensions.  "
                        "This section of code needs to be reexamined."
                    )
                # Perform the actual subsampling
                LOG.info("Before zoom")
                zoom_factor = zoom_factor.astype(np.int)

                # NOTE: Strides are broken for netCDF4 library version < 4.6.2.
                #       At present, the most recent stable release is 4.6.1.
                #       Once 4.6.2 is released, this should be retested.
                #       See https://github.com/Unidata/netcdf4-python/issues/680

                rad_data = np.float64(
                    df.variables["Rad"][...][:: zoom_factor[0], :: zoom_factor[0]]
                )
                qf = df.variables["DQF"][...][:: zoom_factor[0], :: zoom_factor[0]]
                # rad_data = np.float64(
                #     df.variables['Rad'][::zoom_factor[0], ::zoom_factor[0]]
                # )
                # qf = df.variables['DQF'][::zoom_factor[0], ::zoom_factor[0]]
                LOG.info("After zoom")
            else:
                raise ValueError(
                    "Zoom factor cannot be computed.  "
                    "All either both dimensions of geolocation data must be "
                    "larger than the data dimensions or vice versa."
                )

    data = {"Rad": rad_data}
    # Originally was using -1, but this is a uint8 and set to 255 for off of disk
    data["Rad"][np.where(qf == 255)] = BADVALS["Off_Of_Disk"]
    data["Rad"][np.where(qf == 1)] = BADVALS["Conditional"]
    # This flag is ignored for now.  It masks good data that is useful for imagery.
    # I am unsure if this should be used in digital products.
    # data['Rad'][np.where(qf == 2)] = BADVALS['Out_Of_Valid_Range']
    data["Rad"][np.where(qf == 3)] = BADVALS["No_Value"]
    data["Rad"] = np.ma.masked_less_equal(data["Rad"], -999.0)

    # Get the bad data mask from radiances to reuse
    bad_data_mask = data["Rad"].mask

    # If reflectance is requested
    # Note, weird memory manipulations to save memory when radiances are not requested
    if ref:
        if band_num not in range(1, 7):
            raise ValueError(
                "Unable to calculate reflectances for band #{0}".format(band_num)
            )

        # Get the radiance data
        # Have to do this when using numexpr
        rad_data = data["Rad"][~bad_data_mask]  # NOQA

        # If we don't need radiances, then reuse the memory
        if not rad:
            data["Ref"] = data.pop("Rad")
        else:
            data["Ref"] = np.empty_like(data["Rad"])

        k0 = md["var_info"]["kappa0"]  # NOQA
        sun_zenith = gvars["solar_zenith_angle"][~bad_data_mask]  # NOQA
        # zoom_info = (
        #     np.array(rad_data.shape, dtype=np.float) /
        #     np.array(sun_zenith.shape, dtype=np.float
        # )
        # if zoom_info[0] == zoom_info[1] and int(zoom_info[0]) == zoom_info[0]:
        #     if zoom_info[0] > 1 and int(zoom_info[0]) == zoom_info[0]:
        #         sun_zenith = zoom(sun_zenith, zoom_info[0])
        #     elif zoom_info[0] < 1 and int(zoom_info[0]**-1) == zoom_info[0]**-1:
        #         sun_zenith = sun_zenith[::zoom_info[0]**-1, :: zoom_info[0]**-1]
        #     elif zoom_info[0] == 1:
        #         pass
        #     else:
        #         ValueError('Inappropriate zoom level calculated.')
        # else:
        #     ValueError('Inappropriate zoom level calculated.')

        deg2rad = np.pi / 180.0  # NOQA
        # NOTE:: ABI docs suggest doing solar zenith angle correction here, but
        #        since some algorithms (e.g. Fire-Temperature RGB) required uncorrected
        #        data, we will not do this here, instead leaving it to the algorithm
        #        developer to handle.
        data["Ref"][~bad_data_mask] = ne.evaluate("k0 * rad_data")

    if bt:
        if band_num not in range(7, 17):
            raise ValueError(
                "Unable to calculate brightness temperatures for band #{0}".format(
                    band_num
                )
            )

        # Get the radiance data
        # Have to do this when using numexpr
        rad_data = data["Rad"][~bad_data_mask]

        # Sometimes negative values occur due to oddities in calibration
        # These break the conversion to BT
        # Since these values are likely caused by very dark (cold) scenes
        #   that are below the sensor's sensitivity and we are not interested in
        #   having bad data scattered throughout the imager, we will set this
        #   to a very small value
        rad_data[rad_data <= 0] = 0.001

        # If we don't need radiances, then reuse the memory
        if not rad:
            data["BT"] = data.pop("Rad")
        else:
            data["BT"] = np.empty_like(data["Rad"])

        fk1 = md["var_info"]["planck_fk1"]  # NOQA
        fk2 = md["var_info"]["planck_fk2"]  # NOQA
        bc1 = md["var_info"]["planck_bc1"]  # NOQA
        bc2 = md["var_info"]["planck_bc2"]  # NOQA

        data["BT"][~bad_data_mask] = ne.evaluate(
            "(fk2 / log(fk1 / rad_data + 1) - bc1) / bc2"
        )

    # latitude is sometimes fully specified from area_def... So does not
    # relate to actual masked data..
    # This should only occur when area_def was provided and breaks when it wasn't.
    if "Lines" in gvars:
        usemask = np.ma.masked_less(gvars["Lines"], -990).mask
    else:
        usemask = gvars["latitude"].mask

    for varname in gvars.keys():
        if varname in ["latitude", "longitude"]:
            continue
        if hasattr(gvars[varname], "mask"):
            gvars[varname].mask = usemask
    for varname in data.keys():
        if hasattr(data[varname], "mask"):
            data[varname].mask = usemask
    return data
