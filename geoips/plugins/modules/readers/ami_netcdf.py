# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Standard GeoIPS xarray dictionary based GeoKOMPSAT AMI NetCDF data reader."""

# Python Standard Libraries
from datetime import datetime, timedelta
import glob
import logging
import os
from pathlib import Path
from geoips.filenames.base_paths import PATHS

# Third-Party Libraries
import netCDF4 as ncdf
import numpy as np
import xarray

from geoips.interfaces import readers
from geoips.filenames.base_paths import PATHS as gpaths
from geoips.utils.context_managers import import_optional_dependencies
from geoips.plugins.modules.readers.utils.geostationary_geolocation import (
    check_geolocation_cache_backend,
    get_geolocation_cache_filename,
    get_geolocation,
)

LOG = logging.getLogger(__name__)

with import_optional_dependencies(loglevel="info"):
    """Attempt to import a package & print to LOG.info if the import fails."""
    # If this reader is not installed on the system, don't fail alltogether,
    # just skip this import. This reader will not work if the import fails
    # and the package will have to be installed to process data of this type.
    import numexpr as ne
    import zarr

nprocs = 6

try:
    ne.set_num_threads(nprocs)
except Exception:
    LOG.info(
        f"Failed numexpr.set_num_threads in {__file__}. "
        "If numexpr is not installed and you need it, install it."
    )


interface = "readers"
family = "standard"
name = "ami_netcdf"
source_names = ["ami"]

# These should be added to the data file object
BADVALS = {
    "Off_Of_Disk": -999.9,
    "Conditional": -999.8,
    "Out_Of_Valid_Range": -999.7,
    "No_Value": -999.6,
    "Unitialized": -9999.9,
}

ALL_GEO_VARS = [
    "solar_zenith_angle",
    "satellite_zenith_angle",
    "solar_azimuth_angle",
    "satellite_azimuth_angle",
    "latitude",
    "longitude",
]

DATASET_INFO = {
    "MED": ["VI004", "VI005", "VI008"],
    "HIGH": ["VI006"],
    "LOW": [
        "NR013",
        "NR016",
        "SW038",
        "WV063",
        "WV069",
        "WV073",
        "IR087",
        "IR096",
        "IR105",
        "IR112",
        "IR123",
        "IR133",
    ],
}

CENTER_WAVENUMBERS = {
    "VI004": 0.4702,
    "VI005": 0.5086,
    "VI006": 0.6394,
    "VI008": 0.8630,
    "NR013": 1.3740,
    "NR016": 1.6092,
    "SW038": 2612.677373521110,
    "WV063": 1617.609242531340,
    "WV069": 1441.575428760170,
    "WV073": 1365.249992024440,
    "IR087": 1164.949392856340,
    "IR096": 1039.960216776110,
    "IR105": 966.153383926055,
    "IR112": 891.713057301260,
    "IR123": 810.609007871230,
    "IR133": 753.590621482278,
}


DONT_AUTOGEN_GEOLOCATION = PATHS["DONT_AUTOGEN_GEOLOCATION"]


"""
Equations and code from GEO-KOMPSAT-2A Level 1B Data User Manual.
"""


