# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""DataTree-spec Workflow composite executor.

The ``Workflow`` class is a non-registered runtime executor that loads a
validated ``WorkflowSpecModel``, resolves plugins, builds a topological step
order, and walks through the steps collecting downstream provenance into an
``xr.DataTree``.  Retention is governed by the Strategy pattern so the
execution loop never branches on the policy name.

Split / join steps are accepted by the schema but are not implemented;
the runtime raises ``NotImplementedError`` when encountering them.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
import dataclasses
from collections import deque
from datetime import datetime, timezone
from typing import Any

import xarray as xr

from geoips.pydantic_models.v1.workflows import (
    DEFAULT_RETENTION,
    SCAFFOLD_KINDS,
    WorkflowSpecModel,
)
from geoips.utils.types.datatree_ditto import DataTreeDitto
from geoips.utils.types.tokenization import (
    compute_arguments_hash,
    compute_step_output_token,
)

LOG = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class StepProvenance:
    """Per-step provenance bundle stamped into a step node's ``attrs``."""

    plugin_name: str
    plugin_kind: str
    start_time: str
    end_time: str
    arguments_hash: str
    output_token: str
    gc_status: str = "kept"


class RetentionPolicy(ABC):
    """Decides whether a step's data variables may be garbage-collected.

    Parameters
    ----------
    spec : WorkflowSpecModel
        The workflow specification.
    """

    def __init__(self, spec: WorkflowSpecModel) -> None:
        self._spec = spec

    @abstractmethod
    def can_gc(self, step_id: str, *, executed: set[str]) -> bool:
        """Return True if the step's ``data_vars`` can be dropped."""

    def _is_output(self, step_id: str) -> bool:
        return step_id in (self._spec.outputs or ())

    def _is_kept(self, step_id: str) -> bool:
        return self._spec.steps[step_id].keep is True

    def _has_pending_consumers(self, step_id: str, executed: set[str]) -> bool:
        for other_id, other_step in self._spec.steps.items():
            if other_id not in executed:
                for dep in other_step.depends_on or ():
                    if dep == step_id:
                        return True
        return False


class KeepAllPolicy(RetentionPolicy):
    """Never GC any step data."""

    def can_gc(self, step_id: str, *, executed: set[str]) -> bool:
        """Return True if the step's data_vars can be dropped."""
        return False


class KeepReferencedPolicy(RetentionPolicy):
    """GC when no remaining downstream step references this step."""

    def can_gc(self, step_id: str, *, executed: set[str]) -> bool:
        """Return True if the step's data_vars can be dropped."""
        if self._is_output(step_id) or self._is_kept(step_id):
            return False
        return not self._has_pending_consumers(step_id, executed)


class KeepOutputsOnlyPolicy(RetentionPolicy):
    """GC everything except declared outputs and ``keep=True`` steps."""

    def can_gc(self, step_id: str, *, executed: set[str]) -> bool:
        """Return True if the step's data_vars can be dropped."""
        return not (self._is_output(step_id) or self._is_kept(step_id))


_POLICIES: dict[str, type[RetentionPolicy]] = {
    "keep_all": KeepAllPolicy,
    "keep_referenced": KeepReferencedPolicy,
    "keep_outputs_only": KeepOutputsOnlyPolicy,
}


