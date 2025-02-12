# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Apply min/max values, normalize, and invert data arrays."""
# Python Standard Libraries
import logging

# Installed Libraries
import numpy
from xarray import DataArray

LOG = logging.getLogger(__name__)


def mask_day(data_array, sunzen_array, max_zenith=90):
    """Mask where solar zenith angle less than the maxinum specified value.

    Mask all pixels within the data array where the solar zenith angle is less
    than the maxinum specified value.

    Parameters
    ----------
    data_array : numpy.ndarray or numpy.ma.MaskedArray
        data values to be masked
    sunzen_array : numpy.ndarray
        numpy.ndarray or numpy.ma.MaskedArray of solar zenith angles,
        of the same shape as the data array
    max_zenith : float, optional
        Mask all locations in data_array where sunzen_array is less
        than max_zenith, by default 90

    Returns
    -------
    numpy.ma.MaskedArray
        Data array with all locations corresponding to a
        solar zenith angle less than max_zenith masked.
    """
    LOG.info(
        "CORRECTION Masking day less than sun zenith angle of %s, "
        "min sun zen in array %s, max sun zen %s",
        max_zenith,
        sunzen_array.min(),
        sunzen_array.max(),
    )
    return numpy.ma.masked_where(sunzen_array < max_zenith, data_array)


def mask_night(data_array, sunzen_array, min_zenith=90):
    """Mask where solar zenith angle greater than the minimum specified value.

    Mask all pixels within the data array where the solar zenith angle is
    greater than the mininum specified value.

    Parameters
    ----------
    data_array : numpy.ndarray or numpy.ma.MaskedArray
        data values to be masked.
    sunzen_array : numpy.ndarray or numpy.ma.MaskedArray
        array of solar zenith angles, same shape as the data array.
    min_zenith : float, optional
        Mask all locations in data_array where sunzen_array is greater than
        min_zenith, by default 90.

    Returns
    -------
    numpy.ma.MaskedArray
        Data array with all locations corresponding to a
        solar zenith angle greater than min_zenith masked.
    """
    LOG.info(
        "CORRECTION Masking night greater than sun zenith angle of %s, "
        "min sun zen in array %s, max sun zen %s",
        min_zenith,
        sunzen_array.min(),
        sunzen_array.max(),
    )
    return numpy.ma.masked_where(sunzen_array > min_zenith, data_array)


def apply_gamma(data_array, gamma):
    """Apply gamma correction to all values in the data array.

    Gamma correction applied as: data_array ** (1.0 / float(gamma))

    Parameters
    ----------
    data_array : numpy.ndarray or numpy.ma.MaskedArray
        data array to which gamma will be applied
    gamma : float
        gamma correction value

    Returns
    -------
    numpy.ndarray
        Return numpy.ndarray or numpy.ma.MaskedArray
        if data_array was MaskedArray with gamma correction applied
        data_array ** (1.0 / float(gamma))
    """
    LOG.info("CORRECTION Applying gamma correction of %s", gamma)
    return data_array ** (1.0 / float(gamma))


def apply_solar_zenith_correction(data_array, sunzen_array):
    """Apply solar zenith angle correction to all values in data_array.

    Solar zenith correction applied as: data / cos(sunzen)

    Parameters
    ----------
    data_array : numpy.ndarray or numpy.ma.MaskedArray
        data values to be masked
    sunzen_array : numpy.ndarray or numpy.ma.MaskedArray
        solar zenith angles of the same shape as the data array.

    Returns
    -------
    numpy.ndarray
        Return numpy.ndarray or numpy.ma.MaskedArray if original
        data_array was MaskedArray with each value in the
        data_array divided by cos(sunzen).
    """
    origmask = data_array.mask
    LOG.info(
        "CORRECTION Applying solar zenith correction to array with min "
        "solar zenith angle %s and max %s",
        sunzen_array.min(),
        sunzen_array.max(),
    )
    return numpy.ma.masked_array(
        (data_array / numpy.cos(numpy.deg2rad(sunzen_array))).data, origmask
    )


