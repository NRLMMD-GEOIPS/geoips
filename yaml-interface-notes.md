# GeoIPS YAML interface notes

## `base.yaml`

### Interface and Family
Currently, the `interface` is set at the top level of a plugin while the `family` is set in the metadata. Is this appropriate? Maybe `family` should be at the top level as well?

One proposal might be to change `base.yaml` to:
```yaml
type: object
parameters:
  interface:
    type: string
  family:
    type: string
    default: standard
  metadata:
    ...
  spec:
    ...
```

### Descriptions
Are we okay with the names `short-description` and `long-description`?