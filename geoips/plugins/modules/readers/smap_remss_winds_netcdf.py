# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Read derived surface winds from REMSS SMAP netcdf data."""

# Python Standard Libraries
from glob import glob
import logging
from os.path import basename

# Third-Party Libraries
import xarray

# GeoIPS imports
from geoips.plugins.modules.readers.utils.remss_reader import (
    read_remss_data,
)

from geoips.xarray_utils.time import (
    get_min_from_xarray_time,
    get_max_from_xarray_time,
)

LOG = logging.getLogger(__name__)

MS_TO_KTS = 1.94384
DEG_TO_KM = 111.321

interface = "readers"
family = "standard"
name = "smap_remss_winds_netcdf"
source_names = ["smap-spd"]


def call(fnames, metadata_only=False, chans=None, area_def=None, self_register=False):
    """Read one of SMAP derived winds from netcdf data.

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
    # Only SAR reads multiple files
    fname = fnames[0]
    wind_xarray = xarray.open_dataset(str(fname))
    wind_xarray.attrs["source_name"] = "smap-spd"
    wind_xarray.attrs["platform_name"] = "smap"
    wind_xarray.attrs["data_provider"] = "rss"
    wind_xarray.attrs["source_file_names"] = [basename(fname)]
    wind_xarray.attrs["interpolation_radius_of_influence"] = 20000
    wind_xarray.attrs["sample_distance_km"] = DEG_TO_KM / 4
    wind_xarray.attrs["minimum_coverage"] = 20

    LOG.info("Read data from %s", fname)

    if (
        hasattr(wind_xarray, "institution")
        and "Remote Sensing Systems" in wind_xarray.institution
    ):
        if hasattr(wind_xarray, "title") and "SMAP" in wind_xarray.title:
            wind_xarrays = read_remss_data(wind_xarray, "smap")

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
            "Read data %s start_dt %s source %s platform %s data_provider %s roi "
            "%s native resolution",
            wind_xarray.attrs["start_datetime"],
            wind_xarray.attrs["source_name"],
            wind_xarray.attrs["platform_name"],
            wind_xarray.attrs["data_provider"],
            wind_xarray.attrs["interpolation_radius_of_influence"],
            wind_xarray.attrs["sample_distance_km"],
        )

    wind_xarrays["METADATA"] = wind_xarray[[]]

    return wind_xarrays


def get_test_files(test_data_dir):
    """Generate test xarray from test files for unit testing."""
    filepath = test_data_dir + "/test_data_smap/data/*.nc"
    filelist = glob(filepath)
    tmp_xr = call(filelist)
    if len(filelist) == 0:
        raise NameError("No files found")
    return tmp_xr


def get_test_parameters():
    """Generate test data key for unit testing."""
    return [{"data_key": "WINDSPEED_1", "data_var": "wind_speed_kts"}]
