<!--
# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.
-->

(datatree)=

# The DataTree data model

GeoIPS 2.0 uses a single container for the data flowing through processing: an
[`xarray.DataTree`](https://docs.xarray.dev/en/stable/generated/xarray.DataTree.html). Both
{ref}`Order-Based Processing <order-based-processing>` workflows and
{ref}`scripting <scripting-guide>` are built on this model.

## One container, steps as nodes

Every step takes a `DataTree` and returns a `DataTree`. The workflow (or accumulated
script tree) is itself a `DataTree` whose children are the per-step results. This replaces
the 1.x situation where each plugin "family" consumed a different container type (numpy
arrays, xarray Datasets, datatrees, custom dicts) and had to branch on the type.

Because each step's output is a node in the tree, you can:

- keep every intermediate result (for debugging), or
- reduce older results to metadata only, or
- discard them entirely once consumed —

all controlled by {ref}`retention policies <retention-policies>`.

## Input discovery

When a step receives the accumulated tree, GeoIPS inspects the tree's child nodes and
extracts the inputs meaningful to that step; unrelated nodes are ignored. If more than one
node can supply the same input, the most recent matching node wins (by insertion order).
Explicit keyword arguments always take precedence over values found in the tree.

## Provenance in `attrs`

Each step node records standard metadata as native xarray attributes (`attrs`) — the step
id, plugin kind and name, start/end times, retention policy, and content tokens. This means
an output `DataTree` carries enough information to describe how it was produced, even after
intermediate data has been garbage-collected.

## Non-xarray results: `DataTreeDitto`

Some plugin results are not naturally xarray objects (a scalar, a colormap dict, a numpy
array). These are wrapped in a {ref}`DataTreeDitto <datatree-ditto>` — a `DataTree`
subclass that stores non-xarray values while preserving enough metadata to recover the
original object. Using non-xarray objects incurs more overhead, so `DataTreeDitto` is
intended to be phased out over time in favor of native xarray results.

## Going deeper

The full DataTree runtime — workflow execution, topological sort, `split`/`join`
fan-out, tokenization, and provenance tables — is specified in the developer guide's
{ref}`DataTree specification <datatree-spec>`.

## See also

- {ref}`order-based-processing` — the workflow form of this model.
- {ref}`scripting-guide` — driving the same model from Python.
- {ref}`retention-policies` — controlling how much of the tree is kept.
- {ref}`datatree-ditto` — the non-xarray wrapper type.
