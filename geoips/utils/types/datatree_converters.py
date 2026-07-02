# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Converter registration for ``DataTreeDitto`` and the shared registry.

Registers converters for ``dict``, ``xr.DataArray``, ``np.ndarray``,
``np.ma.MaskedArray``, and ``list`` via a single call site —
``DataTreeDitto.register_converter`` — which populates *both* the shared
``TypeConverterRegistry`` singleton (the live dispatch path used by the
plugin-lifecycle hooks and by ``DataTreeDitto`` conversions) and the
``DataTreeDitto._converters`` backward-compatibility mirror.  Using one
call per type means the two surfaces cannot drift out of sync.

This module contains *only wiring* — every converter function lives in the
single canonical module :mod:`geoips.utils.types.converters`. This module
imports those functions and registers them.

Registration is idempotent — calling this module twice (e.g. via
reload) will not produce duplicate entries.
"""

from __future__ import annotations

import logging

import numpy as np
import xarray as xr

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
from geoips.utils.types.datatree_ditto import DataTreeDitto

LOG = logging.getLogger(__name__)

# ============================================================================
# Register all converters via the single ``register_converter`` call site.
#
# ``DataTreeDitto.register_converter`` registers each pair on the shared
# ``TypeConverterRegistry`` (via ``register_bidirectional``) AND mirrors it onto
# ``DataTreeDitto._converters``, so both surfaces are populated from one call.
# ============================================================================

DataTreeDitto.register_converter(np.ndarray, numpy_to_dataset, dataset_to_numpy)
DataTreeDitto.register_converter(
    np.ma.MaskedArray,
    masked_array_to_dataset,
    dataset_to_masked_array,
)
DataTreeDitto.register_converter(dict, dict_to_dataset, dataset_to_dict)
DataTreeDitto.register_converter(
    xr.DataArray, dataarray_to_dataset, dataset_to_dataarray
)
DataTreeDitto.register_converter(list, list_to_dataset, dataset_to_list)

# Note: xr.Dataset is intentionally NOT registered. DataTreeDitto.__init__
# short-circuits when the input is already a Dataset (it does not call the
# converter dispatcher in that path), so a registered identity converter
# would be dead code.  ``get_original()`` returns a Dataset unchanged when
# no ``_ditto_original_type`` attr is present, which is exactly what we
# want for the Dataset passthrough case.
