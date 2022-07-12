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

''' Routines for apply min/max values, normalizing, and inverting data arrays '''
# Python Standard Libraries
import logging

# Installed Libraries
import numpy

LOG = logging.getLogger(__name__)


def mask_day(data_array, sunzen_array, max_zenith=90):
    ''' Mask all pixels within the data array where the solar zenith angle is less than the maxinum specified value.


    Args:
        data_array (ndarray) : numpy.ndarray or numpy.MaskedArray of data values to be masked
        sunzen_array (ndarray) : numpy.ndarray or numpy.MaskedArray of solar zenith angles, of the same shape as
                                 the data array
        min_zenith (float, optional) : DEFAULT 90, Mask all locations in data_array where sunzen_array is less 
                                       than max_zenith

    Returns:
        (MaskedArray) : Return numpy.ma.MaskedArray, masking all locations corresponding to a solar zenith angle
                        less than max_zenith.
    '''
    LOG.info('CORRECTION Masking day less than sun zenith angle of %s, min sun zen in array %s, max sun zen %s',
             max_zenith,
             sunzen_array.min(),
             sunzen_array.max())
    return numpy.ma.masked_where(sunzen_array < max_zenith, data_array)


def mask_night(data_array, sunzen_array, min_zenith=90):
    ''' Mask all pixels within the data array where the solar zenith angle is greater than the mininum specified value.


    Args:
        data_array (ndarray) : numpy.ndarray or numpy.MaskedArray of data values to be masked
        sunzen_array (ndarray) : numpy.ndarray or numpy.MaskedArray of solar zenith angles, of the same shape as
                                 the data array
        min_zenith (float, optional) : DEFAULT 90, Mask all locations in data_array where sunzen_array is greater
                                       than min_zenith

    Returns:
        (MaskedArray) : Return numpy.ma.MaskedArray, masking all locations corresponding to a solar zenith angle
                        greater than min_zenith.
    '''
    LOG.info('CORRECTION Masking night greater than sun zenith angle of %s, min sun zen in array %s, max sun zen %s',
             min_zenith,
             sunzen_array.min(),
             sunzen_array.max())
    return numpy.ma.masked_where(sunzen_array > min_zenith, data_array)


def apply_gamma(data_array, gamma):
    ''' Apply gamma correction to all values in the data array: data_array ** (1.0 / float(gamma))

    Args:
        data_array (ndarray) : numpy.ndarray or numpy.ma.MaskedArray of data values
        gamma (float) : gamma correction value

    Returns:
        (ndarray) : Return numpy.ndarray (or numpy.ma.MaskedArray if data_array was MaskedArray) with gamma correction
                    applied: data_array ** (1.0 / float(gamma))
    '''
    LOG.info('CORRECTION Applying gamma correction of %s', gamma)
    return data_array**(1.0/float(gamma))


def apply_solar_zenith_correction(data_array, sunzen_array):
    ''' Apply solar zenith angle correction to all values in data_array: data / cos(sunzen)

    Args:
        data_array (ndarray) : numpy.ndarray or numpy.ma.MaskedArray of data values to be masked
        sunzen_array (ndarray) : numpy.ndarray or numpy.ma.MaskedArray of solar zenith angles,
                                 of the same shape as the data array

    Returns:
        (ndarray) : Return numpy.ndarray (or numpy.ma.MaskedArray if original data_array was MaskedArray)
                    with each value in the data_array divided by cos(sunzen) at that location
    '''
    origmask = data_array.mask
    LOG.info('CORRECTION Applying solar zenith correction to array with min solar zenith angle %s and max %s',
             sunzen_array.min(), sunzen_array.max())
    return numpy.ma.masked_array((data_array / numpy.cos(numpy.deg2rad(sunzen_array))).data, origmask)


def apply_scale_factor(data_array, scale_factor):
    ''' Apply scale factor to all values in data_array: data_array * scale_factor

    Args:
        data_array (ndarray) : numpy.ndarray or numpy.ma.MaskedArray of data values
        scale_factor (float) : requested scale factor

    Returns:
        (MaskedArray) : Return numpy.ma.MaskedArray with scale factor applied: data_array * scale_factor
    '''

    LOG.info('CORRECTION Applying scale factor of %s to array with min %s and max %s',
             scale_factor, data_array.min(), data_array.max())
    return data_array*scale_factor


def apply_offset(data_array, offset):
    ''' Apply offset to all values in data_array: data_array + offset 

    Args:
        data_array (ndarray) : numpy.ndarray or numpy.ma.MaskedArray of data values
        scale_factor (float) : requested offset

    Returns:
        (ndarray) : Return numpy.ndarray or numpy.ma.MaskedArray with offset applied: data_array + offset
    '''
    LOG.info('CORRECTION Applying offset of %s to array with min %s and max %s',
             offset, data_array.min(), data_array.max())
    return data_array+offset