def latlon_from_lincol_geos(
    resolution,
    line,
    column,
    metadata,
    geolocation_cache_backend="memmap",
    chunk_size=None,
    resource_tracker=None,
):
    """Calculate latitude and longitude from array indices.

    Uses geostationary projection (likely won't work with extended local area files).
    Equations and code from GEO-KOMPSAT-2A Level 1B Data User Manual.
    """
    check_geolocation_cache_backend(geolocation_cache_backend)
    fname = get_geolocation_cache_filename(
        "GEOLL",
        metadata,
        geolocation_cache_backend=geolocation_cache_backend,
        chunk_size=chunk_size,
    )
    if resource_tracker is not None:
        key = Path(fname).name
        if metadata.get("area_id"):
            key += f"_{metadata.get('area_id')}"
        resource_tracker.track_resource_usage(logstr="MEMUSG", verbose=False, key=key)
    if not os.path.isfile(fname):
        degtorad = 3.14159265358979 / 180.0

        # Note metadata included directly in the data files is incorrect for
        # some AMI data files.  These hard coded values are pulled from the
        # manual for correct geolocation.
        if resolution == "HIGH":
            COFF = 11000.5
            CFAC = 8.170135561335742e7
            LOFF = 11000.5
            LFAC = 8.170135561335742e7
        elif resolution == "MED":
            COFF = 5500.5
            CFAC = 4.0850677806678705e7
            LOFF = 5500.5
            LFAC = 4.0850677806678705e7
        else:
            COFF = 2750.5
            CFAC = 2.0425338903339352e7
            LOFF = 2750.5
            LFAC = 2.0425338903339352e7
        sub_lon = 128.2

        # COFF = metadata["COFF"]
        # CFAC = metadata["CFAC"]
        # LOFF = metadata["LOFF"]
        # LFAC = metadata["LFAC"]
        # sub_lon = metadata["sub_lon"]

        sub_lon = sub_lon * degtorad

        x = np.empty_like(column)
        y = np.empty_like(line)
        cosx = np.empty_like(x)
        cosy = np.empty_like(x)
        sinx = np.empty_like(x)
        siny = np.empty_like(x)
        cosxy = np.empty_like(x)
        A = np.empty_like(x)
        Sd = np.empty_like(x)
        Sn = np.empty_like(x)
        S1 = np.empty_like(x)
        S2 = np.empty_like(x)
        S3 = np.empty_like(x)
        Sxy = np.empty_like(x)

        x = degtorad * ((column - COFF) * 2**16 / CFAC)
        y = degtorad * ((line - LOFF) * 2**16 / LFAC)
        x = x.astype(np.float32)
        y = y.astype(np.float32)
        ne.evaluate("cos(x)", out=cosx)
        ne.evaluate("cos(y)", out=cosy)
        ne.evaluate("sin(x)", out=sinx)
        ne.evaluate("sin(y)", out=siny)
        ne.evaluate("cosx * cosy", out=cosxy)
        ne.evaluate("42164 * cosxy", out=A)
        B = cosy**2 + 1.006739501 * siny**2
        B = B.astype(np.float32)
        ne.evaluate("sqrt(A**2 - B*1737122264)", out=Sd)
        ne.evaluate("(A - Sd) / B", out=Sn)
        ne.evaluate("42164 - (Sn * cosxy)", out=S1)
        ne.evaluate("Sn * (sinx * cosy)", out=S2)
        ne.evaluate("-Sn * siny", out=S3)
        ne.evaluate("sqrt((S1*S1) + (S2*S2))", out=Sxy)
        nlon = (np.arctan(S2 / S1) + sub_lon) / degtorad
        nlat = np.arctan((1.006739501 * S3) / Sxy) / degtorad

        nlat[np.where(np.isnan(nlat))] = -999.9
        nlon[np.where(np.isnan(nlon))] = -999.9
        if geolocation_cache_backend == "memmap":
            with open(fname, "w") as df:
                nlat.tofile(df)
                nlon.tofile(df)
        elif geolocation_cache_backend == "zarr":
            if chunk_size:
                chunks = (chunk_size, chunk_size)
            else:
                chunks = None
            LOG.info("Storing to %s (chunks=%s)", fname, chunks)
            # zarr does NOT have a close method, so you can NOT use the with context.
            zf = zarr.open(fname, mode="w")
            # Assume both arrays have the same shape and dtype
            kwargs = {
                "shape": nlat.shape,
                "dtype": nlat.dtype,
            }
            # As of Python 3.11, can't pass chunks=None into create_dataset
            if chunks:
                kwargs["chunks"] = chunks
            zf.create_dataset("lats", **kwargs)
            zf.create_dataset("lons", **kwargs)
            zf["lats"][:] = nlat
            zf["lons"][:] = nlon
    else:
        # Create memmap to the lat/lon file
        # Nothing will be read until explicitly requested
        # We are mapping this here so that the lats and lons are available when
        # calculating satlelite angles
        if geolocation_cache_backend == "memmap":
            shape = (metadata["num_lines"], metadata["num_samples"])
            offset = 4 * metadata["num_samples"] * metadata["num_lines"]
            nlat = np.memmap(fname, mode="r", dtype=np.float32, offset=0, shape=shape)
            nlon = np.memmap(
                fname, mode="r", dtype=np.float32, offset=offset, shape=shape
            )
        elif geolocation_cache_backend == "zarr":
            LOG.info(
                "GETGEO zarr to {} : lat/lon file for {}".format(
                    fname, metadata["scene"]
                )
            )
            zf = zarr.open(fname, mode="r")
            nlat = zf["lats"]
            nlon = zf["lons"]
    if resource_tracker is not None:
        resource_tracker.track_resource_usage(logstr="MEMUSG", verbose=False, key=key)

    return (nlat, nlon)


# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# Metadata collection functions.
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
def _check_file_consistency(metadata):
    """
    Check that all input metadata are from the same image time.

    Performs cheks on satellite_name, instrument_name, observation_mode, and time.
    If these are all equal, returns True.
    If any differ, returns False.
    """
    # Checking file-level metadata for exact equality in the following fields
    checks = {
        "satellite_name": "general",
        "instrument_name": "general",
        "observation_mode": "observation",
        "observation_start_time": "observation",
    }
    for name, level in checks.items():
        check_set = set(
            [metadata[fname]["global"][level][name] for fname in metadata.keys()]
        )
        if len(check_set) != 1:
            LOG.debug("Failed on {0}. Found: {1}".format(name, check_set))
            return False
    return True


def _get_general_metadata(df):
    """Gather all of the general file-level metadata."""
    metadata = {}
    md_names = [
        "satellite_name",
        "instrument_name",
        "data_processing_center",
        "data_processing_mode",
        "channel_spatial_resolution",
        "channel_center_wavelength",
        "scene_acquisition_time",
        "mission_reference_time",
        "file_generation_time",
        "file_name",
        "file_format_version",
        "geometric_correction_sw_version",
        "star_catalog_version",
        "landmark_catalog_version",
    ]

    for name in md_names:
        if hasattr(df, name):
            metadata[name] = getattr(df, name)
        else:
            LOG.info("Warning! File-level metadata field missing: {0}".format(name))
    return metadata


def _get_data_metadata(df):
    """Gather all of the data-size metadata."""
    metadata = {}
    md_names = [
        "total_pixel_data_size",
        "number_of_total_swaths",
        "number_of_columns",
        "number_of_lines",
    ]

    for name in md_names:
        if hasattr(df, name):
            metadata[name] = getattr(df, name)
        else:
            LOG.info("Warning! Data metadata field missing: {0}".format(name))
    return metadata


def _get_observation_metadata(df):
    """Gather all of the observation metadata."""
    metadata = {}
    md_names = [
        "observation_mode",
        "observation_start_time",
        "observation_end_time",
        "time_synchro_obt",
        "time_synchro_utc",
    ]

    for name in md_names:
        if hasattr(df, name):
            metadata[name] = getattr(df, name)
        else:
            LOG.info("Warning! Observation metadata field missing: {0}".format(name))
    return metadata


def _get_projection_metadata(df):
    """Gather all of the projection metadata."""
    metadata = {}
    md_names = [
        "projection_type",
        "sub_longitude",
        "cfac",
        "lfac",
        "coff",
        "loff",
        "nominal_satellite_height",
        "earth_equatorial_radius",
        "earth_polar_radius",
        "earth_ellipsoid_center",
        "image_upperleft_latitude",
        "image_upperleft_longitude",
        "image_lowerright_latitude",
        "image_lowerright_longitude",
        "image_center_latitude",
        "image_center_longitude",
        "image_upperleft_x",
        "image_upperleft_y",
        "image_lowerright_x",
        "image_lowerright_y",
        "resampling_kernel_type",
    ]

    for name in md_names:
        if hasattr(df, name):
            metadata[name] = getattr(df, name)
        else:
            LOG.info("Warning! Projection metadata field missing: {0}".format(name))
    return metadata


def _get_global_metadata(df):
    """Get file-level metadata."""
    metadata = {}
    metadata["general"] = _get_general_metadata(df)
    metadata["data"] = _get_data_metadata(df)
    metadata["observation"] = _get_observation_metadata(df)
    metadata["projection"] = _get_projection_metadata(df)
    return metadata


def _get_variable_metadata(df):
    """Gather all of the variable metadata."""
    metadata = {}
    md_names = [
        "channel_name",
        "detector_side",
        "number_of_total_pixels",
        "number_of_error_pixels",
        "max_pixel_value",
        "max_pixel_value",
        "average_pixel_value",
        "stddev_pixel_value",
        "number_of_total_bits_per_pixel",
        "number_of_data_quality_flag_bits_per_pixel",
        "number_of_valid_bits_per_pixel",
        "data_quality_flag_meaning",
        "ground_sample_distance_ew",
        "ground_sample_distance_ns",
    ]

    for name in md_names:
        if hasattr(df.variables["image_pixel_values"], name):
            metadata[name] = getattr(df.variables["image_pixel_values"], name)
        else:
            LOG.info("Warning! Projection metadata field missing: {0}".format(name))
    return metadata


