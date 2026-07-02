# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Pure type-conversion functions and ``FamilyConversionSpec``.

Every converter here is a standalone function with no side effects,
independently testable, and reusable by ``DataTreeDitto``, the
``TypeConverterRegistry``, and the plugin-lifecycle hooks.

Metadata policy
---------------
* ``_ditto_*`` keys in ``attrs`` — storage-layer metadata used by
  ``DataTreeDitto`` for round-trip recovery (original type, shape,
  dtype, …).
* ``_conv_*`` keys in ``attrs`` — semantic-conversion metadata used
  by the plugin-lifecycle hooks to record context (e.g. variable
  ordering, mask presence).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import numpy as np
import xarray as xr

# ---------------------------------------------------------------------------
# FamilyConversionSpec
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FamilyConversionSpec:
    """Defines the type conversions needed for a single plugin family.

    Parameters
    ----------
    input_type : type or None
        The type expected by the plugin's ``call()`` after the input
        converter has been applied.  ``None`` means "no conversion".
    input_converter : callable or None
        ``converter(dataset) → input_type``.  Called by ``_pre_call``.
    output_type : type or None
        The type produced by the plugin's ``call()``.
    output_converter : callable or None
        ``converter(plugin_result) → xr.Dataset``.  Called by
        ``_post_call``.  ``None`` means the plugin already returns a
        ``Dataset``.
    """

    input_type: type | None = None
    input_converter: Callable | None = None
    output_type: type | None = None
    output_converter: Callable | None = None


# ---------------------------------------------------------------------------
# numpy.ndarray ↔ xr.Dataset
# ---------------------------------------------------------------------------


def numpy_to_dataset(
    obj: np.ndarray,
    name: str = "data",
    dims: list[str] | None = None,
    **kwargs: Any,
) -> xr.Dataset:
    """Convert a numpy array to an ``xr.Dataset`` with ``_ditto_*`` metadata.

    Parameters
    ----------
    obj : np.ndarray
        Input array (may be a regular ndarray or MaskedArray).
    name : str
        Data-variable name in the resulting dataset.
    dims : list[str] or None
        Dimension names.  Auto-generated (``dim_0``, ``dim_1``, …) when
        ``None``.
    **kwargs
        Ignored — forward-compatibility slot.

    Returns
    -------
    xr.Dataset
    """
    if dims is None:
        dims = [f"dim_{i}" for i in range(obj.ndim)]

    data_array = xr.DataArray(obj, dims=dims, name=name)
    dataset = data_array.to_dataset()

    dataset.attrs.update(
        {
            "_ditto_original_type": _type_key(type(obj)),
            "_ditto_original_shape": obj.shape,
            "_ditto_original_dtype": str(obj.dtype),
            "_ditto_var_name": name,
            "_ditto_dims": dims,
        }
    )
    return dataset


def dataset_to_numpy(dataset: xr.Dataset, **kwargs: Any) -> np.ndarray:
    """Extract a numpy array from a dataset produced by ``numpy_to_dataset``.

    Uses ``_ditto_var_name`` metadata to locate the correct data
    variable; falls back to the first data variable.

    Parameters
    ----------
    dataset : xr.Dataset
    **kwargs
        Ignored.

    Returns
    -------
    np.ndarray
    """
    var_name = dataset.attrs.get("_ditto_var_name", "data")
    if var_name not in dataset.data_vars:
        if not dataset.data_vars:
            raise ValueError(
                "Dataset has no data variables; cannot extract numpy array"
            )
        var_name = next(iter(dataset.data_vars))
    return dataset[var_name].values


# ---------------------------------------------------------------------------
# numpy.ma.MaskedArray ↔ xr.Dataset
# ---------------------------------------------------------------------------


def masked_array_to_dataset(
    obj: np.ma.MaskedArray,
    name: str = "data",
    dims: list[str] | None = None,
    **kwargs: Any,
) -> xr.Dataset:
    """Convert a ``numpy.ma.MaskedArray`` to ``xr.Dataset``.

    Stores the mask as a companion data variable (``{name}_mask``) and
    the ``fill_value`` in ``attrs`` so that ``dataset_to_masked_array``
    can reconstruct the original MaskedArray faithfully.

    Parameters
    ----------
    obj : np.ma.MaskedArray
    name : str
        Base data-variable name.
    dims : list[str] or None
    **kwargs
        Ignored.

    Returns
    -------
    xr.Dataset
    """
    if dims is None:
        dims = [f"dim_{i}" for i in range(obj.ndim)]

    # Store the underlying data preserving the original dtype. Do NOT fill
    # masked entries with NaN: NaN is not representable in integer/unsigned/
    # string dtypes (``np.ma.filled(int_array, np.nan)`` raises), and even
    # where it succeeds it silently upcasts the dtype. The companion mask
    # variable records which entries are masked so the exact original array is
    # reconstructed in ``dataset_to_masked_array``.
    data_arr = xr.DataArray(np.ma.getdata(obj), dims=dims, name=name)
    dataset = data_arr.to_dataset()

    # Store mask as bool
    mask_name = f"{name}_mask"
    dataset[mask_name] = xr.DataArray(
        np.ma.getmaskarray(obj), dims=dims, name=mask_name
    )

    dataset.attrs.update(
        {
            "_ditto_original_type": _type_key(np.ma.MaskedArray),
            "_ditto_original_shape": obj.shape,
            "_ditto_original_dtype": str(obj.dtype),
            "_ditto_var_name": name,
            "_ditto_dims": dims,
            "_conv_mask_var": mask_name,
        }
    )
    # Preserve the fill_value as a native scalar without forcing a float cast
    # (integer and string MaskedArrays have non-float fill values).
    fill_value = getattr(obj, "fill_value", None)
    if fill_value is not None:
        dataset.attrs["_conv_fill_value"] = (
            fill_value.item() if hasattr(fill_value, "item") else fill_value
        )

    return dataset


