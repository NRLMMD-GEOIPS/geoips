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

"""Data manipulation steps for "Night_Vis_IR" product.

This algorithm expects two VIIRS channels (DNBRad and M16BT) for a RGB image
"""
import logging

LOG = logging.getLogger(__name__)

interface = "algorithms"
family = "list_numpy_to_numpy"
name = "Night_Vis_IR"


def call(arrays):
    """Night_Vis_IR RGB product algorithm data manipulation steps.

    This algorithm expects DNBRad in reflectance and
    M16BT Brightness Temperatures in units of degrees Kelvin,
    and returns red green and blue gun arrays.

    Parameters
    ----------
    arrays : list of numpy.ndarray
        * list of numpy.ndarray or numpy.MaskedArray of channel data,
            in order of sensor "channels" list
        * Degrees Kelvin

    Returns
    -------
    numpy.ndarray
        numpy.ndarray or numpy.MaskedArray of qualitative RGBA image output

    Notes
    -----
    It will generate a product in daytime if we do not apply the daytime check.
    For now, it is for both day/night.

    We will decide whether this product is only for nighttime.
    If so, a daytime check will be required.

    We may focus only on nighttime product with moonlight after additional
    validation (TBD).
    """
    ch1 = arrays[0]  # Red gun: DNBRad
    ch2 = arrays[0]  # Green gun: DNBRad
    ch3 = arrays[1]  # Blue gun: M16BT (200-300K)

    val_max = ch1.max()

    if (
        val_max < 1.0e-3 and val_max >= 1.0e-8
    ):  # nighttime DNBRad is very small, normally aound 1.0e-8
        val_max = (
            0.05 * val_max
        )  # add a tuning factor 0.05 to the val_max with moonlight
    if val_max < 1.0e-8:
        val_max = (
            0.5 * val_max
        )  # add a tuning factor 0.5 to the val_max without moonlight

    data_range1 = [0, val_max]
    data_range2 = [200, 300]

    from geoips.data_manipulations.corrections import apply_data_range, apply_gamma

    red = ch1
    red = apply_data_range(
        red,
        min_val=data_range1[0],
        max_val=data_range1[1],
        min_outbounds="crop",
        max_outbounds="crop",
        norm=True,
        inverse=False,
    )  # need inverse option?
    red = apply_gamma(red, 1.0)

    grn = ch2
    grn = apply_data_range(
        grn,
        min_val=data_range1[0],
        max_val=data_range1[1],
        min_outbounds="crop",
        max_outbounds="crop",
        norm=True,
        inverse=False,
    )
    grn = apply_gamma(grn, 1.0)

    blu = ch3
    blu = apply_data_range(
        blu,
        min_val=data_range2[0],
        max_val=data_range2[1],
        min_outbounds="crop",
        max_outbounds="crop",
        norm=True,
        inverse=True,
    )  # create image of deep clouds in blueish color
    # norm=True, inverse=False)    #create image of deep clouds in yellowish color
    blu = apply_gamma(blu, 1.0)

    from geoips.image_utils.mpl_utils import alpha_from_masked_arrays, rgba_from_arrays

    alp = alpha_from_masked_arrays([red, grn, blu])
    rgba = rgba_from_arrays(red, grn, blu, alp)

    return rgba
