# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Standard GeoIPS xarray dictionary based FCI NetCDF data reader."""

from datetime import datetime, timedelta
import logging
import numpy as np
import os
from pathlib import Path
from pyorbital.astronomy import sun_earth_distance_correction
import xarray
import zarr

from geoips.interfaces import readers
from geoips.plugins.modules.readers.utils.geostationary_geolocation import (
    check_geolocation_cache_backend,
    get_geolocation_cache_filename,
    get_geolocation,
    AutoGenError,
)
from geoips.utils.context_managers import import_optional_dependencies

with import_optional_dependencies(loglevel="info"):
    """Attempt to import a package and print to LOG.info if the import fails."""
    import numexpr as ne
    from satpy.scene import Scene
    import netCDF4 as ncdf

    # Need to uncomment if HDF5_PLUGIN_PATH env variable is not set upstream,
    # though you will still not be able to interact with the data after using Scene.load
    # Until this works out of the box with out the need to set HDF5_PLUGIN_PATH
    # import hdf5plugin

LOG = logging.getLogger(__name__)

interface = "readers"
family = "standard"
name = "fci_netcdf"
source_names = ["fci"]

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

# Needed until the satpy devs can fix this issue:
# https://github.com/pytroll/satpy/issues/3067
# Used to convert from wavenumber (mW·m⁻²·sr⁻¹·(cm⁻¹)⁻¹)
# to wavelength (W·m⁻²·sr⁻¹·µm⁻¹)
RADIANCE_CONVERSION_COEFFICIENTS = {
    "B01Rad": 50.26570892,
    "B02Rad": 38.74919891,
    "B03Rad": 24.66601944,
    "B04Rad": 13.51755047,
    "B05Rad": 11.98462009,
    "B06Rad": 5.261388779,
    "B07Rad": 3.84947896,
    "B08Rad": 1.965775013,
    "B09Rad": 0.697183013,
    "B10Rad": 0.2536683083,
    "B11Rad": 0.1817249954,
    "B12Rad": 0.1306722015,
    "B13Rad": 0.1071347967,
    "B14Rad": 0.0899727419,
    "B15Rad": 0.06602230668,
    "B16Rad": 0.05665054172,
    "HRB03Rad": 24.66601944,
    "HRB09Rad": 0.697183013,
    "HRB14Rad": 0.0899727419,
}

DATASET_INFO = {
    # HIGH resolution = 0.5km at nadir
    "HIGH": ["vis_06_hr", "nir_22_hr"],
    # MED resolution = 1.0km at nadir
    "MED": [
        "vis_04",
        "vis_05",
        "vis_06",
        "vis_08",
        "vis_09",
        "nir_13",
        "nir_16",
        "nir_22",
        "ir_38_hr",
        "ir_105_hr",
    ],
    # LOW resolution = 2.0km at nadir
    "LOW": ["ir_38", "wv_63", "wv_73", "ir_87", "ir_97", "ir_105", "ir_123", "ir_133"],
}

BAND_MAP = {
    "B01Ref": "vis_04",
    "B01Rad": "vis_04",
    "B02Ref": "vis_05",
    "B02Rad": "vis_05",
    "B03Ref": "vis_06",
    "B03Rad": "vis_06",
    "B04Ref": "vis_08",
    "B04Rad": "vis_08",
    "B05Ref": "vis_09",
    "B05Rad": "vis_09",
    "B06Ref": "nir_13",
    "B06Rad": "nir_13",
    "B07Ref": "nir_16",
    "B07Rad": "nir_16",
    "B08Ref": "nir_22",
    "B08Rad": "nir_22",
    "B09BT": "ir_38",
    "B09Rad": "ir_38",
    "B10BT": "wv_63",
    "B10Rad": "wv_63",
    "B11BT": "wv_73",
    "B11Rad": "wv_73",
    "B12BT": "ir_87",
    "B12Rad": "ir_87",
    "B13BT": "ir_97",
    "B13Rad": "ir_97",
    "B14BT": "ir_105",
    "B14Rad": "ir_105",
    "B15BT": "ir_123",
    "B15Rad": "ir_123",
    "B16BT": "ir_133",
    "B16Rad": "ir_133",
    "HRB03Ref": "vis_06_hr",
    "HRB03Rad": "vis_06_hr",
    "HRB09BT": "ir_38_hr",
    "HRB09Rad": "ir_38_hr",
    "HRB14BT": "ir_105_hr",
    "HRB14Rad": "ir_105_hr",
}

CHAN_MAP = {val: key for key, val in BAND_MAP.items()}

ALL_GEO_VARS = [
    "solar_zenith_angle",
    "satellite_zenith_angle",
    "solar_azimuth_angle",
    "satellite_azimuth_angle",
    "latitude",
    "longitude",
]

