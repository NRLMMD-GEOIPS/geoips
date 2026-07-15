# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Exercise the doc-owned tutorial example plugins.

These examples live under
``docs/source/tutorials/extending-with-plugins/examples/`` and are shown verbatim in the
tutorials via ``literalinclude``. Importing and calling them here keeps the documented
tutorial code runnable and regression-tested in CI.
"""

import importlib.util
from pathlib import Path

import numpy as np
import xarray as xr

DOCS_EXAMPLES = (
    Path(__file__).resolve().parents[3]
    / "docs"
    / "source"
    / "tutorials"
    / "extending-with-plugins"
    / "examples"
)


def _load(module_name, filename):
    """Load a doc-owned example module by file path."""
    spec = importlib.util.spec_from_file_location(
        module_name, DOCS_EXAMPLES / filename
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_my_cloud_depth_algorithm_metadata_and_call():
    """The example algorithm carries the required attrs and computes cloud depth."""
    mod = _load("my_cloud_depth_example", "my_cloud_depth.py")
    plugin = mod.MyCloudDepthAlgorithmPlugin()

    assert plugin.interface == "algorithms"
    assert plugin.family == "xarray_to_xarray"
    assert plugin.name == "my_cloud_depth"

    xobj = xr.Dataset(
        {
            "cloud_top_height": (("y", "x"), np.array([[5000.0, 8000.0]])),
            "cloud_base_height": (("y", "x"), np.array([[1000.0, 2000.0]])),
        }
    )

    result = plugin(
        xobj,
        variables=["cloud_top_height", "cloud_base_height"],
        product_name="My-Cloud-Depth",
        output_data_range=[0.0, 20.0],
        scale_factor=0.001,
    )

    assert "My-Cloud-Depth" in result
    depth = result["My-Cloud-Depth"].values
    # (5000-1000)*0.001 = 4.0 km ; (8000-2000)*0.001 = 6.0 km
    np.testing.assert_allclose(depth, np.array([[4.0, 6.0]]))


def test_scripting_cloud_depth_example_runs():
    """The doc-owned scripting example runs and computes cloud depth via geoips.scripting."""
    mod = _load("script_cloud_depth_example", "script_cloud_depth.py")
    depth = mod.compute_cloud_depth()
    np.testing.assert_allclose(depth.values, np.array([[4.0, 6.0]]))
