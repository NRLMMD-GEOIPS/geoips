# OBP-Style Plugin Calls In Scripts

GeoIPS plugins can be called directly from Python scripts using the same
DataTree-based data model used by order-based workflows. In this mode, the
script owns a top-level `xarray.DataTree` and passes it from plugin to plugin
as processing progresses.

Each plugin receives the accumulated tree, extracts the inputs it understands,
writes its result back into the tree under a named step, applies the requested
retention policy, and returns the updated tree.

## Initializing A Script Tree

Scripts should initialize their top-level tree with a GeoIPS helper rather than
constructing a bare `xarray.DataTree` directly.

```python
from geoips.utils.types.script_datatree import initialize_script_tree

tree = initialize_script_tree(
    name="abi_infrared_test",
    retention_policy="metadata_only",
)
```

The initializer validates the requested retention policy and stamps standard
script-level metadata, such as:

```python
{
    "execution_mode": "script",
    "retention_policy": "metadata_only",
    "start_time": "...",
}
```

For now, scripts still pass `_obp_initiated=True` on each plugin call. In the
future, GeoIPS should infer OBP/script behavior from `execution_mode="script"`.

## Example: Full ABI Infrared Processing

```python
import glob
import os

from geoips.interfaces import (
    algorithms,
    colormappers,
    coverage_checkers,
    filename_formatters,
    interpolators,
    output_formatters,
    readers,
    sectors,
)
from geoips.utils.types.script_datatree import (
    add_data_step,
    get_current_data,
    get_output_products,
    initialize_script_tree,
)


fnames = sorted(
    glob.glob(
        os.path.join(
            os.environ["GEOIPS_TESTDATA_DIR"],
            "test_data_abi/data/goes16_20200918_1950/*",
        )
    )
)

tree = initialize_script_tree(
    name="abi_infrared_test",
    retention_policy="metadata_only",
)

reader = readers.get_plugin("abi_netcdf")
sector = sectors.get_plugin("conus")
interpolator = interpolators.get_plugin("interp_nearest")
algorithm = algorithms.get_plugin("single_channel")
colormapper = colormappers.get_plugin("Infrared")
coverage_checker = coverage_checkers.get_plugin("masked_arrays")
filename_formatter = filename_formatters.get_plugin("geoips_fname")
output_formatter = output_formatters.get_plugin("imagery_clean")

tree = reader(
    data=tree,
    filenames=fnames,
    step_id="read_data",
    _obp_initiated=True,
    varnames=["B14BT"],
)

tree = sector(
    data=tree,
    step_id="load_sector",
    _obp_initiated=True,
)

tree = interpolator(
    data=tree,
    step_id="interpolate_data",
    _obp_initiated=True,
    varlist=["B14BT"],
)

tree = algorithm(
    data=tree,
    step_id="apply_algorithm",
    _obp_initiated=True,
    output_data_range=[-90.0, 30.0],
    input_units="Kelvin",
    output_units="celsius",
    min_outbounds="crop",
    max_outbounds="crop",
    norm=False,
    inverse=False,
)

# Optional user manipulation between plugin calls.
xobj = get_current_data(tree)
xobj["data"] = xobj["data"].where(xobj["data"] > -80)

tree = add_data_step(
    tree,
    xobj,
    step_id="mask_cold_pixels",
)

tree = colormapper(
    data=tree,
    step_id="build_colormap",
    _obp_initiated=True,
    data_range=[-90.0, 30.0],
)

tree = coverage_checker(
    data=tree,
    step_id="check_coverage",
    _obp_initiated=True,
    variable_name="data",
)

tree = filename_formatter(
    data=tree,
    step_id="format_filename",
    _obp_initiated=True,
    product_name="Infrared",
    output_type="png",
)

tree = output_formatter(
    data=tree,
    step_id="write_image",
    _obp_initiated=True,
    product_name="Infrared",
    product_name_title="G16 Infrared @ 11.2 um",
)

output_products = get_output_products(tree)
print(output_products)
```

