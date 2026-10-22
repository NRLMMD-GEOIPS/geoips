# TEMPORARY — Interface rename and Plugin/PluginConfig mapping worksheet

Delete once the decisions land in `class_based_plugins.md`.

## Terminology being adopted

- **Plugin** — what is currently called a class-based plugin.
- **PluginConfig** — what is currently called a YAML-based plugin.

Every PluginConfig interface maps to exactly one Plugin interface. A Plugin interface does
not require a PluginConfig.

## Decisions made

- The writer config is **`WriterConfigs`**, following the `Writers` Plugin name.
- `FeatureAnnotators` and `GridlineAnnotators` are **retained as interfaces**, renamed
  `WriterFeatureConfigs` and `WriterGridlineConfigs`. `WriterConfigs` references them rather
  than absorbing them, so one annotator definition can be shared across writers.

## Current interfaces

`Kind` is the singular form used in a workflow step today.

| # | Current interface | Type | Kind | → Plugin | → PluginConfig | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `algorithms` | Plugin | `algorithm` | | `AlgorithmConfigs` (row 19) | |
| 2 | `colormappers` | Plugin | `colormapper` | **`Colormaps`** | `ColormapConfigs` (row 20) | |
| 3 | `coverage_checkers` | Plugin | `coverage_checker` | | | |
| 4 | `databases` | Plugin | `database` | **`Reporters`** | | |
| 5 | `filename_formatters` | Plugin | `filename_formatter` | | | Possible future `FilenameFormatterConfigs` |
| 6 | `interpolators` | Plugin | `interpolator` | | | |
| 7 | `output_checkers` | Plugin | `output_checker` | | | |
| 8 | `output_formatters` | Plugin | `output_formatter` | **`Writers`** | `WriterConfigs` (row 21) | |
| 9 | `procflows` | Plugin | `procflow` | | | Being retired in favour of OBP — may need no new name |
| 10 | `readers` | Plugin | `reader` | | | Possible future `ReaderConfigs` |
| 11 | `title_formatters` | Plugin | `title_formatter` | | | Possible future `TitleFormatterConfigs` |
| 12 | `validators` | Plugin | `validator` | | | |
| 13 | `feature_annotators` | PluginConfig | `feature_annotator` | `Writers` | **`WriterFeatureConfigs`** | Retained as its own interface, referenced by `WriterConfigs` |
| 14 | `gridline_annotators` | PluginConfig | `gridline_annotator` | `Writers` | **`WriterGridlineConfigs`** | Retained as its own interface, referenced by `WriterConfigs` |
| 15 | `product_defaults` | PluginConfig | `product_default` | `Workflows` | *(retained as-is)* | Backwards compatibility only. Converts to a `WorkflowConfig` at runtime. Deprecated |
| 16 | `products` | PluginConfig | `product` | `Workflows` | *(retained as-is)* | Backwards compatibility only. Converts to a `WorkflowConfig` at runtime. Deprecated |
| 17 | `sectors` | PluginConfig | `sector` | **new `Sectors` Plugin** | **`SectorConfigs`** | Static sectors. The dynamic sector interfaces are deferred — see the tabled design topic |
| 18 | `workflows` | PluginConfig | `workflow` | **new `Workflows` Plugin** | **`WorkflowConfigs`** | The Plugin becomes an explicit registered interface rather than the implicit one in `interfaces/class_based/workflow.py` |
| 19 | *(none)* | PluginConfig | *(new)* | `Algorithms` | **`AlgorithmConfigs`** | New interface. Declarative algorithm definitions, along the lines of the RGB configs in [#1484](https://github.com/NRLMMD-GEOIPS/geoips/pull/1484) |
| 20 | *(none)* | PluginConfig | *(new)* | `Colormaps` | **`ColormapConfigs`** | New interface |
| 21 | *(none)* | PluginConfig | *(new)* | `Writers` | **`WriterConfigs`** | New interface. References `WriterFeatureConfigs` and `WriterGridlineConfigs` |

## Open questions raised by the table

**Dynamic sectors are deferred.** `sector_adjusters`, `sector_metadata_generators`, and
`sector_spec_generators` have been removed from this table. Consolidating them into
`DynamicSectors` and `DynamicSectorConfigs` is recorded as a tabled design topic in
`class_based_plugins.md`. They keep their current names until that is decided, so whether a
`Sectors` Plugin relates to them is deferred with it.

**Products and ProductDefaults map to `Workflows` through conversion, not directly.** Both
are backwards-compatibility surfaces. A Product is converted into a `WorkflowConfig` at
runtime and executed by the `Workflows` Plugin, so the mapping rule is satisfied through that
conversion rather than by giving either its own Plugin. Both are deprecated, and their names
do not change — renaming a surface that exists only for compatibility would defeat its
purpose.

## Deprecation requirement

Current kinds continue to be accepted and raise a deprecation warning when encountered.
Every rename in the table above therefore produces a deprecation-register entry with an
old kind, a new kind, a warning, and a removal schedule.
