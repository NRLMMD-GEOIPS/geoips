# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Data manipulation steps for standard "single_channel" algorithm.

Generalized algorithm to apply data manipulation steps in a standard order
to apply corrections to a single channel output product.
"""

import logging

LOG = logging.getLogger(__name__)

KtoC_conversion = -273.15

interface = "algorithms"
family = "list_numpy_to_numpy"
name = "single_channel"


def call(
    arrays,
    output_data_range=None,
    input_units=None,
    output_units=None,
    min_outbounds="crop",
    max_outbounds="crop",
    norm=False,
    inverse=False,
    sun_zen_correction=False,
    mask_night=False,
    max_day_zen=None,
    mask_day=False,
    min_night_zen=None,
    gamma_list=None,
    scale_factor=None,
    satellite_zenith_angle_cutoff=None,
):
    """Apply data range and requested corrections to a single channel product.

    Data manipulation steps for applying a data range and requested corrections
    to a single channel product

    Parameters
    ----------
    arrays : list of numpy.ndarray
        * list of numpy.ndarray or numpy.MaskedArray of channel data
        * MUST be length one for single_channel algorithm.
        * If applying solar zenith corrections and diurnal masking, the second index in
          the arrays list must be the solar zenith angle array. This is controlled in
          product YAML.
        * If applying a satellite zenith angle cutoff, the final index in the arrays
          list must be the satellite zenith angle array. This is controlled in the
          product YAML.
    output_data_range : list of float, default=None
        * list of min and max value for output data product.
        * This is applied LAST after all other corrections/adjustments
        * If None, use data min and max.
    input_units : str, default=None
        * Units of input data, for applying necessary conversions
        * If None, no conversion
    output_units : str, default=None
        * Units of output data, for applying necessary conversions
        * If None, no conversion
    min_outbounds : str, default='crop'
        * Method to use when applying bounds.  Valid values are:

            * retain: keep all pixels as is
            * mask: mask all pixels that are out of range
            * crop: set all out of range values to either min_val or max_val
              as appropriate
    max_outbounds : str, default='crop'
        * Method to use when applying bounds.  Valid values are:

            * retain: keep all pixels as is
            * mask: mask all pixels that are out of range
            * crop: set all out of range values to either min_val or max_val
              as appropriate
    norm : bool, default=False
        * Boolean flag indicating whether to normalize (True) or not (False)

            * If True, returned data will be in the range from 0 to 1
            * If False, returned data will be in the range from min_val to max_val
    inverse : bool, default=False
        * Boolean flag indicating whether to inverse (True) or not (False)

            * If True, returned data will be inverted
            * If False, returned data will not be inverted
    sun_zenith_correction : bool, default=False
        * Boolean flag indicating whether to apply solar zenith correction
          (True) or not (False)

            * If True, returned data will have solar zenith correction applied
              (see data_manipulations.corrections.apply_solar_zenith_correction)
            * If False, returned data will not be modified based on solar zenith
              angle
    satellite_zenith_angle_cutoff : float, default=None
        * Cutoff for masking data where satellite zenith angle exceeds threshold
        * If None, no masking

    Notes
    -----
    Order of operations, based on the passed arguments, is:

    1. Mask night
    2. Mask day
    3. Apply satellite zenith angle cutoff
    4. Apply solar zenith correction
    5. Apply gamma values
    6. Apply scale factor
    7. Convert units
    8. Apply data range.

    NOTE: If "norm=True" is specified, the "output_data_range" will NOT
    match the actual range of the returned data, since the normalized data
    will be returned between 0 and 1.

    If you require a different order of operations than that specified within
    "single_channel" algorithm, please create a new algorithm for your desired
    order of operations.

    Returns
    -------
    numpy.ndarray
        numpy.ndarray or numpy.MaskedArray of appropriately scaled channel data,
        in units "output_units".
    """
    data = arrays[0]
    if output_data_range is None:
        output_data_range = [data.min(), data.max()]

    # Mask everything greater than max_day_zen
    # day zenith angles are less than 90
    # night zenith angles are greater than 90
    if max_day_zen and len(arrays) >= 2:
        from geoips.data_manipulations.info import percent_unmasked
        from geoips.data_manipulations.corrections import mask_night

        sun_zenith = arrays[1]
        LOG.info("Percent unmasked day/night %s", percent_unmasked(data))
        data = mask_night(data, sun_zenith, max_day_zen)
        LOG.info("Percent unmasked day only %s", percent_unmasked(data))

    # Mask everything less than min_night_zen
    # day zenith angles are less than 90
    # night zenith angles are greater than 90
    if mask_day and min_night_zen and len(arrays) >= 2:
        from geoips.data_manipulations.info import percent_unmasked
        from geoips.data_manipulations.corrections import mask_day

        sun_zenith = arrays[1]
        LOG.info("Percent unmasked day/night %s", percent_unmasked(data))
        data = mask_day(data, sun_zenith, min_night_zen)
        LOG.info("Percent unmasked night only %s", percent_unmasked(data))

    if satellite_zenith_angle_cutoff is not None and len(arrays) >= 2:
        from geoips.data_manipulations.info import percent_unmasked
        from geoips.data_manipulations.corrections import apply_satellite_zenith_cutoff

        sat_zenith = arrays[-1]
        data = apply_satellite_zenith_cutoff(
            data, sat_zenith, satellite_zenith_angle_cutoff
        )
        LOG.info(
            "Percent unmasked after zenith angle cutoff %s", percent_unmasked(data)
        )

    if sun_zen_correction and len(arrays) >= 2:
        sun_zenith = arrays[1]
        from geoips.data_manipulations.corrections import apply_solar_zenith_correction

        data = apply_solar_zenith_correction(data, sun_zenith)

    if gamma_list is not None:
        from geoips.data_manipulations.corrections import apply_gamma

        for gamma in gamma_list:
            data = apply_gamma(data, gamma)

    if scale_factor is not None:
        from geoips.data_manipulations.corrections import apply_scale_factor

        data = apply_scale_factor(data, scale_factor)

    from geoips.data_manipulations.conversions import unit_conversion

    data = unit_conversion(data, input_units, output_units)

    from geoips.data_manipulations.corrections import apply_data_range

    data = apply_data_range(
        data,
        min_val=output_data_range[0],
        max_val=output_data_range[1],
        min_outbounds=min_outbounds,
        max_outbounds=max_outbounds,
        norm=norm,
        inverse=inverse,
    )

    return data
