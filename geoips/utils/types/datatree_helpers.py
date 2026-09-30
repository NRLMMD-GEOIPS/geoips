# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Neutral helpers for flattening ``xr.DataTree`` nodes into mutable Datasets.

These helpers previously lived as duplicated methods on plugin base classes
(``BaseClassPlugin._to_mutable_dataset``) and inside
``geoips.utils.types.script_datatree``. They have one home now so the
interface-level plugin classes (algorithms, coverage_checkers,
filename_formatters) can share a single implementation without reaching back
into the base plugin class or the scripting module.

The canonical flattener is **recursive** and runs
``normalize_geoips_dataset_coords`` on the result, matching the behavior the
legacy plugin ``_pre_call`` overrides relied on before this refactor.
"""

from __future__ import annotations

import xarray as xr

from geoips.xarray_utils.coords import normalize_geoips_dataset_coords


def has_data_vars(node):
    """Return whether *node* or any descendant contains data variables.

    Parameters
    ----------
    node : xarray.DataTree
        DataTree node to inspect.

    Returns
    -------
    bool
        ``True`` if *node* itself carries data variables, or any of its
        descendant nodes do.
    """
    if node.ds is not None and bool(node.ds.data_vars):
        return True
    return any(has_data_vars(child) for child in node.children.values())


def to_mutable_dataset(node):
    """Return a mutable ``xr.Dataset`` flattening *node* and its descendants.

    ``DataTree.ds`` returns an immutable ``DatasetView``. Plugins that write
    back into the dataset (e.g. ``xobj[product_name] = ...``) need a mutable
    ``xr.Dataset``. This helper recursively collects every descendant that
    carries data variables, merges them into a single mutable Dataset,
    propagates node attributes, and applies
    ``normalize_geoips_dataset_coords`` so the result matches the GeoIPS
    coordinate convention legacy ``call()`` methods expect.

    Parameters
    ----------
    node : xarray.DataTree
        DataTree node to flatten. May be a reader-style multi-level tree
        (root attrs-only, sub-children holding each variable group) or a
        single-level multi-child tree.

    Returns
    -------
    xarray.Dataset
        A mutable, coord-normalized Dataset merging all data-bearing
        descendants of *node*. ``attrs`` are merged with node attrs taking
        precedence.
    """
    datasets = []
    if node.ds is not None and bool(node.ds.data_vars):
        datasets.append(node.to_dataset())
    for child in node.children.values():
        if has_data_vars(child):
            datasets.append(to_mutable_dataset(child))

    if not datasets:
        dataset = xr.Dataset(attrs=dict(node.attrs))
    elif len(datasets) == 1:
        dataset = datasets[0].copy(deep=True)
    else:
        dataset = xr.merge(datasets).copy(deep=True)
    dataset.attrs = {**dict(node.attrs), **dict(dataset.attrs)}
    return normalize_geoips_dataset_coords(dataset)
