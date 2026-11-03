<!-- # # # This source code is subject to the license referenced at -->
<!-- # # # https://github.com/NRLMMD-GEOIPS. -->

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
