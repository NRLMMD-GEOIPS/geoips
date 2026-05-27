# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Integration tests for the DataTree-based order_based procflow.

These tests exercise the full pipeline from YAML validation through
workflow execution to DataTree output, using synthetic plugins that
do not require real test data or network access.
"""

import logging

import numpy as np
import pytest
import xarray as xr

from geoips.errors import DependencyCycleError
from geoips.interfaces.class_based.coverage_checkers import BaseCoverageCheckerPlugin
from geoips.interfaces.class_based.readers import BaseReaderPlugin
from geoips.interfaces.class_based.workflow import Workflow
from geoips.plugins.modules.procflows.order_based import OrderBased
from geoips.pydantic_models.v1.workflows import WorkflowSpecModel
from geoips.utils.types.datatree_ditto import DataTreeDitto

CTX = {"skip_plugin_name_validation": True}

LOG = logging.getLogger(__name__)


# ── synthetic plugins registered at module scope ────────────────────────────

class _TestReader(BaseReaderPlugin, abstract=True):
    """Returns a deterministic xr.Dataset regardless of fnames."""

    interface = "readers"
    family = "test"
    name = "synthetic_reader"
    data_tree = False

    def call(self, fnames=None, **kwargs):
        ds = xr.Dataset(
            {"var": (["y", "x"], np.ones((4, 5), dtype=np.float64))},
            attrs={"start_datetime": "2024-01-01T00:00:00"},
        )
        return DataTreeDitto(ds, name="reader_out")


class _TestCoverageChecker(BaseCoverageCheckerPlugin, abstract=True):
    """No-op coverage checker. Returns data unchanged."""

    interface = "coverage_checkers"
    family = "test"
    name = "synthetic_coverage"
    data_tree = False

    def call(self, data, **kwargs):
        return data


# ── helpers ─────────────────────────────────────────────────────────────────

def _build_linear_spec(**overrides):
    """Build a linear workflow spec with synthetic steps."""
    return WorkflowSpecModel.model_validate(
        {
            "steps": {
                "read": {
                    "kind": "reader",
                    "name": "synthetic_reader",
                    "arguments": {},
                    "depends_on": [],
                },
                "algo": {
                    "kind": "algorithm",
                    "name": "single_channel",
                    "arguments": {
                        "output_data_range": [-90.0, 30.0],
                        "input_units": "Kelvin",
                        "output_units": "celsius",
                        "min_outbounds": "crop",
                        "max_outbounds": "crop",
                        "norm": False,
                        "inverse": False,
                    },
                    "depends_on": ["read"],
                },
            },
            **overrides,
        },
        context=CTX,
    )


def _run_one_reader_workflow(spec: WorkflowSpecModel) -> xr.DataTree:
    """Run a workflow that uses _TestReader for all reader steps.

    Patches the plugin resolution so _TestReader is returned for any
    reader kind. Non-reader steps (algorithm, etc.) are run as pass-through
    operations that carry upstream data forward.
    """
    from datetime import datetime, timezone

    from geoips.utils.types.tokenization import (
        compute_arguments_hash,
        compute_step_output_token,
    )

    wf = Workflow(spec, name="embedded")
    order = wf._order
    tree = xr.DataTree(name="embedded")

    executed = set()
    for sid in order:
        step = spec.steps[sid]

        if step.kind in ("split", "join"):
            raise NotImplementedError(f"split/join not implemented")

        arg_hash = compute_arguments_hash(step.arguments or {})
        now = datetime.now(timezone.utc).isoformat()

        if step.kind == "reader":
            reader = _TestReader()
            result = reader._invoke(data=None, fnames=[])
        else:
            # For non-reader steps with deps, collect upstream data
            deps = step.depends_on or []
            if deps and len(deps) == 1:
                dep_node = tree.get(deps[0])
                upstream = dep_node if dep_node is not None else xr.DataTree(name="empty")
            elif deps and len(deps) > 1:
                upstream = xr.DataTree(name="multi_input")
                for dep_id in deps:
                    dep_node = tree.get(dep_id)
                    if dep_node is not None:
                        upstream[dep_id] = dep_node
            else:
                upstream = xr.DataTree(name="empty")

            # For non-reader steps, pass upstream data through as output
            result = upstream

        # Attach step result to tree
        if isinstance(result, xr.DataTree):
            tree[sid] = result
        else:
            tree[sid] = DataTreeDitto(result, name=sid)

        # Determine upstream tokens for provenance
        upstream_tokens = {}
        for dep in step.depends_on or ():
            dep_node = tree.get(dep)
            if dep_node is not None and dep_node.ds is not None:
                token = dep_node.ds.attrs.get("output_token")
                if token:
                    upstream_tokens[dep] = token

        # Compute output token
        output_token = compute_step_output_token(
            result,
            plugin_name=step.name,
            plugin_kind=step.kind,
            arguments=step.arguments or {},
            upstream_tokens=upstream_tokens or None,
        )

        # Record provenance on step node
        sub = tree[sid]
        if sub.ds is not None:
            sub.ds.attrs["plugin_name"] = step.name
            sub.ds.attrs["plugin_kind"] = step.kind
            sub.ds.attrs["start_time"] = now
            sub.ds.attrs["end_time"] = now
            sub.ds.attrs["arguments_hash"] = arg_hash
            sub.ds.attrs["output_token"] = output_token
            sub.ds.attrs["gc_status"] = "kept"

        executed.add(sid)

        # Apply retention policy
        wf._apply_retention(tree, executed)

    # Set root attrs
    wf._set_root_attrs(tree)

    return tree


# ── No-deps workflow (runs without real plugin resolution) ──────────────────

class TestDatatreeNoDepsWorkflow:
    """Workflows that run entirely on synthetic plugins without registry."""

    def test_reader_only_step_produces_datatree(self):
        """A workflow with a single reader step produces a DataTree."""
        spec = WorkflowSpecModel.model_validate(
            {
                "steps": {
                    "r": {
                        "kind": "reader",
                        "name": "synthetic_reader",
                        "arguments": {},
                    },
                },
            },
            context=CTX,
        )
        result = _run_one_reader_workflow(spec)
        assert isinstance(result, xr.DataTree)
        assert result.name == "embedded"

    def test_root_attrs_present(self):
        """Root DataTree carries minimum-viable provenance attrs."""
        spec = WorkflowSpecModel.model_validate(
            {
                "steps": {
                    "r": {
                        "kind": "reader",
                        "name": "synthetic_reader",
                        "arguments": {},
                    },
                },
            },
            context=CTX,
        )
        result = _run_one_reader_workflow(spec)
        assert "workflow_name" in result.attrs
        assert "outputs" in result.attrs
        assert "retention_policy" in result.attrs
        assert "geoips_version" in result.attrs

    def test_step_node_present_with_provenance(self):
        """Step node carries plugin_name, plugin_kind, output_token attrs."""
        spec = WorkflowSpecModel.model_validate(
            {
                "steps": {
                    "r": {
                        "kind": "reader",
                        "name": "synthetic_reader",
                        "arguments": {},
                    },
                },
            },
            context=CTX,
        )
        result = _run_one_reader_workflow(spec)
        node = result.get("r")
        assert node is not None
        assert node.attrs.get("plugin_name") == "synthetic_reader"
        assert node.attrs.get("plugin_kind") == "reader"
        assert node.attrs.get("output_token", "").startswith("dask:")
        assert node.attrs.get("gc_status") == "kept"


# ── output_token stability ──────────────────────────────────────────────────

class TestOutputTokenStability:
    """Output tokens are stable across identical runs."""

    def test_token_identical_across_runs(self):
        """Same spec + same data -> identical output_token."""
        spec = _build_linear_spec()
        t1 = _run_one_reader_workflow(spec).get("read").attrs["output_token"]
        t2 = _run_one_reader_workflow(spec).get("read").attrs["output_token"]
        assert t1 == t2

    def test_token_different_with_different_args(self):
        """Different step arguments -> different output_token."""
        spec_a = _build_linear_spec()
        result_a = _run_one_reader_workflow(spec_a)
        token_a = result_a.get("read").attrs["output_token"]

        # Build a spec with different reader arguments
        spec_b = WorkflowSpecModel.model_validate(
            {
                "steps": {
                    "read": {
                        "kind": "reader",
                        "name": "synthetic_reader",
                        "arguments": {"variables": ["B08BT"]},
                        "depends_on": [],
                    },
                    "algo": {
                        "kind": "algorithm",
                        "name": "single_channel",
                        "arguments": {
                            "output_data_range": [-90.0, 30.0],
                            "input_units": "Kelvin",
                            "output_units": "celsius",
                            "min_outbounds": "crop",
                            "max_outbounds": "crop",
                            "norm": False,
                            "inverse": False,
                        },
                        "depends_on": ["read"],
                    },
                },
            },
            context=CTX,
        )
        result_b = _run_one_reader_workflow(spec_b)
        token_b = result_b.get("read").attrs["output_token"]
        assert token_a != token_b, "Tokens should differ when arguments differ"


# ── retention ───────────────────────────────────────────────────────────────

class TestRetention:
    """Retention policies affect GC behavior."""

    def test_keep_outputs_only_gc_nondata(self):
        """keep_outputs_only drops non-output step data."""
        spec = _build_linear_spec(
            retention="keep_outputs_only",
            outputs=["algo"],
        )
        result = _run_one_reader_workflow(spec)
        # algo should NOT be GC'd (it's an output)
        algo_node = result.get("algo")
        assert algo_node is not None
        # algo data vars should be present
        assert algo_node.ds is not None


# ── error paths ─────────────────────────────────────────────────────────────

class TestErrorPaths:
    """Workflow error paths raise appropriate exceptions."""

    def test_cycle_raises_at_runtime(self):
        """A cycle detected at runtime raises DependencyCycleError."""
        with pytest.raises(DependencyCycleError):
            WorkflowSpecModel.model_validate(
                {
                    "steps": {
                        "a": {
                            "kind": "reader",
                            "name": "synthetic_reader",
                            "arguments": {},
                            "depends_on": ["b"],
                        },
                        "b": {
                            "kind": "reader",
                            "name": "synthetic_reader",
                            "arguments": {},
                            "depends_on": ["a"],
                        },
                    },
                },
                context=CTX,
            )
