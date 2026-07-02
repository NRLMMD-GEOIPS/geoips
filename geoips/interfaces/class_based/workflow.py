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

from geoips.commandline.log_setup import setup_logging
from geoips.pydantic_models.v1.workflows import (
    DEFAULT_RETENTION,
    INPUT_REF,
    WorkflowSpecModel,
    WorkflowStepDefinitionModel,
)
from geoips.errors import PluginResolutionError
from geoips.utils.types.datatree_ditto import DataTreeDitto
from geoips.utils.types.partial_lexeme import Lexeme
from geoips.utils.types.yaml_plugin_callable import YamlPluginCallable
from geoips.utils.types.tokenization import (
    compute_arguments_hash,
    compute_step_output_token,
)

# LOG = logging.getLogger(__name__)

LOG = setup_logging(logging_level="info")


def _dep_head(dep: str) -> str:
    """Return the top-level step id of a (possibly dotted) ``depends_on`` ref.

    A dotted reference such as ``"subwf.algo"`` or ``"split.scope.algo"``
    depends, at the top-level DAG, on its container step (``"subwf"`` /
    ``"split"``). Plain references are returned unchanged.
    """
    return dep.split(".", 1)[0]


def _resolve_ref_node(tree: xr.DataTree, ref: str):
    """Return the node at a (possibly dotted) ``depends_on`` ref, or None.

    Dotted references are translated to node paths (``"subwf.algo"`` ->
    ``"subwf/algo"``). ``DataTree.get`` only performs single-level lookups, so
    path indexing (``tree[path]``) is used and ``KeyError`` is caught to signal
    an unresolved reference.
    """
    path = ref.replace(".", "/")
    try:
        return tree[path]
    except KeyError:
        return None


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
        return any(
            step_id in {_dep_head(dep) for dep in (other_step.depends_on or ())}
            for other_id, other_step in self._spec.steps.items()
            if other_id not in executed
        )


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
    ) -> None:
        self._spec = spec
        self._wf_name = workflow_name
        self._order: list[str] = self._topological_order()
        self._entry_steps: set[str] = self._resolve_entry_steps()
        self._retention: RetentionPolicy = _POLICIES[
            self._spec.retention or DEFAULT_RETENTION
        ](self._spec)

    def _resolve_entry_steps(self) -> set[str]:
        """Return the step ids that receive externally-injected data.

        An *entry step* is any step whose ``depends_on`` contains the magic
        ``_input`` token. When no step declares ``_input``, the first step (by
        insertion order) is the implicit entry step — a backward-compatible
        fallback matching the pre-``_input`` behavior where a sub-workflow's
        first step consumed the seeded input tree.
        """
        explicit = {
            sid
            for sid, step in self._spec.steps.items()
            if INPUT_REF in (step.depends_on or ())
        }
        if explicit:
            return explicit
        step_ids = list(self._spec.steps.keys())
        return {step_ids[0]} if step_ids else set()

    def _topological_order(self) -> list[str]:
        """Return step ids in a valid execution order.

        Uses Kahn's algorithm.  Cyclicity is enforced at pydantic validation
        time by ``_validate_dependencies``; this function assumes a DAG.
        """
        step_ids = list(self._spec.steps.keys())
        # Collapse dotted references to their top-level head so ordering is by
        # container step; use a set per step so multiple references into the
        # same container count as a single incoming edge.
        dep_heads = {
            sid: {_dep_head(d) for d in (step.depends_on or ()) if d != INPUT_REF}
            for sid, step in self._spec.steps.items()
        }
        indegree = {sid: len(dep_heads[sid]) for sid in step_ids}

        queue = deque(sid for sid in step_ids if indegree[sid] == 0)
        order: list[str] = []
        while queue:
            sid = queue.popleft()
            order.append(sid)
            for other_sid in step_ids:
                if sid in dep_heads[other_sid]:
                    indegree[other_sid] -= 1
                    if indegree[other_sid] == 0:
                        queue.append(other_sid)

        return order

    def _collect_upstream_data(
        self,
        tree: xr.DataTree,
        depends_on: list[str],
        injected: dict[str, xr.DataTree],
        is_entry: bool,
    ) -> xr.DataTree:
        """Collect a step's input data into a single ``multi_input`` DataTree.

        Two sources are merged:

        * **Real dependencies** — each ``depends_on`` reference (excluding the
          magic ``_input`` token) is resolved to its node in *tree* and added
          under its (sanitized) reference.
        * **Injected data** — when *is_entry* is True, the *injected* children
          (the parent's upstream tree for a sub-workflow/branch, or ``{}`` at
          top level) are merged in. A real dependency of the same key is never
          clobbered.

        The result is always an ``xr.DataTree`` named ``multi_input`` (possibly
        empty, e.g. a top-level entry step, which is passed through as the
        "empty dataset").

        Dotted references (e.g. ``"subwf.algo"``) are resolved as node paths
        (``tree.get("subwf/algo")``); the ``.`` is replaced with ``__`` for the
        child key because ``/`` is illegal in a DataTree node name. Plain
        references are unaffected (no dot to translate).
        """
        result = xr.DataTree(name="multi_input")
        for dep_id in depends_on:
            if dep_id == INPUT_REF:
                continue
            dep_node = _resolve_ref_node(tree, dep_id)
            if dep_node is not None:
                result[dep_id.replace(".", "__")] = dep_node
        if is_entry:
            for child_name, child in injected.items():
                if child_name not in result.children:
                    result[child_name] = child
        return result

    def _attach_step_node(
        self,
        tree: xr.DataTree,
        step_id: str,
        step_data: Any,
    ) -> None:
        """Attach a step's output as a child node in the DataTree.

        The step output is normalized to a ``DataTreeDitto`` so every node in
        the workflow tree is the same type. The node name is *not* forced on
        construction; assigning it under ``step_id`` sets the name. Plugins
        routinely name their output node after themselves (e.g. ``single_channel``)
        and it is then renamed to the ``step_id`` (e.g. ``algorithm``); this is
        normal, so the rename is logged at ``debug`` level rather than warned —
        warning on every step proved far too noisy in practice.

        Parameters
        ----------
        tree : xr.DataTree
            The workflow's root DataTree.
        step_id : str
            Step identifier used as the child node name.
        step_data : Any
            The return value of calling the plugin, ``plugin(...)``.
        """
        if isinstance(step_data, DataTreeDitto):
            node = step_data
        elif isinstance(step_data, xr.DataTree):
            node = DataTreeDitto.from_datatree(step_data)
        else:
            node = DataTreeDitto(step_data)

        existing_name = getattr(node, "name", None)
        if existing_name and existing_name != step_id:
            LOG.debug(
                "Renaming DataTree node '%s' to step id '%s'.",
                existing_name,
                step_id,
            )

        tree[step_id] = node

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

    def _set_root_attrs(self, tree: xr.DataTree, start_time: str) -> None:
        """Stamp minimum-viable root provenance on the workflow DataTree.

        Parameters
        ----------
        tree : xr.DataTree
            The workflow's root DataTree.
        start_time : str
            ISO-8601 UTC timestamp captured immediately before the step loop.
            Recorded as the workflow's ``start_time`` (the matching
            ``end_time`` is stamped by ``call`` after the loop). Uses the
            same attr keys as ``StepProvenance`` so every node — steps and
            (sub-)workflow roots alike — carries start/end times.
        """
        import geoips

        tree.attrs["workflow_name"] = self._wf_name
        tree.attrs["outputs"] = self._spec.outputs or []
        tree.attrs["retention_policy"] = self._spec.retention or "keep_referenced"
        tree.attrs["geoips_version"] = getattr(geoips, "__version__", "unknown")
        tree.attrs["api_version"] = "geoips/v1"
        tree.attrs["start_time"] = start_time

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
        # Externally-injected data: the parent's upstream tree for a
        # sub-workflow / split branch, or ``{}`` for a top-level run. It is
        # snapshotted here (before any step runs) and routed to this workflow's
        # entry step(s) via ``_collect_upstream_data``. The root ``tree`` is
        # always fresh so injected data flows only through entry steps rather
        # than living alongside step outputs at the root.
        injected: dict[str, xr.DataTree] = (
            dict(workflow_tree.children)
            if isinstance(workflow_tree, xr.DataTree)
            else {}
        )
        tree = xr.DataTree(name=self._wf_name)
        wf_start_iso = datetime.now(timezone.utc).isoformat()
        self._set_root_attrs(tree, start_time=wf_start_iso)
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

            is_entry = sid in self._entry_steps
            upstream = self._collect_upstream_data(
                tree, step_def.depends_on or [], injected, is_entry
            )

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
                    step_def, upstream, is_entry=is_entry, fnames=fnames
                )

            end_iso = datetime.now(timezone.utc).isoformat()

            # A step may depend on more than one upstream step (e.g. an
            # output_formatter that consumes an algorithm, colormapper, and
            # sector), so collect one output token per dependency. These feed
            # into this step's own token, making it content-addressable on the
            # full set of inputs that produced it.
            upstream_tokens: dict[str, str] = {}
            for dep in step_def.depends_on or ():
                if dep == INPUT_REF:
                    continue
                dep_node = _resolve_ref_node(tree, dep)
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

        # Stamp the root workflow end time once all steps have completed. Nested
        # sub-workflows and split branches run their own ``call`` and therefore
        # get their own start/end times on their respective root nodes.
        tree.attrs["end_time"] = datetime.now(timezone.utc).isoformat()

        return tree

    def _invoke_plugin_step(self, step_def, upstream, *, is_entry, fnames):
        """Resolve and call a single plugin step (not split/join/workflow).

        The data a step receives depends on its role:

        * a ``reader`` always gets ``fnames``; it additionally gets
          ``data=upstream`` when it should receive input (an entry step or a
          step with real dependencies). A legacy (``data_tree=False``) reader
          strips that tree in its ``_pre_call`` and reads only from ``fnames``;
          a ``data_tree=True`` reader consumes it.
        * a non-reader gets ``data=upstream`` when it is an entry step or has
          real dependencies. An entry step receives ``data`` even when the tree
          is empty (the top-level "empty dataset").
        * any other independent step is called with no data.
        """
        plg = self._resolve_plugin(step_def.kind, step_def.name)
        arguments = step_def.arguments or {}
        has_real_deps = any(d != INPUT_REF for d in (step_def.depends_on or ()))
        pass_data = is_entry or has_real_deps
        if step_def.kind == "reader":
            if pass_data:
                return plg(
                    data=upstream, fnames=fnames, _obp_initiated=True, **arguments
                )
            return plg(fnames=fnames, _obp_initiated=True, **arguments)
        if pass_data:
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

        The branch body's entry step — the step whose ``depends_on`` contains
        ``_input``, or the first step if none declares it — receives this tree
        (see ``_collect_upstream_data``), so seeding a ``sector`` node here
        makes the per-branch ``area_def`` available to the body's steps through
        the normal conduit extraction.
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
        # ``geoips.interfaces`` is imported locally on purpose: this module
        # lives *inside* the ``geoips.interfaces`` package, and importing the
        # heavy parent package at module load time risks a circular import.
        from geoips import interfaces

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
            return YamlPluginCallable(result)
        return result
