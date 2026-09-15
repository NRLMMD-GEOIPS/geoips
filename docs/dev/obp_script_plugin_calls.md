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
from geoips.scripting import RetentionPolicy, initialize_script_tree

tree = initialize_script_tree(
    name="abi_infrared_test",
    retention_policy=RetentionPolicy.keep_all,
)
```

The initializer validates the requested retention policy and stamps standard
script-level metadata, such as:

```python
{
    "execution_mode": "script",
    "retention_policy": "metadata_only",
    "start_time": "...",
    "end_time": None,
}
```

Root `start_time` and `end_time` are managed by GeoIPS. `start_time` is set
automatically when the script tree is initialized, and `end_time` starts as
`None`. Scripts should not supply either value to `initialize_script_tree()`.

Initialized script trees infer OBP/script behavior from `execution_mode="script"`, so normal script calls do not need to pass `_obp_initiated=True`.

The public scripting API is exposed from `geoips.scripting`. Lower-level helpers
may live elsewhere internally, but user scripts should prefer imports from
`geoips.scripting`.

Supported retention policies are available as `RetentionPolicy` values:

```python
from geoips.scripting import RETENTION_POLICIES, RetentionPolicy, initialize_script_tree

print(RETENTION_POLICIES)

tree = initialize_script_tree(
    name="abi_infrared_test",
    retention_policy=RetentionPolicy.keep_all,
)
```

String values such as `"metadata_only"` are also accepted for scripts that load
configuration dynamically, but `RetentionPolicy.metadata_only` is preferred in
ordinary Python code.

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
from geoips.scripting import (
    RetentionPolicy,
    add_data_step,
    attach_plugin_result,
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
    retention_policy=RetentionPolicy.metadata_only,
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
    variables=["B14BT"],
)

# YAML-based plugins do not yet route through class-based script invocation,
# so attach their result explicitly.
sector_result = sector()
tree = attach_plugin_result(
    tree,
    sector_result,
    step_id="load_sector",
    plugin_kind="sector",
    plugin_name="conus",
)

tree = interpolator(
    data=tree,
    step_id="interpolate_data",
    varlist=["B14BT"],
)

tree = algorithm(
    data=tree,
    step_id="apply_algorithm",
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
    data_range=[-90.0, 30.0],
)

tree = coverage_checker(
    data=tree,
    step_id="check_coverage",
    variable_name="data",
)

tree = filename_formatter(
    data=tree,
    step_id="format_filename",
    product_name="Infrared",
    output_type="png",
)

tree = output_formatter(
    data=tree,
    step_id="write_image",
    product_name="Infrared",
    product_name_title="G16 Infrared @ 11.2 um",
)

output_products = get_output_products(tree, step_id="write_image")
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
from geoips.scripting import (
    RetentionPolicy,
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
    retention_policy=RetentionPolicy.keep_all,
)

reader = readers.get_plugin("abi_netcdf")

tree = reader(
    data=tree,
    filenames=fnames,
    step_id="read_b14_b15",
    variables=["B14BT", "B15BT"],
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

## Bringing Your Own Data

Scripts can also start from data that was not read by a GeoIPS reader. For now,
that data must be provided as an xarray object, such as an `xarray.Dataset`,
`xarray.DataArray`, or `xarray.DataTree`, and inserted into the script tree with
`add_data_step()`. Downstream plugins still expect the dataset to contain the
variables, coordinates, and metadata attributes required by those plugins.

```python
import xarray as xr

from geoips.scripting import (
    RetentionPolicy,
    add_data_step,
    initialize_script_tree,
)

tree = initialize_script_tree(
    name="external_data_example",
    retention_policy=RetentionPolicy.metadata_only,
)

xobj = xr.Dataset(
    data_vars={
        "my_variable": (("y", "x"), data_values),
    },
    coords={
        "latitude": (("y", "x"), latitude_values),
        "longitude": (("y", "x"), longitude_values),
    },
    attrs={
        "source_name": "my_source",
        "platform_name": "my_platform",
        "data_provider": "my_provider",
        "start_datetime": start_datetime,
        "end_datetime": end_datetime,
    },
)

