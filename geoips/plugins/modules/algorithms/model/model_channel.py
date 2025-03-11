# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Data manipulation steps for model products.

This algorithm expects one model variable/channel for a single channel image.
"""
import logging
import numpy as np
import xarray as xr
from pandas import to_datetime

LOG = logging.getLogger(__name__)

interface = "algorithms"
family = "xarray_to_xarray"
name = "model_channel"


def call(
    xobj,
    variables,
    product_name,
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
    """Model-Channel algorithm data manipulation steps, standard version.

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
    invar = variables[0]

    indata = xobj[invar]
    indims = xobj[invar].dims

    # time slicing
    time_idx = indims.index(time_key)
    slice_idx = [slice(0, None)] * len(indims)

    if time_fcst == -1:
        LOG.info("Slicing for max forcast time")
        slice_idx[time_idx] = slice(time_fcst, None)
    # elif time_fcst == 'closest':
    #    # find closest time to user specified value
    #    if time_dim:

    else:
        slice_idx[time_idx] = slice(time_fcst, time_fcst + 1)
    # pressure slicing (if given)
    if pressure_key:
        pres_idx = indims.index(pressure_key)
        pressure_match = [
            p
            for p, i in enumerate(xobj[invar][pressure_key])
            if pressure_level_range == i
        ]
        if len(pressure_match) == 0:
            raise ValueError(
                f"No pressure found at level {pressure_level_range} for "
                + f"range of {xobj[invar][pressure_key]} in data"
            )

        pressure_idx = pressure_match[0]
        slice_idx[pres_idx] = slice(pressure_idx, pressure_idx + 1)

    slice_tup = tuple(i for i in slice_idx)
    idx_data = indata[slice_tup]

    idx_data = idx_data.squeeze()

    if output_data_range:
        from geoips.data_manipulations.corrections import apply_data_range

        idx_data = apply_data_range(
            idx_data,
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

    xobj[invar] = idx_data
    xobj[product_name] = idx_data
    # update for proper title
    xobj.attrs["start_datetime"] = to_datetime(xobj[time_key].values[time_fcst])
    # print(xobj)
    # raise
    return xobj