BADVALS = {
    "Off_Of_Disk": -999.9,
    "Conditional": -999.8,
    "Out_Of_Valid_Range": -999.7,
    "No_Value": -999.6,
    "Unitialized": -9999.9,
}


def get_geolocation_metadata(xarray_attrs):
    """Get geolocation metadata."""
    geomet = {}
    geomet["platform_name"] = xarray_attrs["platform_name"]
    geomet["source_name"] = xarray_attrs["source_name"]  # sensor == fci
    # Used for cached filenames
    if "orbital_parameters" in xarray_attrs:
        # xarray from converted satpy.scene
        geomet["lon0"] = xarray_attrs["orbital_parameters"][
            "satellite_nominal_longitude"
        ]
        geomet["num_lines"] = xarray_attrs["area"].y_size
        geomet["num_samples"] = xarray_attrs["area"].x_size
        geomet["scan_mode"] = xarray_attrs["area"].area_id
    else:
        geomet["lon0"] = xarray_attrs["mtg_geos_projection"][
            "longitude_of_projection_origin"
        ]
        geomet["Re_m"] = xarray_attrs["mtg_geos_projection"]["semi_major_axis"]
        geomet["Rp_m"] = xarray_attrs["mtg_geos_projection"]["semi_minor_axis"]
        geomet["scan_mode"] = xarray_attrs["coverage"]
        geomet["num_lines"] = xarray_attrs["num_lines"]
        geomet["num_samples"] = xarray_attrs["num_samples"]
        geomet["mtg_geos_projection"] = xarray_attrs["mtg_geos_projection"]
    geomet["scene"] = geomet["scan_mode"]
    geomet["start_datetime"] = xarray_attrs["start_datetime"]
    geomet["end_datetime"] = xarray_attrs["end_datetime"]
    if "H_m" not in geomet:
        geomet["H_m"] = 42164000.0
        geomet["Re_m"] = 6378137.0
        geomet["Rp_m"] = 6356752.298215968
    geomet["H_km"] = geomet["H_m"] / 1000.0
    geomet["Re_km"] = geomet["Re_m"] / 1000.0
    geomet["Rp_km"] = geomet["Rp_m"] / 1000.0
    geomet["roi_factor"] = 5
    return geomet


