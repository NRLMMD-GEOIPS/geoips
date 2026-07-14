# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

r"""End-to-end OBP safety-net test for the real reader contract.

GeoIPS readers return ``{key: xr.Dataset}`` dicts (not pre-wrapped
``DataTree``\ s).  This is the most-traveled OBP path — read → process — and
it was previously broken in two ways that no test exercised:

1. ``BaseReaderPlugin._post_call`` used ``xr.*`` without importing ``xarray``.
2. ``BaseClassPlugin._invoke`` early-returned on ``data is None`` (the reader
   case), so ``_post_call`` — and therefore the ``dict -> DataTree`` merge —
   never ran, and ``_attach_step_node`` crashed trying to wrap a raw dict.

These tests use a reader whose ``call()`` returns the real dict contract and
run it through the *real* ``Workflow`` / ``_invoke`` / ``_pre_call`` /
``_post_call`` chain, so the read→algorithm path stays exercised.
"""

from __future__ import annotations

import numpy as np
import pytest
import xarray as xr

from geoips.interfaces.class_based.readers import BaseReaderPlugin
from geoips.interfaces.class_based.algorithms import BaseAlgorithmPlugin
from geoips.interfaces.class_based.workflow import Workflow
from geoips.pydantic_models.v1.workflows import WorkflowSpecModel

CTX = {"skip_plugin_name_validation": True}


class _DictReader(BaseReaderPlugin):
    """Reader using the real GeoIPS contract: returns ``{key: xr.Dataset}``."""

    interface = "readers"
    family = "standard"
    name = "dict_reader"

    def call(self, fnames=None, **kwargs):
        ds = xr.Dataset(
            {"B14BT": (["y", "x"], np.arange(6, dtype=np.float64).reshape(2, 3))},
            attrs={"source_name": "abi"},
        )
        meta = xr.Dataset(attrs={"platform_name": "goes-16"})
        return {"DATA": ds, "METADATA": meta}


class _XrToXrAlgo(BaseAlgorithmPlugin):
    """Real-base xarray_to_xarray algorithm that records what type it received."""

    interface = "algorithms"
    family = "xarray_to_xarray"
    name = "xr_to_xr_algo"

    received_type: str | None = None

    def call(self, data, **kwargs):
        type(self).received_type = type(data).__name__
        return data


def _resolve(kind, name):
    if kind == "reader":
        return _DictReader()
    if kind == "algorithm":
        return _XrToXrAlgo()
    return _XrToXrAlgo()


@pytest.fixture
def patch_reader_path(monkeypatch):
    """Patch workflow plugin resolution and reset algorithm call tracking."""
    monkeypatch.setattr(Workflow, "_resolve_plugin", staticmethod(_resolve))
    _XrToXrAlgo.received_type = None


def _spec(steps, **overrides):
    return WorkflowSpecModel.model_validate({"steps": steps, **overrides}, context=CTX)


def test_reader_dict_merged_into_datatree(patch_reader_path):
    """A reader returning a dict is merged into a DataTree with data + metadata."""
    spec = _spec(
        {
            "read": {
                "kind": "reader",
                "name": "dict_reader",
                "arguments": {},
                "depends_on": [],
                "keep": True,
            },
        }
    )
    result = Workflow(spec, workflow_name="t").call(fnames=[])
    node = result.get("read")
    assert isinstance(node, xr.DataTree)
    assert node.ds is not None
    # Data payload survived under the reader's DATA child.
    assert "B14BT" in node["DATA"].ds.data_vars
    assert node["DATA"].ds.attrs.get("source_name") == "abi"
    # METADATA attrs were merged onto the reader root node.
    assert node.ds.attrs.get("platform_name") == "goes-16"


def test_reader_to_algo_receives_dataset(patch_reader_path):
    """Downstream algorithm receives the upstream reader data as an xr.Dataset."""
    spec = _spec(
        {
            "read": {
                "kind": "reader",
                "name": "dict_reader",
                "arguments": {},
                "depends_on": [],
            },
            "algo": {
                "kind": "algorithm",
                "name": "xr_to_xr_algo",
                "arguments": {},
                "depends_on": ["read"],
            },
        }
    )
    result = Workflow(spec, workflow_name="chain").call(fnames=[])
    assert result.get("algo") is not None
    # The xarray_to_xarray family converter delivered a Dataset to call().
    assert _XrToXrAlgo.received_type == "Dataset"


def test_reader_step_has_provenance(patch_reader_path):
    """Reader step node carries provenance + a stable output token."""
    spec = _spec(
        {
            "read": {
                "kind": "reader",
                "name": "dict_reader",
                "arguments": {},
                "depends_on": [],
            },
        }
    )
    result = Workflow(spec, workflow_name="prov").call(fnames=[])
    node = result.get("read")
    assert node.attrs.get("plugin_kind") == "reader"
    assert node.attrs.get("plugin_name") == "dict_reader"
    token = node.attrs.get("output_token", "")
    assert token.startswith("dask:") or token.startswith("untokenizable:")
    assert "gc_status" in node.attrs
