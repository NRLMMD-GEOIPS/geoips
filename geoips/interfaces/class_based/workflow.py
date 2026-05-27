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
from datetime import datetime, timezone
from typing import Any

import xarray as xr

from geoips.interfaces.class_based_plugin import BaseClassPlugin
from geoips.pydantic_models.v1.workflows import WorkflowSpecModel
from geoips.utils.types.datatree_ditto import DataTreeDitto
from geoips.utils.types.tokenization import (
    compute_arguments_hash,
    compute_step_output_token,
)

LOG = logging.getLogger(__name__)


# -- StepProvenance dataclass --


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


# -- RetentionPolicy Strategy --


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


# -- Workflow composite class --


class Workflow(BaseClassPlugin, abstract=True):
    """Non-registered runtime executor for a validated workflow spec.

    Parameters
    ----------
    spec : WorkflowSpecModel
        A pydantic-validated workflow specification.
    name : str
        The workflow name (used as the root DataTree node name).
    """

    interface = "workflows"
    family = "order_based"
    name = "__workflow_runtime__"
    data_tree = True

    def __init__(self, spec: WorkflowSpecModel, name: str) -> None:
        self._spec = spec
        self._wf_name = name
        self._order: list[str] = self._topological_order()
        self._retention: RetentionPolicy = _POLICIES[
            self._spec.retention or "keep_referenced"
        ](self._spec)

    # -- topology --

    def _topological_order(self) -> list[str]:
        """Return step ids in a valid execution order.

        Uses Kahn's algorithm.  Re-raises pydantic-cycle errors (should
        already be caught at validation time).

        Raises
        ------
        DependencyCycleError
            If a cycle was somehow not caught at validation time.
        """
        from geoips.errors import DependencyCycleError

        step_ids = list(self._spec.steps.keys())
        indegree: dict[str, int] = {sid: 0 for sid in step_ids}
        for sid, step in self._spec.steps.items():
            for dep in step.depends_on or ():
                indegree[sid] = indegree.get(sid, 0) + 1

        queue = [sid for sid in step_ids if indegree[sid] == 0]
        order: list[str] = []
        while queue:
            sid = queue.pop(0)
            order.append(sid)
            for other_sid, other_step in self._spec.steps.items():
                if sid in (other_step.depends_on or ()):
                    indegree[other_sid] -= 1
                    if indegree[other_sid] == 0:
                        queue.append(other_sid)

        if len(order) != len(step_ids):
            raise DependencyCycleError(
                "Cycle detected at runtime (missed at validation time)"
            )
        return order

    # -- data collection --

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

        if len(depends_on) == 1:
            dep_id = depends_on[0]
            dep_node = tree.get(dep_id)
            if dep_node is not None and dep_node.children:
                result = xr.DataTree(name=dep_id)
                for child_name, child in dep_node.children.items():
                    result[child_name] = child
                if dep_node.ds is not None:
                    result.ds = dep_node.ds
                return result
            return xr.DataTree(name="empty")

        multi = xr.DataTree(name="multi_input")
        for dep_id in depends_on:
            dep_node = tree.get(dep_id)
            if dep_node is not None:
                multi[dep_id] = dep_node
        return multi

    # -- step attachment & provenance --

    def _attach_step_node(
        self, tree: xr.DataTree, step_id: str, step_data: Any
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
            node.ds.attrs["plugin_name"] = prov.plugin_name
            node.ds.attrs["plugin_kind"] = prov.plugin_kind
            node.ds.attrs["start_time"] = prov.start_time
            node.ds.attrs["end_time"] = prov.end_time
            node.ds.attrs["arguments_hash"] = prov.arguments_hash
            node.ds.attrs["output_token"] = prov.output_token
            node.ds.attrs["gc_status"] = prov.gc_status

    # -- garbage collection --

    def _gc_step_data(self, tree: xr.DataTree, step_id: str) -> None:
        """Drop ``data_vars`` from a step node while preserving ``attrs``.

        Does not delete the node; keeps coordinate / attr metadata intact.
        """
        node = tree.get(step_id)
        if node is None or node.ds is None:
            return
        for var_name in list(node.ds.data_vars):
            del node.ds[var_name]
        node.ds.attrs["gc_status"] = "data_dropped"

    def _apply_retention(self, tree: xr.DataTree, executed: set[str]) -> None:
        """Run garbage collection over the completed step set.

        For each executed step, check the retention policy and drop
        ``data_vars`` if the policy permits it.
        """
        for sid in sorted(executed):
            if self._retention.can_gc(sid, executed=executed):
                self._gc_step_data(tree, sid)

    # -- root attrs --

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

    # -- execution --

    def call(
        self,
        workflow_tree=None,
        *,
        fnames=None,
        command_line_args=None,
        **kwargs,
    ):
        """Execute the workflow steps in topological order.

        Parameters
        ----------
        workflow_tree : xr.DataTree or None
            A DataTree to execute into. If None, a new root is created.
        fnames : list[str] or None
            Input filenames for reader steps.
        command_line_args : Any or None
            Command-line arguments forwarded to plugins.
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

        for sid in self._order:
            step_def = self._spec.steps[sid]

            # --- scaffolding: split / join ---
            if step_def.kind in ("split", "join"):
                raise NotImplementedError(
                    f"split/join execution is not yet implemented "
                    f"(encountered at step '{sid}')"
                )

            # --- when: expression ---
            if step_def.when is not None:
                LOG.warning("step '%s' has when expression; ignored in v1", sid)

            arg_hash = compute_arguments_hash(step_def.arguments or {})
            start_iso = datetime.now(timezone.utc).isoformat()

            # --- resolve plugin ---
            try:
                plugin_name = step_def.name
                if step_def.kind in ("split", "join"):
                    raise PluginResolutionError(
                        f"split/join execution not implemented for step '{sid}'"
                    )
                plg = self._resolve_plugin(step_def.kind, step_def.name)
            except Exception as exc:
                raise PluginResolutionError(
                    f"Cannot resolve plugin for step '{sid}' "
                    f"({step_def.kind}/{step_def.name}): {exc}"
                ) from exc

            # --- reader path ---
            if not (step_def.depends_on or []):
                step_result = plg(fnames=fnames, **(step_def.arguments or {}))
            else:
                upstream = self._collect_upstream_data(tree, step_def.depends_on or [])
                step_result = plg(data=upstream, **(step_def.arguments or {}))

            end_iso = datetime.now(timezone.utc).isoformat()

            # --- upstream tokens ---
            upstream_tokens: dict[str, str] = {}
            for dep in step_def.depends_on or ():
                dep_node = tree.get(dep)
                if dep_node is not None and dep_node.attrs:
                    token = dep_node.attrs.get("output_token")
                    if token:
                        upstream_tokens[dep] = token

            # --- provenance ---
            output_token = compute_step_output_token(
                step_result,
                plugin_name=plugin_name,
                plugin_kind=step_def.kind,
                arguments=step_def.arguments or {},
                upstream_tokens=upstream_tokens or None,
            )

            prov = StepProvenance(
                plugin_name=plugin_name,
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
            An instantiated plugin, or raises ``PluginResolutionError``.
        """
        from geoips import interfaces
        from geoips.utils.types.partial_lexeme import Lexeme

        interface_name = str(Lexeme(kind).plural)
        try:
            iface = getattr(interfaces, interface_name, None)
            if iface is None:
                raise AttributeError(f"No interface '{interface_name}'")
            return iface.get_plugin(name)
        except Exception as exc:
            from geoips.errors import PluginResolutionError

            raise PluginResolutionError(
                f"Kind '{kind}' -> interface '{interface_name}': "
                f"cannot resolve plugin '{name}': {exc}"
            ) from exc
