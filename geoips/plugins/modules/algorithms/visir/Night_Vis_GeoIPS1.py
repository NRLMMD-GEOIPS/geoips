# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Data manipulation steps for "Night_Vis" product, GeoIPS 1 Version.

This algorithm expects one VIIRS channel (DNBRad) for a single channel image.
"""
import logging
from geoips.data_manipulations.corrections import mask_day
from geoips.data_manipulations.corrections import apply_data_range, apply_gamma

LOG = logging.getLogger(__name__)

interface = "algorithms"
family = "list_numpy_to_numpy"
name = "Night_Vis_GeoIPS1"


def call(arrays, min_outbounds="crop", max_outbounds="crop", max_night_zen=90):
    """Night Vis product algorithm data manipulation steps, GeoIPS 1 version.

    This algorithm expects DNBRad in reflectance, and returns the adjusted
    array.

    Parameters
    ----------
    arrays : list of numpy.ndarray
        * list of numpy.ndarray or numpy.MaskedArray of channel data,
            in order of sensor "channels" list
        * Degrees Kelvin

    Returns
    -------
    numpy.ndarray
        numpy.ndarray or numpy.MaskedArray of adjusted DNB output.

    Notes
    -----
    It will generate a product in daytime if we do not apply the daytime check.
    For now, it is for both day/night.

    We will decide whether this product is only for nighttime.
    If so, a daytime check will be required.

    We may focus only on nighttime product with moonlight after additional
    validation (TBD).
    """
    data = arrays[0]
    sun_zenith = arrays[1]

    data = mask_day(data, sun_zenith, max_night_zen)

    data_range1 = [5.0e-10, 2.5e-8]

    data = apply_data_range(
        data,
        min_val=data_range1[0],
        max_val=data_range1[1],
        min_outbounds=min_outbounds,
        max_outbounds=max_outbounds,
        norm=True,
        inverse=False,
    )
    data = apply_gamma(data, 2.0)

    return data
