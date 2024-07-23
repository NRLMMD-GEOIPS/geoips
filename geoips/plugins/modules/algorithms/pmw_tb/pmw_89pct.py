# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Passive Microwave 89 GHz Polarization Corrected Temperature.

Data manipulation steps for the "89pct" product.
This algorithm expects Brightness Temperatures in units of degrees Kelvin
"""
import logging

LOG = logging.getLogger(__name__)

interface = "algorithms"
family = "list_numpy_to_numpy"
name = "pmw_89pct"


def call(
    arrays,
    output_data_range,
    min_outbounds="crop",
    max_outbounds="mask",
    norm=False,
    inverse=False,
):
    """89pct product algorithm data manipulation steps.

    This algorithm expects Brightness Temperatures in units of degrees Kelvin,
    and returns degrees Kelvin

    Parameters
    ----------
    arrays : list of numpy.ndarray
        * list of numpy.ndarray or numpy.MaskedArray of channel data
            and other variables, in order of sensor "variables" list
        * Channel data: Degrees Kelvin

    Returns
    -------
    numpy.ndarray
        numpy.ndarray or numpy.MaskedArray of appropriately scaled channel data,
        in degrees Kelvin.
    """
    h89 = arrays[0]
    v89 = arrays[1]

    out = (1.7 * v89) - (0.7 * h89)

    from geoips.data_manipulations.corrections import apply_data_range

    data = apply_data_range(
        out,
        min_val=output_data_range[0],
        max_val=output_data_range[1],
        min_outbounds=min_outbounds,
        max_outbounds=max_outbounds,
        norm=norm,
        inverse=inverse,
    )

    return data
