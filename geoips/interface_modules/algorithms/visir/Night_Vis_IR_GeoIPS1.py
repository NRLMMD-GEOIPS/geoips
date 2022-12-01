# # # Distribution Statement A. Approved for public release. Distribution unlimited.
# # #
# # # Author:
# # # Naval Research Laboratory, Marine Meteorology Division
# # #
# # # This program is free software:
# # # you can redistribute it and/or modify it under the terms
# # # of the NRLMMD License included with this program.
# # #
# # # If you did not receive the license, see
# # # https://github.com/U-S-NRL-Marine-Meteorology-Division/
# # # for more information.
# # #
# # # This program is distributed WITHOUT ANY WARRANTY;
# # # without even the implied warranty of MERCHANTABILITY
# # # or FITNESS FOR A PARTICULAR PURPOSE.
# # # See the included license for more details.

''' Data manipulation steps for "Night_Vis_IR" product.

    This algorithm expects two VIIRS channels (DNBRad and M16BT) for a RGB image
'''

import logging
from geoips.data_manipulations.corrections import mask_day
LOG = logging.getLogger(__name__)

alg_func_type = 'list_numpy_to_numpy'


def Night_Vis_IR_GeoIPS1(arrays, max_night_zen=90):
    ''' Data manipulation steps for "rgb" product algorithm.

    This algorithm expects DNBRad in reflectance and M16BT Brightness Temperatures in units of degrees Kelvin,
    and returns red green and blue gun arrays.
    it will generate a product in daytime if we do not apply the daytime chech. For now, it is for both day/night.
    (Will decide whether this product is only for nighttime.  if so, a daytime check is required.)
    We might focus only on nighttime product with moonlight after additional validation (TBD).

    Args:
        data (list[numpy.ndarray]) :
            * list of numpy.ndarray or numpy.MaskedArray of channel data, in order of sensor "channels" list
            * Degrees Kelvin

    Returns:
        numpy.ndarray : numpy.ndarray or numpy.MaskedArray of qualitative RGBA image output
    '''

    ch1 = arrays[0]  # Red gun: DNBRad
    ch2 = arrays[0]  # Green gun: DNBRad
    ch3 = arrays[1]  # Blue gun: M16BT (200-300K)
    sun_zenith = arrays[2]

    ch1 = mask_day(ch1, sun_zenith, max_night_zen)
    ch2 = mask_day(ch2, sun_zenith, max_night_zen)
    ch3 = mask_day(ch3, sun_zenith, max_night_zen)

    data_range1 = [0, 2.5e-8]
    data_range2 = [200, 300]

    from geoips.data_manipulations.corrections import apply_data_range, apply_gamma
    red = ch1
    red = apply_data_range(red, min_val=data_range1[0], max_val=data_range1[1],
                           min_outbounds='crop', max_outbounds='crop',
                           norm=True, inverse=False)  # need inverse option?
    red = apply_gamma(red, 2.0)

    grn = ch2
    grn = apply_data_range(grn, min_val=data_range1[0], max_val=data_range1[1],
                           min_outbounds='crop', max_outbounds='crop',
                           norm=True, inverse=False)
    grn = apply_gamma(grn, 2.0)

    blu = ch3
    blu = apply_data_range(blu, min_val=data_range2[0], max_val=data_range2[1],
                           min_outbounds='crop', max_outbounds='crop',
                           norm=True, inverse=True)  # create image of deep clouds in blueish color
    blu = apply_gamma(blu, 1.2)

    from geoips.image_utils.mpl_utils import alpha_from_masked_arrays, rgba_from_arrays
    alp = alpha_from_masked_arrays([red, grn, blu])
    rgba = rgba_from_arrays(red, grn, blu, alp)

    return rgba
