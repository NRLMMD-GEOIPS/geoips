# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Scripting example: compute cloud depth from synthetic data.

This is the doc-owned example used by the
:ref:`scripting tutorial <scripting-tutorial>`.
It uses the :mod:`geoips.scripting` DataTree API with *synthetic* input data (the
"bring your own data" pattern), so it runs without any external data files.
It is executed
by ``tests/unit_tests/docs/test_tutorial_examples.py``
so the tutorial code stays runnable.
"""

import numpy as np
import xarray as xr

from geoips.scripting import (
    RetentionPolicy,
    add_data_step,
    get_current_data,
    initialize_script_tree,
)


def compute_cloud_depth():
    """Build a script tree, add synthetic data, and compute cloud depth."""
    # 1. Initialize a script tree. Every scripting session starts here.
    tree = initialize_script_tree(
        name="cloud_depth_demo",
        retention_policy=RetentionPolicy.keep_all,
    )

    # 2. Bring your own data: build a synthetic xarray Dataset with the coordinates and
    #    metadata GeoIPS plugins expect, and insert it as a data step.
    xobj = xr.Dataset(
        data_vars={
            "cloud_top_height": (("y", "x"), np.array([[5000.0, 8000.0]])),
            "cloud_base_height": (("y", "x"), np.array([[1000.0, 2000.0]])),
        },
        coords={
            "latitude": (("y", "x"), np.array([[10.0, 10.1]])),
            "longitude": (("y", "x"), np.array([[-50.0, -49.9]])),
        },
        attrs={"source_name": "demo", "platform_name": "demo"},
    )
    tree = add_data_step(tree, xobj, step_id="load_synthetic_data")

    # 3. Pull the current data out of the tree, manipulate it, and reinsert it as a new
    #    step. get_current_data returns a mutable copy of the most recent data step.
    current = get_current_data(tree)
    depth_km = (current["cloud_top_height"] - current["cloud_base_height"]) * 0.001
    current["cloud_depth"] = depth_km
    tree = add_data_step(tree, current, step_id="compute_cloud_depth")

    # 4. Read the result back out.
    result = get_current_data(tree)
    return result["cloud_depth"]


if __name__ == "__main__":
    print(compute_cloud_depth().values)