def apply_minimum_value(data, min_val, outbounds):
    ''' Apply minimum values to an array of data.

    Args:
        data (ndarray) : numpy.ndarray or numpy.ma.MaskedArray of data values
        min_val (float) : The minimum bound to be applied to the input data as a scalar.
        outbounds (str) : Method to use when applying bounds as a string.
                            Valid values are:
                                retain: keep all pixels as is
                                mask: mask all pixels that are out of range.
                                crop: set all out of range values to either min_val
    Returns:
        (ndarray) : numpy.ndarray or numpy.ma.MaskedArray with values below "min_val" retained, cropped, or masked.
    '''
    LOG.info('Applying minimum value of %r to data with min %f', min_val, data.min())

    # #Determine if mask is currently hardened
    # hardmask = data.hardmask
    # #Harden the mask to avoid unmasking bad values
    # if hardmask is False:
    #    data.harden_mask()

    # Allow for numpy arrays that are not masked arrays
    hardmask = None
    if hasattr(data, 'hardmask'):
        # Determine if mask is currently hardened
        hardmask = data.hardmask
        # Harden the mask to avoid unmasking bad values
        if hardmask is False:
            data.harden_mask()

    # If outbounds is set to "mask" then mask the out of range data
    if outbounds == 'mask':
        data = numpy.ma.masked_less(data, min_val)
    # If outbounds set to crop, then set out of range data to the minimum value
    elif outbounds == 'crop':
        data[data < min_val] = min_val
    else:
        raise ValueError('outbounds must be either "mask" or "crop".  Got %s.' % outbounds)

    # If the mask was originally not hardened, then unharden it now
    if hardmask is False:
        data.soften_mask()

    return data


def apply_maximum_value(data, max_val, outbounds):
    ''' Apply maximum value to an array of data.

    Args:
        data (ndarray) : numpy.ndarray or numpy.ma.MaskedArray of data values
        max_val (float) : The maximum bound to be applied to the input data as a scalar.
        outbounds (str) : Method to use when applying bounds as a string.
                            Valid values are:
                                retain: keep all pixels as is
                                mask: mask all pixels that are out of range.
                                crop: set all out of range values to max_val
    Returns:
        (ndarray) : numpy.ndarray or numpy.ma.MaskedArray with values above "max_val" retained, cropped, or masked.
    '''
    LOG.info('Applying maximum value of %r to data with max %f', max_val, data.max())

    # #Determine if mask is currently hardened
    # hardmask = data.hardmask
    # #Harden the mask to avoid unmasking bad values
    # if hardmask is False:
    #    data.harden_mask()

    # Allow for numpy arrays that are not masked arrays
    hardmask = None
    if hasattr(data, 'hardmask'):
        # Determine if mask is currently hardened
        hardmask = data.hardmask
        # Harden the mask to avoid unmasking bad values
        if hardmask is False:
            data.harden_mask()

    # If outboudns is set to "mask" then mask the out of range data
    if outbounds == 'mask':
        data = numpy.ma.masked_greater(data, max_val)
    # If outbounds is set to crop, then set out of range data to the maximum value
    elif outbounds == 'crop':
        data[data > max_val] = max_val
    else:
        raise ValueError('outbounds must be either "mask" or "crop".  Got %s.' % outbounds)

    # If the mask was originally not hardened, then unharden it now
    if hardmask is False:
        data.soften_mask()

    return data


def apply_data_range(data, min_val=None, max_val=None, min_outbounds='crop', max_outbounds='crop', norm=True, inverse=False):
    '''
    Apply minimum and maximum values to an array of data.

    +------------+----------------------------------------------------------------+
    | Parameters | Description                                                    |
    +============+================================================================+
    | data       | Array of data where isinstance(numpy.ndarray) is True.         |
    +------------+----------------------------------------------------------------+

    +-----------+-------------------------------------------------------------------------------+
    | Keywords  | Description                                                                   |
    +===========+===============================================================================+
    | min_val   | The minimum bound to be applied to the input data as a scalar.                |
    |           | Default: None                                                                 |
    +-----------+-------------------------------------------------------------------------------+
    | max_val   | The maximum bound to be applied to the input data as a scalar.                |
    |           | Default: None                                                                 |
    +-----------+-------------------------------------------------------------------------------+
    | min_outbounds | Method to use when applying bounds as a string.                               |
    |               | Valid values are:                                                             |
    |               | retain: keep all pixels as is                                                 |
    |               | mask: mask all pixels that are out of range.                                  |
    |               | crop: set all out of range values to either min_val or max_val as appropriate |
    |               | Default: 'crop' (to match default found in productfile/xml.py and utils/normalize.py)|
    +-----------+-------------------------------------------------------------------------------+
    | max_outbounds | Method to use when applying bounds as a string.                               |
    |               | Valid values are:                                                             |
    |               | retain: keep all pixels as is                                                 |
    |               | mask: mask all pixels that are out of range.                                  |
    |               | crop: set all out of range values to either min_val or max_val as appropriate |
    |               | Default: 'crop' (to match default found in productfile/xml.py and utils/normalize.py)|
    +-----------+-------------------------------------------------------------------------------+
    | norm      | Boolean flag indicating whether to normalize (True) or not (False).           |
    |           | If True, returned data will be in the range from 0 to 1.                      |
    |           | If False, returned data will be in the range from min_val to max_val.         |
    |           | Default: True (to match default found in productfile/xml.py)                  |
    +-----------+-------------------------------------------------------------------------------+
    | inverse   | Boolean flag indicating whether to inverse (True) or not (False).             |
    |           | If True, returned data will be inverted                                       |
    |           | If False, returned data will not be inverted                                  |
    |           | Default: True (to match default found in productfile/xml.py)                  |
    +-----------+-------------------------------------------------------------------------------+
    '''
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
    return data


