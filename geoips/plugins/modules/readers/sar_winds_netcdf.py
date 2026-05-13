# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Read derived surface winds from SAR netcdf data."""

# Python Standard Libraries
from datetime import datetime
import logging
from os.path import basename

# Third-Party Libraries
import numpy
import xarray

# GeoIPS imports
from geoips.xarray_utils.time import (
    get_min_from_xarray_time,
    get_max_from_xarray_time,
)

LOG = logging.getLogger(__name__)

MS_TO_KTS = 1.94384
DEG_TO_KM = 111.321

interface = "readers"
family = "standard"
name = "sar_winds_netcdf"
source_names = ["sar-spd"]


def read_sar_data(wind_xarray):
    """Reformat SAR xarray object appropriately.

    * variables: latitude, longitude, time, wind_speed_kts
    * attributes: source_name, platform_name, data_provider,
      interpolation_radius_of_influence
    """
    # Setting standard geoips attributes
    LOG.info("Reading SAR data")
    wind_xarray.attrs["source_name"] = "sar-spd"

    rcm_attribution_short = "CSA-NOAA/NESDIS/STAR/SOCD"
    rcm_attribution = [
        "RADARSAT Constellation Mission Imagery Copyright Government of Canada 2025",
        "RADARSAT is an official mark of the Canadian Space Agency",
        "Data pre-processed by NOAA/NESDIS/STAR/SOCD",
    ]

    sentinel_attribution_short = "ESA-NOAA/NESDIS/STAR/SOCD"
    sentinel_attribution = [
        "Contains modified Copernicus Sentinel data",
        "Data pre-processed by NOAA/NESDIS/STAR/SOCD",
    ]

    if (
        "platform" in wind_xarray.attrs
        and wind_xarray.platform.lower() == "sentinel-1a"
    ):
        wind_xarray.attrs["platform_name"] = "sentinel-1"
        data_provider = "esa-star"
        data_attribution_title = sentinel_attribution
        data_attribution_short = sentinel_attribution_short

    elif "platform" in wind_xarray.attrs and wind_xarray.platform.lower() == "rcm-1":
        wind_xarray.attrs["platform_name"] = "rcm-1"
        data_provider = "csa-star"
        data_attribution_title = rcm_attribution
        data_attribution_short = rcm_attribution_short

    elif "platform" in wind_xarray.attrs and wind_xarray.platform.lower() == "rcm-2":
        wind_xarray.attrs["platform_name"] = "rcm-2"
        data_provider = "csa-star"
        data_attribution_title = rcm_attribution
        data_attribution_short = rcm_attribution_short

    elif "platform" in wind_xarray.attrs and wind_xarray.platform.lower() == "rcm-3":
        wind_xarray.attrs["platform_name"] = "rcm-3"
        data_provider = "csa-star"
        data_attribution_title = rcm_attribution
        data_attribution_short = rcm_attribution_short

    elif (
        "platform" in wind_xarray.attrs and wind_xarray.platform.lower() == "radarsat-2"
    ):
        wind_xarray.attrs["platform_name"] = "radarsat-2"
        data_provider = "csa-star"
        data_attribution_title = rcm_attribution
        data_attribution_short = rcm_attribution_short

    else:
        raise ValueError(
            f"Unsupported satellite name for SAR data: {wind_xarray.platform}"
        )

    wind_xarray.attrs["data_attribution"] = {
        "short": data_attribution_short,
        "title": data_attribution_title,
        "long": " ".join(data_attribution_title),
    }
    wind_xarray.attrs["data_provider"] = data_provider

    wind_xarray.attrs["interpolation_radius_of_influence"] = 3000
    # For resampling to a minimum-sized grid
    wind_xarray.attrs["sample_distance_km"] = 3.0
    wind_xarray.attrs["sample_pixels_x"] = 300
    wind_xarray.attrs["sample_pixels_y"] = 300
    wind_xarray.attrs["minimum_coverage"] = 0
    wind_xarray.attrs["granule_minutes"] = 0.42
    # if "acknowledgment" in wind_xarray.attrs and "NOAA" in wind_xarray.acknowledgment:
    #     wind_xarray.attrs["data_provider"] = "star"
    # Used for tc filenames / text files

    LOG.info("Shape: %s", wind_xarray["sar_wind"].shape)
    # setting wind_speed_kts appropriately
    wind_xarray["wind_speed_kts"] = wind_xarray["sar_wind"] * MS_TO_KTS
    wind_xarray["wind_speed_kts"].attrs = wind_xarray["sar_wind"].attrs
    wind_xarray["wind_speed_kts"].attrs["units"] = "kts"
    wind_xarray["wind_speed_kts"] = xarray.where(
        wind_xarray.mask == -1, wind_xarray.wind_speed_kts, numpy.nan
    )

    # Set lat/lons appropriately
    wind_xarray = wind_xarray.rename({"latitude": "latitude", "longitude": "longitude"})

    # Set time appropriately
    # Get the full array of times.  pandas is much better with time series.
    wind_pandas = wind_xarray.to_dataframe()

    # This worked with xarray version 0.16.1
    # wind_xarray['time'] = wind_pandas['acquisition_time'][:, 5, :].to_xarray()
    #                                                                       .transpose()

    # Make sure it grabs the right ones, no matter which order x, y, and xfit are in.
    # Later versions (0.18.0) of xarray can have different orders -
    # ensure we use labels, not explicit locations
    time_array = (
        wind_pandas["acquisition_time"]
        .to_xarray()[dict(x=slice(None), y=slice(None), xfit=5)]
        .transpose("y", "x")
    )
    # Remove the xfit coordinate - no longer needed
    wind_xarray["time"] = time_array.reset_coords("xfit", drop=True)

    wind_xarray = wind_xarray.set_coords(["time"])
    wind_xarray["sigma"] = xarray.where(
        wind_xarray.sigma == 0, numpy.nan, wind_xarray.sigma
    )
    # This is not correct - should be -35 to -20, need to find documentation
    # for deriving NRCS from sigma
    wind_xarray["nrcs"] = 10 * numpy.log10(wind_xarray.sigma)
    wind_xarray["incident_angle"] = wind_xarray["incid"]
    return [wind_xarray]


