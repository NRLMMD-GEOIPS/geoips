# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Data manipulation steps for model windbarbs."""
import logging
import numpy as np
import xarray as xr

LOG = logging.getLogger(__name__)

interface = "algorithms"
family = "xarray_to_numpy"
name = "model_windbarbs"


def call(
    xobj,
    output_data_range=None,
    pressure_level_range=1000,
    pressure_key=None,
    time_key="atime",
    time_fcst=-1,
    min_outbounds="crop",
    max_outbounds="crop",
    norm=False,
    inverse=False,
    time_dim=None,
    grid_geo=False,
):
    """Model-windbarbs algorithm data manipulation steps, similar to model channel.

    Parameters
    ----------
    xobj : xarray.Dataset
        * Dataset holding at minimum wind speed, direction, and pressure data
    variables : list of str
        * list of input variables used in algorithm, selects the first
    product_name : str
        * Name used to store output of algorithm to xobj

    Returns
    -------
    xarray.Dataset with new data variable named after product_name
        numpy.ndarray or numpy.MaskedArray of appropriately scaled data
    """
    # need spd and direction
    # rain flag/pressure optional

    indata = xobj["windspeed_kts"]
    indims = xobj["windspeed_kts"].dims

    # time slicing
    time_idx = indims.index(time_key)
    slice_idx = [slice(0, None)] * len(indims)

    if time_fcst == -1:
        LOG.info("Slicing for max forcast time")
        slice_idx[time_idx] = slice(time_fcst, None)
    else:
        slice_idx[time_idx] = slice(time_fcst, time_fcst + 1)

    # pressure slicing (if given)
    if pressure_key:
        pres_idx = indims.index(pressure_key)
        pressure_match = [
            p
            for p, i in enumerate(xobj["windspeed_kts"][pressure_key])
            if pressure_level_range == i
        ]
        if len(pressure_match) == 0:
            raise ValueError(
                f"No pressure found at level {pressure_level_range} for "
                + f"range of {xobj['windspeed_kts'][pressure_key]} in data"
            )

        pressure_idx = pressure_match[0]
        slice_idx[pres_idx] = slice(pressure_idx, pressure_idx + 1)

    slice_tup = tuple(i for i in slice_idx)

    spd = indata[slice_tup]
    spd = spd.squeeze()
    # should be same shape as winds
    direction = xobj["winddir"][slice_tup].squeeze()

    # rain flag
    if "rain_flag" not in list(xobj.variables):
        rain_flag = np.zeros(direction.shape)

    if output_data_range:
        from geoips.data_manipulations.corrections import apply_data_range

        spd = apply_data_range(
            spd,
            min_val=output_data_range[0],
            max_val=output_data_range[1],
            min_outbounds=min_outbounds,
            max_outbounds=max_outbounds,
            norm=norm,
            inverse=inverse,
        )

    # grid geo (lat/lon), interps expect gridded geos
    if grid_geo:
        lat, lon = np.meshgrid(
            xobj["latitude"].values, xobj["longitude"].values, indexing="ij"
        )
        xobj["latitude"] = xr.DataArray(lat, dims=("latitude", "longitude"))
        xobj["longitude"] = xr.DataArray(lon, dims=("latitude", "longitude"))

    barb_stack = np.ma.dstack((spd.values, direction.values, rain_flag)).squeeze()

    return barb_stack
