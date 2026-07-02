# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Integration tests for ``split`` / ``join`` fan-out in the OBP.

A ``split`` step runs its inline body sub-workflow once per branch (here, per
explicit ``scope``), nesting results under ``/<split_id>/<scope>``.  A ``join``
step re-collects those branches.  This is the mechanism behind static
multi-sector processing (one branch per sector).
"""

from __future__ import annotations

import numpy as np
import pytest
import xarray as xr

from geoips.interfaces.class_based.workflow import Workflow
from geoips.pydantic_models.v1.workflows import WorkflowSpecModel
from geoips.utils.types.datatree_ditto import DataTreeDitto

CTX = {"skip_plugin_name_validation": True}


class _Reader:
    interface = "readers"
    family = "test"
    name = "synthetic_reader"
    data_tree = False

    def call(self, fnames=None, **kwargs):
        ds = xr.Dataset(
            {"B14BT": (["y", "x"], np.arange(6, dtype=np.float64).reshape(2, 3))},
            attrs={"source_name": "abi"},
        )
        return DataTreeDitto(ds, name="reader_output")

    def __call__(self, fnames=None, **kwargs):
        return self.call(fnames=fnames, **kwargs)


class _Passthrough:
    """A data_tree plugin that returns whatever upstream it is handed."""

    data_tree = True

    def call(self, data=None, **kwargs):
        return data

    def __call__(self, data=None, **kwargs):
        if data is not None:
            return data
        return xr.DataTree(name="empty")


def _resolve(kind, name):
    if kind == "reader":
        return _Reader()
    return _Passthrough()


@pytest.fixture
def patch_split(monkeypatch):
    monkeypatch.setattr(Workflow, "_resolve_plugin", staticmethod(_resolve))


def _spec(steps, **overrides):
    return WorkflowSpecModel.model_validate({"steps": steps, **overrides}, context=CTX)


def _split_spec():
    return _spec(
        {
            "read": {
                "kind": "reader",
                "name": "synthetic_reader",
                "arguments": {},
                "depends_on": [],
            },
            "per_scope": {
                "kind": "split",
                "arguments": {"scopes": ["alpha", "beta"]},
                "spec": {
                    "steps": {
                        "process": {
                            "kind": "algorithm",
                            "name": "passthrough",
                            "arguments": {},
                            "depends_on": [],
                        },
                    },
                },
                "depends_on": ["read"],
            },
            "combine": {
                "kind": "join",
                "arguments": {},
                "depends_on": ["per_scope"],
            },
        }
    )


def test_split_validates():
    """A split step with an inline body spec + scopes validates."""
    spec = _split_spec()
    assert spec.steps["per_scope"].kind == "split"
    assert spec.steps["per_scope"].spec is not None
    assert spec.steps["combine"].kind == "join"


def test_split_runs_body_once_per_scope(patch_split):
    """The split node has one child branch per scope."""
    result = Workflow(_split_spec(), workflow_name="t").call(fnames=[])
    split_node = result.get("per_scope")
    assert split_node is not None
    children = dict(split_node.children)
    assert set(children) == {"alpha", "beta"}
    assert list(split_node.attrs.get("split_scopes")) == ["alpha", "beta"]


def test_join_collects_branches(patch_split):
    """The join node records the scopes it merged."""
    result = Workflow(_split_spec(), workflow_name="t").call(fnames=[])
    join_node = result.get("combine")
    assert join_node is not None
    assert set(join_node.attrs.get("joined_scopes")) == {"alpha", "beta"}
    # branch subtrees are re-nested under the join node
    assert set(dict(join_node.children)) == {"alpha", "beta"}


def _split_spec_with_input():
    """Split whose branch body routes injected branch data via ``_input``."""
    return _spec(
        {
            "read": {
                "kind": "reader",
                "name": "synthetic_reader",
                "arguments": {},
                "depends_on": [],
            },
            "per_scope": {
                "kind": "split",
                "arguments": {"scopes": ["alpha", "beta"]},
                "spec": {
                    "steps": {
                        "prep": {
                            "kind": "algorithm",
                            "name": "passthrough",
                            "arguments": {},
                            "depends_on": [],
                        },
                        "process": {
                            "kind": "algorithm",
                            "name": "passthrough",
                            "arguments": {},
                            "depends_on": ["_input"],
                        },
                    },
                },
                "depends_on": ["read"],
            },
        }
    )


def test_split_branch_input_step_receives_seed(patch_split):
    """A branch body ``_input`` step receives the seeded branch data."""
    result = Workflow(_split_spec_with_input(), workflow_name="t").call(fnames=[])
    for scope in ("alpha", "beta"):
        process = result[f"per_scope/{scope}/process"]
        prep = result[f"per_scope/{scope}/prep"]
        # entry step ("_input") received the seeded branch tree; the non-entry
        # "prep" step ran with no upstream data.
        assert dict(process.children), f"{scope}/process should receive seed"
        assert not dict(prep.children), f"{scope}/prep should get no data"


def test_split_requires_scopes_or_over(patch_split):
    """A split with neither 'scopes' nor 'over' raises at runtime."""
    spec = _spec(
        {
            "read": {
                "kind": "reader",
                "name": "synthetic_reader",
                "arguments": {},
                "depends_on": [],
            },
            "bad": {
                "kind": "split",
                "arguments": {},
                "spec": {
                    "steps": {
                        "p": {
                            "kind": "algorithm",
                            "name": "passthrough",
                            "arguments": {},
                            "depends_on": [],
                        },
                    },
                },
                "depends_on": ["read"],
            },
        }
    )
    from geoips.errors import PluginResolutionError

    with pytest.raises(PluginResolutionError):
        Workflow(spec, workflow_name="t").call(fnames=[])