def apply_scale_factor(data_array, scale_factor):
    """Apply scale factor to all values in data_array.

    Scale factor applied as: data_array * scale_factor

    Parameters
    ----------
    data_array : numpy.ndarray or numpy.ma.MaskedArray
        data values to be scaled
    scale_factor : float
        requested scale factor

    Returns
    -------
    numpy.ndarray
        Return numpy.ndarray or numpy.ma.MaskedArray
        Input data array with scale factor applied
        data_array * scale_factor
    """
    LOG.info(
        "CORRECTION Applying scale factor of %s to array with min %s and max %s",
        scale_factor,
        data_array.min(),
        data_array.max(),
    )
    return data_array * scale_factor


def apply_offset(data_array, offset):
    """Apply offset to all values in data_array.

    Offset applied as: data_array + offset

    Parameters
    ----------
    data_array : numpy.ndarray or numpy.ma.MaskedArray
        data values to which offset will be applied.
    scale_factor : float
        requested offset.

    Returns
    -------
    numpy.ndarray
        Return numpy.ndarray or numpy.ma.MaskedArray
        Input data array with offset applied
        data_array + offset
    """
    LOG.info(
        "CORRECTION Applying offset of %s to array with min %s and max %s",
        offset,
        data_array.min(),
        data_array.max(),
    )
    return data_array + offset


def apply_minimum_value(data, min_val, outbounds):
    """Apply minimum values to an array of data.

    Parameters
    ----------
    data : numpy.ndarray or numpy.ma.MaskedArray
        data values to which the minimum value will be applied.
    min_val : float
        The minimum bound to be applied to the input data as a scalar.
    outbounds : str
        Method to use when applying bounds as a string. Valid values are:
          retain: keep all pixels as is
          mask: mask all pixels that are out of range.
          crop: set all out of range values to min_val.

    Returns
    -------
    numpy.ndarray
        Return numpy.ndarray or numpy.ma.MaskedArray
        Input data array with values below 'min_val'
        retained, cropped, or masked appropriately.
    """
    LOG.info("Applying minimum value of %r to data with min %f", min_val, data.min())

    # #Determine if mask is currently hardened
    # hardmask = data.hardmask
    # #Harden the mask to avoid unmasking bad values
    # if hardmask is False:
    #    data.harden_mask()

    # Allow for numpy arrays that are not masked arrays
    hardmask = None
    if hasattr(data, "hardmask"):
        # Determine if mask is currently hardened
        hardmask = data.hardmask
        # Harden the mask to avoid unmasking bad values
        if hardmask is False:
            data.harden_mask()

    # If outbounds is set to "mask" then mask the out of range data
    if outbounds == "mask":
        data = numpy.ma.masked_less(data, min_val)
    # If outbounds set to crop, then set out of range data to the minimum value
    elif outbounds == "crop":
        data[data < min_val] = min_val
    else:
        raise ValueError(
            'outbounds must be either "mask" or "crop".  Got %s.' % outbounds
        )

    # If the mask was originally not hardened, then unharden it now
    if hardmask is False:
        data.soften_mask()

    return data


def apply_maximum_value(data, max_val, outbounds):
    """Apply maximum value to an array of data.

    Parameters
    ----------
    data : numpy.ndarray or numpy.ma.MaskedArray
        data values to which the maximum value will be applied.
    max_val : float
        The maximum bound to be applied to the input data as a scalar.
    outbounds : str
        Method to use when applying bounds as a string. Valid values are:
          retain: keep all pixels as is
          mask: mask all pixels that are out of range.
          crop: set all out of range values to max_val.

    Returns
    -------
    numpy.ndarray
        Return numpy.ndarray or numpy.ma.MaskedArray
        Input data array with values above 'max_val'
        retained, cropped, or masked appropriately.
    """
    LOG.info("Applying maximum value of %r to data with max %f", max_val, data.max())

    # #Determine if mask is currently hardened
    # hardmask = data.hardmask
    # #Harden the mask to avoid unmasking bad values
    # if hardmask is False:
    #    data.harden_mask()

    # Allow for numpy arrays that are not masked arrays
    hardmask = None
    if hasattr(data, "hardmask"):
        # Determine if mask is currently hardened
        hardmask = data.hardmask
        # Harden the mask to avoid unmasking bad values
        if hardmask is False:
            data.harden_mask()

    # If outboudns is set to "mask" then mask the out of range data
    if outbounds == "mask":
        data = numpy.ma.masked_greater(data, max_val)
    # If outbounds is set to crop, then set out of range data to the maximum value
    elif outbounds == "crop":
        data[data > max_val] = max_val
    else:
        raise ValueError(
            'outbounds must be either "mask" or "crop".  Got %s.' % outbounds
        )

    # If the mask was originally not hardened, then unharden it now
    if hardmask is False:
        data.soften_mask()

    return data


