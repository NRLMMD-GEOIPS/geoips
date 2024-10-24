# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Read derived surface winds from KNMI scatterometer netcdf data."""

# Python Standard Libraries
from copy import deepcopy
from glob import glob
import logging
from os.path import basename

# Third-Party Libraries
import numpy
import xarray

# GeoIPS imports
from geoips.xarray_utils.time import (
    get_min_from_xarray_time,
    get_max_from_xarray_time,
    fix_datetime,
)

LOG = logging.getLogger(__name__)

MS_TO_KTS = 1.94384
DEG_TO_KM = 111.321

interface = "readers"
family = "standard"
name = "scat_knmi_winds_netcdf"
source_names = ["ascat", "oscat", "hscat"]


def read_knmi_data(wind_xarray):
    """Reformat ascat xarray object appropriately.

    * variables: latitude, longitude, time,
      wind_speed_kts, wind_dir_deg_met
    * attributes: source_name, platform_name, data_provider,
      interpolation_radius_of_influence
    """
    geoips_metadata = {}
    geoips_metadata["data_provider"] = "knmi"
    # Setting standard geoips attributes
    LOG.info("Reading %s data", wind_xarray.source)
    if wind_xarray.source == "MetOp-C ASCAT":
        geoips_metadata["source_name"] = "ascat"
        geoips_metadata["platform_name"] = "metop-c"
    elif wind_xarray.source == "MetOp-B ASCAT":
        geoips_metadata["source_name"] = "ascat"
        geoips_metadata["platform_name"] = "metop-b"
    elif wind_xarray.source == "MetOp-A ASCAT":
        geoips_metadata["source_name"] = "ascat"
        geoips_metadata["platform_name"] = "metop-a"
    elif wind_xarray.source == "ScatSat-1 OSCAT":
        geoips_metadata["source_name"] = "oscat"
        geoips_metadata["platform_name"] = "scatsat-1"
    elif wind_xarray.source == "Oceansat-3 OSCAT":
        geoips_metadata["source_name"] = "oscat"
        geoips_metadata["platform_name"] = "oceansat-3"
    elif wind_xarray.source == "HY-2D HSCAT":
        geoips_metadata["source_name"] = "hscat"
        geoips_metadata["platform_name"] = "hy-2d"
        # geoips_metadata['data_provider'] = 'Copyright-2021-EUMETSAT'
    elif wind_xarray.source == "HY-2C HSCAT":
        geoips_metadata["source_name"] = "hscat"
        geoips_metadata["platform_name"] = "hy-2c"
        # geoips_metadata['data_provider'] = 'Copyright-2021-EUMETSAT'
    elif wind_xarray.source == "HY-2B HSCAT":
        geoips_metadata["source_name"] = "hscat"
        geoips_metadata["platform_name"] = "hy-2b"
        # geoips_metadata['data_provider'] = 'Copyright-2021-EUMETSAT'

    # Pixel size stored as "25.0 km"
    pixel_size = float(wind_xarray.pixel_size_on_horizontal.replace(" km", ""))

    # Interpolation Radius of Influence
    geoips_metadata["interpolation_radius_of_influence"] = pixel_size * 1000.0

    geoips_metadata["sample_distance_km"] = pixel_size

    # setting wind_speed_kts appropriately
    wind_xarray["wind_speed_kts"] = wind_xarray["wind_speed"] * MS_TO_KTS
    wind_xarray["wind_speed_kts"].attrs = wind_xarray["wind_speed"].attrs
    wind_xarray["wind_speed_kts"].attrs["units"] = "kts"

    # Directions in netcdf file use oceanography conventions
    wind_xarray["wind_dir_deg_met"] = wind_xarray["wind_dir"] - 180
    wind_xarray["wind_dir_deg_met"].attrs = wind_xarray["wind_dir"].attrs
    wind_xarray["wind_dir_deg_met"] = wind_xarray["wind_dir_deg_met"].where(
        wind_xarray["wind_dir_deg_met"] >= 0, wind_xarray["wind_dir_deg_met"] + 360
    )
    wind_xarray.wind_dir_deg_met.attrs["standard_name"] = "wind_from_direction"
    wind_xarray.wind_dir_deg_met.attrs["valid_max"] = 360

    # Set lat/lons/time appropriately
    wind_xarray = wind_xarray.rename(
        {"lat": "latitude", "lon": "longitude", "time": "time"}
    )

    RAIN_FLAG_BIT = 9
    if hasattr(xarray, "ufuncs"):
        # ufuncs no longer available as of xarray v2022.06 (at least)
        wind_xarray["rain_flag"] = xarray.ufuncs.logical_and(
            wind_xarray["wvc_quality_flag"], (1 << RAIN_FLAG_BIT)
        )
    else:
        # Can not figure out how to do the logical and in xarray now -
        # so do it in numpy.
        # This may not be the most efficient, especially if we are trying to use
        # dask / lazy processing.
        # Dropping the ".to_masked_array()" appears to lose the nan values -
        # but could perhaps do that then re-mask?
        rf = numpy.logical_and(
            wind_xarray["wvc_quality_flag"].to_masked_array(), (1 << RAIN_FLAG_BIT)
        )
        wind_xarray["rain_flag"] = xarray.DataArray(
            rf.astype(int), coords=wind_xarray.coords, dims=wind_xarray.dims
        )

    wind_xarray = wind_xarray.set_coords(["time"])
    return wind_xarray, geoips_metadata


