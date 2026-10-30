# DataTree Spec Reconciliation

## 1. Purpose

This document records changes that the class-based plugin *Specification* effort will make
to `docs/source/devguide/datatree-spec.md`. It is a companion to
[`class_based_plugins.md`](class_based_plugins.md), which is normative for the decisions
recorded here; this document translates those decisions into edits.

Work these changes during Phase 6 integration.

## 2. Governing Relationship

The datatree spec is normative for DataTree structure. The plan is normative for the
class-based plugin contract. Where the two conflict, the plan governs and the datatree spec
is updated to match — a conflict is never resolved by weakening a decision recorded in the
plan.

Three kinds of change appear below:

- **Propagations** — requirements the plan states that the datatree spec does not yet state.
- **Corrections** — places where the datatree spec is wrong, ambiguous, or inconsistent with
  itself.
- **Cross-references** — material that stays in the plan, which the datatree spec should
  point at rather than restate.

## 3. Propagations

Requirements stated in the plan that the datatree spec needs to carry. Each row names the
datatree spec sections to change.

| Plan requirement | Datatree spec sections to change |
| --- | --- |
| Root holds only step children and workflow attrs; no datasets or DataArrays at root | §5.1 Canonical Anatomy |
| Data-bearing steps hold dataset nodes, one per coordinate-compatible variable group | §5.1 Canonical Anatomy, which currently shows data directly on the step node. The term "coordinate-compatible variable group" does not exist in the datatree spec and needs introducing in §5 |
| Retention operates on the `/<step_id>/<dataset_id>` hierarchy | §10.4 What Is GC'd, What Survives; §10.5 GC Algorithm |
| Retention provenance records policy, request, state, and reason | §5.4 Per-Step Provenance, which currently carries only `gc_status`; §10.7 GC Visibility in Provenance |
| `start_datetime` and `end_datetime` required on every dataset node | §5.2 Root-Level Attributes, where both are currently required at the root as an aggregate and become derived values; a dataset-level statement needs adding to §5 |
| Execution timing renamed to `execution_start_time` / `execution_end_time` | §5.3 Workflow-Level Provenance (`processing_history` schema); §5.4 Per-Step Provenance; §3.2 worked example |

### 3.1. Temporal Extent Is Not A Root Aggregate

The datatree spec defines `start_datetime` and `end_datetime` only at the workflow root, as
an aggregate across inputs. The *Specifications* depend on per-dataset temporal metadata —
two reader steps producing datasets for the same source at different observation times are
distinguished by it — so an aggregate at the root is not sufficient. The root value becomes
derived from the dataset-level values rather than being their source of truth.

## 4. Corrections

### 4.1. The Dataset Level Is Ambiguous

The datatree spec is internally inconsistent about whether a dataset level exists between a
step node and its variables. Its §3.2 worked example uses both structures: the `/read_abi`
step contains a `B14BT(xr.Dataset)` dataset node holding a `B14BT` variable, while the
`/single_channel` step places `B14BT_clipped` directly on the step node as a data variable.
Sections §5.1, §5.7, §10.4, and §11.1 all read as the flat form.

The plan resolves this in favor of always requiring one dataset per coordinate-incompatible
group of variables, whether there is one group or many. The datatree spec should state that
hierarchy normatively and correct the sections that assume the flat form.

### 4.2. The `workflows` Interface Is YAML-Based

Datatree spec §4.1 states that "the `workflows` interface is class-based." It is registered
as a YAML-based interface in `geoips/interfaces/__init__.py`. Relatedly, §4.7 places
`Workflow(Plugin)` in the class-based plugin hierarchy and §15.2 documents it as a class at
`geoips/interfaces/class_based/workflow.py`.

These conflate the registered YAML-based `workflows` plugin interface with possible internal
workflow runtime machinery. Consult the plan's tabled design topic on `depends_on` and
conduit resolution before revising them, since the container-object discussion governs which
concept each passage means.

### 4.3. `kind: sectorizer` Is Not A Registered Interface

Datatree spec §3.1's example uses `kind: sectorizer`, which is not a registered interface and
appears to be placeholder text. The registered sector-related interfaces are `sectors`
(YAML-based), `sector_adjusters`, `sector_metadata_generators`, and `sector_spec_generators`.
The `kind: sector` usage in §4.6 is valid and resolves to the YAML-based `sectors` interface.

### 4.4. Variable-Level Metadata Requirement Is Relaxed

Datatree spec §5.5 requires every `DataArray` holding primary geophysical data to set
`units`, `long_name`, and `standard_name`. GeoIPS does not populate these consistently and
does not validate them at all: across reader modules `units` appears in 18, `long_name` in
one, and `standard_name` in two, with no validation of any of the three in
`geoips/interfaces/` or `geoips/pydantic_models/`. Enforcing the requirement would generate
conformance gaps against essentially every reader without improving any of them.

All three become optional for v2.0.0. The intent is to restore them as requirements once
GeoIPS populates and validates them, rather than to abandon them; no target release is set.

### 4.5. Execution Timing Keys Are Confusable

The datatree spec uses `start_time` and `end_time` for step execution timing, in per-step
provenance and in `processing_history`. These are confusable with `start_datetime` and
`end_datetime`, which mean data collection or valid time — a one-syllable difference carrying
entirely different semantics, and the distinction is never stated as a convention.

The plan renames execution timing to `execution_start_time` and `execution_end_time`. The
datatree spec's per-step provenance, `processing_history` schema, and worked example all need
updating. The example is ambiguous either way: it places `start_time` inside a reader step's
attrs among `source_name`, `platform_name`, and `wavelength`, where observation time is the
natural reading.

### 4.6. Token Prefix Contradicts Its Own Examples

The datatree spec abstract mentions a `dask:` prefix for token values. Its examples in §3.2
and §10.7 use `blake2b:`. The plan adopts `blake2b:`; the abstract should be corrected.

## 5. Cross-References

Material that stays in the plan. The datatree spec should point at it rather than restate
it, so that a single statement governs.

- **Dimensions and composition.** The datatree spec has no equivalent statement about which
  dimensions a dataset carries, and should point at the plan rather than developing a
  parallel one.
- **Dataset identity and scientific compatibility, including the join operator validation
  contract.** The datatree spec describes `split` and `join` only as execution scaffolding
  and does not define them as operators with contracts. That definition is a deliverable of
  this effort; the datatree spec should reference the resulting contract rather than
  restating it.

## 6. Reference Links

- [`class_based_plugins.md`](class_based_plugins.md) — the plan these changes derive from.
- `docs/source/devguide/datatree-spec.md` — the document being changed.
- `geoips/interfaces/__init__.py` — registered interface list, for §4.2.
