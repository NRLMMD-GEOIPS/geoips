# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Data manipulation steps for "Night_Vis" product, standard Version.

This algorithm expects one VIIRS channel (DNBRad) for a single channel image.
"""
import logging

LOG = logging.getLogger(__name__)

interface = "algorithms"
family = "list_numpy_to_numpy"
name = "Night_Vis"


def call(
    arrays,
    output_data_range=None,
    scale_factor=None,
    gamma_list=None,
    input_units=None,
    output_units=None,
    min_outbounds=None,
    max_outbounds=None,
    max_night_zen=None,
    norm=None,
    inverse=None,
):
    """Night-Vis algorithm data manipulation steps, standard version.

    DNB obs for visible product.

    This algorithm expects radaiance, between 0 and 2.5*10^-8

    This is only for nighttime product.

    Parameters
    ----------
    arrays : list of numpy.ndarray
        * list of numpy.ndarray or numpy.MaskedArray of channel data
        * Channel data: Radiance, between 0 and 2.5*10^-8

    Returns
    -------
    numpy.ndarray
        numpy.ndarray or numpy.MaskedArray of appropriately scaled channel data

    Notes
    -----
    Due to a relative maximum value of the DNBRad is much larger than
    that of the majority pixels in  moonlight/lighting situation,
    it could lead to a black image if the original maximum is
    used to normalize the data (i.e., the normlized value is close to 0).
    Thus, we need to setup an tuning factor to normalize the DNBRad.

    We start to use 0.05 to tune the val_max in moonlight/other lighing source,
    0.5 for no lighting source.

    We might have to generate night-vis product only when moonlight is present
    (TBD).
    """
    dnb_data = arrays[0]
    sun_zenith = arrays[1]

    val_min = 0
    val_max = dnb_data.max()

    if val_max >= 1.0e-8:
        val_max = 0.05 * val_max  # with moonlight
    else:
        val_max = 0.5 * val_max  # no moonlight/other light source

    from geoips.data_manipulations.info import percent_unmasked
    from geoips.data_manipulations.corrections import mask_day

    # apply the day_mask to mask daytime obs.
    dnb_data = mask_day(dnb_data, sun_zenith, max_night_zen)
    LOG.info("Percent unmasked night only %s", percent_unmasked(dnb_data))

    # apply data range correction and normalization (output range: 0-1)
    from geoips.data_manipulations.corrections import apply_data_range

    dnb_data = apply_data_range(
        dnb_data,
        min_val=val_min,
        max_val=val_max,
        min_outbounds=min_outbounds,
        max_outbounds=max_outbounds,
        norm=True,
        inverse=False,
    )

    from geoips.data_manipulations.corrections import apply_gamma

    for gamma in gamma_list:
        dnb_data = apply_gamma(dnb_data, gamma)

    from geoips.data_manipulations.corrections import apply_scale_factor

    dnb_data = apply_scale_factor(dnb_data, scale_factor)

    return dnb_data