def call(fnames, metadata_only=False, chans=None, area_def=None, self_register=False):
    """Read KNMI scatterometer derived winds from netcdf data.

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
    final_wind_xarrays = {}
    ingested = []
    for fname in fnames:
        try:
            wind_xarray = xarray.open_dataset(str(fname))
        except ValueError:
            # <=2023.08 versions of xarray would filter bad dates
            # current versions >=2023.9 raise Value Errors now
            # Note: This is important for oscat, but not for any other sensors.
            # This persists in versions as new as 2024.02.0 and I don't expect
            # that it will be "fixed" because oscat's times are non-conforming
            # with the CF standard.
            wind_xarray = xarray.open_dataset(str(fname), decode_times=False)
            # filters out negative dates, converting them to NaT
            wind_xarray = fix_datetime(wind_xarray)

        LOG.info("Read data from %s", fname)

        if (
            hasattr(wind_xarray, "title_short_name")
            and "ASCAT" in wind_xarray.title_short_name
        ):
            wind_xarray, geoips_metadata = read_knmi_data(wind_xarray)

        if (
            hasattr(wind_xarray, "title_short_name")
            and "OSCAT" in wind_xarray.title_short_name
        ):
            wind_xarray, geoips_metadata = read_knmi_data(wind_xarray)

        if (
            hasattr(wind_xarray, "title_short_name")
            and "HSCAT" in wind_xarray.title_short_name
        ):
            wind_xarray, geoips_metadata = read_knmi_data(wind_xarray)

        geoips_metadata["source_file_names"] = [basename(fname)]
        geoips_metadata["minimum_coverage"] = 20
        ingested += [(wind_xarray, geoips_metadata)]

    for curr_xobj, curr_geoips_metadata in ingested:
        curr_file_metadata = deepcopy(curr_xobj.attrs)
        curr_xobj.attrs = {**curr_file_metadata, **curr_geoips_metadata}

        if "WINDSPEED" not in final_wind_xarrays:
            final_xobj = curr_xobj.copy()
            final_xobj.attrs = curr_geoips_metadata
            final_xobj.attrs["source_file_attributes"] = [curr_file_metadata]
            final_xobj.attrs["source_file_names"] = curr_geoips_metadata[
                "source_file_names"
            ].copy()
            final_wind_xarrays["WINDSPEED"] = final_xobj
            continue

        final_xobj = final_wind_xarrays["WINDSPEED"]

        for attr_name in ["source_name", "platform_name"]:
            if final_xobj.attrs[attr_name] != curr_xobj.attrs[attr_name]:
                raise ValueError(
                    f"Attribute '{attr_name}' must match on all data files"
                    f"Expected '{final_xobj.attrs[attr_name]}',"
                    f"Current value '{curr_xobj.attrs[attr_name]}'"
                )
        final_xobj = xarray.concat([final_xobj, curr_xobj], dim="NUMROWS")
        final_xobj.attrs["source_file_names"] += curr_geoips_metadata[
            "source_file_names"
        ]
        final_xobj.attrs["source_file_attributes"] += [curr_file_metadata]
        final_wind_xarrays["WINDSPEED"] = final_xobj

    for wind_xarray in final_wind_xarrays.values():
        LOG.info("Setting standard metadata")
        wind_xarray.attrs["start_datetime"] = get_min_from_xarray_time(
            wind_xarray, "time"
        )
        wind_xarray.attrs["end_datetime"] = get_max_from_xarray_time(
            wind_xarray, "time"
        )

        if "wind_speed_kts" in wind_xarray.variables:
            # These text files store wind speeds natively in kts
            wind_xarray["wind_speed_kts"].attrs["units"] = "kts"

        LOG.info(
            "Read data %s start_dt %s source %s platform %s data_provider %s roi "
            "%s native resolution",
            wind_xarray.attrs["start_datetime"],
            wind_xarray.attrs["source_name"],
            wind_xarray.attrs["platform_name"],
            wind_xarray.attrs["data_provider"],
            wind_xarray.attrs["interpolation_radius_of_influence"],
            wind_xarray.attrs["sample_distance_km"],
        )

    final_wind_xarrays["METADATA"] = wind_xarray[[]]

    return final_wind_xarrays


def get_test_files(test_data_dir):
    """Generate test xarray from test data for unit testing."""
    filepath = test_data_dir + "/test_data_scat/data/metopc*knmi*/*coa*.nc"
    filelist = glob(filepath)
    tmp_xr = call(filelist)
    if len(filelist) == 0:
        raise NameError("No files found")
    return tmp_xr


def get_test_parameters():
    """Generate test data key for unit testing."""
    return [{"data_key": "WINDSPEED", "data_var": "wind_speed_kts"}]