def _get_metadata(df, fname):
    """
    Gather metadata for the data file and return as a dictionary.

    Note: We are gathering all of the available metadata in case it is needed at
    some point.
    """
    metadata = {}
    # Gather all file-level metadata.
    metadata["global"] = _get_global_metadata(df)
    # Gather all variable-level metadata.
    metadata["var_info"] = _get_variable_metadata(df)
    # Gather some useful info to the top level.
    try:
        metadata["path"] = df.filepath()
    except ValueError:
        # Without cython installed, df.filepath() does not work
        metadata["path"] = fname
    metadata["satellite"] = metadata["global"]["general"]["satellite_name"]
    metadata["sensor"] = df.instrument_name
    # These were being returned as np.int32's, causing an overflow when passed
    # to numpy 2.x memmap call in latlon_from_lincol_geos function below.
    # Explicitly cast to np.int64 to avoid overflow in memmap
    metadata["num_lines"] = np.int64(df.number_of_lines)
    metadata["num_samples"] = np.int64(df.number_of_columns)
    return metadata


def metadata_to_datetime(metadata):
    """Use information from the metadata to get the image datetime."""
    start_time = metadata["global"]["observation"]["observation_start_time"]
    end_time = metadata["global"]["observation"]["observation_end_time"]
    epoch = datetime(2000, 1, 1, 12, 0, 0)
    start_time = epoch + timedelta(seconds=start_time)
    end_time = epoch + timedelta(seconds=end_time)
    return start_time, end_time


def _get_geolocation_metadata(metadata):
    """
    Gather all of the metadata used in creating geolocation data for input file.

    This is split out so we can easily create a chash of the data for creation
    of a unique filename. This allows us to avoid recalculation of angles that
    have already been calculated.
    """
    metadata = metadata["global"]
    geomet = {}
    geomet["platform_name"] = metadata["general"]["satellite_name"]
    geomet["Re"] = metadata["projection"]["earth_equatorial_radius"]
    geomet["Rp"] = metadata["projection"]["earth_polar_radius"]
    geomet["e"] = 0.0818191910435
    # Nominal satellite height is from the center of the Earth.
    geomet["H_m"] = metadata["projection"]["nominal_satellite_height"]
    geomet["pphgt"] = geomet["H_m"] - geomet["Re"]
    geomet["lat0"] = metadata["projection"]["image_center_latitude"]
    geomet["lon0"] = metadata["projection"]["image_center_longitude"] * 180.0 / np.pi
    geomet["scene"] = metadata["observation"]["observation_mode"]
    # Just getting the nadir resolution in kilometers.  Must extract from a string.
    geomet["res_km"] = float(metadata["general"]["channel_spatial_resolution"])
    geomet["roi_factor"] = 5  # roi = res * roi_factor, was 10
    # These were being returned as np.int32's, causing an overflow when passed
    # to numpy 2.x memmap call in latlon_from_lincol_geos function below.
    # Explicitly cast to np.int64 to avoid overflow in memmap
    geomet["num_lines"] = np.int64(metadata["data"]["number_of_lines"])
    geomet["num_samples"] = np.int64(metadata["data"]["number_of_columns"])
    # Dynamically get offsets and scale factors needed for correct geolocation
    # calculation
    geomet["sub_lon"] = metadata["projection"]["sub_longitude"]
    geomet["CFAC"] = np.abs(metadata["projection"]["cfac"])
    geomet["COFF"] = np.abs(metadata["projection"]["coff"])
    geomet["LFAC"] = np.abs(metadata["projection"]["lfac"])
    geomet["LOFF"] = np.abs(metadata["projection"]["loff"])
    return geomet


# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# Get pixel data.
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
def get_data(gvars, fname, rad=False, ref=False, bt=False):
    """Get actual pixel data from a specific file using geolocation information."""
    if "Lines" in gvars and "Samples" in gvars:
        full_disk = False
        line_inds = gvars["Lines"]
        sample_inds = gvars["Samples"]
    else:
        full_disk = True

    ds = ncdf.Dataset(fname, "r")
    ipixel = ds.variables["image_pixel_values"]

    if not full_disk:
        counts = ipixel[:].data[line_inds, sample_inds]
    else:
        # Leaving out zoom stuff in abi reader for now, since it seems
        #   those conditions shouldn't be reached for these files.
        counts = ipixel[:].data

    # The following section of bitwise "masking" is from the manual.
    # I believe what is expected to happen is that, if a pixel is out-of-area
    # or erroneous, it will be exactly 32768 or 49152, and will be 0 after the
    # masking. Conditional pixels will be treated as "good enough" and will have
    # a value less than 16384 (i.e. the "normal data" range after the bitwise
    # mask is applied.
    channel = ipixel.getncattr("channel_name")
    if (channel == "VI004") or (channel == "VI005") or (channel == "NR016"):
        mask = 0b0000011111111111  # 11bit mask
    elif (channel == "VI006") or (channel == "NR013") or (channel == "WV063"):
        mask = 0b0000111111111111  # 12bit mask
    elif channel == "SW038":
        mask = 0b0011111111111111  # 14bit mask
    else:
        mask = 0b0001111111111111  # 13bit mask

    if channel.startswith("VI") or channel.startswith("NR"):
        reflectance_chan = True
    else:
        reflectance_chan = False

    counts_masked = np.bitwise_and(counts, mask)

    # So far, looks like the binary masking from the manual is sufficient.
    # (Good and conditional values will be kept.)
    # The following code is a starting point if conditional values need to be
    # masked.
    # conditional_threshold = 16384
    # out_of_area_threshold = 32768
    # erroneous_threshold = 49152
    # counts_masked = np.ma.masked_where(counts >= conditional_threshold, counts)

    gain = ds.DN_to_Radiance_Gain
    offset = ds.DN_to_Radiance_Offset

    # Equations from last page of manual (Table 14)
    # radiance = gain * count + offset
    radiance = gain * counts_masked + offset

    data = {}
    if rad:
        data["Rad"] = radiance

    if reflectance_chan and ref:
        # Visible and Near IR
        c_prime = ds.Radiance_to_Albedo_c
        albedo = radiance * c_prime
        data["Ref"] = albedo

    if bt and not reflectance_chan:
        # IR
        # Using hard-coded values for nu, since the values obtained from the
        #   dataset don't quite match the values from the manual.
        nu = CENTER_WAVENUMBERS[channel]
        h = ds.Plank_constant_h
        k = ds.Boltzmann_constant_k
        c = ds.light_speed
        c0 = ds.Teff_to_Tbb_c0
        c1 = ds.Teff_to_Tbb_c1
        c2 = ds.Teff_to_Tbb_c2
        T_e = (h * c / k * (nu * 100)) / np.log(
            (2 * h * c**2) * (nu * 100) ** 3 / (radiance * 1e-5) + 1
        )
        T_b = c0 + c1 * T_e + c2 * T_e**2

        data["BT"] = T_b

    ds.close()

    return data