def get_latitude_longitude(
    metadata,
    x_1d,
    y_1d,
    BADVALS,
    sect=None,
    geolocation_cache_backend="zarr",
    chunk_size=None,
    resource_tracker=None,
):
    """
    Get latitudes and longitudes.

    This routine accepts a dictionary containing metadata as read from a NCDF4
    format file, and returns latitudes and longitudes for a full disk.
    """
    check_geolocation_cache_backend(geolocation_cache_backend)
    # If the filename format needs to change for the pre-generated geolocation
    # files, please discuss prior to changing.  It will force recreation of all
    # files, which can be problematic for large numbers of sectors
    fname = get_geolocation_cache_filename(
        "GEOLL",
        metadata,
        geolocation_cache_backend=geolocation_cache_backend,
        chunk_size=chunk_size,
    )
    if resource_tracker is not None:
        key = Path(fname).name
        if sect:
            key += f"_{sect.area_id}"
        resource_tracker.track_resource_usage(logstr="MEMUSG", verbose=False, key=key)
    if not Path(fname).exists():
        if sect is not None and DONT_AUTOGEN_GEOLOCATION and "tc2019" not in sect.name:
            msg = (
                f"GETGEO Requested NO AUTOGEN GEOLOCATION. "
                f"Could not create latlonfile for ad {metadata['scene']}: {fname}"
            )
            LOG.error(msg)
            raise AutoGenError(msg)
        # Anywhere you see NOQA or noqa: F841, this is added since the variables are
        # used however they are not recognized by flake8 linter under numexpr.evaluate()
        # Constants
        pi = np.pi
        # Must include rad2deg variable, because it is used within the
        # numexpr command below.  flake8 does not recognize it as being
        # used, so must include # NOQA flag
        rad2deg = 180.0 / pi  # NOQA
        Re = metadata["Re_km"]  # Earth equatorial radius (km)
        Rp = metadata["Rp_km"]  # Earth polar radius (km)
        # The parameter h in the equations above refers to the geostationary radius.
        # The geostationary radius is the distance from the Earth’s centre to the
        # satellite in geostationary orbit and can be calculated from the sum of the
        # geostationary altitude (35786.4km) and the equatorial Earth radius.
        h = metadata["H_km"]

        s4 = Re**2 / Rp**2  # noqa: F841
        s5 = h**2 - Re**2  # noqa: F841

        lon0 = metadata["lon0"]  # noqa: F841

        x, y = np.meshgrid(x_1d, y_1d)

        cos_x = np.cos(x)
        sin_x = np.sin(x)  # noqa: F841
        cos_y = np.cos(y)
        sin_y = np.sin(y)  # noqa: F841

        sd = ne.evaluate("(h * cos_x * cos_y)**2 - (cos_y**2 + s4 * sin_y**2) * s5")
        bad_mask = sd < 0.0
        sd[bad_mask] = 0.0
        sd **= 0.5

        # Doing inplace operations when variables are no longer needed

        # sd no longer needed
        sn = sd
        ne.evaluate("(h * cos_x * cos_y - sd) / (cos_y**2 +s4 * sin_y**2)", out=sn)

        # cos_x no longer needed
        s1 = cos_x
        ne.evaluate("h - (sn * cos_x * cos_y)", out=s1)

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
        ne.evaluate("rad2deg * arctan(s4 * s3 / sxy)", out=lats)

        # s1 no longer needed
        lons = s1
        ne.evaluate("rad2deg * arctan(s2 / s1) + lon0", out=lons)
        lons[lons > 180.0] -= 360

        # Set bad values
        lats[bad_mask] = BADVALS["Off_Of_Disk"]
        lons[bad_mask] = BADVALS["Off_Of_Disk"]
        LOG.info("Done calculating latitudes and longitudes")

        if geolocation_cache_backend == "memmap":
            with open(fname, "w") as df:
                lats.tofile(df)
                lons.tofile(df)
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
                "shape": lats.shape,
                "dtype": lats.dtype,
            }
            # As of Python 3.11, can't pass chunks=None into create_dataset
            if chunks:
                kwargs["chunks"] = chunks
            zf.create_dataset("lats", **kwargs)
            zf.create_dataset("lons", **kwargs)
            zf["lats"][:] = lats
            zf["lons"][:] = lons
    else:
        # Create memmap to the lat/lon file
        # Nothing will be read until explicitly requested
        # We are mapping this here so that the lats and lons are available when
        # calculating satlelite angles
        if geolocation_cache_backend == "memmap":
            shape = (metadata["num_lines"], metadata["num_samples"])
            offset = 8 * metadata["num_samples"] * metadata["num_lines"]
            lats = np.memmap(fname, mode="r", dtype=np.float64, offset=0, shape=shape)
            lons = np.memmap(
                fname, mode="r", dtype=np.float64, offset=offset, shape=shape
            )
        elif geolocation_cache_backend == "zarr":
            LOG.info(
                "GETGEO zarr to {} : lat/lon file for {}".format(
                    fname, metadata["scene"]
                )
            )
            # NOTE zarr does NOT have a close method, so you can NOT use with context.
            zf = zarr.open(fname, mode="r")
            lats = zf["lats"]
            lons = zf["lons"]
    if resource_tracker is not None:
        resource_tracker.track_resource_usage(logstr="MEMUSG", verbose=False, key=key)

    return np.flipud(lats), np.fliplr(lons)


def get_standard_geoips_attrs(file_attrs, area_def):
    """Set the standard geoips attrs.

    Parameters
    ----------
    file_attrs : dict
        Dictionary holding attributes found in source file

    Returns
    -------
    dict
        Dictionary of all source file attrs, along with required GeoIPS attrs
    """
    # Native metadata in file
    all_attrs = file_attrs.copy()
    all_attrs["platform_name"] = file_attrs["platform"].replace("MTI", "MTG-I")
    all_attrs["source_name"] = file_attrs["data_source"].lower()
    all_attrs["data_provider"] = "EUMETSAT"
    date_time_position = datetime.strptime(
        all_attrs["date_time_position"], "%Y%m%d%H%M%S"
    )
    if "TRAIL" in all_attrs["mtg_name"]:
        # Time coverage start/end will differ across each individual granule that
        # comprises a full scan. So instead of setting the start/end datetime to the
        # time coverage start/end attr in the file metadata, use the date_time_position
        # attr, which is consistent across all files.
        all_attrs["start_datetime"] = date_time_position
        all_attrs["actual_start_datetime"] = datetime.strptime(
            file_attrs["time_coverage_start"], "%Y%m%d%H%M%S"
        )
        all_attrs["end_datetime"] = datetime.strptime(
            file_attrs["time_coverage_end"], "%Y%m%d%H%M%S"
        )
    else:
        all_attrs["start_datetime"] = date_time_position
        all_attrs["end_datetime"] = date_time_position
    all_attrs["scan_datetime"] = date_time_position
    all_attrs["interpolation_radius_of_influence"] = 50 * 1000
    all_attrs["area_definition"] = area_def
    if area_def:
        area_id = area_def.area_id
    else:
        area_id = None
    all_attrs["area_id"] = area_id
    return all_attrs