def invert_data_range(data, min_val=None, max_val=None):
    '''
    Invert data range to an array of data

    +------------+----------------------------------------------------------------+
    | Parameters | Description                                                    |
    +============+================================================================+
    | data       | Array of data where isinstance(numpy.ndarray) is True.         |
    +------------+----------------------------------------------------------------+

    +-----------+-------------------------------------------------------------------------------+
    | Keywords  | Description                                                                   |
    +===========+===============================================================================+
    | min_val   | The minimum bound to be applied to the input data as a scalar.                |
    |           | Default: None                                                                 |
    +-----------+-------------------------------------------------------------------------------+
    | max_val   | The maximum bound to be applied to the input data as a scalar.                |
    |           | Default: None                                                                 |
    +-----------+-------------------------------------------------------------------------------+
    '''
    if min_val is None:
        min_val = data.min()
    if max_val is None:
        max_val = data.max()
    LOG.info('Inverting data between %r and %r', min_val, max_val)

    if min_val > max_val:
        min_val, max_val = max_val, min_val

    if hasattr(data, 'mask'):
        # Preserve mask
        origmask = data.mask
        data = numpy.ma.masked_array((max_val - (data - min_val)).data, origmask)
    else:
        data = (max_val - (data - min_val))

    return data, min_val, max_val


def normalize(data, min_val=None, max_val=None, min_bounds='crop', max_bounds='crop'):
    '''
    Normalize data array with min_val and max_val to range 0 to 1
    bounds default is 'crop' to match apply_datarange

    +------------+----------------------------------------------------------------+
    | Parameters | Description                                                    |
    +============+================================================================+
    | data       | Array of data where isinstance(numpy.ndarray) is True.         |
    +------------+----------------------------------------------------------------+

    +-----------+-------------------------------------------------------------------------------+
    | Keywords  | Description                                                                   |
    +===========+===============================================================================+
    | min_val   | The minimum bound to be applied to the input data as a scalar.                |
    |           | Default: None                                                                 |
    +-----------+-------------------------------------------------------------------------------+
    | max_val   | The maximum bound to be applied to the input data as a scalar.                |
    |           | Default: None                                                                 |
    +-----------+-------------------------------------------------------------------------------+
    | min_outbounds | Method to use when applying bounds as a string.                               |
    |               | Valid values are:                                                             |
    |               | retain: keep all pixels as is                                                 |
    |               | mask: mask all pixels that are out of range.                                  |
    |               | crop: set all out of range values to either min_val or max_val as appropriate |
    |               | Default: 'crop' (to match default found in apply_data_range                   |
    +-----------+-------------------------------------------------------------------------------+
    | max_outbounds | Method to use when applying bounds as a string.                               |
    |               | Valid values are:                                                             |
    |               | retain: keep all pixels as is                                                 |
    |               | mask: mask all pixels that are out of range.                                  |
    |               | crop: set all out of range values to either min_val or max_val as appropriate |
    |               | Default: 'crop' (to match default found in apply_data_range                   |
    +-----------+-------------------------------------------------------------------------------+
    '''

    # Determine if mask is currently hardened
    hardmask = None
    if hasattr(data, 'hardmask'):
        hardmask = data.hardmask

    # Harden the mask to avoid unmasking bad values
    if hardmask is False:
        data.harden_mask()

    if min_val == None:
        min_val = data.min()
    if max_val == None:
        max_val = data.max()
    if min_bounds is None:
        min_bounds = 'retain'
    if max_bounds is None:
        max_bounds = 'retain'

    data = data.copy()
    data -= min_val
    data *= abs(1.0/(max_val - min_val))

    if min_bounds == 'retain':
        pass
    elif min_bounds == 'crop':
        data[numpy.ma.where(data < 0.0)] = 0.0
    elif min_bounds == 'mask':
        data = numpy.ma.masked_less(data, 0.0)

    if max_bounds == 'retain':
        pass
    elif max_bounds == 'crop':
        data[numpy.ma.where(data > 1.0)] = 1.0
    elif max_bounds == 'mask':
        data = numpy.ma.masked_greater(data, 1.0)

    # If the mask was originally not hardened, then unharden it now
    if hardmask is False:
        data.soften_mask()

    return data