tree = add_data_step(
    tree,
    xobj,
    step_id="load_external_data",
)
```

This is intentionally a low-level contract. Scripters are responsible for making
the xarray object look enough like a GeoIPS plugin result for the next plugin
they call.

## Step Names

Use `step_id` to name the result of each plugin call in the accumulated tree.

```python
tree = algorithm(
    data=tree,
    step_id="apply_algorithm",
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

If multiple upstream nodes can provide the same conduit-derived input, the most
recent matching node wins. "Most recent" is determined from the insertion order
of the top-level child nodes in the script tree.

For example, if a tree contains both reader output and interpolator output, an
algorithm will use the interpolator output because it was produced later.

GeoIPS does not yet warn when older candidate nodes are ignored. Better conflict
diagnostics are planned for a later update.

## Non-Data Conflicts

Non-data conduit inputs currently follow the same latest-value behavior as data
inputs. For example, if a tree contains two filename formatter outputs and an
output formatter needs filenames, GeoIPS uses the later filename formatter
result.

Scripts should avoid keeping ambiguous non-data nodes in the tree until stricter
conflict handling is implemented.

## Explicit Keyword Arguments

Explicit keyword arguments provided by the script take precedence over values
found in the accumulated tree. This is useful for ordinary plugin configuration
arguments such as `product_name`, `product_name_title`, `varlist`, or
`data_range`.

Scripts should still prefer passing data through the accumulated `data` tree
rather than through legacy data keywords such as `xarray_obj`. A future update
may reject explicit data-related conduit keywords in script mode to prevent new
scripts from depending on legacy argument names.

## Retention Policies

Retention policies control how much previously produced data remains in the
accumulated script tree after each plugin call.

Retention is applied automatically whenever a plugin result is attached to the
script tree. In normal scripts, each plugin call returns the tree after the
current step has been inserted and the effective retention policy has been
applied.

Scripts must explicitly choose a retention policy when initializing the tree:

```python
from geoips.scripting import RetentionPolicy, initialize_script_tree

tree = initialize_script_tree(
    name="abi_infrared_test",
    retention_policy=RetentionPolicy.metadata_only,
)
```

A plugin call can override that policy for a single step:

```python
tree = interpolator(
    data=tree,
    step_id="interpolate_data",
    retention_policy=RetentionPolicy.keep_all,
    varlist=["B14BT"],
)
```

Supported policies:

`RetentionPolicy.keep_all`

Keep every plugin result intact. This is useful for debugging, exploratory
scripts, notebooks, and tests where the user wants to inspect intermediate data.

Example: keep reader and interpolator data while investigating whether
interpolation changed geolocation or variable values.

`RetentionPolicy.metadata_only`

Keep the current plugin result intact and keep the latest xarray-data provider
(reader, interpolator, algorithm, or manual data step) intact. Older results are
reduced to attrs only. This is useful for normal processing where downstream
plugins need metadata from earlier steps, but only need one full science-data
object available for later plugin calls.

Example: after interpolation, keep the interpolated data but reduce the original
reader output to metadata so the script preserves provenance without carrying a
second large data array. Later metadata-only steps such as sectors,
colormappers, coverage checkers, and filename formatters do not cause the latest
algorithm/interpolator data to be reduced before an output formatter can use it.

`RetentionPolicy.current_only`

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
    retention_policy=RetentionPolicy.keep_all,
)

tree = reader(
    data=tree,
    filenames=fnames,
    step_id="read_data",
    variables=["B14BT"],
)

tree = interpolator(
    data=tree,
    step_id="interpolate_data",
    varlist=["B14BT"],
)

tree = algorithm(
    data=tree,
    step_id="apply_algorithm",
    retention_policy=RetentionPolicy.metadata_only,
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

`plugin_kind` must be a registered GeoIPS plugin kind or `"manual"` for
user-created script data. Product and workflow steps are intentionally excluded
from scripted step attachment for now; workflow support may be added later.
`plugin_name` is required for registered plugin kinds. For `"manual"` data,
`plugin_name` may be omitted and defaults to `"manual"`.

Registered plugin results receive automatic `start_time` and `end_time` values
when explicit times are not provided. Manual steps do not receive automatic
timestamps; their `start_time` and `end_time` values remain `None` unless the
script supplies them explicitly. Explicit step timestamps must be
`datetime.datetime` instances; GeoIPS stores them as ISO strings in step attrs.

## Script Step Data Inputs

Script step data must be representable as a `DataTree` node. Plugin results may
be supplied as `xarray.DataTree`, `DataTreeDitto`, `xarray.Dataset`,
`xarray.DataArray`, or another type supported by the `DataTreeDitto` converter
registry.

Scalars and other simple values should be wrapped in a supported structure
before being attached:

```python
tree = attach_plugin_result(
    tree,
    {"value": 0},
    step_id="manual_value",
    plugin_kind="manual",
)
```

Passing an unsupported value directly raises a script-specific `TypeError` that
identifies the step, the unsupported type, and the original converter error when
available. Supported container types may still reject unsupported contents; for
example, dict conversion accepts scalars and numpy arrays, but not arbitrary
Python lists.

## User-Modified Data

Scripts may extract a mutable copy of the current data, modify it, and reinsert
it as a new step.

```python
from geoips.scripting import add_data_step, get_current_data

xobj = get_current_data(tree)
xobj["data"] = xobj["data"].where(xobj["data"] > -80)

tree = add_data_step(
    tree,
    xobj,
    step_id="mask_cold_pixels",
)
```

`get_current_data()` returns a mutable dataset copy from the most recent
data-containing step. Edits to that dataset do not modify the existing tree step
in place; use `add_data_step()` to reinsert the modified data as a new manual
step.

The inserted data step is treated like any other data-containing step. Downstream
plugins will see it as the most recent data input.

## Script Mode Detection

Plugins infer script-mode OBP behavior from an initialized script tree. Pass the
accumulated tree as `data`; `_obp_initiated=True` is not required for normal
script calls.

```python
tree = plugin(
    data=tree,
    step_id="some_action",
    ...
)
```

## Future Features

Future improvements may include:

- Memory tracking for each plugin step.
- Additional helpers for extracting common values from script trees.
- Convenience helpers for adding or resolving sectors in scripts.
- Helpers for inspecting available step outputs and retained metadata.
- Functions for graphing useful runtime information such as elapsed time, CPU
  usage, and memory usage.
- A cleaner public scripting API for common scripted processing patterns.
- A formal external-data contract, plus helper functions for validating or
  standardizing user-provided xarray objects before they are passed to GeoIPS
  plugins.
- Better conflict diagnostics that warn when older data candidates are ignored
  and raise useful errors when ambiguous non-data conduit inputs are present.
- Stricter handling for explicit data-related conduit keywords in script mode.
- Better visualization of the script execution tree and retained intermediate
  results.
