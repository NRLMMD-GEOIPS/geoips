<!--
# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.
-->

(workflows)=

# The `workflows` interface

A **workflow** is a YAML plugin (`interface: workflows`, `family: order_based`) that
defines an ordered sequence of {ref}`OBP <order-based-processing>` steps. This page is
the reference for how a workflow is structured.

:::{note}
If you have not read {ref}`order-based-processing` yet, start there — this page assumes
the ETCVO model and the basic step vocabulary.
:::

## Top-level fields

A workflow plugin uses the standard GeoIPS plugin header plus a `spec`:

```yaml
apiVersion: geoips/v1
interface: workflows
family: order_based
name: my_workflow            # unique, valid Python identifier
docstring: What this workflow produces.
package: geoips
spec:
  globals: {}                # arguments applied to every step (optional)
  steps: {}                  # the ordered steps (required)
```

## Steps

`spec.steps` maps a **step id** to a step definition. The step id is a unique, valid
Python identifier and also names the step's output in the processing tree.

Each step definition accepts:

`kind`
: The plugin interface for this step (`reader`, `algorithm`, `interpolator`,
  `colormapper`, `sector`, `coverage_checker`, `filename_formatter`,
  `output_formatter`, `output_checker`, `product`, `product_default`, or `workflow`).

`name`
: The specific plugin of that `kind` (for `product` steps, a `[source, product]` pair).

`arguments`
: A mapping validated against the plugin's call signature. Unsupported arguments are
  rejected by Pydantic before processing starts.

`depends_on`
: A list of step ids whose output feeds this step. If omitted, GeoIPS infers the most
  recent data-producing step. Use dotted notation to depend on a step inside an embedded
  workflow: `depends_on: [abi_Infrared.algorithm]`.

`keep`
: Whether to retain this step's result in the processing tree after it is consumed
  (defaults to a retention policy — see {ref}`retention-policies`).

Steps must **accept** data conforming to the GeoIPS {ref}`xarray standard
<xarray_standards>` (except `reader` steps, which produce it) and **return** data in the
same standard (except `output_formatter` steps, which write files).

## Global and kind arguments

`spec.globals` supplies arguments applied to **every** step (e.g. `sector_list`,
`logging_level`, `product_name`). Arguments a given plugin does not accept are dropped
automatically before that plugin is called. A workflow's `test` section can also carry a
`kinds` block that applies arguments to every step of a given interface `kind` (e.g. a
`satellite_zenith_angle_cutoff` for all `readers`).

## Embedded workflows (reuse)

A step of `kind: workflow`, `kind: product`, or `kind: product_default` expands into an
embedded set of steps at runtime, so you can compose complex workflows from smaller ones:

- **Workflow-in-workflow** — reference another registered workflow by name; its steps are
  loaded and nested in place.
- **Product-in-workflow** — a `product` step is expanded into the ordered steps implied by
  its product family (e.g. `interpolator_algorithm_colormapper` inserts an interpolator,
  then an algorithm, then a colormapper).
- **Product-default-in-workflow** — same idea, driven by a `product_default`.

When a product/product_default expands, the first data-consuming step depends on the last
data output from the parent workflow, and subsequent steps chain from there. See
{ref}`running-obp` for a fully worked expansion example.

The **ordered** product families (about 95% of GeoIPS products) are:

```python
ORDERED_PRODUCT_FAMILIES = [
    "algorithm",
    "algorithm_colormapper",
    "algorithm_interpolator_colormapper",
    "interpolator",
    "interpolator_algorithm",
    "interpolator_algorithm_colormapper",
]
```

## The `test` section

A workflow can carry a `test` section describing how it is validated in CI: the input
`fnames`, expected `outputs` (with comparison paths and output checkers), and override
blocks (`steps`, `kinds`, `globals`). The same override structure can be supplied on the
command line — see {ref}`running-obp`.

```yaml
test:
  fnames: !ENV ${GEOIPS_TESTDATA_DIR}/test_data_abi/data/goes16_20200918_1950/*
  outputs:
    output_formatter:
      full_test_policy: on_token_mismatch   # always | never
      compare_path: !ENV $GEOIPS_PACKAGES_DIR/geoips/tests/outputs/abi.static.<product>.imagery_clean
      output_checker_name: image
```

## Model reference

The workflow YAML is validated against the following Pydantic model. The fields below are
generated directly from the code, so they always match the current validation rules:

```{eval-rst}
.. autopydantic_model:: geoips.pydantic_models.v1.workflows.WorkflowPluginModel
   :members:
   :noindex:
```

## See also

- {ref}`running-obp` — run a workflow and apply overrides from the command line.
- {ref}`obp-best-practices` — when to compose vs. script, `depends_on` patterns.
