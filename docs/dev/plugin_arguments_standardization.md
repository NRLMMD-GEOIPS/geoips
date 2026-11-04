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
