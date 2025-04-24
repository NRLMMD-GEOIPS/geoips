# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Introspection functions on data arrays."""

import logging
import numpy

LOG = logging.getLogger(__name__)


def percent_unmasked(data_array):
    """Determine percent of a numpy.ma.Masked array that is not masked.

    Parameters
    ----------
    data_array : numpy.ma.MaskedArray
        Final processed array from which to determine coverage

    Returns
    -------
    float
        percent of input data array that is not masked.
    """
    return 100 * (float(numpy.ma.count(data_array)) / data_array.size)


def percent_not_nan(data_array):
    """Determine percent of a numpy.ndarray that is not NaN values.

    Parameters
    ----------
    data_array : numpy.ndarray
        Final processed array from which to determine coverage, invalid values
        specified by "numpy.nan".

    Returns
    -------
    float
        percent of input data array that is not numpy.nan.
    """
    return 100.0 * (
        1.0 - (numpy.count_nonzero(numpy.isnan(data_array)) / data_array.size)
    )
