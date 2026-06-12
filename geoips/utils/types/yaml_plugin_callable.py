# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Universal adapter that wraps any YAML plugin dict into a callable DataTree
participant.

Every YAML-defined plugin (feature_annotator, gridline_annotator, product,
product_default, sector, …) becomes a first-class DAG step that adds its
configuration / metadata to the step DataTree.

The ``Workflow._resolve_plugin`` static method automatically wraps ``dict``
results (from YAML-based interfaces) in a ``YamlPluginCallable`` so that
the workflow executor can call them uniformly.
"""

from __future__ import annotations

import logging
from typing import Any

import xarray as xr

from geoips.utils.types.datatree_ditto import DataTreeDitto

LOG = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# kind → downstream kwarg name mapping
# ---------------------------------------------------------------------------

_KIND_TO_KWARG: dict[str, str] = {
    "algorithm": "xarray_obj",
    "colormapper": "mpl_colors_info",
    "feature_annotator": "feature_annotator",
    "filename_formatter": "output_fnames",
    "gridline_annotator": "gridline_annotator",
    "product": "product_name",
    "product_default": "product_default_info",
    "sector": "area_def",
}


class YamlPluginCallable:
    """Wraps a YAML plugin dict into a callable DataTree participant.

    The adapter satisfies the informal protocol that
    ``Workflow.call()`` expects::

        plg(data=upstream, **arguments) -> xr.DataTree

    It stores the YAML plugin's ``spec`` in the returned DataTree's
    ``ds.attrs`` together with metadata keys (``plugin_kind``,
    ``output_key``) that downstream hooks use to map the child node
    to the correct keyword argument.

    Parameters
    ----------
    yaml_plugin : dict
        The raw YAML plugin dict as returned by a YAML-based interface's
        ``get_plugin(name)``.  Must contain at least ``"interface"`` and
        ``"spec"``; ``"name"`` and ``"family"`` are optional.
    """

    def __init__(self, yaml_plugin: dict[str, Any]) -> None:
        self._yaml = yaml_plugin
        self.interface: str = yaml_plugin.get("interface", "")
        self.family: str = yaml_plugin.get("family", "")
        self.name: str = yaml_plugin.get("name", "yaml_callable")
        self.data_tree: bool = True

    # ------------------------------------------------------------------
    # callable protocol
    # ------------------------------------------------------------------

    def call(self, data: xr.DataTree | None = None, **kwargs: Any) -> xr.DataTree:
        """Produce a DataTree node carrying the YAML plugin's specification.

        Parameters
        ----------
        data : xr.DataTree or None
            Upstream DataTree (ignored for most YAML plugins; gridline
            annotators may use it for automatic spacing computation).
        **kwargs
            Step arguments from the workflow specification.  Currently
            forwarded for interface-specific post-processing.

        Returns
        -------
        xr.DataTree
            A ``DataTreeDitto`` whose ``ds.attrs`` contain the plugin's
            ``spec`` dictionary and the standard routing metadata.
        """
        spec = dict(self._yaml.get("spec", {}))
        kind = self.interface.rstrip("s")  # e.g. "gridline_annotators" → "gridline_annotator"

        if self.interface == "gridline_annotators" and data is not None:
            from geoips.dev.output_config import set_lonlat_spacing
            area_def = None
            if hasattr(data, "ds") and data.ds is not None:
                area_def = data.ds.attrs.get("area_definition")
            if area_def is None and hasattr(data, "children"):
                for child in data.children.values():
                    if hasattr(child, "ds") and child.ds is not None:
                        ad = child.ds.attrs.get("area_definition")
                        if ad is not None:
                            area_def = ad
                            break
            if area_def is not None:
                try:
                    spec = set_lonlat_spacing(spec, area_def)
                except Exception as exc:
                    LOG.warning(
                        "Failed to compute gridline spacing for %r: %s", self.name, exc
                    )

        ds = xr.Dataset(attrs={
            "spec": spec,
            "plugin_kind": kind,
            "output_key": _KIND_TO_KWARG.get(kind, kind),
        })
        dt = DataTreeDitto(ds, name=self.name)
        return dt

    def __call__(self, data: xr.DataTree | None = None, **kwargs: Any) -> xr.DataTree:
        """See :meth:`call`."""
        return self.call(data=data, **kwargs)

    # ------------------------------------------------------------------
    # introspection
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"interface={self.interface!r}, "
            f"name={self.name!r})"
        )
