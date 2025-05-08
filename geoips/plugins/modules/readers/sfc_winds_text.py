# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Read derived surface winds from SAR, SMAP, SMOS, and AMSR text data."""

# Python Standard Libraries
import logging

# Third-Party Libraries
import numpy
import pandas

LOG = logging.getLogger(__name__)

MS_TO_KTS = 1.94384

interface = "readers"
family = "standard"
name = "sfc_winds_text"
source_names = ["sar-spd", "smap-spd", "smos-spd", "amsr2"]


def call(fnames, metadata_only=False, chans=None, area_def=None, self_register=False):
    """Read one of SAR, SMAP, SMOS, AMSR derived winds from text data.

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
    if len(fnames) > 1:
        raise ValueError(
            "Multiple files not supported with this reader. "
            "Please call with a single file."
        )
    fname = fnames[0]

    LOG.info("Reading file %s", fname)
    data = numpy.loadtxt(fname, dtype=str, skiprows=0)

    if data[0][0] == "SAR":
        source_name = "sar-spd"
        platform_name = "sentinel-1"
        interpolation_roi = 3000
        data_provider = "star"
    elif data[0][0] == "SMAP":
        source_name = "smap-spd"
        platform_name = "smap"
        interpolation_roi = 15000
        data_provider = "rss"
    elif data[0][0] == "SMOS":
        source_name = "smos-spd"
        platform_name = "smos"
        interpolation_roi = 25000
        data_provider = "esa"
    elif data[0][0] == "AMSR":
        source_name = "amsr2"
        platform_name = "gcom-w1"
        interpolation_roi = 10000
        data_provider = "star"

    LOG.info("Making full dataframe")
    # make a data frame
    columns = ["dataType", "latitude", "longitude", "wind_speed_kts", "time"]
    wind_xarray = pandas.DataFrame(data=data, columns=columns)

    LOG.info("Converting lat to numeric")
    # make appropriate data types
    wind_xarray["longitude"] = pandas.to_numeric(
        wind_xarray["longitude"], errors="coerce"
    )
    LOG.info("Converting lon to numeric")
    wind_xarray["latitude"] = pandas.to_numeric(
        wind_xarray["latitude"], errors="coerce"
    )
    LOG.info("Converting windspeed to numeric")
    wind_xarray["wind_speed_kts"] = pandas.to_numeric(
        wind_xarray["wind_speed_kts"], errors="coerce"
    )
    LOG.info("Converting to time to datetime")

    # This is ORDERS OF MAGNITUDE slower than giving the format directly.
    # Seconds vs minutes
    # wind_xarray['time'] = pandas.to_datetime(wind_xarray['time'],
    #                                               infer_datetime_format=True,
    #                                               errors='coerce')
    wind_xarray["time"] = pandas.to_datetime(
        wind_xarray["time"], format="%Y%m%d%H%M", errors="coerce"
    )

    wind_xarray = wind_xarray.to_xarray()

    wind_xarray.attrs["source_name"] = source_name
    wind_xarray.attrs["platform_name"] = platform_name
    wind_xarray.attrs["start_datetime"] = (
        wind_xarray.to_dataframe()["time"].min().to_pydatetime()
    )
    wind_xarray.attrs["end_datetime"] = (
        wind_xarray.to_dataframe()["time"].max().to_pydatetime()
    )
    wind_xarray.attrs["data_provider"] = data_provider
    # 20000 leaves gaps
    wind_xarray.attrs["interpolation_radius_of_influence"] = interpolation_roi

    # These text files store wind speeds natively in kts
    wind_xarray["wind_speed_kts"].attrs["units"] = "kts"
    wind_xarray["longitude"].attrs["units"] = "degrees"
    wind_xarray["latitude"].attrs["units"] = "degrees"

    return {"WIND": wind_xarray, "METADATA": wind_xarray[[]]}
