# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""DataTree-spec Workflow composite executor.

The ``Workflow`` class is a non-registered runtime executor that loads a
validated ``WorkflowSpecModel``, resolves plugins, builds a topological step
order, and walks through the steps collecting downstream provenance into an
``xr.DataTree``.  Retention is governed by the Strategy pattern so the
execution loop never branches on the policy name.

``split`` steps fan a workflow out into one branch per scope (e.g. one per
static sector in ``globals.sector_list``), running an inline body sub-workflow
per branch; ``join`` steps re-collect those branches.  Conditional execution
(``when``) is accepted by the schema but not yet implemented and raises
``NotImplementedError`` at runtime.
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
    WorkflowSpecModel,
    WorkflowStepDefinitionModel,
)
from geoips.errors import PluginResolutionError
from geoips.utils.types.datatree_ditto import DataTreeDitto
from geoips.utils.types.yaml_plugin_callable import YamlPluginCallable
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

    @classmethod
    def from_attrs(cls, attrs: dict) -> "StepProvenance":
        """Reconstruct from a node's ``ds.attrs`` dict."""
        return cls(
            plugin_name=attrs.get("plugin_name", "unknown"),
            plugin_kind=attrs.get("plugin_kind", "unknown"),
            start_time=attrs.get("start_time", ""),
            end_time=attrs.get("end_time", ""),
            arguments_hash=attrs.get("arguments_hash", ""),
            output_token=attrs.get("output_token", ""),
            gc_status=attrs.get("gc_status", "kept"),
        )


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