def call(fnames, metadata_only=False, chans=None, area_def=None, self_register=False):
    """Read SAR derived winds from netcdf data.

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
    wind_xarray.attrs["data_provider"] = "unknown"
    wind_xarray.attrs["source_name"] = "unknown"
    wind_xarray.attrs["platform_name"] = "unknown"
    wind_xarray.attrs["interpolation_radius_of_influence"] = "unknown"
    wind_xarray.attrs["source_file_names"] = [basename(fname)]
    wind_xarray.attrs["sample_distance_km"] = "unknown"

    LOG.info("Read data from %s", fname)

    if (
        hasattr(wind_xarray, "source")
        and ("SAR" in wind_xarray.source or "SAR" in wind_xarray.title)
        and hasattr(wind_xarray, "title")
    ):
        wind_xarrays = []
        columns = None
        for fname in fnames:
            LOG.info("    Reading file %s", fname)
            wind_xarray = xarray.open_dataset(str(fname))
            LOG.info(
                "        rows: %s, columns: %s", wind_xarray.rows, wind_xarray.columns
            )
            if columns is None:
                columns = wind_xarray.columns
            if columns == wind_xarray.columns:
                wind_xarrays += read_sar_data(wind_xarray)
            else:
                LOG.info("            COLUMNS DOES NOT MATCH, NOT APPENDING")
        if len(fnames) == 1:
            wind_xarrays = {"WINDSPEED": wind_xarrays[0]}
        else:
            final_xarray = xarray.Dataset()
            lat_array = xarray.DataArray(
                numpy.vstack(
                    [
                        curr_xarray.latitude.to_masked_array()
                        for curr_xarray in wind_xarrays
                    ]
                )
            )
            lon_array = xarray.DataArray(
                numpy.vstack(
                    [
                        curr_xarray.longitude.to_masked_array()
                        for curr_xarray in wind_xarrays
                    ]
                )
            )
            time_array = xarray.DataArray(
                numpy.vstack(
                    [curr_xarray.time.to_masked_array() for curr_xarray in wind_xarrays]
                )
            )
            wspd_array = xarray.DataArray(
                numpy.vstack(
                    [
                        curr_xarray.wind_speed_kts.to_masked_array()
                        for curr_xarray in wind_xarrays
                    ]
                )
            )
            sigma_array = xarray.DataArray(
                numpy.vstack(
                    [
                        curr_xarray.sigma.to_masked_array()
                        for curr_xarray in wind_xarrays
                    ]
                )
            )
            final_xarray["latitude"] = lat_array
            final_xarray["longitude"] = lon_array
            final_xarray["time"] = time_array
            final_xarray["wind_speed_kts"] = wspd_array
            final_xarray["sigma"] = sigma_array
            final_xarray.attrs = wind_xarrays[0].attrs

            wind_xarrays = {"WINDSPEED": final_xarray}

    for wind_xarray in wind_xarrays.values():
        if not hasattr(wind_xarray, "minimum_coverage"):
            wind_xarray.attrs["minimum_coverage"] = 20

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
    if wind_xarrays["METADATA"].start_datetime == wind_xarrays["METADATA"].end_datetime:
        # Use alternate attributes to set start and end datetime
        try:
            wind_xarrays["METADATA"].attrs["start_datetime"] = datetime.strptime(
                wind_xarray.time_coverage_start, "%Y%m%dT%H%M%S"
            )
            wind_xarrays["METADATA"].attrs["end_datetime"] = datetime.strptime(
                wind_xarray.time_coverage_end, "%Y%m%dT%H%M%S"
            )
        except ValueError:
            # 20221103 used YYYYMMDDTHHMNSS, on 20221105 switched to
            #                                                       YYYY-MM-DDTHH:MN:SSZ
            # Allow both
            wind_xarrays["METADATA"].attrs["start_datetime"] = datetime.strptime(
                wind_xarray.time_coverage_start, "%Y-%m-%dT%H:%M:%SZ"
            )
            wind_xarrays["METADATA"].attrs["end_datetime"] = datetime.strptime(
                wind_xarray.time_coverage_end, "%Y-%m-%dT%H:%M:%SZ"
            )

    return wind_xarrays
