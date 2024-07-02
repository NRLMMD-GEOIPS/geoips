# # # Distribution Statement A. Approved for public release. Distribution is unlimited.
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

"""Data manipulation steps for "Night_Vis_IR" product.

This algorithm expects two VIIRS channels (DNBRad and M16BT) for a RGB image
"""
import logging

LOG = logging.getLogger(__name__)

interface = "algorithms"
family = "list_numpy_to_numpy"
name = "RGB_Default"


def call(arrays):
    """Apply default RGB algorithm.

    Plots RGB with the red gun being the first variable specified in the
    product YAML, green second, and blue third.

    Note this is currently entirely unused, and is included here for
    reference/completeness.  Eventually we may want to fully support
    this generalized RGB default algorithm, where you can pass in
    ranges, channel combinations, etc for RGB output, but for now it
    will ONLY plot arrays 0, 1, 2 as red, green, blue respectively,
    with no adjustments/combinations.

    Parameters
    ----------
    arrays : list of numpy.ndarray
        * list of numpy.ndarray or numpy.MaskedArray of channel data,
            in order of sensor "channels" list

    Returns
    -------
    numpy.ndarray
        numpy.ndarray or numpy.MaskedArray of qualitative RGBA image output
    """
    red = arrays[0]  # Red gun: First listed variable
    grn = arrays[1]  # Green gun: Second listed variable
    blu = arrays[2]  # Blue gun: Third listed variable

    from geoips.image_utils.mpl_utils import alpha_from_masked_arrays, rgba_from_arrays

    alp = alpha_from_masked_arrays([red, grn, blu])
    rgba = rgba_from_arrays(red, grn, blu, alp)

    return rgba
