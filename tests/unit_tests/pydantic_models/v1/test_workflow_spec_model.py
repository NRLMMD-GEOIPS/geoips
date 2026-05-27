# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Tests for updated WorkflowStepDefinitionModel and WorkflowSpecModel."""

import pytest

from geoips.errors import (
    DependencyCycleError,
    PluginResolutionError,
    DanglingOutputError,
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

    def test_scope_field_accepts_string(self):
        """Accept a string value for the scope field."""
        step = WorkflowStepDefinitionModel.model_validate(
            {"kind": "algorithm", "name": "single_channel", "scope": "cloudy"},
            context=CTX,
        )
        assert step.scope == "cloudy"

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
        """Accept split and join as valid step kinds."""
        step = WorkflowStepDefinitionModel.model_validate(
            {"kind": "split", "name": "split_by_data"}
        )
        assert step.kind == "split"
        step = WorkflowStepDefinitionModel.model_validate(
            {"kind": "join", "name": "merge_data"}
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

    def test_outputs_default_to_last_step(self):
        """Default outputs to the last step in the spec."""
        spec = WorkflowSpecModel.model_validate(self._make_linear_spec(), context=CTX)
        assert spec.outputs == ["output"]

    def test_outputs_accepts_explicit_list(self):
        """Accept an explicit list for outputs."""
        spec = WorkflowSpecModel.model_validate(
            self._make_linear_spec(outputs=["algo", "output"]), context=CTX
        )
        assert spec.outputs == ["algo", "output"]

    def test_outputs_rejects_dangling_step_id(self):
        """Reject an output that references a nonexistent step."""
        with pytest.raises(DanglingOutputError):
            WorkflowSpecModel.model_validate(
                self._make_linear_spec(outputs=["nonexistent_step"]), context=CTX
            )

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

    def test_depends_on_rejects_unknown_step(self):
        """Reject a depends_on reference to an unknown step."""
        spec_data = {
            "steps": {
                "a": {
                    "kind": "reader",
                    "name": "r1",
                    "arguments": {},
                    "depends_on": ["ghost"],
                },
            },
        }
        with pytest.raises(PluginResolutionError):
            WorkflowSpecModel.model_validate(spec_data, context=CTX)

    def test_cycle_detection_rejects_direct_cycle(self):
        """Reject a spec with a direct dependency cycle."""
        spec_data = {
            "steps": {
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
            },
        }
        with pytest.raises(DependencyCycleError):
            WorkflowSpecModel.model_validate(spec_data, context=CTX)

    def test_cycle_detection_accepts_linear_dag(self):
        """Accept a spec with a valid linear DAG."""
        WorkflowSpecModel.model_validate(self._make_linear_spec(), context=CTX)

    def test_retention_field_accepts_valid_values(self):
        """Accept all valid retention policy values."""
        for val in ["keep_all", "keep_referenced", "keep_outputs_only"]:
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

    def test_defaults_field_accepts_per_kind_dict(self):
        """Accept a per-kind defaults dictionary."""
        spec = WorkflowSpecModel.model_validate(
            self._make_linear_spec(defaults={"reader": {"self_register": False}}),
            context=CTX,
        )
        assert spec.defaults["reader"]["self_register"] is False

    def test_retention_by_kind_field_accepts_overrides(self):
        """Accept per-kind retention overrides."""
        spec = WorkflowSpecModel.model_validate(
            self._make_linear_spec(retention_by_kind={"reader": "keep_all"}),
            context=CTX,
        )
        assert spec.retention_by_kind["reader"] == "keep_all"