class Workflow:
    """Non-registered runtime executor for a validated workflow spec.

    This is an *orchestrator* that co-ordinates registered plugins — it does
    not inherit from ``BaseClassPlugin`` and is not itself registerable.
    Plugins are resolved via ``geoips.interfaces`` at runtime.

    Parameters
    ----------
    spec : WorkflowSpecModel
        A pydantic-validated workflow specification.
    workflow_name : str
        The workflow name (used as the root DataTree node name).
    """

    def __init__(self, spec: WorkflowSpecModel, workflow_name: str) -> None:
        self._spec = spec
        self._wf_name = workflow_name
        self._order: list[str] = self._topological_order()
        self._retention: RetentionPolicy = _POLICIES[
            self._spec.retention or DEFAULT_RETENTION
        ](self._spec)

    def _topological_order(self) -> list[str]:
        """Return step ids in a valid execution order.

        Uses Kahn's algorithm.  Cyclicity is enforced at pydantic validation
        time by ``_validate_dependencies``; this function assumes a DAG.
        """
        step_ids = list(self._spec.steps.keys())
        indegree = {sid: len(step.depends_on or ()) for sid, step in self._spec.steps.items()}

        queue = deque(sid for sid in step_ids if indegree[sid] == 0)
        order: list[str] = []
        while queue:
            sid = queue.popleft()
            order.append(sid)
            for other_sid, other_step in self._spec.steps.items():
                if sid in (other_step.depends_on or ()):
                    indegree[other_sid] -= 1
                    if indegree[other_sid] == 0:
                        queue.append(other_sid)

        return order

    def _collect_upstream_data(
        self,
        tree: xr.DataTree,
        depends_on: list[str],
    ) -> xr.DataTree:
        """Collect upstream step outputs into a single DataTree.

        Returns an ``xr.DataTree`` named ``multi_input`` with each
        upstream node as a child under its step id.  Readers (empty
        ``depends_on``) receive an empty DataTree.
        """
        if not depends_on:
            return xr.DataTree(name="empty")

        result = xr.DataTree(name="multi_input")
        for dep_id in depends_on:
            dep_node = tree.get(dep_id)
            if dep_node is not None:
                result[dep_id] = dep_node
        return result

    def _attach_step_node(
        self, tree: xr.DataTree, step_id: str, step_data: Any,
        step_kind: str = "",
    ) -> None:
        """Attach a step's output as a child node in the DataTree.

        Parameters
        ----------
        tree : xr.DataTree
            The workflow's root DataTree.
        step_id : str
            Step identifier used as the child node name.
        step_data : Any
            The return value of ``plugin._invoke(...)``.
        step_kind : str
            The step kind, used to specialise handling (e.g. readers).
        """
        if isinstance(step_data, xr.DataTree):
            tree[step_id] = step_data
        elif isinstance(step_data, dict) and step_kind == "reader":
            primary_ds = None
            extra_attrs = {}
            for key, value in step_data.items():
                if isinstance(value, xr.Dataset):
                    if key == "METADATA":
                        extra_attrs.update(value.attrs)
                    elif primary_ds is None:
                        primary_ds = value
                        extra_attrs["_reader_dataset_key"] = key
                    else:
                        # Merge additional datasets into the primary
                        try:
                            primary_ds = xr.merge([primary_ds, value])
                        except Exception as exc:
                            LOG.warning(
                                "Could not merge reader dataset %r into primary: %s",
                                key, exc,
                            )
                            extra_attrs[f"_reader_extra_{key}"] = str(key)
            ds = (primary_ds or xr.Dataset()).assign_attrs(**extra_attrs)
            tree[step_id] = DataTreeDitto(ds, name=step_id)
        else:
            tree[step_id] = DataTreeDitto(step_data, name=step_id)

    def _record_provenance(self, node: xr.DataTree, prov: StepProvenance) -> None:
        """Stamp provenance fields into the step node's ``attrs``.

        Parameters
        ----------
        node : xr.DataTree
            The step's output DataTree node (in-place).
        prov : StepProvenance
            Provenance bundle to record.
        """
        if node.ds is not None:
            node.ds.attrs.update(dataclasses.asdict(prov))

    def _gc_step_data(self, tree: xr.DataTree, step_id: str) -> None:
        """Drop ``data_vars`` from a step node and re-stamp provenance.

        Reads the existing provenance from attrs, creates a fresh
        ``StepProvenance`` with ``gc_status="data_dropped"``, then
        drops data variables and re-writes provenance attrs.
        """
        node = tree.get(step_id)
        if node is None or node.ds is None:
            return

        # Drop data_vars from the underlying dataset
        for var_name in list(node.ds.data_vars):
            del node.ds[var_name]

        # Reconstruct provenance from existing attrs; mark as GC'd
        prov = StepProvenance(
            plugin_name=node.ds.attrs.get("plugin_name", "unknown"),
            plugin_kind=node.ds.attrs.get("plugin_kind", "unknown"),
            start_time=node.ds.attrs.get("start_time", ""),
            end_time=node.ds.attrs.get("end_time", ""),
            arguments_hash=node.ds.attrs.get("arguments_hash", ""),
            output_token=node.ds.attrs.get("output_token", ""),
            gc_status="data_dropped",
        )
        self._record_provenance(node, prov)

    def _apply_retention(self, tree: xr.DataTree, executed: set[str]) -> None:
        """Run garbage collection over the completed step set.

        For each executed step, check the retention policy and drop
        ``data_vars`` if the policy permits it.
        """
        for sid in sorted(executed):
            if self._retention.can_gc(sid, executed=executed):
                self._gc_step_data(tree, sid)

    def _resolve_area_defs(self) -> list:
        """Resolve ``globals.sector_list`` sector names to AreaDefinition objects.

        Returns
        -------
        list of pyresample.AreaDefinition
            Empty list if ``sector_list`` is absent or resolution fails.
        """
        from geoips.sector_utils.utils import get_sectors_from_yamls

        _globals = self._spec.globals
        if _globals is None:
            sector_list = []
        elif hasattr(_globals, "sector_list"):
            sector_list = list(getattr(_globals, "sector_list") or [])
        elif hasattr(_globals, "get"):  # plain dict fallback
            sector_list = list(_globals.get("sector_list") or [])
        else:
            sector_list = []
        if not sector_list:
            return []
        try:
            area_defs = get_sectors_from_yamls(sector_list)
            LOG.interactive(
                "Resolved %d area_def(s) from sector_list %s", len(area_defs), sector_list
            )
            return area_defs
        except Exception as exc:
            LOG.warning("Could not resolve sector_list %s: %s", sector_list, exc)
            return []

    def _set_root_attrs(self, tree: xr.DataTree) -> None:
        """Stamp minimum-viable root provenance on the workflow DataTree.

        Parameters
        ----------
        tree : xr.DataTree
            The workflow's root DataTree.
        """
        import geoips

        tree.attrs["workflow_name"] = self._wf_name
        tree.attrs["outputs"] = self._spec.outputs or []
        tree.attrs["retention_policy"] = self._spec.retention or "keep_referenced"
        tree.attrs["geoips_version"] = getattr(geoips, "__version__", "unknown")
        tree.attrs["api_version"] = "geoips/v1"

    def call(
        self,
        workflow_tree=None,
        *,
        fnames=None,
        **kwargs,
    ):
        """Execute the workflow steps in topological order.

        Parameters
        ----------
        workflow_tree : xr.DataTree or None
            A DataTree to execute into. If None, a new root is created.
        fnames : list[str] or None
            Input filenames for reader steps.
        ``**kwargs``
            Additional keyword arguments forwarded to plugins.

        Returns
        -------
        xr.DataTree
            The fully-populated workflow DataTree.
        """
        from geoips.errors import PluginResolutionError

        tree = (
            xr.DataTree(name=self._wf_name) if workflow_tree is None else workflow_tree
        )
        self._set_root_attrs(tree)
        executed: set[str] = set()

        # Resolve sectors and inject common globals into every step invocation.
        # _invoke's OBP arg-filtering drops kwargs silently for steps that don't
        # declare the corresponding parameter.
        area_defs = self._resolve_area_defs()
        _globals_kwargs = {"area_def": area_defs[0]} if area_defs else {}

        _globals = self._spec.globals
        if _globals is not None:
            pn = getattr(_globals, "product_name", None)
            if pn is None and hasattr(_globals, "get"):
                pn = _globals.get("product_name")
            if pn:
                _globals_kwargs["product_name"] = pn

        for sid in self._order:
            step_def = self._spec.steps[sid]

            if step_def.kind in SCAFFOLD_KINDS:
                raise NotImplementedError(
                    f"split/join execution is not yet implemented "
                    f"(encountered at step '{sid}')"
                )

            if step_def.when is not None:
                LOG.info("step '%s' has when expression; not yet implemented", sid)

            arg_hash = compute_arguments_hash(step_def.arguments or {})
            start_iso = datetime.now(timezone.utc).isoformat()

            plg = self._resolve_plugin(step_def.kind, step_def.name)
            LOG.interactive("Step '%s' (%s: %s) starting ...", sid, step_def.kind, step_def.name)

            # Step explicit arguments take priority over globals-derived kwargs.
            _step_kwargs = {**_globals_kwargs, **(step_def.arguments or {})}

            if step_def.kind == "reader":
                # Readers always need fnames. When they depend on upstream steps
                # (e.g. a sector step that provides area_def), collect upstream
                # so _extract_child_kwargs can inject area_def, but also pass
                # fnames so the reader can open files.
                if step_def.depends_on:
                    upstream = self._collect_upstream_data(tree, step_def.depends_on)
                    step_result = plg(
                        data=upstream, fnames=fnames, _obp_initiated=True, **_step_kwargs
                    )
                else:
                    step_result = plg(fnames=fnames, _obp_initiated=True, **_step_kwargs)
            elif not (step_def.depends_on or []):
                step_result = plg(_obp_initiated=True, **_step_kwargs)
            else:
                upstream = self._collect_upstream_data(tree, list(executed))
                step_result = plg(data=upstream, _obp_initiated=True, **_step_kwargs)

            end_iso = datetime.now(timezone.utc).isoformat()

            upstream_tokens: dict[str, str] = {}
            for dep in step_def.depends_on or ():
                dep_node = tree.get(dep)
                if dep_node is not None and dep_node.attrs:
                    token = dep_node.attrs.get("output_token")
                    if token:
                        upstream_tokens[dep] = token

            output_token = compute_step_output_token(
                step_result,
                plugin_name=step_def.name,
                plugin_kind=step_def.kind,
                arguments=step_def.arguments or {},
                upstream_tokens=upstream_tokens or None,
            )

            prov = StepProvenance(
                plugin_name=step_def.name,
                plugin_kind=step_def.kind,
                start_time=start_iso,
                end_time=end_iso,
                arguments_hash=arg_hash,
                output_token=output_token,
            )

            self._attach_step_node(tree, sid, step_result, step_kind=step_def.kind)
            self._record_provenance(tree[sid], prov)
            executed.add(sid)
            self._apply_retention(tree, executed)
            self._log_step_result(tree, sid, step_def)


        LOG.interactive("Full DataTree after workflow run:\n%s", tree)
        return tree

    def _log_step_result(self, tree: xr.DataTree, sid: str, step_def) -> None:
        """Log node state and output files after a step completes."""
        node = tree.get(sid)
        if node is not None:
            ds = node.ds
            attr_types = (
                {k: type(v).__name__ for k, v in ds.attrs.items()}
                if ds is not None
                else {}
            )
            attr_values = (
                {k: repr(v) for k, v in ds.attrs.items()}
                if ds is not None
                else {}
            )
            data_var_types = (
                {k: type(v.values).__name__ for k, v in ds.data_vars.items()}
                if ds is not None
                else {}
            )
            LOG.interactive(
                "DataTree node after step '%s':\n"
                "  node type      : %s\n"
                "  ds type        : %s\n\n"
                "  attr types     : %s\n\n"
                "  attr values    : %s\n\n"
                "  data_var types : %s",
                sid,
                type(node).__name__,
                type(ds).__name__ if ds is not None else "None",
                attr_types,
                attr_values,
                data_var_types,
            )

            if node.ds is not None:
                output_files = (
                    node.ds.attrs.get("output_fnames")
                    or node.ds.attrs.get("_ditto_list_value")
                )
                if output_files and isinstance(output_files, (list, tuple)):
                    for fpath in output_files:
                        LOG.interactive("Output file: %s", fpath)

        LOG.interactive(
            "Completed step '%s' - Kind: %s with plugin_name: %s.",
            sid,
            step_def.kind,
            step_def.name,
        )

    @staticmethod
    def _resolve_plugin(kind: str, name: str):
        """Resolve a registered plugin by (kind, name).

        Parameters
        ----------
        kind : str
            Plugin kind (e.g. ``"reader"``).
        name : str
            Plugin name (e.g. ``"abi_netcdf"``).

        Returns
        -------
        BaseClassPlugin
            An instantiated plugin.

        Raises
        ------
        PluginResolutionError
            If the interface or plugin cannot be resolved.
        """
        from geoips import interfaces
        from geoips.errors import PluginResolutionError
        from geoips.utils.types.partial_lexeme import Lexeme

        interface_name = str(Lexeme(kind).plural)
        iface = getattr(interfaces, interface_name, None)
        if iface is None:
            raise PluginResolutionError(
                f"Kind '{kind}' -> interface '{interface_name}': "
                f"no such interface found"
            )
        try:
            result = iface.get_plugin(name)
        except Exception as exc:
            raise PluginResolutionError(
                f"Kind '{kind}' -> interface '{interface_name}': "
                f"cannot resolve plugin '{name}': {exc}"
            ) from exc

        if isinstance(result, dict) and not callable(getattr(result, "call", None)):
            from geoips.utils.types.yaml_plugin_callable import YamlPluginCallable
            return YamlPluginCallable(result)
        return result
