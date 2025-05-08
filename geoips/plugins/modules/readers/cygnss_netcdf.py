# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Read derived surface winds from CYGNSS netcdf data."""

# Python Standard Libraries
import glob
import logging

# Third-Party Libraries
import xarray

# GeoIPS imports
from geoips.xarray_utils.time import get_min_from_xarray_time, get_max_from_xarray_time

LOG = logging.getLogger(__name__)

MS_TO_KTS = 1.94384
DEG_TO_KM = 111.321

interface = "readers"
family = "standard"
name = "cygnss_netcdf"


def call(fnames, metadata_only=False, chans=None, area_def=None, self_register=False):
    """Read CYGNSS derived winds from netcdf data.

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
    out_dict = {}

    # Single file is full day of data, so only need one.
    fname = fnames[0]

    wind_xarray = xarray.open_dataset(str(fname))
    wind_xarray = wind_xarray.rename(
        {"lat": "latitude", "lon": "longitude", "sample_time": "time"}
    )
    wind_xarray.attrs["source_name"] = "cygnss"
    wind_xarray.attrs["platform_name"] = "cygnss"
    wind_xarray.attrs["data_provider"] = "noaa-nesdis-star-socd-oswt"
    wind_xarray.attrs["source_file_names"] = fnames
    wind_xarray.attrs["interpolation_radius_of_influence"] = 20000
    wind_xarray.attrs["sample_distance_km"] = DEG_TO_KM / 4

    wind_xarray.attrs["start_datetime"] = get_min_from_xarray_time(wind_xarray, "time")
    wind_xarray.attrs["end_datetime"] = get_max_from_xarray_time(wind_xarray, "time")

    out_dict["METADATA"] = wind_xarray[[]]
    if metadata_only:
        return out_dict

    if chans:
        if "wind_speed_kts" in chans:
            wind_xarray["wind_speed_kts"] = wind_xarray["wind_speed"] * MS_TO_KTS
            wind_xarray["wind_speed_kts"].attrs["units"] = "kts"

    ds_var_list = list(wind_xarray.variables.keys())

    if chans:
        for chan in chans:
            if chan not in ds_var_list:
                raise ValueError(f"Variable {chan} not found in dataset.")

        wind_xarray = wind_xarray[chans]

    out_dict["CYGNSS"] = wind_xarray

    return out_dict


# Unit test functions
def get_test_files(test_data_dir):
    """
    Generate a testing xarray dataset from NetCDF files in the test data directory.

    Parameters
    ----------
    test_data_dir : str
        Path to the directory containing test data.

    Returns
    -------
    xarray.Dataset
        The dataset created from the NetCDF test files.

    Raises
    ------
    FileNotFoundError
        If no NetCDF files are found in the specified directory.
    """
    filepath = test_data_dir + "/test_data_cygnss/data/*.nc"
    filelist = glob.glob(filepath)
    if not filelist:
        raise FileNotFoundError("No files found")
    tmp_xr = call(filelist)
    return tmp_xr


def get_test_parameters():
    """Generate test data key for unit testing."""
    return [
        {"data_key": "CYGNSS", "data_var": "wind_speed", "mean": 7.0251474},
    ]
