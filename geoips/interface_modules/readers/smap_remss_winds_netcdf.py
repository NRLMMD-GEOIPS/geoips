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

"""Read derived surface winds from REMSS SMAP netcdf data."""
import logging
from os.path import basename

LOG = logging.getLogger(__name__)

MS_TO_KTS = 1.94384
DEG_TO_KM = 111.321

reader_type = "standard"


def smap_remss_winds_netcdf(
    fnames, metadata_only=False, chans=None, area_def=None, self_register=False
):
    """Read one of SMAP derived winds from netcdf data.

    All GeoIPS 2.0 readers read data into xarray Datasets - a separate
    dataset for each shape/resolution of data - and contain standard metadata information.

    Args:
        fnames (list): List of strings, full paths to files
        metadata_only (Optional[bool]):
            * DEFAULT False
            * return before actually reading data if True
        chans (Optional[list of str]):
            * NOT YET IMPLEMENTED
                * DEFAULT None (include all channels)
                * List of desired channels (skip unneeded variables as needed)
        area_def (Optional[pyresample.AreaDefinition]):
            * NOT YET IMPLEMENTED
                * DEFAULT None (read all data)
                * Specify region to read
        self_register (Optional[str]):
            * NOT YET IMPLEMENTED
                * DEFAULT False (read multiple resolutions of data)
                * register all data to the specified resolution.

    Returns:
        list of xarray.Datasets: list of xarray.Dataset objects with required
            Variables and Attributes: (See geoips/docs :doc:`xarray_standards`)
    """

    from geoips.xarray_utils.timestamp import (
        get_min_from_xarray_timestamp,
        get_max_from_xarray_timestamp,
    )
    import xarray

    # Only SAR reads multiple files
    fname = fnames[0]
    wind_xarray = xarray.open_dataset(str(fname))
    wind_xarray.attrs["source_name"] = "smap-spd"
    wind_xarray.attrs["platform_name"] = "smap"
    wind_xarray.attrs["data_provider"] = "rss"
    wind_xarray.attrs["original_source_filenames"] = [basename(fname)]
    wind_xarray.attrs["interpolation_radius_of_influence"] = 20000
    wind_xarray.attrs["sample_distance_km"] = DEG_TO_KM / 4
    wind_xarray.attrs["minimum_coverage"] = 20

    LOG.info("Read data from %s", fname)

    if (
        hasattr(wind_xarray, "institution")
        and "Remote Sensing Systems" in wind_xarray.institution
    ):
        if hasattr(wind_xarray, "title") and "SMAP" in wind_xarray.title:
            from .utils.remss_reader import read_remss_data

            wind_xarrays = read_remss_data(wind_xarray, "smap")

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
