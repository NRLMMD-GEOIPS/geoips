# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Derived Motion Winds at vertical pressure levels plotted as Barbs in Knots or m s-1.

Data manipulation steps for derived motion winds products.
This algorithm expects derived motion wind speeds at various pressures
"""
import logging

LOG = logging.getLogger(__name__)

interface = "algorithms"
family = "xarray_to_xarray"
name = "windbarbs_dmw"


def call(
    xobj,
    variables,
    product_name,
    output_data_range=None,
    pressure_level_range=None,
    input_units=None,
    output_units=None,
    min_outbounds="crop",
    max_outbounds="crop",
    norm=False,
    inverse=False,
    var_map=None,
):
    """Windbarbs product algorithm data manipulation steps.

    This algorithm expects input windspeed with units in either "m s-1" or "kts",
    and returns in either "m s-1" or "kts" (as specified in product YAML).

    Parameters
    ----------
    xobj : xarray.Dataset
        * Dataset holding at minimum wind speed, direction, and pressure data
    variables : list of str
        * list of input variables used in algorithm
    product_name : str
        * Name used to store output of algorithm to xobj
    output_data_range : list of float, default=None
        * list of min and max value for wind speeds (kts or m s-1)
        * defaults to None, which results in using data.min and data.max.
    pressure_level_range : list of float, default=None
        * list of min and max pressure levels to filter derived motion wind retrievals.
        * defaults to None, which results in using all wind retrievals
    input_units : str, default=None
        * Units of input data, for applying necessary conversions
        * defaults to None, resulting in no unit conversions.
    output_units : str, default=None
        * Units of output data, for applying necessary conversions
        * defaults to None, resulting in no unit conversions.
    min_outbounds : str, default='crop'
        * Method to use when applying bounds.  Valid values are:

            * retain: keep all pixels as is
            * mask: mask all pixels that are out of range
            * crop: set all out of range values to either min_val or max_val
              as appropriate
    max_outbounds : str, default='crop'
        * Method to use when applying bounds.  Valid values are:

            * retain: keep all pixels as is
            * mask: mask all pixels that are out of range
            * crop: set all out of range values to either min_val or max_val
              as appropriate
    norm : bool, default=False
        * Boolean flag indicating whether to normalize (True) or not (False)

            * If True, returned data will be in the range from 0 to 1
            * If False, returned data will be in the range from min_val to
              max_val
    inverse : bool, default=False
        * Boolean flag indicating whether to inverse (True) or not (False)

            * If True, returned data will be inverted
            * If False, returned data will not be inverted
    var_map : dict, default=None
        * Dictionary that maps input variables to names used in xobj

    Returns
    -------
    xarray.Dataset with new data variable named after product_name
        numpy.ndarray or numpy.MaskedArray of appropriately scaled channel data,
        dstacked as follows:

        * (spd, direction, rain_flag)
        * spd in kts
        * direction in degrees
        * rain_flag 0 (for compatibility with windbarb output formatter)
    """
    import numpy

    if not var_map:
        var_map = {}

    spd = xobj[var_map.get("speed", "wind_speed")]
    direction = xobj[var_map.get("direction", "wind_direction")]
    pressure = xobj[var_map.get("pressure", "pressure")]
    if output_data_range is None:
        output_data_range = (float(spd.min()), float(spd.max()))
    if pressure_level_range is None:
        pressure_level_range = (float(pressure.min()), float(pressure.max()))

    from geoips.data_manipulations.conversions import unit_conversion

    spd = unit_conversion(spd, input_units, output_units)

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
    pressure_mask = (pressure.data >= pressure_level_range[0]) & (
        pressure.data <= pressure_level_range[1]
    )

    stacked = numpy.dstack(
        (
            spd.where(pressure_mask),
            direction.where(pressure_mask),
            numpy.zeros(spd.shape),
            pressure.where(pressure_mask),
        )
    ).squeeze()
    stacked_dims = ("dim_0", "dim_1", "dim_2")[: stacked.ndim - 1]
    xobj[product_name] = ((*stacked_dims, product_name), stacked)
    xobj[product_name].attrs["windbarb_data_columns"] = [
        "speed",
        "direction",
        "rain_flag",
        "pressure",
    ]
    return xobj
