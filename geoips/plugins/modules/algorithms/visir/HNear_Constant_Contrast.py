# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Data algorithm for High Near constant contrast imagery product.

Algorithm is based upon work by Zinke (2017) for improved NCC VIIRS DNB imagery.
"""

# python libs
import logging

# installed libs
import numpy as np

# geoips libs
from geoips.data_manipulations.corrections import apply_data_range

LOG = logging.getLogger(__name__)

interface = "algorithms"
family = "list_numpy_to_numpy"
name = "high_near_constant_contrast"


def gain_func(angle):
    """Gain factor for angle correction.

    Angle in degrees.
    """
    # given an ndarray
    # create masks and then calculate based upon the masks
    intervals = [-np.inf, 87.541, 96, 101, 103.49, np.inf]

    masks = []
    for i, j in enumerate(intervals[:-1]):
        tmp_mask = np.logical_and(angle > j, angle <= intervals[i + 1])
        masks.append(tmp_mask)

    gain_fac = np.full(angle.shape, np.nan)

    # angle <= 87.541:
    gain_fac[masks[0]] = (58 + (4 / np.cos(angle[masks[0]]))) / 5
    # angle <= 96.00 and angle > 87.541:
    gain_fac[masks[1]] = (123 * np.exp(1.06 * (angle[masks[1]] - 89.589))) * (
        (((angle[masks[1]] - 93) ** 2) / 18) + 0.5
    )
    # angle <= 101 and angle > 96:
    gain_fac[masks[2]] = 123 * np.exp(1.06 * (angle[masks[2]] - 89.589))
    # angle <= 103.49 and angle > 101:
    gain_fac[masks[3]] = (123 * np.exp(1.06 * (101 - 89.589))) * np.log(
        angle[masks[3]] - (101 - np.e)
    ) ** 2
    # else:
    gain_fac[masks[4]] = 6e7

    return gain_fac


def call(
    arrays,
):
    """Calculate HNCC.

    Must have solar/lunar zenith angle and moon illumination fraction.
    """
    # check data
    if len(arrays) != 4:
        raise ValueError(
            "Incongruent shape, please pass data,solar_zenith_angle,lunar_zenith_angle"
        )

    data, sza, lza, moon_ill_frac = arrays

    gain_solar = gain_func(sza)
    gain_lza = gain_func(lza)
    LOG.info(
        "Producing HNCC imagery with moon illumination of {0:.2f}".format(
            np.nanmean(moon_ill_frac)
        )
    )
    # calculate the lunar brightness
    # apparent solar magnitude
    mag_sol = -26.74
    # mean apparent mag of moon
    mam_moon_mag = -12.74

    mag_moon_variation = (
        0.026 * np.arccos(2 * moon_ill_frac - 1)
        + (np.arccos(2 * moon_ill_frac - 1) ** 4) * 4e-9
    )
    mag_moon = mag_moon_variation + mam_moon_mag
    bt_ratio = 10 ** ((mag_sol - mag_moon) / -2.5)
    gain_lunar = bt_ratio * gain_lza
    # systematic bias for radiances
    # from Liao et al. 2013, 12712
    bias_rad = data + 2.6e-10

    total_gain = 1 / ((1 / gain_solar) + (1 / gain_lunar))
    norm_rad = bias_rad * total_gain
    hncc_arr = apply_data_range(
        norm_rad,
        min_val=0.0,
        max_val=0.2,
        min_outbounds="mask",
        max_outbounds="mask",
        norm=True,
        inverse=False,
    )
    return hncc_arr