## Example: Read, Manipulate, And Plot ABI Data

This example reads two ABI brightness temperature channels, extracts the current
data from the script tree, calculates a channel difference, and plots the result
with matplotlib.

```python
import glob
import os

import matplotlib.pyplot as plt

from geoips.interfaces import readers
from geoips.utils.types.script_datatree import (
    add_data_step,
    get_current_data,
    initialize_script_tree,
)


fnames = sorted(
    glob.glob(
        os.path.join(
            os.environ["GEOIPS_TESTDATA_DIR"],
            "test_data_abi/data/goes16_20200918_1950/*",
        )
    )
)

tree = initialize_script_tree(
    name="abi_channel_difference",
    retention_policy="keep_all",
)

reader = readers.get_plugin("abi_netcdf")

tree = reader(
    data=tree,
    filenames=fnames,
    step_id="read_b14_b15",
    _obp_initiated=True,
    varnames=["B14BT", "B15BT"],
)

xobj = get_current_data(tree)

difference = xobj["B14BT"] - xobj["B15BT"]
difference.name = "B14BT_minus_B15BT"
difference.attrs["long_name"] = "ABI B14BT minus B15BT"
difference.attrs["units"] = xobj["B14BT"].attrs.get("units", "")

xobj["B14BT_minus_B15BT"] = difference

tree = add_data_step(
    tree,
    xobj,
    step_id="calculate_b14_b15_difference",
)

plt.figure(figsize=(10, 8))
xobj["B14BT_minus_B15BT"].plot(cmap="RdBu_r")
plt.title("ABI B14BT - B15BT")
plt.tight_layout()
plt.show()
```

## Step Names

Use `step_id` to name the result of each plugin call in the accumulated tree.

```python
tree = algorithm(
    data=tree,
    step_id="apply_algorithm",
    _obp_initiated=True,
    ...
)
```

`step_id` serves the same purpose as a workflow step ID. It should describe what
the script is doing, so active names such as `read_data`, `load_sector`,
`interpolate_data`, `apply_algorithm`, `format_filename`, and `write_image` are
preferred.

If `step_id` is not provided, GeoIPS uses the plugin name. If that name
conflicts with an existing node, GeoIPS raises an error asking the user to
provide a unique `step_id`.

## Input Discovery

When a plugin is called with an accumulated `DataTree`, GeoIPS inspects the
tree's child nodes and extracts the inputs that are meaningful for that plugin.

For example, an algorithm can receive a tree that contains both reader output
and filename formatter output. The reader output can provide the algorithm's
data input, while the filename formatter output is ignored if the algorithm does
not need it.

Unknown or irrelevant nodes are ignored.

## Data Conflicts

If multiple upstream nodes can provide the primary data input, GeoIPS uses the
most recently produced data node and raises a warning.

"Most recently produced" is determined from the insertion order of the top-level
child nodes in the script tree.

For example, if a tree contains both reader output and interpolator output, an
algorithm will use the interpolator output because it was produced later.

The warning identifies both the accepted node and the ignored nodes.

## Non-Data Conflicts

If multiple upstream nodes provide the same non-data input, GeoIPS raises an
error.

For example, if a tree contains two filename formatter outputs and an output
formatter needs filenames, GeoIPS will not guess which one to use. The script
must ensure that only the intended filename formatter result is present in the
tree.

## Explicit Keyword Arguments

Data must be provided through the `data` tree, not through legacy data keywords
such as `xarray_obj`.

GeoIPS should reject explicit data-related keywords that are part of the OBP
conduit bridge. This prevents scripts from depending on legacy argument names
that are expected to disappear.

Other plugin arguments may still be supplied explicitly. For example, an output
formatter may receive `product_name`, `product_name_title`, or other
configuration arguments directly.

## Retention Policies

Retention policies control how much previously produced data remains in the
accumulated script tree after each plugin call.