def dataset_to_masked_array(dataset: xr.Dataset, **kwargs: Any) -> np.ma.MaskedArray:
    """Reconstruct a ``numpy.ma.MaskedArray`` from a dataset.

    Uses ``_conv_mask_var`` and ``_conv_fill_value`` metadata written
    by ``masked_array_to_dataset``.

    Parameters
    ----------
    dataset : xr.Dataset
    **kwargs
        Ignored.

    Returns
    -------
    np.ma.MaskedArray
    """
    var_name = dataset.attrs.get("_ditto_var_name", "data")
    mask_name = dataset.attrs.get("_conv_mask_var", f"{var_name}_mask")
    fill_value = dataset.attrs.get("_conv_fill_value", None)

    data = dataset[var_name].values
    mask = dataset[mask_name].values if mask_name in dataset.data_vars else False

    # Restore the original dtype if it was recorded. In-memory this is a no-op
    # (the data was stored via ``np.ma.getdata`` with its dtype intact), but it
    # recovers the correct dtype after a serialization round-trip that may have
    # upcast the data (e.g. netCDF promoting integers to float).
    orig_dtype = dataset.attrs.get("_ditto_original_dtype")
    if orig_dtype is not None:
        try:
            data = data.astype(orig_dtype)
        except (TypeError, ValueError):
            pass

    result = np.ma.MaskedArray(data, mask=mask)
    if fill_value is not None:
        try:
            result.fill_value = fill_value
        except (TypeError, ValueError):
            pass
    return result


# ---------------------------------------------------------------------------
# Dataset  ⇄  list[np.ndarray]
# ---------------------------------------------------------------------------


def dataset_vars_to_list(dataset: xr.Dataset, **kwargs: Any) -> list[np.ndarray]:
    """Extract every data variable as a list of arrays.

    Arrays are returned in insertion order (the order they appear when
    iterating ``dataset.data_vars``).  This is stable for a given
    dataset but callers that need a specific ordering should sort or
    filter the list themselves.

    Parameters
    ----------
    dataset : xr.Dataset
    **kwargs
        Ignored — future slot for ``variables`` subset / ordering
        context.

    Returns
    -------
    list[np.ndarray]
        One array per data variable, in insertion order.
    """
    return [dataset[var].values for var in dataset.data_vars]


# ---------------------------------------------------------------------------
# list  →  xr.Dataset
# ---------------------------------------------------------------------------


def list_to_dataset(
    obj: list,
    **kwargs: Any,
) -> xr.Dataset:
    """Store a plain list as attrs in a Dataset.

    Parameters
    ----------
    obj : list
        List of any JSON-serializable values (e.g. filenames).
    **kwargs
        Ignored.

    Returns
    -------
    xr.Dataset
        Dataset with ``_ditto_list_value`` in attrs.
    """
    ds = xr.Dataset(
        attrs={
            "_ditto_original_type": _type_key(list),
            "_ditto_list_value": obj,
        }
    )
    return ds


def dataset_to_list(dataset: xr.Dataset, **kwargs: Any) -> list:
    """Recover a list from attrs.

    Parameters
    ----------
    dataset : xr.Dataset
    **kwargs
        Ignored.

    Returns
    -------
    list
        The stored list value.
    """
    return dataset.attrs.get("_ditto_list_value", [])


# ---------------------------------------------------------------------------
# Dataset  ⇄  dict[str, Dataset]
# ---------------------------------------------------------------------------


def dataset_to_dataset_dict(
    dataset: xr.Dataset, **kwargs: Any
) -> dict[str, xr.Dataset]:
    """Split a multi-variable ``Dataset`` into a dict of single-variable datasets.

    Keys are the data-variable names; each value is a ``Dataset``
    containing exactly one data variable (plus shared coordinates).

    Parameters
    ----------
    dataset : xr.Dataset
    **kwargs
        Ignored.

    Returns
    -------
    dict[str, xr.Dataset]
    """
    result: dict[str, xr.Dataset] = {}
    for var in dataset.data_vars:
        result[var] = dataset[[var]]
    return result


