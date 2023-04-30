# # # Distribution Statement A. Approved for public release. Distribution unlimited.
# # #
# # # Author:
# # # Naval Research Laboratory, Marine Meteorology Division
# # #
# # # This program is free software: you can redistribute it and/or modify it under
# # # the terms of the NRLMMD License included with this program. This program is
# # # distributed WITHOUT ANY WARRANTY; without even the implied warranty of
# # # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the included license
# # # for more details. If you did not receive the license, for more information see:
# # # https://github.com/U-S-NRL-Marine-Meteorology-Division/

"""Read derived surface winds from KNMI scatterometer netcdf data."""
import logging
from os.path import basename

LOG = logging.getLogger(__name__)

MS_TO_KTS = 1.94384
DEG_TO_KM = 111.321

interface = "readers"
family = "standard"
name = "scat_knmi_winds_netcdf"


def read_knmi_data(wind_xarray):
    """Reformat ascat xarray object appropriately.

    * variables: latitude, longitude, timestamp,
      wind_speed_kts, wind_dir_deg_met
    * attributes: source_name, platform_name, data_provider,
      interpolation_radius_of_influence
    """
    wind_xarray.attrs["data_provider"] = "knmi"
    # Setting standard geoips attributes
    LOG.info("Reading %s data", wind_xarray.source)
    if wind_xarray.source == "MetOp-C ASCAT":
        wind_xarray.attrs["source_name"] = "ascat"
        wind_xarray.attrs["platform_name"] = "metop-c"
    elif wind_xarray.source == "MetOp-B ASCAT":
        wind_xarray.attrs["source_name"] = "ascat"
        wind_xarray.attrs["platform_name"] = "metop-b"
    elif wind_xarray.source == "MetOp-A ASCAT":
        wind_xarray.attrs["source_name"] = "ascat"
        wind_xarray.attrs["platform_name"] = "metop-a"
    elif wind_xarray.source == "ScatSat-1 OSCAT":
        wind_xarray.attrs["source_name"] = "oscat"
        wind_xarray.attrs["platform_name"] = "scatsat-1"
    elif wind_xarray.source == "HY-2C HSCAT":
        wind_xarray.attrs["source_name"] = "hscat"
        wind_xarray.attrs["platform_name"] = "hy-2c"
        # wind_xarray.attrs['data_provider'] = 'Copyright-2021-EUMETSAT'
    elif wind_xarray.source == "HY-2B HSCAT":
        wind_xarray.attrs["source_name"] = "hscat"
        wind_xarray.attrs["platform_name"] = "hy-2b"
        # wind_xarray.attrs['data_provider'] = 'Copyright-2021-EUMETSAT'

    # Pixel size stored as "25.0 km"
    pixel_size = float(wind_xarray.pixel_size_on_horizontal.replace(" km", ""))

    # Interpolation Radius of Influence
    wind_xarray.attrs["interpolation_radius_of_influence"] = pixel_size * 1000.0

    wind_xarray.attrs["sample_distance_km"] = pixel_size

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

    # Set lat/lons/timestamp appropriately
    wind_xarray = wind_xarray.rename(
        {"lat": "latitude", "lon": "longitude", "time": "timestamp"}
    )
    import xarray
    import numpy

    RAIN_FLAG_BIT = 9
    if hasattr(xarray, "ufuncs"):
        # ufuncs no longer available as of xarray v2022.06 (at least)
        wind_xarray["rain_flag"] = xarray.ufuncs.logical_and(
            wind_xarray["wvc_quality_flag"], (1 << RAIN_FLAG_BIT)
        )
    else:
        # Can not figure out how to do the logical and in xarray now - so do it in numpy.
        # This may not be the most efficient, especially if we are trying to use dask / lazy processing
        # Dropping the ".to_masked_array()" appears to lose the nan values - but could perhaps do that
        # then re-mask?
        rf = numpy.logical_and(
            wind_xarray["wvc_quality_flag"].to_masked_array(), (1 << RAIN_FLAG_BIT)
        )
        wind_xarray["rain_flag"] = xarray.DataArray(
            rf.astype(int), coords=wind_xarray.coords, dims=wind_xarray.dims
        )

    wind_xarray = wind_xarray.set_coords(["timestamp"])
    return {"WINDSPEED": wind_xarray}


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
    from geoips.xarray_utils.timestamp import (
        get_min_from_xarray_timestamp,
        get_max_from_xarray_timestamp,
    )
    import xarray

    # Only SAR reads multiple files
    fname = fnames[0]
    wind_xarray = xarray.open_dataset(str(fname))

    wind_xarray.attrs["source_name"] = "unknown"
    wind_xarray.attrs["platform_name"] = "unknown"
    wind_xarray.attrs["interpolation_radius_of_influence"] = "unknown"
    wind_xarray.attrs["sample_distance_km"] = "unknown"

    wind_xarray.attrs["original_source_filenames"] = [basename(fname)]
    wind_xarray.attrs["minimum_coverage"] = 20

    LOG.info("Read data from %s", fname)

    if (
        hasattr(wind_xarray, "title_short_name")
        and "ASCAT" in wind_xarray.title_short_name
    ):
        wind_xarrays = read_knmi_data(wind_xarray)

    if (
        hasattr(wind_xarray, "title_short_name")
        and "OSCAT" in wind_xarray.title_short_name
    ):
        wind_xarrays = read_knmi_data(wind_xarray)

    if (
        hasattr(wind_xarray, "title_short_name")
        and "HSCAT" in wind_xarray.title_short_name
    ):
        wind_xarrays = read_knmi_data(wind_xarray)

    for wind_xarray in wind_xarrays.values():
        LOG.info("Setting standard metadata")
        wind_xarray.attrs["start_datetime"] = get_min_from_xarray_timestamp(
            wind_xarray, "timestamp"
        )
        wind_xarray.attrs["end_datetime"] = get_max_from_xarray_timestamp(
            wind_xarray, "timestamp"
        )

        if "wind_speed_kts" in wind_xarray.variables:
            # These text files store wind speeds natively in kts
            wind_xarray["wind_speed_kts"].attrs["units"] = "kts"

        LOG.info(
            "Read data %s start_dt %s source %s platform %s data_provider %s roi %s native resolution",
            wind_xarray.attrs["start_datetime"],
            wind_xarray.attrs["source_name"],
            wind_xarray.attrs["platform_name"],
            wind_xarray.attrs["data_provider"],
            wind_xarray.attrs["interpolation_radius_of_influence"],
            wind_xarray.attrs["sample_distance_km"],
        )

    wind_xarrays["METADATA"] = wind_xarray[[]]

    return wind_xarrays
