<!--
# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.
-->

(scripting-guide)=

# Scripting with GeoIPS plugins

GeoIPS plugins can be called directly from Python using the same DataTree-based data model
that {ref}`Order-Based Processing <order-based-processing>` uses internally. This is the
recommended way to explore data interactively, prototype new processing, and drive GeoIPS
from notebooks.

In this mode your script owns a top-level `xarray.DataTree` and passes it from plugin to
plugin. Each plugin reads the inputs it understands from the tree, writes its result back
under a named step, applies the requested {ref}`retention policy <retention-policies>`,
and returns the updated tree.

:::{note}
The public scripting API lives in `geoips.scripting`. Prefer importing from there; lower
level helpers may move.
:::

## Initialize a script tree

Start every script by initializing a tree with a GeoIPS helper (not a bare
`xarray.DataTree`):

```python
from geoips.scripting import RetentionPolicy, initialize_script_tree

tree = initialize_script_tree(
    name="abi_infrared_test",
    retention_policy=RetentionPolicy.metadata_only,
)
```

The initializer validates the retention policy and stamps script-level metadata
(`execution_mode="script"`, `start_time`, etc.). GeoIPS manages `start_time`/`end_time` —
do not pass them yourself. Because the tree records `execution_mode="script"`, normal
script calls do **not** need `_obp_initiated=True`.

## Call plugins

Resolve plugins from their interfaces and call them, passing the accumulated tree as
`data` and naming each result with `step_id`:

```python
from geoips.interfaces import readers, interpolators, algorithms

reader = readers.get_plugin("abi_netcdf")
tree = reader(data=tree, filenames=fnames, step_id="read_data", variables=["B14BT"])

interpolator = interpolators.get_plugin("interp_nearest")
tree = interpolator(data=tree, step_id="interpolate_data", varlist=["B14BT"])

algorithm = algorithms.get_plugin("single_channel")
tree = algorithm(
    data=tree,
    step_id="apply_algorithm",
    output_data_range=[-90.0, 30.0],
    input_units="Kelvin",
    output_units="celsius",
)
```

Some YAML-based plugins (e.g. `sectors`) do not yet route through class-based script
invocation. Attach their results explicitly:

```python
from geoips.interfaces import sectors
from geoips.scripting import attach_plugin_result

sector = sectors.get_plugin("conus")
tree = attach_plugin_result(
    tree, sector(), step_id="load_sector", plugin_kind="sector", plugin_name="conus"
)
```

## Inspect and modify data between steps

`get_current_data()` returns a mutable copy of the most recent data-containing step. Edit
it and reinsert it as a new manual step with `add_data_step()`:

```python
from geoips.scripting import add_data_step, get_current_data

xobj = get_current_data(tree)
xobj["data"] = xobj["data"].where(xobj["data"] > -80)
tree = add_data_step(tree, xobj, step_id="mask_cold_pixels")
```

## Get outputs

After an output formatter step, collect the written products:

```python
from geoips.scripting import get_output_products

output_products = get_output_products(tree, step_id="write_image")
print(output_products)
```

## Step names

`step_id` names each result in the tree — it is the scripting equivalent of a workflow
step id. Use active, descriptive names (`read_data`, `interpolate_data`,
`apply_algorithm`, `write_image`). If omitted, GeoIPS uses the plugin name and errors if
that would collide with an existing node.

## Input discovery and conflicts

When you call a plugin with an accumulated tree, GeoIPS inspects the tree's child nodes and
extracts the inputs meaningful to that plugin; unrelated nodes are ignored. If multiple
nodes can supply the same input, the **most recent** matching node wins (by insertion
order). Explicit keyword arguments always take precedence over values found in the tree.

## Bring your own data

Scripts can start from data a GeoIPS reader did not produce. Provide it as an xarray object
and insert it with `add_data_step()`; downstream plugins still expect the standard GeoIPS
variables, coordinates, and metadata attributes.

```python
import xarray as xr
from geoips.scripting import add_data_step, initialize_script_tree, RetentionPolicy

tree = initialize_script_tree(name="byo", retention_policy=RetentionPolicy.metadata_only)
xobj = xr.Dataset(
    data_vars={"my_variable": (("y", "x"), data_values)},
    coords={"latitude": (("y", "x"), lat), "longitude": (("y", "x"), lon)},
    attrs={"source_name": "my_source", "platform_name": "my_platform",
           "start_datetime": start, "end_datetime": end},
)
tree = add_data_step(tree, xobj, step_id="load_external_data")
```

## See also

- {ref}`datatree` — the DataTree data model these calls accumulate into.
- {ref}`retention-policies` — control how much intermediate data is kept.
- {ref}`order-based-processing` — the workflow form of the same processing model.
```{toctree}
:hidden:

retention-policies
```
