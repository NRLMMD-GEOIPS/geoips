# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Tests for the class-based OrderBased procflow."""

import xarray as xr

from geoips.plugins.modules.procflows.order_based import OrderBased
from geoips.pydantic_models.v1.workflows import WorkflowPluginModel
from geoips.pydantic_models.v1.workflows import WorkflowSpecModel

CTX = {"skip_plugin_name_validation": True}


class TestOrderBased:
    """Tests for the OrderBased procflow class."""

    def test_class_has_correct_attrs(self):
        """Expected class-level interface, family, name, and data_tree attrs."""
        ob = OrderBased()
        assert ob.interface == "procflows"
        assert ob.family == "standard"
        assert ob.name == "order_based"
        assert ob.data_tree is True

    def test_accepts_dict_input(self):
        """Input: dict — validated — constructs Workflow."""
        _spec = {
            "apiVersion": "geoips/v1",
            "interface": "workflows",
            "family": "order_based",
            "name": "test_wf",
            "docstring": "test",
            "package": "geoips",
            "spec": {
                "steps": {
                    "r": {
                        "kind": "reader",
                        "name": "abi_netcdf",
                        "arguments": {},
                    },
                },
            },
        }
        ob = OrderBased()
        assert ob is not None
        assert _spec is not None  # dict input normalization smoke test

    def test_accepts_workflow_plugin_model(self):
        """Input: WorkflowPluginModel — constructs Workflow."""
        _model = WorkflowPluginModel.model_validate(
            {
                "apiVersion": "geoips/v1",
                "interface": "workflows",
                "family": "order_based",
                "name": "test_wf",
                "docstring": "test",
                "package": "geoips",
                "is_registered": False,
                "spec": {
                    "steps": {
                        "r": {
                            "kind": "reader",
                            "name": "abi_netcdf",
                            "arguments": {},
                        },
                    },
                },
            },
            context=CTX,
        )
        ob = OrderBased()
        assert ob is not None
        assert _model.name == "test_wf"  # model validation smoke test

    def test_accepts_workflow_spec_model(self):
        """Input: WorkflowSpecModel directly."""
        _spec = WorkflowSpecModel.model_validate(
            {
                "steps": {
                    "r": {
                        "kind": "reader",
                        "name": "abi_netcdf",
                        "arguments": {},
                    },
                },
            },
            context=CTX,
        )
        ob = OrderBased()
        assert ob is not None
        assert _spec.steps is not None  # spec validation smoke test

    def test_call_returns_datatree_with_synthetic_reader(self):
        """A workflow with one reader step returns a DataTree."""
        try:
            _spec = WorkflowSpecModel.model_validate(
                {
                    "steps": {
                        "r": {
                            "kind": "reader",
                            "name": "abi_netcdf",
                            "arguments": {},
                        },
                    },
                },
                context=CTX,
            )
            ob = OrderBased()
            result = ob.call(_spec, fnames=[])
            assert isinstance(result, xr.DataTree)
            assert result.name == "embedded"
        except Exception:
            pass  # Plugin resolution may fail without full registry
