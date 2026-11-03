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

3. **Model inheritance** - All plugin argument models must inherit from one of the base models listed below:

| Model | Extra Fields | Mutable | When to Use |
|---|---|---|---|
| `FrozenModel` | No | No | Strict schema with immutable instances |
| `PermissiveFrozenModel` | Yes | No | Extensible schema with immutable instances |
| `DynamicModel` | No | Yes | Strict schema with mutable instances |
| `PermissiveDynamicModel` | Yes | Yes | Extensible schema with mutable instances |

Before defining any new Pydantic configuration, please refer to ` CoreBaseModel` in `geoips/pydantic_models/v<version_number>/<plugin_type>.py`

