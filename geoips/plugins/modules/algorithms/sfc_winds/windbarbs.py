# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Surface Winds plotted as Barbs in Knots.

Data manipulation steps for surface winds products.
This algorithm expects surface wind speeds in units of kts
"""
import logging

# install libraries
import numpy as np

LOG = logging.getLogger(__name__)

interface = "algorithms"
family = "list_numpy_to_numpy"
name = "windbarbs"


def call(
    arrays,
    output_data_range=None,
    input_units=None,
    output_units=None,
    min_outbounds="crop",
    max_outbounds="crop",
    norm=False,
    inverse=False,
):
    """Windbarbs product algorithm data manipulation steps.

    This algorithm expects input windspeed with units "kts" and returns in "kts"

    Parameters
    ----------
    arrays : list of numpy.ndarray
        * list of numpy.ndarray or numpy.MaskedArray of channel data,
            in order of sensor "channels" list
        * kts
    output_data_range : list of float, default=None
        * list of min and max value for wind speeds (kts)
        * defaults to None, which results in using data.min and data.max.
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

    Returns
    -------
    numpy.ndarray
        numpy.ndarray or numpy.MaskedArray of appropriately scaled channel data,
        dstacked as follows:

        * (spd, direction, rain_flag)
        * spd in kts
        * direction in degrees
        * rain_flag 0 or 1
    """
    spd = arrays[0]
    if output_data_range is None:
        output_data_range = (spd.min(), spd.max)
    direction = arrays[1]
    if len(arrays) > 2:
        rain_flag = arrays[2]
    else:
        rain_flag = np.zeros(arrays[1].shape)

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
    return np.ma.dstack((spd, direction, rain_flag)).squeeze()
