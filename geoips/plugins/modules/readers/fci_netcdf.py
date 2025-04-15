# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Standard GeoIPS xarray dictionary based FCI NetCDF data reader."""

from datetime import datetime
import logging
import numpy as np
import xarray

from geoips.interfaces import readers
from geoips.plugins.modules.readers.utils.geostationary_geolocation import (
    get_geolocation,
)
from geoips.utils.context_managers import import_optional_dependencies

with import_optional_dependencies(loglevel="info"):
    """Attempt to import a package and print to LOG.info if the import fails."""
    from satpy.scene import Scene

    # Need to uncomment if HDF5_PLUGIN_PATH env variable is not set upstream,
    # though you will still not be able to interact with the data after using Scene.load
    # Until this works out of the box with out the need to set HDF5_PLUGIN_PATH
    # import hdf5plugin

LOG = logging.getLogger(__name__)

interface = "readers"
family = "standard"
name = "fci_netcdf"
source_names = ["fci"]

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


def get_geolocation_metadata(xarray_attrs):
    """Get geolocation metadata."""
    geomet = {}
    geomet["platform_name"] = xarray_attrs["platform_name"]
    geomet["source_name"] = xarray_attrs["sensor"]  # sensor == fci
    # Used for cached filenames
    geomet["scan_mode"] = xarray_attrs["area"].area_id
    geomet["scene"] = geomet["scan_mode"]
    geomet["lon0"] = xarray_attrs["orbital_parameters"]["satellite_nominal_longitude"]
    geomet["num_lines"] = xarray_attrs["area"].y_size
    geomet["num_samples"] = xarray_attrs["area"].x_size
    geomet["start_datetime"] = xarray_attrs["start_time"]
    geomet["end_datetime"] = xarray_attrs["end_time"]
    geomet["H_km"] = 42164
    geomet["H_m"] = geomet["H_km"] * 1000.0  # Satellite altitude (m)
    geomet["BADVALS"] = {"Off_Of_Disk": -999.9}
    return geomet


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
    # Time coverage start/end will differ across each individual granule that
    # comprises a full scan. So instead of setting the start/end datetime to the
    # time coverage start/end attr in the file metadata, use the date_time_position
    # attr, which is consistent across all files.
    # all_attrs["start_datetime"] = datetime.strptime(
    #     file_attrs["time_coverage_start"], "%Y%m%d%H%M%S"
    # )
    # all_attrs["end_datetime"] = datetime.strptime(
    #     file_attrs["time_coverage_end"], "%Y%m%d%H%M%S"
    # )
    all_attrs["start_datetime"] = date_time_position
    all_attrs["end_datetime"] = date_time_position
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
    all_meta_attrs = {}
    if not group:
        group = ""
    load_group = []
    for grp in group.split("/"):
        meta = xarray.open_dataset(fci_file, group="/".join(load_group)).attrs
        for key, val in meta.items():
            if key not in all_meta_attrs:
                all_meta_attrs[key] = val
        load_group.append(grp)
    if variable and variable in meta:
        for key, val in meta[variable].attrs:
            if key not in all_meta_attrs:
                all_meta_attrs[key] = val
    return all_meta_attrs


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
    meta = xarray.open_dataset(fci_file)
    return list(meta.l1c_channels_present.data)


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
        scn[gchan] = scn[rchan]
        # Delete the satpy named variable
        del scn[rchan]

    if area_def:
        scn = scn.crop(area=area_def)

    xr = scn.to_xarray_dataset()
    lons, lats = scn.finest_area().get_lonlats()
    # Mask inf values with -999.9 for compatibility with get_geolocation func
    lons[np.isinf(lons)] = -999.9
    lats[np.isinf(lats)] = -999.9
    geo_meta = get_geolocation_metadata(xr.attrs)
    gvars = get_geolocation(xr.start_time, geo_meta, lats, lons, geo_meta["BADVALS"])
    xr["latitude"] = (("y", "x"), lats)
    xr["longitude"] = (("y", "x"), lons)
    for gkey, gvar in gvars.items():
        xr[gkey] = (("y", "x"), gvar)
    # Use a set here because gvars could include the same variables as geoips_chans
    # For example, we request satellite and solar zenith angle in our geoips_chans,
    # which is already included in gvars
    for dkey in set(geoips_chans + list(gvars)):
        # Flip data arrays upside down - otherwise image will be upside down in
        # unprojected output
        LOG.debug("Flipping data for %s", dkey)
        xr[dkey].data = np.flipud(xr[dkey].compute().data)
        # Convert from wavenumber to wavelength
        if dkey.endswith("Rad"):
            xr[dkey].data = xr[dkey].data * RADIANCE_CONVERSION_COEFFICIENTS[dkey]

    # Temporarily convert reflectances from % ranging from 0-100 to 0-1
    # This is required until gamma correction can handle reflecances from 0-100
    # This will happen when all readers return reflectance ranging from 0-100
    for dkey in list(xr.variables.keys()):
        if "Ref" in dkey:
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


def satpy_read_fci_netcdf_files(
    fci_files,
    metadata_only=False,
    chans=None,
    area_def=None,
    self_register=False,
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
    standard_meta = get_standard_geoips_attrs(
        load_metadata_single_file(fci_files[0], group="data"), area_def
    )
    standard_meta["source_file_names"] = fci_files
    if "METADATA" not in ingested:
        ingested["METADATA"] = xarray.Dataset(attrs=standard_meta)
    if metadata_only:
        return ingested
    # Loading all chans with satpy will not maintain native resolution for each chan.
    # This is probably OK for now when self-registering (makes things easier as satpy
    # returns all data at the same size of the lowest available resolution)
    if self_register:
        adname = "FULL_DISK"
        ingested[adname] = scene_to_xarray(fci_files, chans, metadata=standard_meta)
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
            LOG.info("Reading in following chans: %s: %s", res, read_geoips_chans)
            # Ingest the returned xarray dataset to the current resolution of the
            # xarray_dictionary
            ingested[res] = scene_to_xarray(
                fci_files, read_geoips_chans, metadata=standard_meta, area_def=area_def
            )
    return ingested


def call(
    fnames,
    metadata_only=False,
    chans=None,
    area_def=None,
    self_register=False,
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
    fci_data = readers.read_data_to_xarray_dict(
        fnames,
        satpy_read_fci_netcdf_files,
        metadata_only,
        chans,
        area_def,
        self_register,
    )

    return fci_data
