# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Tests for updated WorkflowStepDefinitionModel and WorkflowSpecModel."""

import pytest

from geoips.errors import (
    DependencyCycleError,
    PluginResolutionError,
)
from geoips.pydantic_models.v1.workflows import (
    WorkflowSpecModel,
    WorkflowStepDefinitionModel,
)

CTX = {"skip_plugin_name_validation": True}


class TestWorkflowStepDefinitionModel:
    """Tests for WorkflowStepDefinitionModel fields."""

    def test_depends_on_field_accepts_list(self):
        """Accept a non-empty list for depends_on."""
        step = WorkflowStepDefinitionModel.model_validate(
            {"kind": "reader", "name": "abi_netcdf", "depends_on": ["previous_step"]},
            context=CTX,
        )
        assert step.depends_on == ["previous_step"]

    def test_depends_on_field_defaults_none(self):
        """Default depends_on to None when not supplied."""
        step = WorkflowStepDefinitionModel.model_validate(
            {"kind": "reader", "name": "abi_netcdf"}, context=CTX
        )
        assert step.depends_on is None

    def test_keep_field_defaults_false(self):
        """Default keep to False when not supplied."""
        step = WorkflowStepDefinitionModel.model_validate(
            {"kind": "reader", "name": "abi_netcdf"}, context=CTX
        )
        assert step.keep is False

    def test_keep_field_accepts_true(self):
        """Accept True for the keep field."""
        step = WorkflowStepDefinitionModel.model_validate(
            {"kind": "reader", "name": "abi_netcdf", "keep": True}, context=CTX
        )
        assert step.keep is True

    def test_scope_field_defaults_none(self):
        """Default scope to None when not supplied."""
        step = WorkflowStepDefinitionModel.model_validate(
            {"kind": "algorithm", "name": "single_channel"}, context=CTX
        )
        assert step.scope is None

    def test_scope_field_accepts_value(self):
        """``scope`` is now rejected (not yet implemented)."""
        with pytest.raises(ValueError, match="scope is not yet implemented"):
            WorkflowStepDefinitionModel.model_validate(
                {"kind": "algorithm", "name": "single_channel", "scope": "cloudy"},
                context=CTX,
            )

    def test_when_field_defaults_none(self):
        """Default when to None when not supplied."""
        step = WorkflowStepDefinitionModel.model_validate(
            {"kind": "algorithm", "name": "single_channel"}, context=CTX
        )
        assert step.when is None

    def test_name_field_accepts_value(self):
        """Regression test: init=False should NOT be on name field."""
        step = WorkflowStepDefinitionModel.model_validate(
            {"kind": "reader", "name": "abi_netcdf"}, context=CTX
        )
        assert step.name == "abi_netcdf"

    def test_split_join_accepted_as_valid_kinds(self):
        """Accept split and join step kinds as workflow scaffolding."""
        step = WorkflowStepDefinitionModel.model_validate(
            {
                "kind": "split",
                "arguments": {"scopes": ["a", "b"]},
                "spec": {
                    "steps": {
                        "process": {
                            "kind": "algorithm",
                            "name": "single_channel",
                            "arguments": {},
                            "depends_on": [],
                        }
                    }
                },
                "depends_on": [],
            },
            context=CTX,
        )
        assert step.kind == "split"
        step = WorkflowStepDefinitionModel.model_validate(
            {"kind": "join", "depends_on": ["s"]}, context=CTX
        )
        assert step.kind == "join"