GENERATED_WORKFLOW = "GENERATED_WORKFLOW"


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

    def __init__(
        self,
        spec: WorkflowSpecModel,
        workflow_name: str,
        write_tokens: bool = False,
    ) -> None:
        self._spec = spec
        self._wf_name = workflow_name
        self._write_tokens = write_tokens
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
        indegree = {
            sid: len(step.depends_on or ()) for sid, step in self._spec.steps.items()
        }

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
        upstream node as a child under its step id.  When *depends_on*
        is empty but *tree* already has children (a sub-workflow
        receiving data from its parent), the tree itself is returned
        so the first step can access the pre-loaded upstream data.
        """
        if not depends_on:
            if dict(tree.children):
                return tree
            return xr.DataTree(name="empty")

        result = xr.DataTree(name="multi_input")
        for dep_id in depends_on:
            dep_node = tree.get(dep_id)
            if dep_node is not None:
                result[dep_id] = dep_node
        return result

    def _attach_step_node(
        self,
        tree: xr.DataTree,
        step_id: str,
        step_data: Any,
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
        """
        if isinstance(step_data, xr.DataTree):
            tree[step_id] = step_data
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
        prov = StepProvenance.from_attrs(node.ds.attrs)
        prov = dataclasses.replace(prov, gc_status="data_dropped")
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
                "Resolved %d area_def(s) from sector_list %s",
                len(area_defs),
                sector_list,
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
        tree = (
            xr.DataTree(name=self._wf_name) if workflow_tree is None else workflow_tree
        )
        # A *seeded* run is a sub-workflow handed a pre-loaded input tree (e.g. a
        # split branch). For these, a first step (``depends_on: []``) consumes the
        # seeded input. A top-level run (``workflow_tree is None``) is never
        # seeded, so its independent steps receive no upstream data.
        seeded = workflow_tree is not None and bool(dict(workflow_tree.children))
        self._set_root_attrs(tree)
        executed: set[str] = set()

        for sid in self._order:
            step_def = self._spec.steps[sid]

            if step_def.when is not None:
                raise NotImplementedError(
                    f"conditional execution ('when') is not yet implemented "
                    f"(encountered at step '{sid}')"
                )

            arg_hash = compute_arguments_hash(step_def.arguments or {})
            start_iso = datetime.now(timezone.utc).isoformat()

            upstream = self._collect_upstream_data(tree, step_def.depends_on or [])

            if step_def.kind == "split":
                step_result = self._run_split(upstream, step_def, sid, fnames=fnames)
            elif step_def.kind == "join":
                step_result = self._run_join(tree, step_def, sid)
            elif step_def.kind == "workflow":
                sub_spec = self._resolve_workflow_spec(step_def)
                step_result = Workflow(sub_spec, workflow_name=sid).call(
                    workflow_tree=upstream, fnames=fnames
                )
            else:
                step_result = self._invoke_plugin_step(
                    step_def, upstream, seeded=seeded, fnames=fnames
                )

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
                plugin_name=step_def.name or sid,
                plugin_kind=step_def.kind,
                arguments=step_def.arguments or {},
                upstream_tokens=upstream_tokens or None,
            )

            prov = StepProvenance(
                plugin_name=step_def.name or sid,
                plugin_kind=step_def.kind,
                start_time=start_iso,
                end_time=end_iso,
                arguments_hash=arg_hash,
                output_token=output_token,
            )

            self._attach_step_node(tree, sid, step_result)
            self._record_provenance(tree[sid], prov)
            executed.add(sid)
            self._apply_retention(tree, executed)

        return tree

    def _invoke_plugin_step(self, step_def, upstream, *, seeded, fnames):
        """Resolve and call a single plugin step (not split/join/workflow).

        The data a step receives depends on its position:

        * a ``reader`` gets ``fnames`` (and no upstream data);
        * a step with dependencies — or the first step of a *seeded*
          sub-workflow (a split branch) — gets ``data=upstream``;
        * any other independent step is called with no data.
        """
        plg = self._resolve_plugin(step_def.kind, step_def.name)
        arguments = step_def.arguments or {}
        if step_def.kind == "reader":
            return plg(fnames=fnames, _obp_initiated=True, **arguments)
        if step_def.depends_on or seeded:
            return plg(data=upstream, _obp_initiated=True, **arguments)
        return plg(_obp_initiated=True, **arguments)

    # ------------------------------------------------------------------
    # split / join (per-branch fan-out, e.g. one branch per static sector)
    # ------------------------------------------------------------------

    def _run_split(self, upstream, step_def, sid, *, fnames=None):
        """Run a ``split`` step's inline body sub-workflow once per branch.

        Branches come from the step's ``arguments``:

        * ``scopes: [k1, k2, ...]`` — explicit branch keys (no sector context).
        * ``over: sector_list`` — one branch per static sector resolved from
          ``globals.sector_list``; each branch's ``AreaDefinition`` is seeded
          into the branch input tree as a ``sector`` node so the body's steps
          receive it as ``area_def`` via the standard conduit mechanism.

        Each branch result is nested under ``/<sid>/<scope>``.

        Parameters
        ----------
        upstream : xr.DataTree
            Collected upstream data for the split step.
        step_def : WorkflowStepDefinitionModel
            The ``kind="split"`` step definition (carries the inline body spec).
        sid : str
            The split step id (root node name for the branch subtree).
        fnames : list[str] or None
            Input filenames forwarded to each branch sub-workflow.

        Returns
        -------
        xr.DataTree
            A node named *sid* with one child per branch scope.
        """
        body_spec = step_def.spec
        if body_spec is None:
            raise PluginResolutionError(f"split step '{sid}' has no inline body spec")

        branches = self._resolve_branches(step_def, sid)
        split_node = xr.DataTree(name=sid)
        for scope, area_def in branches:
            seed = self._seed_branch_tree(upstream, area_def)
            branch_wf = Workflow(body_spec, workflow_name=scope)
            branch_result = branch_wf.call(workflow_tree=seed, fnames=fnames)
            split_node[scope] = branch_result

        split_node.attrs["split_scopes"] = [scope for scope, _ in branches]
        return split_node

    def _resolve_branches(self, step_def, sid):
        """Return ``[(scope_name, AreaDefinition | None), ...]`` for a split step."""
        args = step_def.arguments or {}
        if args.get("scopes"):
            return [(str(scope), None) for scope in args["scopes"]]
        if args.get("over") == "sector_list":
            branches = self._resolve_sector_branches()
            if not branches:
                raise PluginResolutionError(
                    f"split step '{sid}' uses 'over: sector_list' but no sectors "
                    f"could be resolved from globals.sector_list"
                )
            return branches
        raise PluginResolutionError(
            f"split step '{sid}' must define arguments with either 'scopes' "
            f"(explicit branch keys) or 'over: sector_list'"
        )

    def _resolve_sector_branches(self):
        """Return ``[(scope_name, AreaDefinition)]`` from ``globals.sector_list``."""
        branches: list[tuple[str, Any]] = []
        for area_def in self._resolve_area_defs():
            name = (
                getattr(area_def, "area_id", None)
                or getattr(area_def, "name", None)
                or f"sector_{len(branches)}"
            )
            branches.append((str(name), area_def))
        return branches

    @staticmethod
    def _seed_branch_tree(upstream, area_def):
        """Build a branch input tree: upstream data + an optional sector node.

        The branch body's first step (``depends_on: []``) receives this tree
        directly (see :meth:`_collect_upstream_data`), so seeding a ``sector``
        node here makes the per-branch ``area_def`` available to the body's
        steps through the normal conduit extraction.
        """
        seed = xr.DataTree(name="branch_input")
        if isinstance(upstream, xr.DataTree):
            for child_name, child in dict(upstream.children).items():
                seed[child_name] = child
        if area_def is not None:
            sector_ds = xr.Dataset(
                attrs={"area_definition": area_def, "plugin_kind": "sector"}
            )
            seed["_sector"] = DataTreeDitto(sector_ds, name="_sector")
        return seed

    def _run_join(self, tree, step_def, sid):
        """Collect a split's per-branch outputs into a single node.

        Re-nests each branch subtree under ``/<sid>/<scope>`` and records the
        joined scopes in ``joined_scopes``.
        """
        join_node = xr.DataTree(name=sid)
        joined_scopes: list[str] = []

        for dep in step_def.depends_on or ():
            split_node = tree.get(dep)
            if split_node is None:
                continue
            for scope, branch in dict(split_node.children).items():
                joined_scopes.append(scope)
                join_node[scope] = branch

        join_node.attrs["joined_scopes"] = joined_scopes
        return join_node

    @staticmethod
    def _resolve_workflow_spec(
        step_def: WorkflowStepDefinitionModel,
    ) -> WorkflowSpecModel:
        """Resolve the sub-workflow spec from an expanded workflow step.

        Parameters
        ----------
        step_def : WorkflowStepDefinitionModel
            A step definition with ``kind="workflow"``.

        Returns
        -------
        WorkflowSpecModel
        """
        if step_def.spec is not None:
            return step_def.spec

        plg = Workflow._resolve_plugin(step_def.kind, step_def.name)
        if isinstance(plg, YamlPluginCallable):
            return WorkflowSpecModel.model_validate(plg.spec)
        if hasattr(plg, "spec"):
            return plg.spec

        raise PluginResolutionError(
            f"Could not extract workflow spec for step "
            f"'{step_def.name}' (kind={step_def.kind})"
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
            if interface_name == "workflows" and name is None:
                # occurs for workflow 'plugins' generated at runtimes for product /
                # product default plugins.
                return GENERATED_WORKFLOW
            else:
                raise PluginResolutionError(
                    f"Kind '{kind}' -> interface '{interface_name}': "
                    f"cannot resolve plugin '{name}': {exc}"
                ) from exc

        if isinstance(result, dict) and not callable(getattr(result, "call", None)):
            from geoips.utils.types.yaml_plugin_callable import YamlPluginCallable

            return YamlPluginCallable(result)
        return result
