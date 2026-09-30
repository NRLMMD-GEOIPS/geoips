<!--
# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.
-->

(retention-policies)=

# Retention policies

Retention policies control how much previously produced data remains in the accumulated
{ref}`script tree <scripting-guide>` after each plugin call. Retention is applied
automatically whenever a plugin result is attached.

Scripts must choose a policy when initializing the tree:

```python
from geoips.scripting import RetentionPolicy, initialize_script_tree

tree = initialize_script_tree(
    name="abi_infrared_test",
    retention_policy=RetentionPolicy.metadata_only,
)
```

A single plugin call can override the policy for that step:

```python
tree = interpolator(
    data=tree,
    step_id="interpolate_data",
    retention_policy=RetentionPolicy.keep_all,
    varlist=["B14BT"],
)
```

String values such as `"metadata_only"` are accepted for config-driven scripts, but the
`RetentionPolicy` enum is preferred in ordinary Python.

## The policies

`RetentionPolicy.keep_all`
: Keep every plugin result intact. Best for debugging, exploratory scripts, notebooks, and
  tests where you want to inspect intermediate data.

`RetentionPolicy.metadata_only`
: Keep the current result and the latest xarray-data provider (reader, interpolator,
  algorithm, or manual data step) intact; reduce older results to attrs only. Best for
  normal processing — downstream plugins keep the metadata they need while only one full
  science-data object is carried forward. Metadata-only steps (sectors, colormappers,
  coverage checkers, filename formatters) do not reduce the latest science data before an
  output formatter can use it.

`RetentionPolicy.current_only`
: Keep only the current result and discard older step nodes. Best for memory-sensitive
  processing of very large datasets.

## Mixing policies

Different steps may use different policies — e.g. keep everything early while you trust the
data, then switch to `metadata_only` once the intermediate result is validated:

```python
tree = initialize_script_tree(name="abi", retention_policy=RetentionPolicy.keep_all)
tree = reader(data=tree, filenames=fnames, step_id="read_data", variables=["B14BT"])
tree = interpolator(data=tree, step_id="interpolate_data", varlist=["B14BT"])
tree = algorithm(
    data=tree,
    step_id="apply_algorithm",
    retention_policy=RetentionPolicy.metadata_only,
    output_data_range=[-90.0, 30.0],
    input_units="Kelvin",
    output_units="celsius",
)
```