def load_metadata_single_file(fci_file, group=None, variable=None):
    """Load metadata from an FCI file.

    Parameters
    ----------
    fci_file : str
        Full file path to file
    group : str, optional
        Name of group to load attributes, by default None
    variable : _type_, optional
        Name of variable to load attributes, by default None

    Returns
    -------
    dict
        All metadata attrs for group/variable
    """
    LOG.info("Grabbing metadata for %s", Path(fci_file).name)
    all_meta_attrs = {}
    if not group:
        group = ""
    load_group = []
    for grp in group.split("/"):
        with xarray.open_dataset(fci_file, group="/".join(load_group)) as df:
            meta = df.attrs
        for key, val in meta.items():
            if key not in all_meta_attrs:
                all_meta_attrs[key] = val
        load_group.append(grp)
    if variable and variable in meta:
        for key, val in meta[variable].attrs:
            if key not in all_meta_attrs:
                all_meta_attrs[key] = val
    return all_meta_attrs


def get_ncattrs(fci_file, group=""):
    """Lightweight function to quickly return the attrs for a group in a netCDF file."""
    with ncdf.Dataset(fci_file, "r") as ds:
        attrs = {x: ds[group].getncattr(x) for x in ds[group].ncattrs()}
    return attrs


def avail_chans_in_file(fci_file):
    """Return list of available channels/variables in file.

    Parameters
    ----------
    fci_file : str
        Full file path to FCI file

    Returns
    -------
    list
        list of strings of available variables
    """
    with xarray.open_dataset(fci_file) as df:
        meta = df.l1c_channels_present.data
    return list(meta)


def final_calibrated_variable_name(ncvar_name, chan_map=CHAN_MAP):
    """Determine the final name of dataset variable that should be used in GeoIPS.

    Parameters
    ----------
    ncvar_name : str
        Name of variable in source file
    chan_map : dict, optional
        Mapped band name used by GeoIPS, by default CHAN_MAP

    Returns
    -------
    str
        Variable name used in GeoIPS (e.g. B14BT)
    """
    if any([x in ncvar_name for x in ["vis_", "nir_"]]):
        cal_name = "Ref"
    else:
        cal_name = "BT"
    return chan_map[ncvar_name] + cal_name


def scene_to_xarray(fci_files, geoips_chans, metadata=None, area_def=None):
    """Load files into satpy.Scene object then convert to xarray.Dataset.

    Parameters
    ----------
    fci_files : list
        List of FCI netCDF files on disk
    geoips_chans : list
        Channels/variables denoted in GeoIPS nomenclature to load into memory, where
        'GeoIPS nomenclature' is the common variable mapping used in our geostationary
        readers. See 'BAND_MAP' variable for an example of these channels. Allows us
        to read in radiances, reflectances, or brightness temperatures even though the
        variable in the dataset itself (such as 'vis_04') does not provide that
        information.
    metadata : dict, optional
        Standard geoips attributes, by default None
    area_def : pyresample.AreaDefinition, optional
        Crop data to specific area definition, by default None

    Returns
    -------
    xarray.Dataset
        Calibrated FCI MTG data
    """
    scn = Scene(filenames=fci_files, reader="fci_l1c_nc")
    for gchan in geoips_chans:
        rchan = BAND_MAP.get(gchan)
        if rchan is None:
            # Most likely encountered a geolocation variable which will be computed
            # later
            continue
        if "Rad" in gchan:
            calibration = "radiance"
        elif "Ref" in gchan:
            calibration = "reflectance"
        elif "BT" in gchan:
            calibration = "brightness_temperature"
        else:
            # Star denotes the highest calibration, which is BT I think.
            calibration = "*"
        scn.load([rchan], calibration=calibration)
        # We might be deriving data from the same variable multiple times
        # I.e. B01Rad and B01Ref. Rename these data queries to the GeoIPS variable name
        # so we don't have conflicts.
        scn[gchan] = scn[rchan].copy(deep=True)
        # Delete the satpy named variable
        del scn[rchan]

    # Resample all variables in this scene to the finest resolution area definition
    # found. scn.resample() defaults to scn.finest_area()
    resampled_scn = scn.resample(resampler="native")
    LOG.interactive("Resampled scene to finest resolution.")
    if area_def:
        resampled_scn = resampled_scn.crop(area=area_def)

    xr = resampled_scn.to_xarray_dataset()
    lons, lats = resampled_scn.finest_area().get_lonlats()
    # if area_def:
    #     scn = scn.crop(area=area_def)

    # xr = scn.to_xarray_dataset()
    # lons, lats = scn.finest_area().get_lonlats()
    # Mask inf values with -999.9 for compatibility with get_geolocation func
    lons[np.isinf(lons)] = -999.9
    lats[np.isinf(lats)] = -999.9
    geo_meta = get_geolocation_metadata(xr.attrs)
    gvars = get_geolocation(xr.start_time, geo_meta, lats, lons, geo_meta["BADVALS"])
    xr["latitude"] = (("y", "x"), lats)
    xr["longitude"] = (("y", "x"), lons)
    LOG.debug("Added latitude/longitude to xarray dataset")
    for gkey, gvar in gvars.items():
        LOG.debug("Adding %s to xarray dataset", gkey)
        xr[gkey] = (("y", "x"), gvar)
    # Use a set here because gvars could include the same variables as geoips_chans
    # For example, we request satellite and solar zenith angle in our geoips_chans,
    # which is already included in gvars
    for dkey in set(geoips_chans + list(gvars)):
        # Flip data arrays upside down - otherwise image will be upside down in
        # unprojected output
        LOG.debug("Adding %s to xarray dataset", dkey)
        LOG.debug("Flipping data for %s", dkey)
        xr[dkey].data = np.flipud(xr[dkey].compute().data)
        # Convert from wavenumber to wavelength
        if dkey.endswith("Rad"):
            LOG.info("Converting wavenumber to wavelength")
            xr[dkey].data = xr[dkey].data * RADIANCE_CONVERSION_COEFFICIENTS[dkey]

    # Temporarily convert reflectances from % ranging from 0-100 to 0-1
    # This is required until gamma correction can handle reflecances from 0-100
    # This will happen when all readers return reflectance ranging from 0-100
    for dkey in list(xr.variables.keys()):
        if "Ref" in dkey:
            LOG.debug("Converting Ref range to 0-1")
            xr[dkey] /= 100
    # Add all standard GeoIPS attrs, if not already present
    if not metadata:
        metadata = get_standard_geoips_attrs(
            load_metadata_single_file(fci_files[0], group="data"), area_def
        )
        metadata["source_file_names"] = fci_files
    for smeta, sval in metadata.items():
        if smeta not in xr.attrs:
            xr.attrs[smeta] = sval
    return xr