def apply_data_range(
    data,
    min_val=None,
    max_val=None,
    min_outbounds="crop",
    max_outbounds="crop",
    norm=True,
    inverse=False,
):
    """
    Apply minimum and maximum values to an array of data.

    Normalize, invert, and handle out of bounds data as requested.

    Parameters
    ----------
    data : numpy.ndarray or numpy.ma.MaskedArray
        data values to which the data range will be applied.
    min_val : float, default None
        * The minimum bound to be applied to the input data as a scalar,
        * If None, use data.min().
    max_val : float, default=None
        * The maximum bound to be applied to the input data as a scalar.
        * If None, use data.max().
    min_outbounds : str, default='crop'
        Method to use when applying bounds as a string. Valid values are:

        * retain: keep all pixels as is
        * mask: mask all pixels that are out of range.
        * crop: set all out of range values to min_val
    max_outbounds : str, default='crop'
        Method to use when applying bounds as a string. Valid values are:

        * retain: keep all pixels as is
        * mask: mask all pixels that are out of range.
        * crop: set all out of range values to max_val
    norm : bool, default=True
        Boolean flag indicating whether to normalize (True) or not (False).

        * If True, returned data will be in the range from 0 to 1.
        * If False, returned data will be in the range min_val to max_val.
    inverse : bool, default=False
        Boolean flag indicating whether to invert data (True) or not (False).

        * If True, returned data will be inverted
        * If False, returned data will not be inverted

    Returns
    -------
    numpy.ndarray
        Return numpy.ndarray or numpy.ma.MaskedArray
        Input data array with values above 'max_val' or below 'min_val'
        retained, cropped, or masked.
    """
    # This is a temporary fix to treat xarrays like numpy arrays
    try:
        data = data.to_masked_array()
        is_xarr = True
    except AttributeError:
        pass
        is_xarr = False

    # Invert data if minimum value is greater than maximum value
    if inverse or (min_val is not None and max_val is not None and min_val > max_val):
        data, min_val, max_val = invert_data_range(data, min_val, max_val)

    # If a minimum value is specified, then apply minimum value
    if min_val is not None:
        data = apply_minimum_value(data, min_val, min_outbounds)
    else:
        min_val = data.min()

    # If a maximum value is specified, then apply maximum value
    if max_val is not None:
        data = apply_maximum_value(data, max_val, max_outbounds)
    else:
        max_val = data.max()

    # CHANGE DEFAULTS FOR OUTBOUNDS TO NONE??  If you want it to crop, specify.
    # Need to change in productfile/xml.py and utils/normalize.py
    # Actually, when plotting if you don't crop, it probably crops anyway.
    #   so maybe keep 'crop' as default anyway ?

    # Normalize data if requested
    if norm is True:
        data = normalize(data, min_val, max_val, min_outbounds, max_outbounds)

    if is_xarr:
        data = DataArray(data)

    return data


