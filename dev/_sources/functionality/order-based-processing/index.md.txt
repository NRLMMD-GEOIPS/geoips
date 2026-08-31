<!--
# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.
-->

(order-based-processing)=

# Order-Based Processing (OBP)

**Order-Based Processing (OBP) is the primary way to produce outputs in GeoIPS 2.0.**
An OBP *workflow* is an explicit, ordered list of plugin *steps* — read data, transform
it, compute a product, visualize it, and write output — defined in YAML and validated
with [Pydantic](https://docs.pydantic.dev/latest/).

:::{admonition} OBP replaces the legacy procflows
:class: important

In GeoIPS 1.x, processing ran through fixed *procflows* (`single_source`,
`config_based`, `data_fusion`). Those still run in 2.0a, but they are **deprecated**.
**OBP is a superset: anything a legacy procflow could produce, an OBP workflow can
produce** — and OBP additionally lets you control step order, repeat steps, and validate
inputs up front. New work should use OBP. See the
{ref}`migration guide <migrating-1x-to-2x>` to move existing processing over.
:::

## The ETCVO model

OBP implements an **Extract → Transform → Compute → Visualize → Output** (ETCVO)
workflow. Each stage is one or more plugin steps:

| Stage | Typical plugin kinds | What it does |
|-------|----------------------|--------------|
| **Extract** | `reader` | Read source data into the GeoIPS {ref}`xarray standard <xarray_standards>`. |
| **Transform** | `interpolator`, `sector` | Resample / register / subset the data to a grid. |
| **Compute** | `algorithm`, `coverage_checker` | Turn raw channels into a science product. |
| **Visualize** | `colormapper` | Map product values to colors. |
| **Output** | `filename_formatter`, `output_formatter` | Name and write the final file(s). |

You are not locked into this exact sequence — that is the point of OBP. You specify the
order that a given product needs.

## Why OBP

- **You define the step order.** The workflow specifies the exact sequence of operations.
- **Steps can repeat.** Run multiple algorithms, multiple output formatters, etc.
- **Errors are caught early.** Pydantic validates every step's arguments against the
  plugin's call signature before processing starts.
- **It composes.** Workflows can embed other workflows, products, or product defaults for
  reuse (see {ref}`workflows`).

## A workflow at a glance

A workflow is a `workflows` YAML plugin. Its `spec.steps` maps a unique *step id* to a
plugin step. Each step declares its `kind` (the plugin interface), `name` (the specific
plugin), `arguments`, and optionally `depends_on` (which earlier steps feed it):

```yaml
apiVersion: geoips/v1
interface: workflows
family: order_based
name: abi_static_infrared_imagery_clean
docstring: 11.2 µm ABI Infrared, clean imagery.
package: geoips
spec:
  globals:
    product_name: Infrared
    reader_defined_area_def: False
  steps:
    sector:
      kind: sector
      name: test_goes16_eqc_3km_day_20200918T1950Z
    reader:
      kind: reader
      name: abi_netcdf
      arguments:
        resampled_read: True
      depends_on: [sector]
    abi_Infrared:
      kind: product
      name: [abi, Infrared]
      depends_on: [reader, sector]
    coverage_checker:
      kind: coverage_checker
      name: masked_arrays
      depends_on: [abi_Infrared.algorithm, sector]
      arguments:
        variable_name: data
    filename_formatter:
      kind: filename_formatter
      name: geoips_fname
      depends_on: [abi_Infrared.algorithm, sector, coverage_checker]
      arguments:
        product_name: Infrared
    output_formatter:
      kind: output_formatter
      name: imagery_clean
      depends_on:
        - abi_Infrared.algorithm
        - abi_Infrared.colormapper
        - filename_formatter
        - sector
```

:::{note}
This mirrors a real, CI-tested workflow shipped with GeoIPS at
`geoips/plugins/yaml/workflows/tests/abi_static_infrared_imagery_clean.yaml` (only the
`docstring` differs). Every workflow shown in these docs is exercised by the test suite,
so the examples stay runnable. See {ref}`running-obp` to run it.
:::

## Running a workflow

Run a registered workflow with the {ref}`GeoIPS CLI <command_line>`:

```bash
geoips run order_based abi_static_infrared_imagery_clean \
    $GEOIPS_TESTDATA_DIR/test_data_abi/data/goes16_20200918_1950/*
```

or exercise its built-in `test` section (comparison outputs, output checkers) with:

```bash
geoips test workflow abi_static_infrared_imagery_clean
```

## Where to go next

- {ref}`workflows` — the full `workflows` interface: steps, `globals`/`kinds`,
  `depends_on`, embedded workflows, and the `test` section.
- {ref}`running-obp` — running workflows and applying overrides from the command line.
- {ref}`obp-best-practices` — OBP-native patterns and recommendations.
- {ref}`scripting-guide` — calling GeoIPS plugins directly from Python with the same
  DataTree model OBP uses.

```{toctree}
:maxdepth: 1
:hidden:

workflows
running
best-practices
```