def convert_radiance_to_bt(variable_dataset, line_inds=None, sample_inds=None):
    """Convert effective radiance to effective brightness tempearture.

    The effective brightness temperature of a surface is the temperature of a spatially
    uniform blackbody that emits the equivalent amount of radiant energy as the surface
    within a spectral band characterized by the spectral response function of the
    instrument. Given the band-average spectral radiance per wavenumber Lv, i.e. the
    effective radiance, the effective brightness temperature T_eff can be approximated
    as follows:

    T_eff = (c2 * vc)/(a * ln(1 + (c1 * vc**3) /Lv ) ) - b/a

    The set of coefficients {Vc, A, B}, corresponding to a given spectral response
    function, are found by regression over the required range of temperatures.
    Constants C1 = 2hc2 and C2 = hc/k are radiation constants where c, h, and k are the
    speed of light, Planck, and Boltzmann constant, respectively.

    The variable radiance_to_bt_conversion_coefficient_wavenumber contains the
    wavenumber corresponding to νc.

    The variables radiance_to_bt_conversion_coefficient_a and
    radiance_to_bt_conversion_coefficient_b contain the conversion coefficients a and b
    for IR channels, respectively. They are set to the _FillValue for VNIR channels.

    The variables radiance_to_bt_conversion_constant_c1
    and radiance_to_bt_conversion_constant_c2 contain the
    constants c1 and c2 for IR channels. Note that the values given in the dataset are
    c1=2·1011·hc2 =1.19104282E-05 and c2=100 hc/k=1.43877513 due to unit conversions.
    They are set to the _FillValue for visible and near-infrared channels.

    Parameters
    ----------
    variable_dataset : xarray.Dataset
        The data.<channel>.measured group dataset

    Returns
    -------
    array
        Calibrated brightness temperatures
    """
    LOG.info("Converting effective radiance to brightness temperature")
    a = np.mean(variable_dataset.radiance_to_bt_conversion_coefficient_a)
    b = np.mean(variable_dataset.radiance_to_bt_conversion_coefficient_b)
    c1 = np.mean(variable_dataset.radiance_to_bt_conversion_constant_c1)
    c2 = np.mean(variable_dataset.radiance_to_bt_conversion_constant_c2)
    vc = np.mean(variable_dataset.radiance_to_bt_conversion_coefficient_wavenumber)
    Lv = variable_dataset["effective_radiance"]
    if line_inds is not None:
        Lv = Lv[line_inds, sample_inds]
    t_eff = (c2 * vc) / (a * np.log(1 + (c1 * vc**3) / Lv)) - b / a
    return t_eff


