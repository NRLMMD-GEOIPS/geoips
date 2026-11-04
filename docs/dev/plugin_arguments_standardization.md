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

---


## 2. Algorithm Plugins


### Current

| Argument | Type (declared) | Default | Description |
|---|---|---|---|
| `variables` | `list[str] \| None` | `None` | List of input variables used in algorithm processing. |
| `var_map` | `dict[str, str] \| None` | `{}` | Maps input variable names to names used in xobj. |
| `output_data_range` | `tuple[StrictFloat, StrictFloat] \| None` | `None` | Min and max output value. Applied last, after all other corrections. |
| `min_outbounds` | `str \| None` | `None` | How to handle values below `output_data_range` minimum: `retain`, `mask`, or `crop`. |
| `max_outbounds` | `str \| None` | `None` | How to handle values above `output_data_range` maximum: `retain`, `mask`, or `crop`. |
| `norm` | `StrictBool` | `None` | Normalize output to `[0, 1]`. *(annotation missing `\| None` — pending fix)* |
| `inverse` | `StrictBool` | `None` | Invert output values. *(annotation missing `\| None` — pending fix)* |
| `scale_factor` | `float \| None` | `None` | Scalar multiplier applied to the output data. |
| `input_units` | `str` | `None` | Units of input data for applying necessary conversions. *(annotation missing `\| None` — pending fix)* |
| `output_units` | `str` | `None` | Units of output data for applying necessary conversions. *(annotation missing `\| None` — pending fix)* |
| `gamma_list` | `list[StrictFloat] \| None` | `None` | Gamma correction values to apply per channel. |
| `mask_night` | `bool \| None` | `None` | If True, mask pixels classified as night. |
| `mask_day` | `bool \| None` | `None` | If True, mask pixels classified as day. |
| `max_day_zen` | `float \| None` | `None` | Maximum solar zenith angle in degrees to classify as day. |
| `min_night_zen` | `float \| None` | `None` | Minimum solar zenith angle in degrees to classify as night. |
| `max_night_zen` | `float \| None` | `None` | Maximum solar zenith angle in degrees to classify as night. |
| `sun_zen_correction` | `StrictBool \| None` | `None` | Apply solar zenith angle correction to output. |
| `satellite_zenith_angle_cutoff` | `float \| None` | `None` | Mask data where satellite zenith angle exceeds this threshold. |
| `pressure_level_range` | `tuple[float, float] \| None` | `None` | Min and max pressure levels for filtering DMW retrievals. |
| `pressure_key` | `str \| None` | `None` | Variable name used to identify pressure levels in the dataset. |
| `time_key` | `str \| None` | `None` | Variable name used to identify the time dimension in the dataset. |
| `time_fcst` | `StrictInt \| None` | `None` | Index of the forecast time offset along the time dimension. |
| `time_dim` | `StrictInt \| None` | `None` | Number of elements along the time dimension. Alias: `Time_Dimension` (PascalCase — legacy). |
| `grid_geo` | `StrictBool \| None` | `None` | If True, regrid data to a geographic grid before processing. |

---


## 3. Colormapper Plugins

Colormapper arguments are defined in `geoips/pydantic_models/v1/colormappers.py` as
`ColormapperArgumentsModel`.

### Current

> **`PLUGIN_PROVIDED`** is a sentinel default meaning the plugin's own YAML supplies
> this value. These fields have no system-level fallback.

| Argument | Type | Default | Description |
|---|---|---|---|
| `cbar_full_width` | `bool` | `False` | Extend the colorbar across the full width of the image. |
| `cbar_label` | `str` | plugin-provided | Colorbar label string passed to `cbar.set_label`. |
| `cbar_spacing` | `str` | `"proportional"` | Spacing argument passed to `fig.colorbar`. |
| `cbar_ticks` | `list[float] \| None` | `None` | Explicit list of colorbar tick positions. |
| `cbar_tick_labels` | `list[str] \| None` | `None` | Labels passed to `cbar.set_ticks`. |
| `cmap_name` | `str` | plugin-provided | Name of the matplotlib colormap. |
| `cmap_path` | `str \| None` | `None` | Path to an ASCII colormap file. If None, `cmap_name` is used. |
| `cmap_source` | `str` | plugin-provided | Source identifier for the colormap. |
| `colorbar_kwargs` | `dict \| None` | `None` | Extra kwargs passed directly to `fig.colorbar`. |
| `create_colorbar` | `bool \| None` | `True` | Whether to include a colorbar in the image. |
| `data_range` | `tuple[float, float] \| str` | plugin-provided | Min and max value for colormap normalization. |
| `pressure_range_legend` | `list[str] \| None` | `None` | Strings used for colorbar tick labels. |
| `set_ticks_kwargs` | `dict \| None` | `None` | Extra kwargs passed directly to `cbar.set_ticks`. |
| `set_label_kwarg` | `dict \| None` | `None` | Extra kwargs passed directly to `cbar.set_label`. |


