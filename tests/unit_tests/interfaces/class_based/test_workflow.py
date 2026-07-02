# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Tests for the Workflow composite class."""

import pytest
import xarray as xr

from geoips.interfaces.class_based.workflow import (
    Workflow,
    KeepAllPolicy,
    KeepReferencedPolicy,
    KeepOutputsOnlyPolicy,
    StepProvenance,
)
from geoips.pydantic_models.v1.workflows import WorkflowSpecModel
from geoips.errors import DependencyCycleError

CTX = {"skip_plugin_name_validation": True}


def _make_spec(step_dict, **overrides):
    """Build a validated WorkflowSpecModel from a compact dict."""
    return WorkflowSpecModel.model_validate(
        {"steps": step_dict, **overrides}, context=CTX
    )


class TestWorkflowConstruction:
    """Workflow construction and topological sort."""

    def test_linear_two_steps_constructs(self):
        """Construct a Workflow with reader + algorithm steps."""
        spec = _make_spec(
            {
                "read": {
                    "kind": "reader",
                    "name": "abi_netcdf",
                    "arguments": {},
                    "depends_on": [],
                },
                "algo": {
                    "kind": "algorithm",
                    "name": "single_channel",
                    "arguments": {},
                    "depends_on": ["read"],
                },
            }
        )
        wf = Workflow(spec, workflow_name="test")
        assert len(wf._order) == 2
        assert wf._order == ["read", "algo"]

    def test_topological_sort_respects_depends_on(self):
        """Topological sort orders by dependency, not insertion order."""
        spec = _make_spec(
            {
                "c": {
                    "kind": "output_formatter",
                    "name": "img",
                    "arguments": {},
                    "depends_on": ["b"],
                },
                "a": {
                    "kind": "reader",
                    "name": "abi",
                    "arguments": {},
                    "depends_on": [],
                },
                "b": {
                    "kind": "algorithm",
                    "name": "alg",
                    "arguments": {},
                    "depends_on": ["a"],
                },
            }
        )
        wf = Workflow(spec, workflow_name="test")
        idx_a = wf._order.index("a")
        idx_b = wf._order.index("b")
        idx_c = wf._order.index("c")
        assert idx_a < idx_b
        assert idx_b < idx_c

    def test_cycle_detection_raises(self):
        """Cyclic depends_on raises DependencyCycleError at validation time."""
        with pytest.raises(DependencyCycleError):
            _make_spec(
                {
                    "a": {
                        "kind": "reader",
                        "name": "r1",
                        "arguments": {},
                        "depends_on": ["b"],
                    },
                    "b": {
                        "kind": "algorithm",
                        "name": "a1",
                        "arguments": {},
                        "depends_on": ["a"],
                    },
                }
            )

    def test_default_outputs_last_step(self):
        """outputs: None defaults to last dict key."""
        spec = _make_spec(
            {
                "first": {"kind": "reader", "name": "r1", "arguments": {}},
                "last": {"kind": "algorithm", "name": "a1", "arguments": {}},
            }
        )
        assert spec.outputs == ["last"]


class TestRetention:
    """Retention policy tests."""

    def test_keep_forces_retention(self):
        """Step with keep:True exempt from GC."""
        spec = _make_spec(
            {
                "a": {
                    "kind": "reader",
                    "name": "r1",
                    "arguments": {},
                    "keep": True,
                },
                "b": {"kind": "algorithm", "name": "a1", "arguments": {}},
            }
        )
        assert spec.steps["a"].keep is True

    def test_keep_all_never_gcs(self):
        """The keep_all policy never permits GC."""
        spec = _make_spec(
            {
                "r": {"kind": "reader", "name": "r1", "arguments": {}},
            }
        )
        policy = KeepAllPolicy(spec)
        assert policy.can_gc("r", executed={"r"}) is False

    def test_keep_referenced_gcs_non_output(self):
        """The keep_referenced policy GCs non-output step after all consumers done."""
        spec = _make_spec(
            {
                "r": {
                    "kind": "reader",
                    "name": "r1",
                    "arguments": {},
                    "depends_on": [],
                },
                "a": {
                    "kind": "algorithm",
                    "name": "a1",
                    "arguments": {},
                    "depends_on": ["r"],
                },
            }
        )
        policy = KeepReferencedPolicy(spec)
        assert policy.can_gc("r", executed={"r", "a"}) is True
        assert policy.can_gc("a", executed={"r", "a"}) is False

    def test_keep_outputs_only_gcs_non_output(self):
        """The keep_outputs_only policy GCs everything except declared outputs."""
        spec = _make_spec(
            {
                "r": {
                    "kind": "reader",
                    "name": "r1",
                    "arguments": {},
                    "depends_on": [],
                },
                "a": {
                    "kind": "algorithm",
                    "name": "a1",
                    "arguments": {},
                    "depends_on": ["r"],
                },
            },
            outputs=["a"],
        )
        policy = KeepOutputsOnlyPolicy(spec)
        assert policy.can_gc("r", executed={"r", "a"}) is True
        assert policy.can_gc("a", executed={"r", "a"}) is False