def call(
    fnames,
    metadata_only=False,
    chans=None,
    area_def=None,
    self_register=False,
    roi=None,
    geolocation_cache_backend=gpaths["GEOIPS_GEOLOCATION_CACHE_BACKEND"],
    cache_chunk_size=None,
    cache_solar_angles=False,
    geolocation_only=False,
    resource_tracker=None,
    satellite_zenith_angle_cutoff=75,
):
    """
    Read Geo-Kompsat NetCDF data from a list of filenames.

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
    roi: radius of influence (unit in meter), used in interpolation scheme
        * Default=None, i.e., if not defined in the yaml file
        * Defined in yaml file where variables and tuning parameters are set
    satellite_zenith_angle_cutoff: cutoff for satellite zenith angle in degrees
        * Defaults to 75 for now to be consistent with previous hard coded
          value
        * Later will update to None (will have to update test scripts or
          outputs accordingly)

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
        roi=roi,
        geolocation_cache_backend=geolocation_cache_backend,
        cache_chunk_size=cache_chunk_size,
        cache_solar_angles=cache_solar_angles,
        geolocation_only=geolocation_only,
        resource_tracker=resource_tracker,
        satellite_zenith_angle_cutoff=satellite_zenith_angle_cutoff,
    )


def call_single_time(
    fnames,
    metadata_only=False,
    chans=None,
    area_def=None,
    self_register=False,
    roi=None,
    geolocation_cache_backend="memmap",
    cache_chunk_size=None,
    cache_solar_angles=False,
    geolocation_only=False,
    resource_tracker=None,
    satellite_zenith_angle_cutoff=75,
):
    """
    Read Geo-Kompsat NetCDF data from a list of filenames.

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
    roi: radius of influence (unit in meter), used in interpolation scheme
        * Passed in from Call function
        * Default=None, i.e., if not defined in the yaml file
        * Defined in yaml file where variables and tuning parameters are set
    geolocation_cache_backend : str
        * Specify to use either memmap or zarray to store pre-calculated geolocation
          data.
    cache_chunk_size : int
        * Specify chunk size if using zarray to store pre-calculated geolocation data.
    resource_tracker: geoips.utils.memusg.PidLog object
        * Track resource usage using the PidLog class object from geoips.utils.memusg.
        * The PidLog.track_resource_usage method allows us to snapshot the memory usage
          for the PID associated with the geoips call. The time and stats of the
          snapshot are recorded, and can be accessed using the
          PidLog.checkpoint_usage_stats method.
    satellite_zenith_angle_cutoff: cutoff for satellite zenith angle in degrees
        * Defaults to None

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
    check_geolocation_cache_backend(geolocation_cache_backend)
    gvars = {}
    datavars = {}
    geo_metadata = {}

    if fnames is None or len(fnames) == 0:
        raise ValueError("No input files specified")

    # Get metadata for all input data files
    # Check to be sure that all input files are form the same image time
    all_metadata = {}
    for fname in fnames:
        if chans:
            gotone = False
            for chan in chans:
                currchan = chan[:5].lower()
                if currchan in fname:
                    gotone = True
            if not gotone:
                LOG.info(
                    "SKIPPING file %s, not needed from channel list %s", fname, chans
                )
                continue
        try:
            # Open using with to avoid seg faults due to not properly closing files.
            # This did not seg fault prior to netcdf 1.7 / numpy 2.x
            with ncdf.Dataset(str(fname), "r") as ds:
                all_metadata[fname] = _get_metadata(ds, fname)
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
    for fname, md in all_metadata.items():
        ch = md["var_info"]["channel_name"]
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
    start_dt, end_dt = metadata_to_datetime(highest_md)
    xarray_obj.attrs["start_datetime"] = start_dt
    xarray_obj.attrs["end_datetime"] = end_dt
    xarray_obj.attrs["source_name"] = "ami"  # "ami"
    xarray_obj.attrs["data_provider"] = "nmsc"
    xarray_obj.attrs["platform_name"] = highest_md["global"]["general"][
        "satellite_name"
    ]
    xarray_obj.attrs["area_definition"] = area_def
    xarray_obj.attrs["source_file_names"] = [
        os.path.basename(fname) for fname in fnames
    ]

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
        scene_id = highest_md["global"]["observation"]["observation_mode"].lower()
        if scene_id == "fd":
            xarray_obj.attrs["area_id"] = "Full-Disk"
        elif scene_id == "ela":
            xarray_obj.attrs["area_id"] = "Extended-Local-Area"
        elif scene_id == "la":
            xarray_obj.attrs["area_id"] = "Local-Area"
        elif scene_id == "enh":
            xarray_obj.attrs["area_id"] = "Extend-Northern-Hemisphere"
        elif scene_id == "ea":
            xarray_obj.attrs["area_id"] = "East-Asia"
        elif scene_id == "ko":
            xarray_obj.attrs["area_id"] = "Korea"
        elif scene_id == "tp":
            xarray_obj.attrs["area_id"] = "Typhoon"
        xarray_obj.attrs["area_definition"] = None
    adname = xarray_obj.attrs["area_id"]

    if metadata_only:
        LOG.info("Only need metadata from first file, returning")
        return {"METADATA": xarray_obj}

    # Create list of all possible channels for the case where no channels were requested
    all_chans_list = []
    for chan_list in DATASET_INFO.values():
        for chl in chan_list:
            all_chans_list.append(chl + "Rad")
            if chl.startswith("VI") or chl.startswith("NR"):
                all_chans_list.append(chl + "Ref")
            else:
                all_chans_list.append(chl + "BT")

    # If specific channels were requested, check them against the input data
    # If specific channels were requested, but no files exist for one of the
    # channels, then error
    if chans:
        for chan in chans:
            if chan in ALL_GEO_VARS:
                continue
            if chan not in all_chans_list:
                raise ValueError("Requested channel {0} not recognized.".format(chan))
            if chan[0:5] not in file_info.keys():
                continue

    # If no specific channels were requested, get everything
    if not chans:
        chans = all_chans_list

    # Creates a dictionary whose keys are band numbers in the form {name}##
    # and whose values are lists containing the data types(s) requested for
    # the band (e.g. Rad, Ref, BT).
    chan_info = {}
    for ch in chans:
        if ch in ALL_GEO_VARS:
            continue
        chn = ch[0:5]
        typ = ch[5:]
        if chn not in chan_info:
            chan_info[chn] = []
        chan_info[chn].append(typ)

    # Gather geolocation data
    # Assume datetime the same for all resolutions.  Not true, but close enough.
    # This saves us from having very slightly different solar angles for each channel.
    # Loop over resolutions and get metadata as needed
    if self_register:
        LOG.info("Getting geolocation information for adname %s.", adname)
        geo_metadata[adname] = _get_geolocation_metadata(res_md[self_register])

        i = np.arange(0, geo_metadata[adname]["num_lines"], dtype="f")
        j = np.arange(0, geo_metadata[adname]["num_samples"], dtype="f")
        i, j = np.meshgrid(i, j)
        fldk_lats, fldk_lons = latlon_from_lincol_geos(
            self_register,
            j,
            i,
            geo_metadata[adname],
            geolocation_cache_backend=geolocation_cache_backend,
            resource_tracker=resource_tracker,
        )

        gvars[adname] = get_geolocation(
            start_dt,
            geo_metadata[adname],
            fldk_lats,
            fldk_lons,
            BADVALS,
            area_def,
            geolocation_cache_backend=geolocation_cache_backend,
            cache_solar_angles=cache_solar_angles,
            resource_tracker=resource_tracker,
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
            LOG.info(
                "Getting geolocation information for resolution %s for %s", res, adname
            )
            try:
                geo_metadata[res] = _get_geolocation_metadata(res_md[res])

                i = np.arange(0, geo_metadata[res]["num_lines"], dtype="f")
                j = np.arange(0, geo_metadata[res]["num_samples"], dtype="f")
                i, j = np.meshgrid(i, j)
                fldk_lats, fldk_lons = latlon_from_lincol_geos(
                    res,
                    j,
                    i,
                    geo_metadata[res],
                    geolocation_cache_backend=geolocation_cache_backend,
                    resource_tracker=resource_tracker,
                )
                gvars[res] = get_geolocation(
                    start_dt,
                    geo_metadata[res],
                    fldk_lats,
                    fldk_lons,
                    BADVALS,
                    area_def,
                    geolocation_cache_backend=geolocation_cache_backend,
                    cache_solar_angles=cache_solar_angles,
                    resource_tracker=resource_tracker,
                )
            except IndexError as resp:
                LOG.exception("SKIPPING apparently no coverage or bad geolocation file")
                raise IndexError(resp)

    LOG.interactive("Done with geolocation for {}".format(adname))
    if geolocation_only:
        geo_xarrays = {"METADATA": xarray_obj}
        for dsname in gvars.keys():
            geo_xarrays[dsname] = xarray.Dataset()
            geo_xarrays[dsname].attrs = xarray_obj.attrs.copy()
            for varname in gvars[dsname].keys():
                geo_xarrays[dsname][varname] = xarray.DataArray(gvars[dsname][varname])
        return geo_xarrays

    # Read the data
    # Will read all data if sector_definition is None
    # Will only read required data if an sector_definition is provided
    for chan, types in chan_info.items():
        # If we didn't pass all the channel data, skip non-existent data types
        if chan not in file_info:
            continue
        LOG.info("Reading {}".format(chan))
        if resource_tracker:
            key = f"READ CHAN: ami_netcdf_chan_{chan}_{adname}"
            resource_tracker.track_resource_usage(
                logstr="MEMUSG",
                verbose=False,
                key=key,
                show_log=False,
            )
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

        if self_register:
            gname = adname
        else:
            gname = res

        rad = ref = bt = False
        if "Rad" in types:
            rad = True
        if "Ref" in types:
            ref = True
        if "BT" in types:
            bt = True

        data = get_data(gvars[gname], chan_md["path"], rad, ref, bt)
        for typ, val in data.items():
            if dsname not in datavars:
                datavars[dsname] = {}
            datavars[dsname][chan + typ] = val
        if resource_tracker:
            resource_tracker.track_resource_usage(
                logstr="MEMUSG", verbose=False, key=key
            )

    if area_def:
        for res in ["LOW", "MED", "HIGH"]:
            if res in gvars and gvars[res]:
                gvars_res = gvars.pop(res)
                if adname not in gvars:
                    gvars[adname] = gvars_res

    if self_register:
        # Determine which resolution has geolocation
        LOG.info("Registering to {}".format(self_register))
        all_res = ["LOW", "MED", "HIGH"]
        if self_register not in all_res:
            raise ValueError("No geolocation data found.")

        all_res.remove(self_register)
        datavars[adname] = datavars.pop(self_register)
        for res in all_res:
            if res in datavars:
                for varname, var in datavars[res].items():
                    datavars[adname][varname] = var
                datavars.pop(res)

    # Remove lines and samples arrays.  Not needed.
    for res in gvars.keys():
        # Providing None as a default in case the dictionary is missing 'Lines' or
        # 'Samples'. Since we skip if these don't exist anyways, I don't see this
        # being an issue.

        # The reason this is useful is for cases in which these variables are
        # missing but you still want to mask all of the other variables in this
        # resolution by the satellite zenith angle cutoff provided.
        gvars[res].pop("Lines", None)
        gvars[res].pop("Samples", None)
        for varname, var in gvars[res].items():
            if satellite_zenith_angle_cutoff:
                LOG.info(
                    "Masking var %s greater than %s degrees sat zenith angle",
                    varname,
                    satellite_zenith_angle_cutoff,
                )
                gvars[res][varname] = np.ma.array(
                    var, mask=gvars[res]["satellite_zenith_angle"].mask
                )
                gvars[res][varname] = np.ma.masked_where(
                    gvars[res]["satellite_zenith_angle"]
                    > satellite_zenith_angle_cutoff,
                    gvars[res][varname],
                )
    for ds in datavars.keys():
        if not datavars[ds]:
            datavars.pop(ds)

    # Create the final dictionary of xarray objects.
    xarray_objs = {}
    for dsname in datavars.keys():
        # Create a new xarray object to populate with all the data.
        xobj = xarray.Dataset()
        xobj.attrs = xarray_obj.attrs.copy()

        for varname in datavars[dsname].keys():
            xobj[varname] = xarray.DataArray(datavars[dsname][varname])

        for varname in gvars[dsname].keys():
            xobj[varname] = xarray.DataArray(gvars[dsname][varname])

        # if roi is not defined in yaml file, a default roi is applied
        if roi is None:
            roi = 500
            if hasattr(xobj, "area_definition") and xobj.area_definition is not None:
                roi = max(
                    xobj.area_definition.pixel_size_x, xobj.area_definition.pixel_size_y
                )
                LOG.info("Trying area_def roi %s", roi)
            for curr_res in geo_metadata.keys():
                LOG.info(
                    "Trying metadata roi %s %s",
                    geo_metadata[curr_res]["res_km"] * 1000.0,
                    roi,
                )
                if geo_metadata[curr_res]["res_km"] * 1000.0 > roi:
                    roi = geo_metadata[curr_res]["res_km"] * 1000.0
                    LOG.info("Trying standard_metadata[%s] %s", curr_res, roi)
        xobj.attrs["interpolation_radius_of_influence"] = roi
        xobj.attrs["longitude_of_projection_origin"] = geo_metadata[curr_res][
            "lon0"
        ].round(5)
        xarray_objs[dsname] = xobj
        # At some point we may need to deconflict, but for now just use any of the
        # dataset attributes as the METADATA dataset
        xarray_objs["METADATA"] = xobj[[]]

    LOG.info("Done reading GEOKOMPSAT AMI data for %s", adname)

    return xarray_objs


# Unit test functions
def get_test_files(test_data_dir):
    """Generate testing xarray from test data."""
    filepath = test_data_dir + "/test_data_ami/data/20231208_0300_daytime/*.nc"
    filelist = glob.glob(filepath)
    if len(filelist) == 0:
        raise FileNotFoundError("No files found")
    for file in filelist:
        if not os.path.exists(file):
            raise FileNotFoundError(f"File {file} does not exist")
    tmp_xr = call(filelist)
    return tmp_xr


def get_test_parameters():
    """Generate test data key for unit testing."""
    return [
        {"data_key": "HIGH", "data_var": "VI006Ref", "mean": 0.14788916},
        {"data_key": "LOW", "data_var": "IR112BT", "mean": 286.63754873},
    ]
