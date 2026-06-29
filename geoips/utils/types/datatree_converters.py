# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Converter registration for ``DataTreeDitto`` and the shared registry.

Registers converters for ``dict``, ``xr.DataArray``, ``np.ndarray``,
and ``np.ma.MaskedArray`` on both the ``TypeConverterRegistry``
singleton and the ``DataTreeDitto._converters`` compatibility surface
so that round-trip storage and plugin-lifecycle hooks use the same
conversion functions.

Registration is idempotent — calling this module twice (e.g. via
reload) will not produce duplicate entries.
"""

from __future__ import annotations

import logging

import numpy as np
import xarray as xr

from geoips.utils.types.converter_registry import converter_registry
from geoips.utils.types.converters import (
    dataset_to_list,
    dataset_to_masked_array,
    dataset_to_numpy,
    list_to_dataset,
    masked_array_to_dataset,
    numpy_to_dataset,
)
from geoips.utils.types.datatree_ditto import DataTreeDitto

LOG = logging.getLogger(__name__)

# ============================================================================
# dict ↔ Dataset  (kept local — these are the specialised dict converters
#                  that preserve insertion order via _ditto_keys)
# ============================================================================


def _dict_to_dataset(d: dict, **kwargs) -> xr.Dataset:
    """Convert a ``dict`` to an ``xr.Dataset`` for storage in DataTreeDitto.

    Numpy-array values become data variables (each with synthetic dim
    names of the form ``<key>_dim_<i>``); scalar values (``int``,
    ``float``, ``str``, ``bool``, ``None``) become ``attrs`` under a
    ``_ditto_attr_<key>`` namespace; any other value is stringified.
    Original insertion order is preserved in ``_ditto_keys``.
    """
    ds = xr.Dataset()
    ds.attrs["_ditto_original_type"] = f"{dict.__module__}.{dict.__name__}"
    ds.attrs["_ditto_keys"] = list(d.keys())
    for key, value in d.items():
        if isinstance(value, np.ndarray):
            dims = [f"{key}_dim_{i}" for i in range(value.ndim)]
            ds[key] = xr.DataArray(value, dims=dims)
        elif isinstance(value, (int, float, str, bool)) or value is None:
            ds.attrs[f"_ditto_attr_{key}"] = value
        else:
            LOG.warning(
                "Stringifying non-scalar value for key %r (type %s) — "
                "round-trip will NOT preserve the original object",
                key,
                type(value).__name__,
            )
            ds.attrs[f"_ditto_attr_{key}"] = str(value)
    return ds


def _dataset_to_dict(ds: xr.Dataset, **kwargs) -> dict:
    """Convert a dict-origin ``xr.Dataset`` back to a plain ``dict``.

    Walks ``_ditto_keys`` to preserve original insertion order.
    """
    keys = ds.attrs.get("_ditto_keys", [])
    out: dict = {}
    for k in keys:
        if k in ds.data_vars:
            out[k] = ds[k].values
        elif f"_ditto_attr_{k}" in ds.attrs:
            out[k] = ds.attrs[f"_ditto_attr_{k}"]
    return out


# ============================================================================
# DataArray ↔ Dataset
# ============================================================================


def _da_to_ds(da: xr.DataArray, **kwargs) -> xr.Dataset:
    """Convert a ``DataArray`` to a ``Dataset`` for DataTreeDitto storage."""
    name = da.name or "data"
    ds = da.to_dataset(name=name)
    ds.attrs["_ditto_original_type"] = (
        f"{xr.DataArray.__module__}.{xr.DataArray.__name__}"
    )
    ds.attrs["_ditto_da_name"] = name
    return ds


def _ds_to_da(ds: xr.Dataset, **kwargs) -> xr.DataArray:
    """Convert a DataArray-origin Dataset back to ``xr.DataArray``."""
    name = ds.attrs.get("_ditto_da_name")
    if name is None:
        if len(ds.data_vars) != 1:
            raise ValueError(
                "Cannot convert Dataset to DataArray: "
                "'_ditto_da_name' attr is missing and the Dataset has "
                f"{len(ds.data_vars)} data_vars (need exactly 1)."
            )
        name = next(iter(ds.data_vars))
    return ds[name]


# ============================================================================
# Register on BOTH surfaces
# ============================================================================

# --- converter_registry (shared, used by plugin hooks) -----------------------

converter_registry.register(np.ndarray, xr.Dataset, numpy_to_dataset)
converter_registry.register(xr.Dataset, np.ndarray, dataset_to_numpy)

converter_registry.register(np.ma.MaskedArray, xr.Dataset, masked_array_to_dataset)
converter_registry.register(xr.Dataset, np.ma.MaskedArray, dataset_to_masked_array)

converter_registry.register(dict, xr.Dataset, _dict_to_dataset)
converter_registry.register(xr.Dataset, dict, _dataset_to_dict)

converter_registry.register(xr.DataArray, xr.Dataset, _da_to_ds)
converter_registry.register(xr.Dataset, xr.DataArray, _ds_to_da)

converter_registry.register(list, xr.Dataset, list_to_dataset)
converter_registry.register(xr.Dataset, list, dataset_to_list)

# --- DataTreeDitto._converters (backward-compat surface) ---------------------

DataTreeDitto.register_converter(np.ndarray, numpy_to_dataset, dataset_to_numpy)
DataTreeDitto.register_converter(
    np.ma.MaskedArray, masked_array_to_dataset, dataset_to_masked_array,
)
DataTreeDitto.register_converter(dict, _dict_to_dataset, _dataset_to_dict)
DataTreeDitto.register_converter(xr.DataArray, _da_to_ds, _ds_to_da)
DataTreeDitto.register_converter(list, list_to_dataset, dataset_to_list)

# Note: xr.Dataset is intentionally NOT registered. DataTreeDitto.__init__
# short-circuits when the input is already a Dataset (it does not call the
# converter dispatcher in that path), so a registered identity converter
# would be dead code.  ``get_original()`` returns a Dataset unchanged when
# no ``_ditto_original_type`` attr is present, which is exactly what we
# want for the Dataset passthrough case.