def compute_sun_earth_distance(start_datetime, end_datetime):
    """Compute the sun_earth_distance."""
    middle_time_diff = (start_datetime - end_datetime).total_seconds() / 2
    utc_date = start_datetime + timedelta(seconds=middle_time_diff)
    sun_earth_distance = sun_earth_distance_correction(utc_date)
    LOG.debug(f"The value sun_earth_distance is set to {sun_earth_distance} AU.")
    return sun_earth_distance


def convert_radiance_to_reflectance(
    variable_dataset,
    dataset_name,
    start_datetime,
    end_datetime,
    solar_zenith_angle,
    line_inds=None,
    sample_inds=None,
    earth_sun_distance_km=None,
):
    """Convert radiance to reflectance.

    Parameters
    ----------
    variable_dataset : xarray.Dataset
        Dataset holding all variables from FCI group
    start_datetime : datetime.datetime
        Start time of data
    end_datetime : datetime.datetime
        End time of data

    Returns
    -------
    array
        Calibrated reflectances
    """
    LOG.info("Converting effective radiance to reflectance for %s", dataset_name)
    R = variable_dataset["effective_radiance"]
    # replace any negative radiances with lowest value according to offset and scale
    scaled_low = -R.attrs.get("add_offset", 0) // R.attrs.get("scale_factor", 1) + 1
    R = R.where((~R.notnull()) | (R >= scaled_low), scaled_low)
    # data should already be scaled, but keeping here for reference just in case
    # if dataset_name == "ir_38":
    #     R = xarray.where(
    #         ((2**12 - 1 < R) & (R <= 2**13 - 1)),
    #         (
    #             R * R.attrs.get("warm_scale_factor", 1)
    #             + R.attrs.get("warm_add_offset", 0)
    #         ),
    #         (R * R.attrs.get("scale_factor", 1) + R.attrs.get("add_offset", 0)),
    #     )
    # else:
    #     R = R * R.attrs.get("scale_factor", 1) + R.attrs.get("add_offset", 0)
    if earth_sun_distance_km is None:
        d_t = compute_sun_earth_distance(start_datetime, end_datetime)  # NOQA
    else:
        d_t = earth_sun_distance_km / 149597870.7  # NOQA
    Ir = np.nanmean(variable_dataset.channel_effective_solar_irradiance)  # NOQA
    if line_inds is not None:
        R = R[line_inds, sample_inds]
    brf = np.empty(shape=R.shape)
    pi = np.pi  # NOQA
    cos_sol_zen_ang = np.cos(np.deg2rad(solar_zenith_angle))  # NOQA
    ne.evaluate("(pi * R * d_t**2) / (Ir * cos_sol_zen_ang)", out=brf)
    brf_xarr = xarray.DataArray(
        brf,
        coords={"y": variable_dataset.coords["y"], "x": variable_dataset.coords["x"]},
    )
    # log(mean)/log(0.5) for mean rng 0 to 1
    gamma_correction = np.log(np.nanmean(brf)) / np.log(0.5)
    LOG.debug("Expected gamma correction value: %s", gamma_correction)
    return brf_xarr


