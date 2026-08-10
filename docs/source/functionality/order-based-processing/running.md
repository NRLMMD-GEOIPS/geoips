<!--
# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.
-->

(running-obp)=

# Running workflows

Run a workflow with the {ref}`GeoIPS CLI <command_line>`:

```bash
geoips run order_based <workflow> <filepaths> [options]
```

Two positional arguments are required and ordered:

1. **`workflow`** — the name of a registered workflow plugin, **or a path to a `.yaml`/
   `.json` unregistered workflow**, or a dictionary evaluated as a workflow.
2. **`filepaths`** — the data files to feed the workflow.

```bash
geoips run order_based abi_static_infrared_imagery_clean \
    $GEOIPS_TESTDATA_DIR/test_data_abi/data/goes16_20200918_1950/*
```

To run a workflow's built-in `test` section (comparison outputs, output checkers) instead:

```bash
geoips test workflow abi_static_infrared_imagery_clean
```

## Overrides

Overrides let you change step arguments without editing the workflow. They come in two
equivalent forms.

### String overrides (`-s`, `-k`, `-g`)

Lowercase flags take one or more `key=value` strings — **step** (`-s`),
**kind** (`-k`), and **global** (`-g`):

```bash
geoips run order_based test_product $GEOIPS_TESTDATA_DIR/test_data_abi/data/goes16_20200918_1950/* \
  -s abi_Infrared.spec.steps.algorithm.output_units=Kelvin \
  -s reader.area_def=null \
  -k readers.satellite_zenith_angle_cutoff=80 \
  -g sector_list=global_cylindrical \
  -g logging_level=info
```

Formats:

- **Step:** `<step_id>.<path...>.<argument>=<value>` — the key path maps to the
  **expanded** workflow (run `geoips expand <workflow>` to see it).
- **Kind:** `<kind>.<argument>=<value>` — applies to every step of that interface kind.
- **Global:** `<name>=<value>` — applies to (or adds at) every step.

You can list several overrides after one flag; group by type and add the next flag when
you switch. Arguments a plugin does not accept are dropped automatically.

### Dictionary overrides (`-S`, `-K`, `-G`)

Uppercase flags take a single dictionary each, matching the structure used in a
workflow's `test` section:

```bash
geoips run order_based test_product $GEOIPS_TESTDATA_DIR/test_data_abi/data/goes16_20200918_1950/* \
  -S '{"reader": {"self_register": "LOW"}, "abi_Infrared": {"spec": {"steps": {"algorithm": {"output_units": "kelvin"}}}}}' \
  -K '{"readers": {"satellite_zenith_angle_cutoff": 80}}' \
  -G '{"sector_list": "global_cylindrical", "logging_level": "info"}'
```

These are harder to type by hand but are convenient when scripts generate calls (e.g.
near-real-time processing).

Under the hood, GeoIPS fully expands the workflow, applies the overrides, then
re-validates the modified workflow with Pydantic.

### Output-checker overrides

A workflow's `test` section supports a fourth override type that has no command-line flag:
`outputs`. It inserts an `output_checker` step immediately after the step whose output you
want to verify. The checker plugin is derived from the `compare_path` unless you set
`output_checker_name` explicitly.

```yaml
test:
  outputs:
    <step_id>:
      # output_checker_name: image                # optional; derived from compare_path
      # full_test_policy: on_token_mismatch | always | never
      compare_path: /path/to/comparison/file.ext
      # threshold: 0.05                            # image checker only
```

## Other arguments

`geoips run order_based` also accepts the standard procflow arguments (logging, output
paths, etc.). See the {ref}`CLI reference <command_line>` for the full list.