class TestStepProvenance:
    """StepProvenance dataclass tests."""

    def test_provenance_dataclass_fields(self):
        """Verify StepProvenance carries expected fields."""
        prov = StepProvenance(
            plugin_name="test_reader",
            plugin_kind="reader",
            start_time="2024-01-01T00:00:00+00:00",
            end_time="2024-01-01T00:00:01+00:00",
            arguments_hash="dask:aaa",
            output_token="dask:bbb",
        )
        assert prov.plugin_name == "test_reader"
        assert prov.gc_status == "kept"
        assert prov.output_token == "dask:bbb"

    def test_provenance_is_frozen(self):
        """Verify StepProvenance is immutable."""
        prov = StepProvenance(
            plugin_name="t",
            plugin_kind="r",
            start_time="",
            end_time="",
            arguments_hash="h",
            output_token="t",
        )
        with pytest.raises(Exception):
            prov.plugin_name = "new"  # type: ignore


class TestSplitJoinScaffolding:
    """Split runs its inline body once per branch scope."""

    def test_split_runs_body_per_scope(self, monkeypatch):
        """A split with explicit ``scopes`` runs its body once per scope."""

        class _Passthrough:
            data_tree = True

            def call(self, data=None, **kwargs):
                return data

            def __call__(self, data=None, **kwargs):
                return data if data is not None else xr.DataTree(name="empty")

        monkeypatch.setattr(
            Workflow, "_resolve_plugin", staticmethod(lambda kind, name: _Passthrough())
        )

        spec = _make_spec(
            {
                "s": {
                    "kind": "split",
                    "arguments": {"scopes": ["band1", "band2"]},
                    "spec": {
                        "steps": {
                            "p": {
                                "kind": "algorithm",
                                "name": "passthrough",
                                "arguments": {},
                                "depends_on": [],
                            }
                        }
                    },
                    "depends_on": [],
                },
            }
        )
        result = Workflow(spec, workflow_name="split_test").call()
        split_node = result.get("s")
        assert split_node is not None
        assert set(dict(split_node.children)) == {"band1", "band2"}


class TestRootWorkflowTiming:
    """Root workflow nodes carry ISO-8601 start/end times (spec PR #1319)."""

    @staticmethod
    def _passthrough_spec():
        return _make_spec(
            {
                "p": {
                    "kind": "algorithm",
                    "name": "passthrough",
                    "arguments": {},
                    "depends_on": [],
                }
            }
        )

    def _patch_passthrough(self, monkeypatch):
        class _Passthrough:
            data_tree = True

            def __call__(self, data=None, **kwargs):
                return data if data is not None else xr.DataTree(name="empty")

        monkeypatch.setattr(
            Workflow,
            "_resolve_plugin",
            staticmethod(lambda kind, name: _Passthrough()),
        )

    def test_root_has_start_and_end_times(self, monkeypatch):
        """Root attrs include start_time/end_time with end >= start."""
        from datetime import datetime

        self._patch_passthrough(monkeypatch)
        result = Workflow(self._passthrough_spec(), workflow_name="timed").call()

        assert "start_time" in result.attrs
        assert "end_time" in result.attrs
        start = datetime.fromisoformat(result.attrs["start_time"])
        end = datetime.fromisoformat(result.attrs["end_time"])
        assert end >= start

    def test_sub_workflow_root_has_times(self, monkeypatch):
        """Nested sub-workflow root nodes also carry start/end times."""
        self._patch_passthrough(monkeypatch)
        spec = _make_spec(
            {
                "sub": {
                    "kind": "workflow",
                    "spec": {
                        "steps": {
                            "inner": {
                                "kind": "algorithm",
                                "name": "passthrough",
                                "arguments": {},
                                "depends_on": [],
                            }
                        }
                    },
                    "depends_on": [],
                },
            }
        )
        result = Workflow(spec, workflow_name="outer").call()
        sub_node = result.get("sub")
        assert sub_node is not None
        assert "start_time" in sub_node.attrs
        assert "end_time" in sub_node.attrs


