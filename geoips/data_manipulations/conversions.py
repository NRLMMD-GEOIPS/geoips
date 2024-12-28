# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Routines for converting between units."""

# Python Standard Libraries
import logging

# Installed Libraries

KtoC_conversion = -273.15

LOG = logging.getLogger(__name__)


def unit_conversion(data_array, input_units=None, output_units=None):
    """Convert array in units 'input_units' to units 'output_units'.

    Parameters
    ----------
    data_array : ndarray
        numpy.ndarray or numpy.MaskedArray of data values to be converted
    input_units : str, optional
        Units of input data array, defaults to None
    output_units : str, optional
        Units of output data array, defaults to None

    Returns
    -------
    MaskedArray
        Return numpy.ma.MaskedArray, with units converted
        from 'input_units' to 'output_units'
    """
    if input_units and output_units and input_units != output_units:
        from geoips.data_manipulations.corrections import apply_offset

        valid_units = ["Kelvin", "celsius", "kts", "m s-1"]
        if input_units not in valid_units:
            raise ValueError(f"Input units must be one of {valid_units}")
        if output_units not in valid_units:
            raise ValueError(f"Output units must be one of {valid_units}")

        if input_units == "Kelvin" and output_units == "celsius":
            data_array = apply_offset(data_array, KtoC_conversion)

        if input_units == "celsius" and output_units == "Kelvin":
            data_array = apply_offset(data_array, -KtoC_conversion)

        if input_units == "m s-1" and output_units == "kts":
            data_array *= 1.94384

        if input_units == "kts" and output_units == "m s-1":
            data_array *= 0.514444

    return data_array
