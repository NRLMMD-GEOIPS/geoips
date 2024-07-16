# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Data manipulation steps for "Night_Vis_IR" product, GeoIPS 1 Version.

This algorithm expects two VIIRS channels (DNBRad and M16BT) for a RGB image
"""
import logging
from geoips.data_manipulations.corrections import mask_day

LOG = logging.getLogger(__name__)

interface = "algorithms"
family = "list_numpy_to_numpy"
name = "Night_Vis_IR_GeoIPS1"


def call(arrays, max_night_zen=90):
    """Night Vis IR RGB product algorithm data manipulation steps.

    This algorithm expects DNBRad in reflectance and M16BT
    Brightness Temperatures in units of degrees Kelvin,
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
    sun_zenith = arrays[2]

    ch1 = mask_day(ch1, sun_zenith, max_night_zen)
    ch2 = mask_day(ch2, sun_zenith, max_night_zen)
    ch3 = mask_day(ch3, sun_zenith, max_night_zen)

    data_range1 = [0, 2.5e-8]
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
    red = apply_gamma(red, 2.0)

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
    grn = apply_gamma(grn, 2.0)

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
    blu = apply_gamma(blu, 1.2)

    from geoips.image_utils.mpl_utils import alpha_from_masked_arrays, rgba_from_arrays

    alp = alpha_from_masked_arrays([red, grn, blu])
    rgba = rgba_from_arrays(red, grn, blu, alp)

    return rgba
