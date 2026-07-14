<!--
# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.
-->

(obp-best-practices)=

# OBP-native best practices

This page collects recommendations for building GeoIPS 2.0 processing the
Order-Based way. If you are coming from GeoIPS 1.x, also read the
{ref}`migration guide <migrating-1x-to-2x>`.

## Prefer workflows over legacy procflows

Use {ref}`OBP workflows <order-based-processing>` for new processing. The legacy
`single_source`, `config_based`, and `data_fusion` procflows still run, but they are
deprecated and will not receive new features. **OBP can produce everything the legacy
procflows can**, with explicit step ordering and up-front validation.

## Compose with embedded workflows

If you find yourself repeating the same sequence of steps across products, factor it into
its own workflow and reference it as a `kind: workflow` step. Reach for the three
composition mechanisms in this order:

1. **Product step** (`kind: product`) — when a registered product already describes the
   science you want. Its ordered family expands into the right steps automatically.
2. **Workflow step** (`kind: workflow`) — when you have a reusable multi-step sequence
   that is not a single product.
3. **Inline steps** — only when the sequence is genuinely one-off.

Composition keeps workflows short and makes changes propagate to every consumer.

## Be explicit with `depends_on` when order matters

GeoIPS infers dependencies from the most recent data-producing step, which is convenient
but implicit. When a step must consume a *specific* earlier output — especially inside
embedded workflows — set `depends_on` explicitly, using dotted paths for embedded steps
(`depends_on: [abi_Infrared.algorithm]`). This makes the workflow self-documenting and
avoids surprises when steps are reordered.

## Choose the right retention policy

When {ref}`scripting <scripting-guide>` or tuning memory-sensitive workflows, pick the
{ref}`retention policy <retention-policies>` that matches your needs:

- `keep_all` for debugging, notebooks, and tests where you inspect intermediate data.
- `metadata_only` for normal processing — keeps the latest science data plus provenance.
- `current_only` for memory-constrained processing of very large datasets.

## Script when exploring, write a workflow when operationalizing

The {ref}`scripting API <scripting-guide>` is ideal for interactive exploration, one-off
analysis, and notebooks: you call plugins directly and inspect results between steps. Once
a sequence is stable and you want it registered, reproducible, and testable, capture it as
a workflow YAML with a `test` section.

## Test every workflow

Give each workflow a `test` section with `fnames`, expected `outputs`, and a
`compare_path`. Run it with `geoips test workflow <name>` so regressions are caught
automatically. Doc examples in this documentation are themselves run in CI for exactly
this reason.
