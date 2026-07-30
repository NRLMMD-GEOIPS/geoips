# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Integration tests for the DataTree-based order_based procflow.

These tests exercise the full pipeline from YAML validation through
workflow execution to DataTree output, using the real ``Workflow.call()``
with synthetic plugins that do not require real test data or network access.
"""

import logging

import pytest
import xarray as xr

from geoips.errors import DependencyCycleError
from geoips.interfaces.class_based.workflow import Workflow
from geoips.pydantic_models.v1.workflows import WorkflowSpecModel

CTX = {"skip_plugin_name_validation": True}
LOG = logging.getLogger(__name__)


def _build_linear_spec(**overrides):
    """Build a linear workflow spec with synthetic reader and algorithm steps."""
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


class TestDatatreeNoDepsWorkflow:
    """Workflows that run on synthetic plugins via monkeypatched registry."""

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
        wf = Workflow(spec, workflow_name="embedded")
        result = wf.call(fnames=[])
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
        wf = Workflow(spec, workflow_name="embedded")
        result = wf.call(fnames=[])
        assert "workflow_name" in result.attrs
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
        wf = Workflow(spec, workflow_name="embedded")
        result = wf.call(fnames=[])
        sub = result.get("r")
        assert sub is not None
        assert sub.attrs.get("plugin_name") == "synthetic_reader"
        assert sub.attrs.get("plugin_kind") == "reader"
        token = sub.attrs.get("output_token", "")
        assert token.startswith("dask:") or token.startswith("untokenizable:")
        assert "gc_status" in sub.attrs


class TestOutputTokenStability:
    """Output tokens are stable across identical runs."""

    def test_token_identical_across_runs(self):
        """Same spec + same data -> identical output_token."""
        spec = _build_linear_spec()
        t1 = (
            Workflow(spec, workflow_name="e1")
            .call(fnames=[])
            .get("read")
            .attrs["output_token"]
        )
        t2 = (
            Workflow(spec, workflow_name="e2")
            .call(fnames=[])
            .get("read")
            .attrs["output_token"]
        )
        assert t1 == t2

    def test_token_different_with_different_args(self):
        """Different step arguments -> different output_token."""
        spec_a = _build_linear_spec()
        result_a = Workflow(spec_a, workflow_name="ea").call(fnames=[])
        token_a = result_a.get("read").attrs["output_token"]

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
        result_b = Workflow(spec_b, workflow_name="eb").call(fnames=[])
        token_b = result_b.get("read").attrs["output_token"]
        assert token_a != token_b, "Tokens should differ when arguments differ"


class TestRetention:
    """Retention policies affect GC behavior."""

    def test_keep_referenced_gcs_unreferenced_steps(self):
        """keep_referenced marks steps as data_dropped after consumers run."""
        spec = _build_linear_spec()
        result = Workflow(spec, workflow_name="ret").call(fnames=[])

        read_node = result.get("read")
        algo_node = result.get("algo")
        assert algo_node is not None
        assert algo_node.ds is not None

        assert read_node is not None
        assert read_node.attrs.get("gc_status") == "data_dropped"
        assert algo_node.attrs.get("gc_status") == "data_dropped"


class TestInputMagicRef:
    """The ``_input`` magic dependency routes injected data to an entry step."""

    def _algo_args(self):
        return {
            "output_data_range": [-90.0, 30.0],
            "input_units": "Kelvin",
            "output_units": "celsius",
            "min_outbounds": "crop",
            "max_outbounds": "crop",
            "norm": False,
            "inverse": False,
        }

    def test_subworkflow_input_step_receives_parent_data(self):
        """A child ``_input`` step (not the first) gets the parent's data."""
        spec = WorkflowSpecModel.model_validate(
            {
                "steps": {
                    "read": {
                        "kind": "reader",
                        "name": "synthetic_reader",
                        "arguments": {},
                        "depends_on": [],
                    },
                    "sub": {
                        "kind": "workflow",
                        "depends_on": ["read"],
                        "spec": {
                            "steps": {
                                "pre": {
                                    "kind": "algorithm",
                                    "name": "single_channel",
                                    "arguments": self._algo_args(),
                                    "depends_on": [],
                                },
                                "consume": {
                                    "kind": "algorithm",
                                    "name": "single_channel",
                                    "arguments": self._algo_args(),
                                    "depends_on": ["_input"],
                                },
                            },
                        },
                    },
                },
            },
            context=CTX,
        )
        result = Workflow(spec, workflow_name="parent").call(fnames=[])

        consume = result["sub/consume"]
        pre = result["sub/pre"]
        # The entry step ("_input") received the injected parent tree; the
        # non-entry first step ("pre") ran with no upstream data.
        assert dict(consume.children), "consume (entry step) should receive data"
        assert not dict(pre.children), "pre (non-entry) should get no data"

    def test_top_level_input_step_gets_empty_dataset(self):
        """A top-level ``_input`` step receives an empty DataTree, not an error."""
        spec = WorkflowSpecModel.model_validate(
            {
                "steps": {
                    "entry": {
                        "kind": "algorithm",
                        "name": "single_channel",
                        "arguments": self._algo_args(),
                        "depends_on": ["_input"],
                    },
                },
            },
            context=CTX,
        )
        result = Workflow(spec, workflow_name="top").call(fnames=[])
        assert result.get("entry") is not None


class TestErrorPaths:
    """Workflow error paths raise appropriate exceptions."""

    def test_cycle_raises_at_validation(self):
        """A cycle detected during pydantic validation raises DependencyCycleError."""
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
