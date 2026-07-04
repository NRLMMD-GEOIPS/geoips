# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Converter registration for the shared type-converter registry.

Registers converters for ``dict``, ``xr.DataArray``, ``np.ndarray``,
``np.ma.MaskedArray``, and ``list`` on the shared ``TypeConverterRegistry``
singleton -- the live dispatch path used by the plugin-lifecycle hooks and by
``DataTreeDitto`` conversions.

This module contains *only wiring* -- every converter function lives in the
single canonical module :mod:`geoips.utils.types.converters`. This module
imports those functions and registers them.

Registration is idempotent -- calling this module twice (e.g. via reload) will
not produce duplicate entries.
"""

from __future__ import annotations

import numpy as np
import xarray as xr

from geoips.utils.types.converter_registry import converter_registry
from geoips.utils.types.converters import (
    dataarray_to_dataset,
    dataset_to_dataarray,
    dataset_to_dict,
    dataset_to_list,
    dataset_to_masked_array,
    dataset_to_numpy,
    dict_to_dataset,
    list_to_dataset,
    masked_array_to_dataset,
    numpy_to_dataset,
)

converter_registry.register_bidirectional(
    np.ndarray, xr.Dataset, numpy_to_dataset, dataset_to_numpy
)
converter_registry.register_bidirectional(
    np.ma.MaskedArray, xr.Dataset, masked_array_to_dataset, dataset_to_masked_array
)
converter_registry.register_bidirectional(
    dict, xr.Dataset, dict_to_dataset, dataset_to_dict
)
converter_registry.register_bidirectional(
    xr.DataArray, xr.Dataset, dataarray_to_dataset, dataset_to_dataarray
)
converter_registry.register_bidirectional(
    list, xr.Dataset, list_to_dataset, dataset_to_list
)

# Note: xr.Dataset is intentionally NOT registered. DataTreeDitto.__init__
# short-circuits when the input is already a Dataset (it does not call the
# converter dispatcher in that path), so a registered identity converter
# would be dead code.  ``get_original()`` returns a Dataset unchanged when
# no ``_ditto_original_type`` attr is present, which is exactly what we
# want for the Dataset passthrough case.