---



## 4. Coverage Checker Plugins

### Current

| Argument | Type | Default | Description |
|---|---|---|---|
| `variable_name` | `str` | `None` | Variable name to check percent unmasked. *(annotation missing `\| None` — pending fix)* |
| `area_def` | `str \| None` | `None` | Area definition identifier. |
| `radius_km` | `float \| None` | `300` | Radius in km of center disk to check for coverage. |

---


## 5. Feature Annotator Plugins

Feature annotators have **no step-level arguments** — all configuration lives in the
plugin's own `spec` YAML. A workflow step references the annotator by name only:

```yaml
- kind: feature_annotator
  name: tc_clean
```

The plugin `spec` is validated by models in
`geoips/pydantic_models/v1/feature_annotators.py`.

### `CartopyFeature` fields (per-feature in `spec`)

| Field | Type | Required | Description |
|---|---|---|---|
| `enabled` | `bool` | yes | Enable this cartopy feature layer. |
| `edgecolor` | `ColorType \| None` | when `enabled=True` | Edge color for the feature. |
| `linewidth` | `float \| None` | when `enabled=True` | Line width in pixels. |

A `@model_validator` enforces that `edgecolor` and `linewidth` are both provided
when `enabled=True`.

### `FeatureAnnotatorSpec` top-level keys

`coastline`, `borders`, `rivers`, `states` — each a `CartopyFeature` — plus an
optional `background` color.

---



## 6. Gridline Annotator Plugins

Like feature annotators, gridline annotators have **no step-level arguments**.
All configuration is defined in the plugin's `spec` YAML, validated by models in
`geoips/pydantic_models/v1/gridline_annotators.py`.

### `GridlineAnnotatorSpec` structure

| Section | Key fields | Notes |
|---|---|---|
| `spacing` | `latitude`, `longitude` | `float` or `"auto"` |
| `labels` | `top`, `bottom`, `left`, `right` (required) + 17 optional style fields | Style fields mirror matplotlib `Text` kwargs |
| `lines` | `color`, `linestyle`, `linewidth` | All three required |
| `background` | `ColorType \| None` | Optional |

### Notes

- `linestyle` expects `list[int]` with exactly 2 items (dash pattern). The
  `min_length=2, max_length=2` constraint is enforced via pydantic v2 field constraints.
- `Labels` has 21 fields, 17 of which are optional style pass-throughs. A future
  improvement would be a single `text_kwargs: dict | None` to absorb arbitrary
  matplotlib `Text` kwargs instead of re-declaring each one.

---


## 7. Interpolator Plugins

Interpolator arguments are defined in `geoips/pydantic_models/v1/interpolators.py`
as `InterpolatorArgumentsModel`, which inherits from two parent models:
`InterpGaussInterpolator` and `InterpGridInterpolator`.

### Current

| Argument | Type | Default | Source | Description |
|---|---|---|---|---|
| `sigmaval` | `int` | `10000` | `InterpGaussInterpolator` | Sigma multiplication factor for gaussian interpolation. |
| `drop_nan` | `StrictBool` | `False` | `InterpGaussInterpolator` | Drop NaN values before interpolating. |
| `method` | `str` | `"linear"` | `InterpGridInterpolator` | Grid interpolation method. |
| `area_def` | `str \| None` | `None` | `InterpolatorArgumentsModel` | Area definition identifier. |
| `varlist` | `list[str] \| None` | `None` | `InterpolatorArgumentsModel` | Variables to interpolate. |


### Changes

- use per-interpolator subclasses or a discriminated union so each variant only accepts its own fields.

---


## 8. Output Checker Plugins

Output checker arguments are defined in
`geoips/pydantic_models/v1/output_checkers.py` as
`OutputCheckerArgumentsModel`. Unlike all other argument models, it inherits from
`FrozenModel` (not `PermissiveFrozenModel`) — extra fields are rejected.

