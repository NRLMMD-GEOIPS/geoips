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
from geoips.data_manipulations.corrections import apply_data_range, apply_gamma
LOG = logging.getLogger(__name__)

alg_func_type = 'list_numpy_to_numpy'


def Night_Vis_GeoIPS1(arrays, min_outbounds='crop', max_outbounds='crop', max_night_zen=90):
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

    data = arrays[0]
    sun_zenith = arrays[1]

    data = mask_day(data, sun_zenith, max_night_zen)

    data_range1 = [5.0e-10, 2.5e-8]

    data = apply_data_range(data,
                            min_val=data_range1[0],
                            max_val=data_range1[1],
                            min_outbounds=min_outbounds,
                            max_outbounds=max_outbounds,
                            norm=True,
                            inverse=False)
    data = apply_gamma(data, 2.0)

    return data