def invert_data_range(data, min_val=None, max_val=None):
    """
    Invert data range to an array of data.

    Parameters
    ----------
    data : numpy.ndarray or numpy.ma.MaskedArray
        data values to which the data range will be applied.
    min_val : float, optional
        The minimum bound to be applied to the input data as a scalar,
        by default None, which results in data.min().
    max_val : float, optional
        The maximum bound to be applied to the input data as a scalar.
        by default None, which results in data.max().

    Returns
    -------
    numpy.ndarray
        Return numpy.ndarray or numpy.ma.MaskedArray
        Input data array with values inverted.
    """
    if min_val is None:
        min_val = data.min()
    if max_val is None:
        max_val = data.max()
    LOG.info("Inverting data between %r and %r", min_val, max_val)

    if min_val > max_val:
        min_val, max_val = max_val, min_val

    if hasattr(data, "mask"):
        # Preserve mask
        origmask = data.mask
        data = numpy.ma.masked_array((max_val - (data - min_val)).data, origmask)
    else:
        data = max_val - (data - min_val)

    return data, min_val, max_val


def normalize(data, min_val=None, max_val=None, min_bounds="crop", max_bounds="crop"):
    """
    Normalize data array with min_val and max_val to range 0 to 1.

    Default to cropping outside requested data range.

    Parameters
    ----------
    data : numpy.ndarray or numpy.ma.MaskedArray
        data values to which the data range will be applied.
    min_val : float, default=None
        * The minimum bound to be applied to the input data as a scalar,
        * If None, use data.min().
    max_val : float, default=None
        * The maximum bound to be applied to the input data as a scalar.
        * If None, use data.max().
    min_outbounds : str, default='crop'
        Method to use when applying bounds as a string. Valid values are:

        * retain: keep all pixels as is
        * mask: mask all pixels that are out of range.
        * crop: set all out of range values to min_val
    max_outbounds : str, default='crop'
        Method to use when applying bounds as a string. Valid values are:

        * retain: keep all pixels as is
        * mask: mask all pixels that are out of range.
        * crop: set all out of range values to max_val

    Returns
    -------
    numpy.ndarray
        Return numpy.ndarray or numpy.ma.MaskedArray
        Input data array normalized between 0 and 1, with values above
        'max_val' or below 'min_val' retained, cropped, or masked.
    """
    # Determine if mask is currently hardened
    hardmask = None
    if hasattr(data, "hardmask"):
        hardmask = data.hardmask

    # Harden the mask to avoid unmasking bad values
    if hardmask is False:
        data.harden_mask()

    if min_val is None:
        min_val = data.min()
    if max_val is None:
        max_val = data.max()
    if min_bounds is None:
        min_bounds = "retain"
    if max_bounds is None:
        max_bounds = "retain"

    data = data.copy()
    data -= min_val
    data *= abs(1.0 / (max_val - min_val))

    if min_bounds == "retain":
        pass
    elif min_bounds == "crop":
        data[numpy.ma.where(data < 0.0)] = 0.0
    elif min_bounds == "mask":
        data = numpy.ma.masked_less(data, 0.0)

    if max_bounds == "retain":
        pass
    elif max_bounds == "crop":
        data[numpy.ma.where(data > 1.0)] = 1.0
    elif max_bounds == "mask":
        data = numpy.ma.masked_greater(data, 1.0)

    # If the mask was originally not hardened, then unharden it now
    if hardmask is False:
        data.soften_mask()

    return data


def apply_satellite_zenith_cutoff(data_array, satzen_array, satzen_angle_cutoff):
    """Apply satellite zenith angle cutoff to data_array.

    Mask values in data_array where satzen_array values exceed the cutoff threshold.

    Parameters
    ----------
    data_array : numpy.ndarray or numpy.ma.MaskedArray
        data values to be masked
    satzen_array : numpy.ndarray or numpy.ma.MaskedArray
        satellite zenith angles of the same shape as the data array.
    satzen_angle_cutoff : float
        Cutoff threshold for satellite zenith angle

    Returns
    -------
    numpy.ndarray
        Return numpy.ndarray or numpy.ma.MaskedArray if original
        data_array was MaskedArray with each value in the
        data_array divided by cos(sunzen).
    """
    LOG.info("Applying satellite zenith angle cutoff of %sdeg", satzen_angle_cutoff)
    # zen_mask = satzen_array > satzen_angle_cutoff
    return numpy.ma.masked_where(satzen_array > satzen_angle_cutoff, data_array)