### Current

| Argument | Type | Default | Description |
|---|---|---|---|
| `compare_path` | `FilePath \| str` | **required** | Path to the reference/comparison file. |
| `output_products` | `list[FilePath] \| list[str] \| None` | `None` | Paths to the output files to compare. |
| `threshold` | `float \| None` | `None` | Pixelmatch comparison tolerance (0 = strictest, 1 = most lenient). |



## 9. Output Formatter Plugins

Output formatter arguments are defined in
`geoips/pydantic_models/v1/output_formatters.py` as
`OutputFormatterArgumentsModel`. This is the largest argument model in GeoIPS.

### Current

| Argument | Type | Default | Description |
|---|---|---|---|
| `append` | `bool` | `False` | Open output file in append mode. |
| `area_def` | `AreaDefinition \| None` | `None` | Domain over which to read data. |
| `basedir` | `str` | plugin-provided | Base path used for relative metadata paths. |
| `bg_data` | `Any \| None` | `None` | Background dataset assigned from the DataTree for rendering. |
| `bg_datatype_title` | `str \| None` | `None` | Background data type label. |
| `bg_mpl_colors_info` | `dict \| None` | `None` | Matplotlib colormap config for background dataset. |
| `bg_product_name_title` | `str \| None` | `None` | Title of background product. |
| `bg_xarray` | `Any \| None` | `None` | Background xarray dataset used to construct the platform title string. |
| `cog` | `bool` | `True` | Produce a Cloud-Optimized GeoTIFF. |
| `clean_fname` | `str \| None` | `None` | Output path for overlay-free image. |
| `clobber` | `bool` | `False` | Overwrite output file even if it exists. |
| `existing_image` | `str \| None` | `None` | File path for pre-rendered image to composite onto. |
| `hist_colorbar` | `bool` | plugin-provided | Display histogram-enhanced colorbar. |
| `is_3d` | `bool` | `False` | Interpret product data as a 3D array. |
| `metadata_dir` | `str` | `"metadata"` | Subdirectory name for metadata output. |
| `metadata_fname_dict` | `dict \| None` | `None` | Filename metadata for TC metadata YAML output. |
| `mpl_colors_info` | `dict \| None` | `None` | Matplotlib colormap config dict from `set_matplotlib_colors_standard`. |
| `output_dict` | `dict \| None` | `None` | Product spec overrides for coverage checking. |
| `output_fname_dict` | `dict \| None` | `None` | Mapping of output product keys to their generated file paths. |
| `overwrite` | `bool` | `True` | Skip writing if output file already exists when `False`. |
| `pressure_range_dict` | `dict \| None` | `None` | Pressure range boundaries used for legend tick labels. |
| `product_datatype_title` | `str \| None` | `None` | Display name for data type in figure title. |
| `product_name_title` | `str \| None` | `None` | Display name for product in figure titles. |
| `remove_duplicate_minrange` | `Any \| None` | `None` | Passed to `save_image()` for duplicate removal; currently a no-op. |
| `savefig_kwargs` | `dict \| None` | `None` | Extra kwargs for matplotlib `savefig()`. |
| `title_copyright` | `str \| None` | `None` | Copyright string for figure title. |
| `title_formatter` | `str \| None` | `None` | Title format string. |
| `use_compression` | `bool` | `False` | Apply zlib compression when writing netCDF output. |
| `var_name` | `str \| None` | `None` | Variable name to extract from xarray for plotting. |
| `working_directory` | `str` | plugin-provided | Base output directory for generated files. |
| `x_size` | `int` | `None` | Pixel width of the projected area. |
| `y_size` | `int` | `None` | Pixel height of the projected area. |



## 10. Title Formatter Plugins

Title formatter arguments are defined in
`geoips/pydantic_models/v1/title_formatters.py` as
`TitleFormatterArgumentsModel`.

### Current

| Argument | Type | Default | Description |
|---|---|---|---|
| `area_def` | `str \| None` | `None` | Area definition identifier. |
| `product_name_title` | `str \| None` | `None` | Product name title string. |
| `product_datatype_title` | `str \| None` | `None` | Data type label for the figure title. |
| `bg_product_name_title` | `str \| None` | `None` | Background product name title. |
| `bg_datatype_title` | `str \| None` | `None` | Background data type label. |
| `title_copyright` | `str \| None` | `None` | Copyright string appended to the generated title. |