class TestWorkflowSpecResolution:
    def test_inline_spec_returned_directly(self):
        spec = _make_spec(
            {
                "sub": {
                    "kind": "workflow",
                    "spec": {
                        "steps": {
                            "inner": {
                                "kind": "algorithm",
                                "name": "single_channel",
                                "arguments": {},
                            }
                        }
                    },
                },
            }
        )
        step_def = spec.steps["sub"]
        assert step_def.spec is not None
        resolved = Workflow._resolve_workflow_spec(step_def)
        assert resolved is step_def.spec
        assert "inner" in resolved.steps
        assert resolved.steps["inner"].kind == "algorithm"


class TestSubWorkflowDependsOnRuntime:
    """Runtime resolution of dotted ``depends_on`` into sub-workflow steps."""

    def test_consumer_receives_nested_node(self, monkeypatch):
        """A step depending on ``subwf.inner`` receives that nested node."""
        seen = {}

        class _Plugin:
            data_tree = True

            def __call__(self, data=None, **kwargs):
                if isinstance(data, xr.DataTree):
                    seen["children"] = set(dict(data.children))
                return xr.DataTree(
                    xr.Dataset({"v": (["x"], [1, 2, 3])}), name="out"
                )

        monkeypatch.setattr(
            Workflow,
            "_resolve_plugin",
            staticmethod(lambda kind, name: _Plugin()),
        )

        spec = _make_spec(
            {
                "subwf": {
                    "kind": "workflow",
                    "depends_on": [],
                    "spec": {
                        "steps": {
                            "inner": {
                                "kind": "algorithm",
                                "name": "passthrough",
                                "arguments": {},
                                "depends_on": [],
                            }
                        }
                    },
                },
                "consumer": {
                    "kind": "algorithm",
                    "name": "passthrough",
                    "arguments": {},
                    "depends_on": ["subwf.inner"],
                },
            }
        )
        tree = Workflow(spec, workflow_name="t").call()

        # The nested node is addressable by path...
        assert tree["subwf/inner"] is not None
        # ...and was delivered to the consumer under a sanitized child key.
        assert seen.get("children") == {"subwf__inner"}

    def test_topological_order_uses_head(self):
        """Ordering treats ``subwf.inner`` as a dependency on ``subwf``."""
        spec = _make_spec(
            {
                "consumer": {
                    "kind": "algorithm",
                    "name": "passthrough",
                    "arguments": {},
                    "depends_on": ["subwf.inner"],
                },
                "subwf": {
                    "kind": "workflow",
                    "depends_on": [],
                    "spec": {
                        "steps": {
                            "inner": {
                                "kind": "algorithm",
                                "name": "passthrough",
                                "arguments": {},
                                "depends_on": [],
                            }
                        }
                    },
                },
            }
        )
        order = Workflow(spec, workflow_name="t")._order
        assert order.index("subwf") < order.index("consumer")


class TestCollectUpstreamNested:
    def test_empty_depends_with_children_returns_tree(self):
        parent = xr.DataTree(name="multi_input")
        parent["reader_out"] = xr.DataTree(
            xr.Dataset({"data": (["x"], [1, 2, 3])}), name="reader_out"
        )

        wf = Workflow(
            _make_spec({"r": {"kind": "reader", "name": "x", "arguments": {}}}),
            workflow_name="test",
        )
        result = wf._collect_upstream_data(parent, [])
        assert result is parent

    def test_empty_depends_no_children_returns_empty(self):
        wf = Workflow(
            _make_spec({"r": {"kind": "reader", "name": "x", "arguments": {}}}),
            workflow_name="test",
        )
        empty_root = wf._collect_upstream_data(xr.DataTree(name="fresh"), [])
        assert dict(empty_root.children) == {}
        assert empty_root.name == "empty"