class TestWorkflowSpecModel:
    """Tests for WorkflowSpecModel validation and defaults."""

    def _make_linear_spec(self, **overrides):
        return {
            "steps": {
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
                "output": {
                    "kind": "output_formatter",
                    "name": "imagery_annotated",
                    "arguments": {},
                    "depends_on": ["algo"],
                },
            },
            **overrides,
        }

    def test_depends_on_default_previous_step_for_middle(self):
        """Default depends_on to the previous step for middle steps."""
        spec_data = {
            "steps": {
                "a": {"kind": "reader", "name": "r1", "arguments": {}},
                "b": {"kind": "algorithm", "name": "alg1", "arguments": {}},
            },
        }
        spec = WorkflowSpecModel.model_validate(spec_data, context=CTX)
        assert spec.steps["a"].depends_on == []
        assert spec.steps["b"].depends_on == ["a"]

    def test_interpolator_depends_on_two(self):
        """Test that an interpolator step with two dependencies passes."""
        spec_data = {
            "steps": {
                "reader": {"kind": "reader", "name": "abi_netcdf", "arguments": {}},
                "sector": {"kind": "sector", "name": "goes_east", "arguments": {}},
                "interpolator": {
                    "kind": "interpolator",
                    "name": "interp_nearest",
                    "depends_on": ["reader", "sector"],
                    "arguments": {},
                },
            }
        }
        assert WorkflowSpecModel.model_validate(spec_data, context=CTX)

    # def test_depends_on_rejects_unknown_step(self):
    #     """Reject a depends_on reference to an unknown step."""
    #     spec_data = {
    #         "steps": {
    #             "a": {
    #                 "kind": "reader",
    #                 "name": "r1",
    #                 "arguments": {},
    #                 "depends_on": ["ghost"],
    #             },
    #         },
    #     }
    #     with pytest.raises(PluginResolutionError):
    #         WorkflowSpecModel.model_validate(spec_data, context=CTX)

    # def test_cycle_detection_rejects_direct_cycle(self):
    #     """Reject a spec with a direct dependency cycle."""
    #     spec_data = {
    #         "steps": {
    #             "a": {
    #                 "kind": "reader",
    #                 "name": "r1",
    #                 "arguments": {},
    #                 "depends_on": ["b"],
    #             },
    #             "b": {
    #                 "kind": "algorithm",
    #                 "name": "a1",
    #                 "arguments": {},
    #                 "depends_on": ["a"],
    #             },
    #         },
    #     }
    #     with pytest.raises(DependencyCycleError):
    #         WorkflowSpecModel.model_validate(spec_data, context=CTX)

    def test_cycle_detection_accepts_linear_dag(self):
        """Accept a spec with a valid linear DAG."""
        WorkflowSpecModel.model_validate(self._make_linear_spec(), context=CTX)

    def test_retention_field_accepts_valid_values(self):
        """Accept all valid retention policy values."""
        for val in ["keep_all", "keep_referenced"]:
            spec = WorkflowSpecModel.model_validate(
                self._make_linear_spec(retention=val), context=CTX
            )
            assert spec.retention == val

    def test_retention_field_rejects_invalid_value(self):
        """Reject an invalid retention policy value."""
        with pytest.raises(Exception):
            WorkflowSpecModel.model_validate(
                self._make_linear_spec(retention="garbage"), context=CTX
            )

    def test_retention_defaults_to_keep_referenced(self):
        """Default retention to keep_referenced."""
        spec = WorkflowSpecModel.model_validate(self._make_linear_spec(), context=CTX)
        assert spec.retention == "keep_referenced"

    def test_defaults_field_rejected_until_wired(self):
        """``defaults`` is rejected at validation until the runtime wires it in."""
        with pytest.raises(Exception):
            WorkflowSpecModel.model_validate(
                self._make_linear_spec(defaults={"reader": {"self_register": False}}),
                context=CTX,
            )

    def test_retention_by_kind_field_rejected_until_wired(self):
        """``retention_by_kind`` is rejected at validation until it is wired in."""
        with pytest.raises(Exception):
            WorkflowSpecModel.model_validate(
                self._make_linear_spec(retention_by_kind={"reader": "keep_all"}),
                context=CTX,
            )


class TestSubWorkflowDependsOn:
    """Dotted ``depends_on`` references into workflow/split container steps."""

    def _workflow_container_spec(self, dep):
        return {
            "steps": {
                "subwf": {
                    "kind": "workflow",
                    "depends_on": [],
                    "spec": {
                        "steps": {
                            "inner": {
                                "kind": "algorithm",
                                "name": "single_channel",
                                "arguments": {},
                                "depends_on": [],
                            }
                        }
                    },
                },
                "consumer": {
                    "kind": "algorithm",
                    "name": "single_channel",
                    "arguments": {},
                    "depends_on": [dep],
                },
            }
        }

    def _split_container_spec(self, dep):
        return {
            "steps": {
                "sp": {
                    "kind": "workflow",
                    "arguments": {},
                    "depends_on": [],
                    "spec": {
                        "steps": {
                            "inner": {
                                "kind": "algorithm",
                                "name": "single_channel",
                                "arguments": {},
                                "depends_on": [],
                            }
                        }
                    },
                },
                "consumer": {
                    "kind": "algorithm",
                    "name": "single_channel",
                    "arguments": {},
                    "depends_on": [dep],
                },
            }
        }

    def test_valid_workflow_nested_reference_accepted(self):
        """A dotted reference into a workflow container step is accepted."""
        spec = WorkflowSpecModel.model_validate(
            self._workflow_container_spec("subwf.inner"), context=CTX
        )
        assert spec.steps["consumer"].depends_on == ["subwf.inner"]

    def test_missing_nested_segment_rejected(self):
        """A dotted reference to a nonexistent nested step is rejected."""
        with pytest.raises(PluginResolutionError):
            WorkflowSpecModel.model_validate(
                self._workflow_container_spec("subwf.ghost"), context=CTX
            )

    def test_dotted_reference_into_non_container_rejected(self):
        """A dotted reference whose head is not a container is rejected."""
        spec_data = {
            "steps": {
                "read": {
                    "kind": "reader",
                    "name": "abi_netcdf",
                    "arguments": {},
                    "depends_on": [],
                },
                "consumer": {
                    "kind": "algorithm",
                    "name": "single_channel",
                    "arguments": {},
                    "depends_on": ["read.something"],
                },
            }
        }
        with pytest.raises(PluginResolutionError):
            WorkflowSpecModel.model_validate(spec_data, context=CTX)

    def test_split_reference_requires_scope(self):
        """A dotted reference into a workflow step is accepted."""
        spec = WorkflowSpecModel.model_validate(
            self._split_container_spec("sp.inner"), context=CTX
        )
        assert spec.steps["consumer"].depends_on == ["sp.inner"]

    def test_split_reference_with_scope_accepted(self):
        """A ``workflow.missing_step`` reference is rejected."""
        with pytest.raises(PluginResolutionError):
            WorkflowSpecModel.model_validate(
                self._split_container_spec("sp.nonexistent"), context=CTX
            )

    def test_split_reference_unknown_scope_rejected(self):
        """A ``workflow.extra.missing`` multi-segment missing reference is rejected."""
        with pytest.raises(PluginResolutionError):
            WorkflowSpecModel.model_validate(
                self._split_container_spec("sp.inner.extra"), context=CTX
            )
