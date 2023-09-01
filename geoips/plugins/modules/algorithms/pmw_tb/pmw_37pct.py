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

"""Passive Microwave 37 GHz Polarization Corrected Temperature.

Data manipulation steps for the "37pct" product.
This algorithm expects Brightness Temperatures in units of degrees Kelvin.
"""
import logging

LOG = logging.getLogger(__name__)

interface = "algorithms"
family = "list_numpy_to_numpy"
name = "pmw_37pct"


def call(
    arrays,
    output_data_range=None,
    min_outbounds="crop",
    max_outbounds="mask",
    norm=False,
    inverse=False,
):
    """37pct product algorithm data manipulation steps.

    This algorithm expects Brightness Temperatures in units of degrees Kelvin,
    and returns degrees Kelvin

    Parameters
    ----------
    arrays : list of numpy.ndarray
        * numpy.ndarray or numpy.MaskedArray of channel data, in order of sensor
            "channels" list
        * Degrees Kelvin

    Returns
    -------
    numpy.ndarray
        numpy.ndarray or numpy.MaskedArray of appropriately scaled channel data,
        in degrees Kelvin.
    """
    h37 = arrays[0]
    v37 = arrays[1]

    out = (2.15 * v37) - (1.15 * h37)

    if output_data_range is None:
        output_data_range = [230.0, 280.0]

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
