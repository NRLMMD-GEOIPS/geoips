# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""The Order-Based Procflow (OBP) conduit binding registry.

``OBP_CONDUITS`` maps an upstream node's plugin *kind* to the
keyword-argument name and extractor a downstream plugin expects.  This
previously lived inside ``class_based_plugin`` (as ``_OBP_CONDUITS``) and was
reached back into by ``YamlPluginCallable``; it now has one home, so new plugin
kinds are wired in exactly one place.

This registry holds the **bespoke, per-kind call-signature bindings** for
legacy plugins — i.e. the specific keyword-argument name each legacy plugin
family expects and how to pull that value out of an upstream DataTree node.
It is the companion to ``geoips.utils.types.family_conversions``, which
handles *type* conversions; this module handles *argument wiring*. Together
they let the DataTree-based OBP drive legacy plugins.

Like ``family_conversions``, these bindings are a backwards-compatibility
layer: DataTree-native plugins (``data_tree = True``) consume the DataTree
directly and need no conduit entry, so this registry is expected to shrink as
plugins are migrated. (Originally adapted from @srikanth-kumar's work.)
"""

from __future__ import annotations

import xarray as xr

from geoips.utils.types.datatree_ditto import DataTreeDitto


def _extract_annotator_spec(child):
    spec = child.ds.attrs.get("spec") if child.ds is not None else None
    return {"spec": spec} if spec is not None else None


def _extract_attr(child, attr_name):
    return child.ds.attrs.get(attr_name) if child.ds is not None else None


def _flatten_datatree_for_legacy_plugin(ds, child):
    """Flatten a multi-child DataTree into a single Dataset for legacy plugins.

    Reader plugins produce DataTrees with child nodes per dataset key
    (``/METADATA``, ``/wind_speed``, …).  The root Dataset has no data
    variables — only attrs.  Legacy plugins expect a single flat Dataset,
    so children are merged here into one.

    Parameters
    ----------
    ds : xr.Dataset or None
        Root Dataset of the child node (may be empty).
    child : xr.DataTree
        The upstream child node with sub-datasets as its own children.

    Returns
    -------
    xr.Dataset
        Flattened Dataset, or *ds* unchanged if no children need merging.
    """
    if ds is not None and not ds.data_vars and child.children:
        children = list(child.children.values())
        if len(children) == 1:
            return children[0].to_dataset()
        return xr.merge([c.to_dataset() for c in children])
    return ds


def _extract_ds(child):
    """Extract the Dataset payload from a DataTree child.

    DataTreeDitto and plain DataTree nodes are unwrapped to their
    ``.ds`` attribute.  Reader-style multi-child DataTrees (root has
    attrs only, children hold the actual datasets) are flattened into a
    single Dataset via ``_flatten_datatree_for_legacy_plugin`` so
    legacy downstream plugins see a flat structure.

    Parameters
    ----------
    child : DataTreeDitto or xr.DataTree or Any
        Upstream child node or raw value.

    Returns
    -------
    xr.Dataset or Any
        Extracted/flattened Dataset, or *child* unchanged.
    """
    if isinstance(child, DataTreeDitto):
        ds = child.ds
    elif isinstance(child, xr.DataTree):
        ds = child.ds
    else:
        return child

    return _flatten_datatree_for_legacy_plugin(ds, child)


def _extract_product_name(child):
    return str(child.name) if child.name else None


def _extract_attrs_dict(child):
    return dict(child.ds.attrs) if child.ds is not None else {}


#: Maps an upstream node's plugin *kind* to the downstream kwarg name it feeds
#: and the extractor that pulls the value out of the node.  Add a new plugin
#: kind's wiring here (single location).
OBP_CONDUITS: dict[str, dict] = {
    "algorithm": {"kwarg": "xarray_obj", "extract": _extract_ds},
    "colormapper": {
        "kwarg": "mpl_colors_info",
        "extract": lambda c: _extract_attr(c, "_mpl_colors_info"),
    },
    "coverage_checker": {
        "kwarg": "coverage",
        "extract": lambda c: _extract_attr(c, "coverage"),
    },
    "feature_annotator": {
        "kwarg": "feature_annotator",
        "extract": _extract_annotator_spec,
    },
    "filename_formatter": {
        "kwarg": "output_fnames",
        "extract": lambda c: _extract_attr(c, "output_fnames"),
    },
    "gridline_annotator": {
        "kwarg": "gridline_annotator",
        "extract": _extract_annotator_spec,
    },
    "interpolator": {"kwarg": "xarray_obj", "extract": _extract_ds},
    "product": {"kwarg": "product_name", "extract": _extract_product_name},
    "product_default": {
        "kwarg": "product_default_info",
        "extract": _extract_attrs_dict,
    },
    "reader": {"kwarg": "xarray_obj", "extract": _extract_ds},
    "sector": {
        "kwarg": "area_def",
        "extract": lambda c: _extract_attr(c, "area_definition"),
    },
}


def kwarg_name_for_kind(kind: str) -> str:
    """Return the downstream kwarg name an upstream *kind* feeds.

    Falls back to *kind* itself when the kind has no registered conduit.
    """
    conduit = OBP_CONDUITS.get(kind)
    return conduit["kwarg"] if conduit is not None else kind
