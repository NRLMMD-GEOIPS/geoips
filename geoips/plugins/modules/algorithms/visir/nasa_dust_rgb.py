# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""NASA SPoRT Dust RGB product.

Data manipulation steps for the "nasa_dust_rgb" product.
This algorithm expects Brightness Temperatures in units of degrees Kelvin
"""
import logging

LOG = logging.getLogger(__name__)

interface = "algorithms"
family = "list_numpy_to_numpy"
name = "nasa_dust_rgb"


def call(arrays):
    """nasa_dust_rgb product algorithm data manipulation steps.

    This algorithm expects Brightness Temperatures in units of Kelvins,
    and returns red green and blue gun arrays.

    Parameters
    ----------
    data : list of numpy.ndarray
        * list of numpy.ndarray or numpy.MaskedArray of channel data,
            in order of channels list above
        * Kelvin

    Returns
    -------
    numpy.ndarray
        numpy.ndarray or numpy.MaskedArray of qualitative RGBA image output

    Channels: RED: 15-13 (-6.7,2.6,G1);
              GRN: 14-11 (-0.5,20.0,G2.5)
              BLU: 13 (-11.95,15.55,G1)

    """
    c11 = arrays[0]
    c13 = arrays[1]
    c14 = arrays[2]
    c15 = arrays[3]

    from geoips.data_manipulations.corrections import apply_data_range, apply_gamma

    red = c15 - c13
    red = apply_data_range(
        red,
        -6.7,
        2.6,
        min_outbounds="crop",
        max_outbounds="crop",
        norm=True,
        inverse=False,
    )
    red = apply_gamma(red, 1.0)

    grn = c14 - c11
    grn = apply_data_range(
        grn,
        -0.5,
        20.0,
        min_outbounds="crop",
        max_outbounds="crop",
        norm=True,
        inverse=False,
    )
    grn = apply_gamma(grn, 2.5)

    blu = c13 - 273.15
    blu = apply_data_range(
        blu,
        -11.95,
        15.55,
        min_outbounds="crop",
        max_outbounds="crop",
        norm=True,
        inverse=False,
    )
    blu = apply_gamma(blu, 1.0)

    from geoips.image_utils.mpl_utils import alpha_from_masked_arrays, rgba_from_arrays

    alp = alpha_from_masked_arrays([red, grn, blu])
    rgba = rgba_from_arrays(red, grn, blu, alp)
    return rgba
