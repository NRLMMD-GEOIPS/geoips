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

"""Read derived surface winds from REMSS AMSR netcdf data."""

import logging
from os.path import basename

LOG = logging.getLogger(__name__)

MS_TO_KTS = 1.94384
DEG_TO_KM = 111.321

interface = "readers"
family = "standard"
name = "amsr2_remss_winds_netcdf"


def call(fnames, metadata_only=False, chans=None, area_def=None, self_register=False):
    """Read REMSS AMSR2 derived winds from netcdf data.

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
    from geoips.xarray_utils.time import (
        get_min_from_xarray_time,
        get_max_from_xarray_time,
    )
    import xarray

    # Only SAR reads multiple files
    fname = fnames[0]
    wind_xarray = xarray.open_dataset(str(fname))
    wind_xarray.attrs["source_file_names"] = [basename(fname)]
    wind_xarray.attrs["interpolation_radius_of_influence"] = 20000
    wind_xarray.attrs["sample_distance_km"] = DEG_TO_KM / 4
    wind_xarray.attrs["source_name"] = "amsr2rss"
    wind_xarray.attrs["platform_name"] = "gcom-w1"
    wind_xarray.attrs["data_provider"] = "rss"
    wind_xarray.attrs["minimum_coverage"] = 10

    LOG.info("Read data from %s", fname)

    if (
        hasattr(wind_xarray, "institution")
        and "Remote Sensing Systems" in wind_xarray.institution
    ):
        if hasattr(wind_xarray, "title") and "AMSR2" in wind_xarray.title:
            from .utils.remss_reader import read_remss_data

            wind_xarrays = read_remss_data(wind_xarray, "amsr2")

    for wind_xarray in wind_xarrays.values():
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
            "Read data %s start_dt %s source %s platform %s data_provider %s "
            "roi %s native resolution",
            wind_xarray.attrs["start_datetime"],
            wind_xarray.attrs["source_name"],
            wind_xarray.attrs["platform_name"],
            wind_xarray.attrs["data_provider"],
            wind_xarray.attrs["interpolation_radius_of_influence"],
            wind_xarray.attrs["sample_distance_km"],
        )

    wind_xarrays["METADATA"] = wind_xarray[[]]

    return wind_xarrays