def dataset_dict_to_dataset(dct: dict[str, xr.Dataset], **kwargs: Any) -> xr.Dataset:
    """Merge a dict of datasets into a single ``xr.Dataset``.

    Uses ``xarray.merge`` for alignment.  The dict insertion order is
    preserved via a ``_conv_var_order`` attribute.

    Parameters
    ----------
    dct : dict[str, xr.Dataset]
    **kwargs
        Ignored.

    Returns
    -------
    xr.Dataset
    """
    datasets = list(dct.values())
    merged: xr.Dataset = xr.merge(datasets) if datasets else xr.Dataset()
    merged.attrs["_conv_var_order"] = list(dct.keys())
    return merged


# ---------------------------------------------------------------------------
# dict  ⇄  xr.Dataset  (generic, insertion-order-preserving)
# ---------------------------------------------------------------------------


def dict_to_dataset(obj: dict, **kwargs: Any) -> xr.Dataset:
    """Convert a plain ``dict`` to an ``xr.Dataset`` for DataTreeDitto storage.

    Numpy-array values become data variables (each with synthetic dim
    names of the form ``<key>_dim_<i>``); scalar values (``int``,
    ``float``, ``str``, ``bool``, ``None``) become ``attrs`` under a
    ``_ditto_attr_<key>`` namespace; any other value type raises
    ``TypeError``. Original insertion order is preserved in ``_ditto_keys``.

    Parameters
    ----------
    obj : dict
        Dictionary of numpy arrays and/or scalars.
    **kwargs
        Ignored.

    Returns
    -------
    xr.Dataset
    """
    ds = xr.Dataset()
    ds.attrs["_ditto_original_type"] = _type_key(dict)
    ds.attrs["_ditto_keys"] = list(obj.keys())
    for key, value in obj.items():
        if isinstance(value, np.ndarray):
            dims = [f"{key}_dim_{i}" for i in range(value.ndim)]
            ds[key] = xr.DataArray(value, dims=dims)
        elif isinstance(value, (int, float, str, bool)) or value is None:
            ds.attrs[f"_ditto_attr_{key}"] = value
        else:
            raise TypeError(
                f"Cannot store value of type {type(value).__name__!r} "
                f"for key {key!r} in dict-to-Dataset conversion. "
                f"Only numpy arrays, scalars (int, float, str, bool, None) "
                f"are supported."
            )
    return ds


def dataset_to_dict(dataset: xr.Dataset, **kwargs: Any) -> dict:
    """Recover a plain ``dict`` from a dict-origin ``xr.Dataset``.

    Walks ``_ditto_keys`` to preserve original insertion order.

    Parameters
    ----------
    dataset : xr.Dataset
    **kwargs
        Ignored.

    Returns
    -------
    dict
    """
    keys = dataset.attrs.get("_ditto_keys", [])
    out: dict = {}
    for k in keys:
        if k in dataset.data_vars:
            out[k] = dataset[k].values
        elif f"_ditto_attr_{k}" in dataset.attrs:
            out[k] = dataset.attrs[f"_ditto_attr_{k}"]
    return out


# ---------------------------------------------------------------------------
# xr.DataArray  ⇄  xr.Dataset
# ---------------------------------------------------------------------------


def dataarray_to_dataset(obj: xr.DataArray, **kwargs: Any) -> xr.Dataset:
    """Convert a ``DataArray`` to a ``Dataset`` for DataTreeDitto storage.

    Parameters
    ----------
    obj : xr.DataArray
    **kwargs
        Ignored.

    Returns
    -------
    xr.Dataset
    """
    name = obj.name or "data"
    ds = obj.to_dataset(name=name)
    ds.attrs["_ditto_original_type"] = _type_key(xr.DataArray)
    ds.attrs["_ditto_da_name"] = name
    return ds


def dataset_to_dataarray(dataset: xr.Dataset, **kwargs: Any) -> xr.DataArray:
    """Recover an ``xr.DataArray`` from a DataArray-origin ``xr.Dataset``.

    Parameters
    ----------
    dataset : xr.Dataset
    **kwargs
        Ignored.

    Returns
    -------
    xr.DataArray
    """
    name = dataset.attrs.get("_ditto_da_name")
    if name is None:
        if len(dataset.data_vars) != 1:
            raise ValueError(
                "Cannot convert Dataset to DataArray: "
                "'_ditto_da_name' attr is missing and the Dataset has "
                f"{len(dataset.data_vars)} data_vars (need exactly 1)."
            )
        name = next(iter(dataset.data_vars))
    return dataset[name]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _type_key(t: type) -> str:
    """Return ``module.ClassName`` string used in ``_ditto_original_type``."""
    return f"{t.__module__}.{t.__name__}"
