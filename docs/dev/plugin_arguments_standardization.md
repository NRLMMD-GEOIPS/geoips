<!-- # # # This source code is subject to the license referenced at -->
<!-- # # # https://github.com/NRLMMD-GEOIPS. -->


# Plugin Arguments Standardization

Guidelines for defining, extending, and maintaining plugin ArgumentsModel classes across all GeoIPS plugin kinds.

## Overview

GeoIPS plugin argument models define the interface between workflow YAML files
and the underlying processing plugins. Each plugin kind (algorithm, reader,
output formatter, etc.) has a corresponding pydantic `ArgumentsModel` that
validates the arguments supplied in a workflow's `spec.steps` section.

Standardizing these models ensures that:

- Invalid YAML arguments are caught at parse time, not deep in processing
- New plugin authors have a clear template to follow
- The models serve as accurate, auto-generatable documentation
- Type-checked tooling works without suppression

---

## Standards

1. **Model location** — Each plugin kind's argument model should reside in
   `geoips/pydantic_models/v<version_number>/<plugin_type>.py`.

2. **Naming** — All field names must use `snake_case` naming convention. Avoid `PascalCase` or
   `camelCase` aliases unless required for backwards compatibility with existing
   YAML files; where unavoidable, document the legacy reason in the field
   description.
   Note: We are currently working on [issue #1532](https://github.com/NRLMMD-GEOIPS/geoips/issues/1532) as part of the V2 release.

3. **Model inheritance** - All plugin argument models must inherit from one of the base models listed below:

| Model | Extra Fields | Mutable | When to Use |
|---|---|---|---|
| `FrozenModel` | No | No | Strict schema with immutable instances |
| `PermissiveFrozenModel` | Yes | No | Extensible schema with immutable instances |
| `DynamicModel` | No | Yes | Strict schema with mutable instances |
| `PermissiveDynamicModel` | Yes | Yes | Extensible schema with mutable instances |

Before defining any new Pydantic configuration, please refer to ` CoreBaseModel` in `geoips/pydantic_models/v<version_number>/<plugin_type>.py`

4. **Group cohesive fields** — Fields that are logically related should be consolidated into a nested configuration model rather than maintained as separate flat or top-level fields. This makes field relationships explicit in the schema and keeps manual cross-field validation localized within the nested model. For instance:

   - `cbar_full_width`, `cbar_label`, `cbar_spacing`, `cbar_ticks`, `cbar_tick_labels` in
     `ColormapperArgumentsModel` → `ColorbarConfig`

 **Backward compatibility** Introducing nested configuration models changes the expected structure of YAML inputs. Hence, this standard should be treated as good to have or recommened for the exisitng models but must be adhered for the new plugin models.

5. **Nullable fields** — Any field whose default is `None` must declare `| None` in
 its type annotation. A missing `| None` causes silent coercion or validation
 failure in pydantic v2.

6. **Descriptions** — Every field must include a descriptive `description` string in its `Field()` declaration. These descriptions are used to automatically generate plugin documentation and should clearly explain the field's purpose and expected values.

---


## 1. Reader Plugins

### Current

| Argument | Type | Default | Description |
|---|---|---|---|
| `variables` | `list[str] \| None` | `None` | List of variables to read. Preferred form of the deprecated `chans`. |
| `chans` | `list[str] \| None` | `None` | **Deprecated** — alias for `variables`. Will be removed in GeoIPS 2.0. |
| `area_def` | `AreaDefinition \| None` | `None` | The domain over which to read data. Accepts a dict (converted via `create_area_def`) or an `AreaDefinition` object. |
| `filenames` | `list[Path] \| None` | `None` | Full path(s) to file(s) for static dataset inputs. Supports glob patterns. |
| `metadata_only` | `bool` | `False` | Read metadata only, skip data arrays. |
| `resampled_read` | `bool` | `False` | Enable resampled read, needed for datatypes read within `get_alg_xarray`. |
| `sectored_read` | `bool` | `False` | Enable sectored read. |
| `self_register` | `str \| None` | `None` | Enable self-registration. |
| `self_register_source` | `str \| None` | `None` | Source dataset to use for self-registration. |
| `self_register_dataset` | `str \| None` | `None` | Dataset within the source to use for self-registration. |

### Changes

- refer issue 1533


## 2. Algorithm Plugins


### Current

| Argument | Type (declared) | Default | Description |
|---|---|---|---|
| `variables` | `list[str] \| None` | `None` | List of input variables used in algorithm processing. |
| `var_map` | `dict[str, str] \| None` | `{}` ⚠ | Maps input variable names to names used in xobj. |
| `output_data_range` | `tuple[StrictFloat, StrictFloat] \| None` | `None` | Min and max output value. Applied last, after all other corrections. |
| `min_outbounds` | `str \| None` | `None` | How to handle values below `output_data_range` minimum: `retain`, `mask`, or `crop`. |
| `max_outbounds` | `str \| None` | `None` | How to handle values above `output_data_range` maximum: `retain`, `mask`, or `crop`. |
| `norm` | `StrictBool`  | `None` | Normalize output to `[0, 1]`. |
| `inverse` | `StrictBool`  | `None` | Invert output values. |
| `scale_factor` | `float \| None` | `None` | *(no description)* |
| `input_units` | `str`  | `None` | Units of input data, for applying necessary conversions. |
| `output_units` | `str`  | `None` | *(description says "input data" — copy-paste error)* |
| `gamma_list` | `list[StrictFloat] \| None` | `None` | *(no description)* |
| `mask_night` | `bool`  | `None` | *(no description)* |
| `mask_day` | `bool`  | `None` | *(no description)* |
| `max_day_zen` | `float \| None` | `None` | *(no description)* |
| `min_night_zen` | `float \| None` | `None` | *(no description)* |
| `max_night_zen` | `float \| None` | `None` | *(no description)* |
| `sun_zen_correction` | `StrictBool \| None` | `None` | Apply solar zenith angle correction to output. |
| `satellite_zenith_angle_cutoff` | `float \| None` | `None` | Mask data where satellite zenith angle exceeds this threshold. |
| `pressure_level_range` | `tuple[float, float] \| None` | `None` | Min and max pressure levels for filtering DMW retrievals. |
| `pressure_key` | `str \| None` | `None` | *(no description)* |
| `time_key` | `str`  | `None` | *(no description)* |
| `time_fcst` | `StrictInt \| None` | `None` | *(no description)* |
| `time_dim` | `StrictInt \| None` | `None` | Time dimension index. Alias: `Time_Dimension` (PascalCase — legacy). |
| `grid_geo` | `StrictBool \| None` | `None` | *(no description)* |

