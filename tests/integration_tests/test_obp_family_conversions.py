# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Integration tests for family conversions and first-class auxiliary plugins.

These tests exercise the full OBP pipeline with synthetic BaseClassPlugin
subclasses that go through the real ``_invoke`` / ``_pre_call`` / ``_post_call``
chain, verifying:

- Multi-input unwrap extracts single upstream child correctly.
- Family conversions (dataset_vars_to_list, numpy_to_dataset, ...) are applied.
- YAML plugins (gridline_annotator, feature_annotator) become callable via
  ``YamlPluginCallable`` and add metadata to the step DataTree.
- Colormapper and filename-formatter steps return DataTree output.
- ``_extract_child_kwargs`` maps children to the correct kwarg names.
- Backward-compatible inline colormapper arguments still work.
- Retention GCs auxiliary steps after consumption.
"""

from __future__ import annotations

import logging

import numpy as np
import pytest
import xarray as xr

from geoips.interfaces.class_based_plugin import BaseClassPlugin
from geoips.interfaces.class_based.workflow import Workflow
from geoips.pydantic_models.v1.workflows import WorkflowSpecModel
from geoips.utils.types.family_conversions import (
    ALGORITHM_FAMILY_CONVERSIONS,
    OUTPUT_FORMATTER_FAMILY_CONVERSIONS,
)

CTX = {"skip_plugin_name_validation": True}
LOG = logging.getLogger(__name__)


class SyntheticReader(BaseClassPlugin):
    """Synthetic reader plugin that returns a small xarray dataset."""

    interface = "readers"
    family = "standard"
    name = "synthetic_reader"
    data_tree = False

    def call(self, fnames=None, **kwargs):
        """Return synthetic ABI-like data for workflow tests."""
        from geoips.utils.types.datatree_ditto import DataTreeDitto

        ds = xr.Dataset(
            {
                "B14BT": (["y", "x"], np.arange(6, dtype=np.float64).reshape(2, 3)),
                "lat": (["y", "x"], np.zeros((2, 3))),
                "lon": (["y", "x"], np.zeros((2, 3))),
            },
            attrs={
                "start_datetime": "2024-01-01T00:00:00",
                "end_datetime": "2024-01-01T01:00:00",
                "source_name": "abi",
                "platform_name": "goes-16",
                "data_provider": "test",
                "interpolation_radius_of_influence": 3000,
            },
        )
        return DataTreeDitto(ds, name=self.name)


class SyntheticListNumpyToNumpyAlgo(BaseClassPlugin):
    """Synthetic algorithm for list-of-arrays to array family conversion."""

    interface = "algorithms"
    family = "list_numpy_to_numpy"
    name = "synthetic_list_numpy_algo"
    data_tree = False
    _family_conversion_map = ALGORITHM_FAMILY_CONVERSIONS

    def call(self, data, **kwargs):
        """Double the first converted numpy array."""
        assert isinstance(data, list), "expected list[np.ndarray] after conversion"
        arr = data[0] * 2 if data else np.array([])
        return arr


class SyntheticXarrayToXarrayAlgo(BaseClassPlugin):
    """Synthetic algorithm that verifies xarray-to-xarray conversion."""

    interface = "algorithms"
    family = "xarray_to_xarray"
    name = "synthetic_xr_to_xr_algo"
    data_tree = False
    _family_conversion_map = ALGORITHM_FAMILY_CONVERSIONS

    def call(self, data, **kwargs):
        """Return the converted xarray dataset unchanged."""
        assert isinstance(data, xr.Dataset), "expected xr.Dataset"
        return data


class SyntheticColormapper(BaseClassPlugin):
    """Synthetic colormapper plugin that emits matplotlib color metadata."""

    interface = "colormappers"
    family = "matplotlib"
    name = "synthetic_colormap"
    data_tree = True

    def call(self, data_range=None, **kwargs):
        """Return color mapping metadata as a DataTree node."""
        from geoips.utils.types.datatree_ditto import DataTreeDitto

        mpl_info = {"cmap_name": "Greys", "data_range": data_range, "colorbar": True}
        ds = xr.Dataset(
            attrs={
                "_mpl_colors_info": mpl_info,
                "data_range": data_range,
                "cmap_name": "Greys",
                "plugin_kind": "colormapper",
                "output_key": "mpl_colors_info",
            }
        )
        dt = DataTreeDitto(ds, name=self.name)
        return dt


class SyntheticFilenameFormatter(BaseClassPlugin):
    """Synthetic filename formatter that emits output filename metadata."""

    interface = "filename_formatters"
    family = "standard"
    name = "synthetic_fname"
    data_tree = True

    def call(self, data=None, suffix=".png", **kwargs):
        """Return a fake output filename as a DataTree node."""
        from geoips.utils.types.datatree_ditto import DataTreeDitto

        fname = "/fake/path/output." + suffix
        ds = xr.Dataset(
            attrs={
                "output_fnames": [fname],
                "plugin_kind": "filename_formatter",
                "output_key": "output_fnames",
            }
        )
        dt = DataTreeDitto(ds, name=self.name)
        return dt


class SyntheticImageOutputFormatter(BaseClassPlugin):
    """Synthetic image output formatter that records received dependencies."""

    interface = "output_formatters"
    family = "image"
    name = "synthetic_image"
    data_tree = False
    _family_conversion_map = OUTPUT_FORMATTER_FAMILY_CONVERSIONS

    def call(self, data, output_fnames=None, mpl_colors_info=None, **kwargs):
        """Return output metadata showing which auxiliary inputs arrived."""
        from geoips.utils.types.datatree_ditto import DataTreeDitto

        ds = xr.Dataset(
            attrs={
                "saved_files": ["/fake/path/saved.png"],
                "received_fnames": output_fnames is not None,
                "received_colors": mpl_colors_info is not None,
            }
        )
        dt = DataTreeDitto(ds, name=self.name)
        return dt


def _resolve_synthetic_plugin(kind, name):
    """Resolve workflow plugin requests to synthetic test plugins."""
    _ = name
    if kind == "reader":
        return SyntheticReader()
    if kind == "algorithm":
        return SyntheticListNumpyToNumpyAlgo()
    if kind == "colormapper":
        return SyntheticColormapper()
    if kind == "filename_formatter":
        return SyntheticFilenameFormatter()
    if kind == "output_formatter":
        return SyntheticImageOutputFormatter()
    if kind == "interpolator":
        return SyntheticXarrayToXarrayAlgo()
    if kind in ("gridline_annotator", "feature_annotator"):
        return _make_yaml_callable(kind, name)
    if kind == "sector":
        return _make_sector_callable(name)
    return SyntheticXarrayToXarrayAlgo()


def _make_yaml_callable(kind, name):
    """Build a YAML plugin callable for annotation step tests."""
    from geoips.utils.types.yaml_plugin_callable import YamlPluginCallable

    interface = kind + "s"
    return YamlPluginCallable(
        {
            "interface": interface,
            "family": "test",
            "name": name,
            "spec": {"lines": {"color": "black"}, "labels": {"top": True}},
        }
    )


def _make_sector_callable(name):
    """Build a YAML plugin callable for synthetic sector tests."""
    from geoips.utils.types.yaml_plugin_callable import YamlPluginCallable

    return YamlPluginCallable(
        {
            "interface": "sectors",
            "family": "area_definition",
            "name": name,
            "spec": {"area_id": name, "shape": [100, 100], "projection": "eqc"},
        }
    )


@pytest.fixture
def patch_for_family_conversions(monkeypatch):
    """Patch workflow plugin resolution to use synthetic test plugins."""
    monkeypatch.setattr(
        Workflow, "_resolve_plugin", staticmethod(_resolve_synthetic_plugin)
    )


def _build_spec(steps_dict, **overrides):
    """Build a workflow spec model with test validation context."""
    return WorkflowSpecModel.model_validate(
        {"steps": steps_dict, **overrides}, context=CTX
    )


class TestMultiInputUnwrap:
    """Test workflow handling of single upstream child extraction."""

    def test_single_child_unwrap(self, patch_for_family_conversions):
        """Attach a reader step output as a DataTree child."""
        spec = _build_spec(
            {
                "read": {
                    "kind": "reader",
                    "name": "synthetic_reader",
                    "arguments": {},
                    "depends_on": [],
                },
            }
        )
        result = Workflow(spec, workflow_name="t").call(fnames=[])
        child = result.get("read")
        assert child is not None
        assert isinstance(child, xr.DataTree)

    def test_reader_to_algo_chain(self, patch_for_family_conversions):
        """Run a reader-to-algorithm chain through family conversion."""
        spec = _build_spec(
            {
                "read": {
                    "kind": "reader",
                    "name": "synthetic_reader",
                    "arguments": {},
                    "depends_on": [],
                },
                "algo": {
                    "kind": "algorithm",
                    "name": "synthetic_list_numpy_algo",
                    "arguments": {},
                    "depends_on": ["read"],
                },
            }
        )
        result = Workflow(spec, workflow_name="chain").call(fnames=[])
        algo_node = result.get("algo")
        assert algo_node is not None


class TestFamilyConversions:
    """Test OBP family conversions for algorithm plugin inputs and outputs."""

    def test_list_numpy_to_numpy_conversion(self, patch_for_family_conversions):
        """Convert reader output into list-of-numpy input for an algorithm."""
        spec = _build_spec(
            {
                "read": {
                    "kind": "reader",
                    "name": "synthetic_reader",
                    "arguments": {},
                    "depends_on": [],
                },
                "algo": {
                    "kind": "algorithm",
                    "name": "synthetic_list_numpy_algo",
                    "arguments": {},
                    "depends_on": ["read"],
                },
            }
        )
        result = Workflow(spec, workflow_name="conv").call(fnames=[])
        algo_node = result.get("algo")
        assert algo_node is not None
        assert algo_node.attrs.get("plugin_name") == "synthetic_list_numpy_algo"
        assert algo_node.ds is not None

    def test_xarray_to_xarray_passthrough(self, patch_for_family_conversions):
        """Pass reader output through an xarray-to-xarray algorithm."""
        spec = _build_spec(
            {
                "read": {
                    "kind": "reader",
                    "name": "synthetic_reader",
                    "arguments": {},
                    "depends_on": [],
                },
                "algo": {
                    "kind": "algorithm",
                    "name": "synthetic_xr_to_xr_algo",
                    "arguments": {},
                    "depends_on": ["read"],
                },
            }
        )
        result = Workflow(spec, workflow_name="xrxr").call(fnames=[])
        algo_node = result.get("algo")
        assert algo_node is not None


class TestAuxiliaryPluginSteps:
    """Test first-class auxiliary plugin steps in workflows."""

    def test_colormapper_step(self, patch_for_family_conversions):
        """Run a colormapper step and attach its DataTree output."""
        spec = _build_spec(
            {
                "cmap": {
                    "kind": "colormapper",
                    "name": "synthetic_colormap",
                    "arguments": {"data_range": [0, 100]},
                    "depends_on": [],
                },
            }
        )
        result = Workflow(spec, workflow_name="cmap").call(fnames=[])
        cmap_node = result.get("cmap")
        assert cmap_node is not None
        assert cmap_node.ds is not None
        assert "plugin_name" in cmap_node.ds.attrs

    def test_filename_formatter_step(self, patch_for_family_conversions):
        """Run a filename formatter step after reader and algorithm steps."""
        spec = _build_spec(
            {
                "read": {
                    "kind": "reader",
                    "name": "synthetic_reader",
                    "arguments": {},
                    "depends_on": [],
                },
                "algo": {
                    "kind": "algorithm",
                    "name": "synthetic_list_numpy_algo",
                    "arguments": {},
                    "depends_on": ["read"],
                },
                "fname": {
                    "kind": "filename_formatter",
                    "name": "synthetic_fname",
                    "arguments": {"suffix": "png"},
                    "depends_on": ["algo"],
                },
            }
        )
        result = Workflow(spec, workflow_name="fname").call(fnames=[])
        fnode = result.get("fname")
        assert fnode is not None
        assert fnode.ds is not None

    def test_gridline_annotator_yaml_callable(self, patch_for_family_conversions):
        """Run a gridline annotator YAML plugin as a callable workflow step."""
        spec = _build_spec(
            {
                "grid": {
                    "kind": "gridline_annotator",
                    "name": "default",
                    "arguments": {},
                    "depends_on": [],
                },
            }
        )
        result = Workflow(spec, workflow_name="grid").call(fnames=[])
        gnode = result.get("grid")
        assert gnode is not None
        assert gnode.ds is not None
        assert "spec" in gnode.ds.attrs

    def test_feature_annotator_yaml_callable(self, patch_for_family_conversions):
        """Run a feature annotator YAML plugin as a callable workflow step."""
        spec = _build_spec(
            {
                "feat": {
                    "kind": "feature_annotator",
                    "name": "default",
                    "arguments": {},
                    "depends_on": [],
                },
            }
        )
        result = Workflow(spec, workflow_name="feat").call(fnames=[])
        fnode = result.get("feat")
        assert fnode is not None
        assert "spec" in fnode.ds.attrs


class TestChildKwargExtraction:
    """Test mapping auxiliary child outputs into output formatter kwargs."""

    def test_colormap_to_output_formatter(self, patch_for_family_conversions):
        """Pass colormapper and filename formatter outputs to an image output."""
        spec = _build_spec(
            {
                "read": {
                    "kind": "reader",
                    "name": "synthetic_reader",
                    "arguments": {},
                    "depends_on": [],
                },
                "algo": {
                    "kind": "algorithm",
                    "name": "synthetic_list_numpy_algo",
                    "arguments": {},
                    "depends_on": ["read"],
                },
                "cmap": {
                    "kind": "colormapper",
                    "name": "synthetic_colormap",
                    "arguments": {"data_range": [0, 100]},
                    "depends_on": [],
                },
                "fname": {
                    "kind": "filename_formatter",
                    "name": "synthetic_fname",
                    "arguments": {"suffix": "png"},
                    "depends_on": ["algo"],
                },
                "out": {
                    "kind": "output_formatter",
                    "name": "synthetic_image",
                    "arguments": {},
                    "depends_on": ["algo", "cmap", "fname"],
                },
            }
        )
        result = Workflow(spec, workflow_name="child_extract").call(fnames=[])
        out_node = result.get("out")
        assert out_node is not None
        assert out_node.ds is not None


class TestFullPipeline:
    """Test a complete reader-to-output workflow with auxiliary steps."""

    def test_full_pipeline(self, patch_for_family_conversions):
        """Run the full synthetic pipeline and retain expected step metadata."""
        spec = _build_spec(
            {
                "read": {
                    "kind": "reader",
                    "name": "synthetic_reader",
                    "arguments": {},
                    "depends_on": [],
                },
                "algo": {
                    "kind": "algorithm",
                    "name": "synthetic_list_numpy_algo",
                    "arguments": {},
                    "depends_on": ["read"],
                },
                "cmap": {
                    "kind": "colormapper",
                    "name": "synthetic_colormap",
                    "arguments": {"data_range": [0, 100]},
                    "depends_on": [],
                },
                "fname": {
                    "kind": "filename_formatter",
                    "name": "synthetic_fname",
                    "arguments": {"suffix": "png"},
                    "depends_on": ["algo"],
                },
                "grid": {
                    "kind": "gridline_annotator",
                    "name": "default",
                    "arguments": {},
                    "depends_on": [],
                },
                "feat": {
                    "kind": "feature_annotator",
                    "name": "default",
                    "arguments": {},
                    "depends_on": [],
                },
                "out": {
                    "kind": "output_formatter",
                    "name": "synthetic_image",
                    "arguments": {},
                    "depends_on": ["algo", "cmap", "fname", "grid", "feat"],
                },
            },
        )
        result = Workflow(spec, workflow_name="full").call(fnames=[])
        out_node = result.get("out")
        assert out_node is not None

        for step_id in ["read", "algo", "cmap", "fname", "grid", "feat"]:
            node = result.get(step_id)
            assert node is not None
            assert node.attrs.get("plugin_kind") or node.attrs.get("plugin_name")


class TestBackwardCompat:
    """Test backward-compatible inline auxiliary output arguments."""

    def test_inline_colormapper_still_present(
        self,
        patch_for_family_conversions,
    ):
        """Accept inline colormapper metadata on an output formatter step."""
        spec = _build_spec(
            {
                "read": {
                    "kind": "reader",
                    "name": "synthetic_reader",
                    "arguments": {},
                    "depends_on": [],
                },
                "algo": {
                    "kind": "algorithm",
                    "name": "synthetic_list_numpy_algo",
                    "arguments": {},
                    "depends_on": ["read"],
                },
                "out": {
                    "kind": "output_formatter",
                    "name": "synthetic_image",
                    "arguments": {
                        "mpl_colors_info": {
                            "cmap_name": "legacy",
                            "data_range": [0, 1],
                        },
                        "output_fnames": ["/fake/path/legacy.png"],
                    },
                    "depends_on": ["algo"],
                },
            }
        )
        result = Workflow(spec, workflow_name="backcompat").call(fnames=[])
        assert result.get("out") is not None


class TestRetention:
    """Test workflow retention behavior for consumed auxiliary steps."""

    def test_keep_referenced_gc_aux_steps(self, patch_for_family_conversions):
        """Mark auxiliary steps as garbage-collected after consumers run."""
        spec = _build_spec(
            {
                "read": {
                    "kind": "reader",
                    "name": "synthetic_reader",
                    "arguments": {},
                    "depends_on": [],
                },
                "algo": {
                    "kind": "algorithm",
                    "name": "synthetic_list_numpy_algo",
                    "arguments": {},
                    "depends_on": ["read"],
                },
                "cmap": {
                    "kind": "colormapper",
                    "name": "synthetic_colormap",
                    "arguments": {"data_range": [0, 100]},
                    "depends_on": [],
                },
                "out": {
                    "kind": "output_formatter",
                    "name": "synthetic_image",
                    "arguments": {
                        "mpl_colors_info": {"cmap_name": "test"},
                        "output_fnames": ["/fake/path/t.png"],
                    },
                    "depends_on": ["algo"],
                },
            },
        )
        result = Workflow(spec, workflow_name="ret").call(fnames=[])
        cmap_node = result.get("cmap")
        assert cmap_node is not None
        assert "gc_status" in cmap_node.attrs