def read_with_xarray(
    fci_files,
    geoips_chans,
    metadata=None,
    area_def=None,
    geolocation_cache_backend="zarr",
    chunk_size=None,
    precise_earth_sun_distance=True,
    resource_tracker=None,
):
    """Load files with xarray and calibrate.

    Parameters
    ----------
    fci_files : list
        List of FCI netCDF files on disk
    geoips_chans : list
        Channels/variables denoted in GeoIPS nomenclature to load into memory, where
        'GeoIPS nomenclature' is the common variable mapping used in our geostationary
        readers. See 'BAND_MAP' variable for an example of these channels. Allows us
        to read in radiances, reflectances, or brightness temperatures even though the
        variable in the dataset itself (such as 'vis_04') does not provide that
        information.
    metadata : dict, optional
        Standard geoips attributes, by default None
    area_def : pyresample.AreaDefinition, optional
        Crop data to specific area definition, by default None

    Returns
    -------
    xarray.Dataset
        Calibrated FCI MTG data
    """
    dset = xarray.Dataset()

    for gchan in geoips_chans:
        rchan = BAND_MAP.get(gchan)
        if rchan is None:
            # Most likely encountered a geolocation variable which will be computed
            # later
            continue
        if resource_tracker:
            key = f"READ CHAN: fci_netcdf_chan_{rchan}"
            if area_def:
                key += f"_{area_def.area_id}"
            resource_tracker.track_resource_usage(
                logstr="MEMUSG",
                verbose=False,
                key=key,
                show_log=False,
            )
        with xarray.open_mfdataset(fci_files, group=f"/data/{rchan}/measured") as df:
            if "latitude" not in dset:
                # Add num_lines and num_samples to metadata
                metadata["num_lines"] = df.y.size
                metadata["num_samples"] = df.x.size
                geolocation_metadata = get_geolocation_metadata(metadata)
                fldk_lats, fldk_lons = get_latitude_longitude(
                    geolocation_metadata,
                    df.x.data,
                    df.y.data,
                    BADVALS,
                    geolocation_cache_backend=geolocation_cache_backend,
                    chunk_size=chunk_size,
                    resource_tracker=resource_tracker,
                )
                gvars = get_geolocation(
                    metadata["start_datetime"],
                    geolocation_metadata,
                    fldk_lats,
                    fldk_lons,
                    BADVALS,
                    area_def,
                    geolocation_cache_backend=geolocation_cache_backend,
                    chunk_size=chunk_size,
                    resource_tracker=resource_tracker,
                )
                for gkey, gvar in gvars.items():
                    if gkey in ["Lines", "Samples"]:
                        continue
                    LOG.debug("Adding %s to xarray dataset", gkey)
                    dset[gkey] = (("y", "x"), gvar)
            if "Rad" in gchan:
                calibration_type = "Radiance"
                # Convert from wavenumber to wavelength
                eff_rad = df["effective_radiance"][...]
                if "Lines" in gvars and "Samples" in gvars:
                    eff_rad = eff_rad[gvars["Lines"], gvars["Samples"]]
                calibrated = eff_rad * RADIANCE_CONVERSION_COEFFICIENTS[gchan]
            elif "Ref" in gchan:
                calibration_type = "Reflectance"
                calibrated = convert_radiance_to_reflectance(
                    df,
                    dataset_name=rchan,
                    start_datetime=metadata["start_datetime"],
                    end_datetime=metadata["end_datetime"],
                    solar_zenith_angle=dset["solar_zenith_angle"],
                    line_inds=gvars.get("Lines"),
                    sample_inds=gvars.get("Samples"),
                )
            elif "BT" in gchan:
                calibration_type = "Brightness Temperature"
                calibrated = convert_radiance_to_bt(
                    df,
                    line_inds=gvars.get("Lines"),
                    sample_inds=gvars.get("Samples"),
                )
            else:
                raise ValueError(f"Unknown data type to calibrate: {gchan}")
        try:
            LOG.info("Masking data off disk")
            sat_zenith = gvars["satellite_zenith_angle"]
            masked = np.ma.array(calibrated, mask=sat_zenith.mask)
            calibrated.data = masked
        except KeyError:
            LOG.info("Did not find satellite zenith angle to mask for %s", gchan)
            pass

        LOG.info("Min %s: %s", calibration_type, float(np.nanmin(calibrated)))
        LOG.info("Max %s: %s", calibration_type, float(np.nanmax(calibrated)))
        LOG.debug("Adding %s to xarray dataset", gchan)
        dset[gchan] = calibrated
        if resource_tracker:
            resource_tracker.track_resource_usage(
                logstr="MEMUSG",
                verbose=False,
                key=key,
                show_log=False,
            )

    # Use a set here because gvars could include the same variables as geoips_chans
    # For example, we request satellite and solar zenith angle in our geoips_chans,
    # which is already included in gvars
    for dkey in set(geoips_chans + list(gvars)):
        # Flip data arrays upside down - otherwise image will be upside down in
        # unprojected output
        LOG.debug("Adding %s to xarray dataset", dkey)
        LOG.debug("Flipping data for %s", dkey)
        dset[dkey].data = np.flipud(dset[dkey].data)

    # Add all standard GeoIPS attrs, if not already present
    for smeta, sval in metadata.items():
        if smeta not in dset.attrs:
            dset.attrs[smeta] = sval
    return dset


