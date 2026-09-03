# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""End-to-end test for static sectoring in the OBP (single-source-procflow parity).

This exercises the order-based procflow (OBP) equivalent of the legacy
single-source procflow's (SSP) static ``sector_list`` behavior: processing a
run against one or more static sectors.

A ``split`` step with ``over: sector_list`` resolves each static sector in
``globals.sector_list`` to an ``AreaDefinition`` and runs the inline body
sub-workflow once per sector, seeding the per-sector ``area_def`` into the
branch so the body's steps receive it.  This is the core capability: one
output branch per static sector in a single run — mirroring how the SSP
produces one output per sector.

Uses *real* sector resolution (``global_cylindrical`` + ``australia``) but a
synthetic reader and a synthetic body step so no input data files are needed.
"""

from __future__ import annotations

import numpy as np
import pytest
import xarray as xr

from geoips.interfaces.class_based.workflow import Workflow
from geoips.interfaces.class_based_plugin import BaseClassPlugin
from geoips.pydantic_models.v1.workflows import WorkflowSpecModel
from geoips.utils.types.datatree_ditto import DataTreeDitto

CTX = {"skip_plugin_name_validation": True}
SECTORS = ["global_cylindrical", "australia"]


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


class _SectorRecorder(BaseClassPlugin):
    """A body step (real plugin base) recording the per-branch ``area_def``.

    Subclasses ``BaseClassPlugin`` so it goes through the real
    ``_invoke``/``_extract_child_kwargs`` chain — i.e. it receives ``area_def``
    via the ``sector`` conduit, exactly as a real interpolator/output step would.
    """

    interface = "algorithms"
    family = "test"
    name = "sector_recorder"
    data_tree = True
    seen_area_ids: list = []

    def call(self, data=None, area_def=None, **kwargs):
        if area_def is not None:
            type(self).seen_area_ids.append(
                getattr(area_def, "area_id", repr(area_def))
            )
        return data if data is not None else xr.DataTree(name="empty")


def _resolve(kind, name):
    if kind == "reader":
        return _Reader()
    return _SectorRecorder()


@pytest.fixture
def patch_sectoring(monkeypatch):
    """Patch workflow plugin resolution and reset recorded sector calls."""
    monkeypatch.setattr(Workflow, "_resolve_plugin", staticmethod(_resolve))
    _SectorRecorder.seen_area_ids = []


def _sbp_spec():
    return WorkflowSpecModel.model_validate(
        {
            "globals": {"sector_list": SECTORS},
            "steps": {
                "read": {
                    "kind": "reader",
                    "name": "synthetic_reader",
                    "arguments": {},
                    "depends_on": [],
                },
                "per_sector": {
                    "kind": "split",
                    "arguments": {"over": "sector_list"},
                    "spec": {
                        "steps": {
                            "apply": {
                                "kind": "algorithm",
                                "name": "sector_recorder",
                                "arguments": {},
                                "depends_on": [],
                            },
                        },
                    },
                    "depends_on": ["read"],
                },
            },
        },
        context=CTX,
    )


def test_sector_list_resolves_to_branches():
    """``_resolve_sector_branches`` maps the static sector_list to area_defs."""
    wf = Workflow(_sbp_spec(), workflow_name="sbp")
    branches = wf._resolve_sector_branches()
    assert len(branches) == len(SECTORS)
    names = {name for name, _ in branches}
    assert "global_cylindrical" in names
    # every branch carries a resolved AreaDefinition
    assert all(area_def is not None for _, area_def in branches)


def test_split_fans_out_one_branch_per_static_sector(patch_sectoring):
    """One output branch is produced per static sector, each given its area_def."""
    result = Workflow(_sbp_spec(), workflow_name="sbp").call(fnames=[])
    split_node = result.get("per_sector")
    assert split_node is not None
    # one branch per static sector
    assert len(dict(split_node.children)) == len(SECTORS)
    # the per-branch area_def was seeded and reached the body step
    assert len(_SectorRecorder.seen_area_ids) == len(SECTORS)
    assert "global_cylindrical" in _SectorRecorder.seen_area_ids
