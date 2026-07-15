<!--
# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.
-->

(first-workflow)=

# Quickstart: run your first workflow

This quickstart takes you from a fresh install to a rendered satellite product using
{ref}`Order-Based Processing <order-based-processing>` (OBP) — the GeoIPS 2.0 way of
producing outputs. It assumes you have already {ref}`installed GeoIPS <installing>`.

## 1. Get some data

GeoIPS ships test datasets you can download with the CLI. Grab the GOES-16 ABI sample:

```bash
geoips config install test_data_abi
```

This downloads the data under `$GEOIPS_TESTDATA_DIR`.

## 2. Run a workflow

A **workflow** is a YAML plugin that lists the ordered plugin steps needed to make a
product. GeoIPS ships several ready-to-run workflows. Run the ABI 11.2 µm infrared
clean-imagery workflow on the sample data:

```bash
geoips run order_based abi_static_infrared_imagery_clean \
    $GEOIPS_TESTDATA_DIR/test_data_abi/data/goes16_20200918_1950/*
```

The log ends with `Return Value 0` on success and prints the path to the output PNG. Open
it to see your first GeoIPS product.

:::{tip}
To run a workflow *and* compare its output against a reference image (the way CI does),
use its built-in test section instead:

```bash
geoips test workflow abi_static_infrared_imagery_clean
```
:::

## 3. See what the workflow did

A workflow references products and other workflows that expand into more steps at runtime.
Print the fully expanded workflow to see every step GeoIPS actually ran:

```bash
geoips expand abi_static_infrared_imagery_clean --color
```

You will see the ordered steps — a `sector`, a `reader`, the `abi_Infrared` product
(itself expanded into an interpolator, algorithm, and colormapper), a `coverage_checker`,
a `filename_formatter`, and an `output_formatter`.

## 4. Change something without editing the workflow

You can override any step argument on the command line. For example, output the product in
Kelvin instead of the default, and switch the sector, using
{ref}`overrides <running-obp>`:

```bash
geoips run order_based abi_static_infrared_imagery_clean \
    $GEOIPS_TESTDATA_DIR/test_data_abi/data/goes16_20200918_1950/* \
    -g logging_level=info
```

See {ref}`running-obp` for the full override syntax (`-s`/`-k`/`-g` and their `-S`/`-K`/`-G`
dictionary forms).

## 5. Explore what is available

```bash
geoips list interfaces -i          # interfaces that have implemented plugins
geoips list readers                # all reader plugins
geoips list products               # all product plugins
geoips describe alg single_channel # details of a specific plugin
```

## Where to go next

- {ref}`order-based-processing` — how workflows and OBP work in depth.
- {ref}`tutorials` — build your own reader, algorithm, colormapper, product, and more.
- {ref}`scripting-guide` — drive the same plugins directly from Python.
- {ref}`migrating-1x-to-2x` — if you are coming from GeoIPS 1.x.
