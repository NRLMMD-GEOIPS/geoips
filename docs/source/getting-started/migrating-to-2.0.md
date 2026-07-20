<!--
# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.
-->

(migrating-1x-to-2x)=

# Migrating from GeoIPS 1.x to 2.0

GeoIPS 2.0 introduces Order-Based Processing (OBP), class-based plugins, a DataTree data
model, and a layered configuration system. GeoIPS 1.x patterns still work where noted, but
are deprecated. This guide summarizes what changed and links to the detailed guides.

## What changed at a glance

| Area | GeoIPS 1.x (≤ 1.19.0) | GeoIPS 2.0 |
|------|------------------------|------------|
| Processing | `single_source` / `config_based` / `data_fusion` procflows | {ref}`Order-Based Processing <order-based-processing>` workflows (legacy procflows still run, deprecated) |
| Running | `run_procflow` / `data_fusion_procflow` scripts | `geoips run order_based <workflow> <files>` (`geoips legacy run` wraps the old scripts) |
| Python plugins | Module with a top-level `call()` function | {ref}`Class-based plugins <writing-class-based-plugins>` in `geoips/plugins/classes/` |
| Scripting | Ad-hoc procflow internals | {ref}`geoips.scripting <scripting-guide>` DataTree API |
| Configuration | `geoips.filenames.base_paths.PATHS` | {ref}`Layered geoips.config <geoips-config>` (`base_paths` is now a deprecation shim) |
| Validation | Schema/JSON | Pydantic models (`geoips.pydantic_models.v1`, plus `v2alpha1`) |

## Processing: procflows → OBP workflows

Replace legacy procflow runs with OBP. **OBP can produce everything the legacy procflows
can.** A `run_procflow ... --procflow single_source` call becomes
`geoips run order_based <workflow> <files>`, where the workflow captures the reader,
algorithm, colormapper, and output steps explicitly. See
{ref}`order-based-processing` and {ref}`running-obp`.

The legacy commands remain available:

```bash
# Deprecated, still supported:
geoips run single_source <files> --reader_name abi_netcdf --product_name Infrared ...
# or the backwards-compat wrapper for old scripts:
geoips legacy run ...
```

## Python plugins: module-based → class-based

Readers, algorithms, interpolators, colormappers, output/filename/title formatters, and
coverage checkers are now Python classes rather than modules with a `call()` function, and
they live under `geoips/plugins/classes/` instead of `geoips/plugins/modules/`. See the
{ref}`module-to-class conversion guide <converting-module-to-class>` for step-by-step
instructions, including the assisted-conversion tooling in `v2_migration_tools/`.

## Configuration: base_paths → geoips.config

The imperative `PATHS` dictionary in `geoips.filenames.base_paths` is replaced by the
layered {ref}`geoips.config <geoips-config>` system (environment variables > project
`.geoips.yaml` > code defaults). `base_paths` still works as a shim that emits deprecation
warnings, so existing imports and dict-style access continue to function.

## Imports and internal APIs

- The module-level `call()` in `geoips.plugins.modules.procflows.order_based` was removed.
  The order-based procflow is now the class-based `OrderBased(BaseProcflowPlugin)`; resolve
  it through the registry:

  ```python
  from geoips import interfaces
  interfaces.procflows.get_plugin("order_based")(workflow_spec, filenames=fnames)
  ```

- Pydantic models live under `geoips.pydantic_models.v1` (with a `v2alpha1` set for newer
  work). Interface argument models such as `AlgorithmArgumentsModel` document the arguments
  each plugin kind accepts.

## Recommended migration order

1. Get your data producing outputs with a legacy procflow (still supported) to establish a
   baseline.
2. Recreate that processing as an {ref}`OBP workflow <order-based-processing>` with a
   `test` section and a `compare_path`.
3. Convert any custom plugins to {ref}`class-based <converting-module-to-class>`.
4. Move hard-coded paths onto {ref}`geoips.config <geoips-config>`.