def read_fci_netcdf_files(
    fci_files,
    metadata_only=False,
    chans=None,
    area_def=None,
    self_register=False,
    use_satpy=False,
    geolocation_cache_backend="zarr",
    cache_chunk_size=None,
    resource_tracker=None,
):
    """Read and calibrate data using satpy's fci_l1c_nc reader.

    Parameters
    ----------
    fci_files : list
        list of files for a given scan time
    metadata_only : bool, optional
        Only return metadata, by default False
    chans : list, optional
        List of channels/variables to load, by default None
    area_def : pyresample.AreaDefinition, optional
        Read in data for specific area definition, by default None
    self_register : bool, optional
        Self register data to given resolution, by default False
        (currently unsupported)

    Returns
    -------
    dict
        dictionary of xarray datasets
    """
    if area_def and self_register:
        raise ValueError(
            "sector_definition and self_register are mutually exclusive keywords"
        )
    avail_vars = avail_chans_in_file(fci_files[0])
    if not chans:
        chans = avail_vars
    ingested = {}
    for fci_file in fci_files:
        if "TRAIL" in fci_file:
            # Use the TRAIL file if possible to
            standard_meta = get_standard_geoips_attrs(
                load_metadata_single_file(fci_file, group="data"), area_def
            )
            break
    else:
        standard_meta = get_standard_geoips_attrs(
            load_metadata_single_file(fci_files[0], group="data"), area_def
        )
    standard_meta["source_file_names"] = fci_files
    if "METADATA" not in ingested:
        ingested["METADATA"] = xarray.Dataset(attrs=standard_meta)
    if metadata_only:
        return ingested
    # Add projection information to top-level metadata, only available in actual data
    # files.
    LOG.info("Getting projection information from %s", Path(fci_files[0]).name)
    with ncdf.Dataset(fci_files[0], "r") as ds:
        plat_group = ds["state/platform"]
        proj_group = ds["data/mtg_geos_projection"]
        for var in plat_group.variables:
            try:
                standard_meta[f"mean_{var}"] = np.mean(plat_group[var][:])
            except AttributeError:
                standard_meta[var] = plat_group[var][:]
        standard_meta["mtg_geos_projection"] = {
            x: proj_group.getncattr(x) for x in proj_group.ncattrs()
        }

    # Loading all chans with satpy will not maintain native resolution for each chan.
    # This is probably OK for now when self-registering (makes things easier as satpy
    # returns all data at the same size of the lowest available resolution)
    if self_register:
        adname = "FULL_DISK"
        if use_satpy:
            ingested[adname] = scene_to_xarray(fci_files, chans, metadata=standard_meta)
        else:
            ingested[adname] = read_with_xarray(
                fci_files,
                chans,
                metadata=standard_meta,
                geolocation_cache_backend=geolocation_cache_backend,
                chunk_size=cache_chunk_size,
            )
    # Otherwise read in chans with similar resolutions to maintain resolution
    else:
        for res, rchans in DATASET_INFO.items():
            # Find the indices of variables that correspond to the current resolution
            read_idxs = np.array([BAND_MAP.get(x, x) in rchans for x in chans])
            if not any(read_idxs) and not metadata_only:
                LOG.info("No channels to read at %s resolution", res)
                continue
            # Use those indices to retrieve the correct 'geoips' variables that we'll
            # need to read
            read_geoips_chans = list(np.array(chans)[read_idxs])
            LOG.info(
                "Reading in following chans: %s: %s", res, " ".join(read_geoips_chans)
            )
            # Ingest the returned xarray dataset to the current resolution of the
            # xarray_dictionary
            if use_satpy:
                ingested[res] = scene_to_xarray(
                    fci_files,
                    read_geoips_chans,
                    metadata=standard_meta,
                    area_def=area_def,
                )
            else:
                ingested[res] = read_with_xarray(
                    fci_files,
                    read_geoips_chans,
                    metadata=standard_meta,
                    area_def=area_def,
                    geolocation_cache_backend=geolocation_cache_backend,
                    chunk_size=cache_chunk_size,
                    resource_tracker=resource_tracker,
                )
    return ingested


def call(
    fnames,
    metadata_only=False,
    chans=None,
    area_def=None,
    self_register=False,
    use_satpy=False,
    geolocation_cache_backend="zarr",
    cache_chunk_size=None,
    resource_tracker=None,
):
    """Read and calibrate FCI data.

    Parameters
    ----------
    fci_files : list
        list of files for a given scan time
    metadata_only : bool, optional
        Only return metadata, by default False
    chans : list, optional
        List of channels/variables to load, by default None
    area_def : pyresample area definition, optional
        Read in data for specific area definition, by default None
        (currently unsupported)
    self_register : bool, optional
        Self register data to given resolution, by default False
        (currently unsupported)

    Returns
    -------
    dict
        dictionary of xarray datasets
    """
    if metadata_only:
        # If metadata_only is True, only pass one file to the reader. Otherwise the
        # readers.read_data_to_xarray_dict method will crack open every FCI file,
        # which more or less has the same metadata information - the only field that
        # changes to my knowledge is the start and end time. The TRAIL file has the
        # overall start and end time across the files, so use that if we can. Otherwise
        # take the first file in the list.
        trail_files = []
        for fci_file in fnames:
            if "TRAIL" in fci_file:
                trail_files.append(fci_file)
        if trail_files:
            fnames = trail_files
    fci_data = readers.read_data_to_xarray_dict(
        fnames,
        read_fci_netcdf_files,
        metadata_only,
        chans,
        area_def,
        self_register,
        use_satpy=use_satpy,
        geolocation_cache_backend=geolocation_cache_backend,
        cache_chunk_size=cache_chunk_size,
    )

    return fci_data
