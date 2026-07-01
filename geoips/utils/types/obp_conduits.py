# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""The Order-Based Procflow (OBP) conduit binding registry.

:data:`OBP_CONDUITS` maps an upstream node's plugin *kind* to the
keyword-argument name and extractor a downstream plugin expects.  This
previously lived inside ``class_based_plugin`` (as ``_OBP_CONDUITS``) and was
reached back into by ``YamlPluginCallable``; it now has one home, so new plugin
kinds are wired in exactly one place.
"""

from __future__ import annotations

import xarray as xr


def _extract_annotator_spec(child):
    spec = child.ds.attrs.get("spec") if child.ds is not None else None
    return {"spec": spec} if spec is not None else None


def _extract_attr(child, attr_name):
    return child.ds.attrs.get(attr_name) if child.ds is not None else None


def _extract_ds(child):
    from geoips.utils.types.datatree_ditto import DataTreeDitto

    if isinstance(child, DataTreeDitto):
        return child.ds
    if isinstance(child, xr.DataTree):
        return child.ds
    return child


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