Scripts must explicitly choose a retention policy when initializing the tree:

```python
tree = initialize_script_tree(
    name="abi_infrared_test",
    retention_policy="metadata_only",
)
```

A plugin call can override that policy for a single step:

```python
tree = interpolator(
    data=tree,
    step_id="interpolate_data",
    retention_policy="keep_all",
    _obp_initiated=True,
    varlist=["B14BT"],
)
```

Supported policies:

```python
"keep_all"
```

Keep every plugin result intact. This is useful for debugging, exploratory
scripts, notebooks, and tests where the user wants to inspect intermediate data.

Example: keep reader and interpolator data while investigating whether
interpolation changed geolocation or variable values.

```python
"metadata_only"
```

Keep the current plugin result intact, but reduce older results to attrs only.
This is useful for normal processing where downstream plugins need context but
not full copies of every previous dataset.

Example: after interpolation, keep the interpolated data but reduce the original
reader output to metadata so the script preserves provenance without carrying a
second large data array.

```python
"current_only"
```

Keep only the current plugin result and discard older step nodes. This is useful
for memory-sensitive processing where the script only needs the latest data
product.

Example: after applying an algorithm to a very large dataset, discard reader and
interpolator outputs entirely to reduce memory before writing output.

Different steps may use different policies. For example, a user might keep all
data during early processing, then switch to metadata-only once they trust the
intermediate result:

```python
tree = initialize_script_tree(
    name="abi_infrared_test",
    retention_policy="keep_all",
)

tree = reader(
    data=tree,
    filenames=fnames,
    step_id="read_data",
    _obp_initiated=True,
    varnames=["B14BT"],
)

tree = interpolator(
    data=tree,
    step_id="interpolate_data",
    _obp_initiated=True,
    varlist=["B14BT"],
)

tree = algorithm(
    data=tree,
    step_id="apply_algorithm",
    retention_policy="metadata_only",
    _obp_initiated=True,
    output_data_range=[-90.0, 30.0],
    input_units="Kelvin",
    output_units="celsius",
)
```

## Step Tracking

GeoIPS records standard step-level metadata as each plugin result is attached to
the script tree.

Each step node may include metadata such as:

```python
{
    "step_id": "apply_algorithm",
    "plugin_kind": "algorithm",
    "plugin_name": "single_channel",
    "start_time": "...",
    "end_time": "...",
    "retention_policy": "metadata_only",
}
```

This allows scripts and helper utilities to inspect what ran, when it ran, and
how much of each result was retained.

## User-Modified Data

Scripts may extract the current data, modify it directly, and reinsert it as a
new step.

```python
from geoips.utils.types.script_datatree import add_data_step, get_current_data

xobj = get_current_data(tree)
xobj["data"] = xobj["data"].where(xobj["data"] > -80)

tree = add_data_step(
    tree,
    xobj,
    step_id="mask_cold_pixels",
)
```

The inserted data step is treated like any other data-producing step. Downstream
plugins will see it as the most recent data input.

## Current OBP Flag

For now, scripts must pass `_obp_initiated=True` when calling plugins in this
style.

```python
tree = plugin(
    data=tree,
    step_id="some_action",
    _obp_initiated=True,
    ...
)
```

A cleaner public scripting API should eventually infer this behavior from the
script tree metadata.

## Future Features

Future improvements may include:

- Infer OBP/script behavior from `execution_mode="script"` so users no longer
  need to pass `_obp_initiated=True` on every plugin call.
- Memory tracking for each plugin step.
- Additional helpers for extracting common values from script trees.
- Convenience helpers for adding or resolving sectors in scripts.
- Helpers for inspecting available step outputs and retained metadata.
- Functions for graphing useful runtime information such as elapsed time, CPU
  usage, and memory usage.
- A cleaner public scripting API for common scripted processing patterns.
- Better visualization of the script execution tree and retained intermediate
  results.
