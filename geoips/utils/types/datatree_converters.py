# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Converter registry for DataTreeDitto round-trip conversion.

These converters are registered at import time so that DataTreeDitto
can automatically convert non-xarray plugin output types to xarray.Dataset
and back. Registration is idempotent.
"""

from __future__ import annotations

import logging

import numpy as np
import xarray as xr

from geoips.utils.types.datatree_ditto import DataTreeDitto

LOG = logging.getLogger(__name__)


def _dict_to_dataset(d: dict, **kwargs) -> xr.Dataset:
    """Convert a ``dict`` to an ``xr.Dataset``.

    Numpy-array values become data variables (each with synthetic dim names
    of the form ``<key>_dim_<i>``); scalar values (``int``, ``float``,
    ``str``, ``bool``, ``None``) become ``attrs`` under a ``_ditto_attr_<key>``
    namespace; any other value is stringified into ``attrs``. The original
    insertion order is preserved in ``_ditto_keys`` so ``_dataset_to_dict``
    can rebuild the dict faithfully.
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
            ds.attrs[f"_ditto_attr_{key}"] = str(value)
    return ds


def _dataset_to_dict(ds: xr.Dataset, **kwargs) -> dict:
    """Convert a dict-origin ``xr.Dataset`` back to a plain ``dict``.

    Walks ``_ditto_keys`` to preserve original insertion order. Data
    variables become numpy arrays (via ``.values``); attrs in the
    ``_ditto_attr_<key>`` namespace are restored as-is.
    """
    keys = ds.attrs.get("_ditto_keys", [])
    out: dict = {}
    for k in keys:
        if k in ds.data_vars:
            out[k] = ds[k].values
        elif f"_ditto_attr_{k}" in ds.attrs:
            out[k] = ds.attrs[f"_ditto_attr_{k}"]
    return out


# Register dict ↔ dataset
DataTreeDitto.register_converter(dict, _dict_to_dataset, _dataset_to_dict)


def _da_to_ds(da: xr.DataArray, **kwargs) -> xr.Dataset:
    """Convert an ``xr.DataArray`` to an ``xr.Dataset`` for storage.

    The DataArray's name (or ``"data"`` if unnamed) becomes the only data
    variable. ``_ditto_da_name`` is stamped into ``attrs`` so the round-trip
    can pick the right variable back out.
    """
    name = da.name or "data"
    ds = da.to_dataset(name=name)
    ds.attrs["_ditto_original_type"] = (
        f"{xr.DataArray.__module__}.{xr.DataArray.__name__}"
    )
    ds.attrs["_ditto_da_name"] = name
    return ds


def _ds_to_da(ds: xr.Dataset, **kwargs) -> xr.DataArray:
    """Convert a DataArray-origin ``xr.Dataset`` back to an ``xr.DataArray``."""
    name = ds.attrs.get("_ditto_da_name") or next(iter(ds.data_vars))
    return ds[name]


# Register DataArray ↔ Dataset
DataTreeDitto.register_converter(xr.DataArray, _da_to_ds, _ds_to_da)


# Note: xr.Dataset is intentionally NOT registered. DataTreeDitto.__init__
# short-circuits when the input is already a Dataset (it does not call the
# converter dispatcher in that path), so a registered identity converter
# would be dead code. ``get_original()`` returns a Dataset unchanged when
# no ``_ditto_original_type`` attr is present, which is exactly what we
# want for the Dataset passthrough case.
