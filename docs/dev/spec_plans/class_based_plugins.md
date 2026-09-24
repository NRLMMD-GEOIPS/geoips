# GeoIPS Class-Based Plugin Specifications: Task Plan

## 1. Purpose

This document is the shared source of truth for planning and tracking the development of GeoIPS class-based plugin *Specification* documentation. It is intentionally a plan, not the *Specifications* themselves. The *Specifications* will be **normative target-state documents for the GeoIPS v2.0.0 release**, not descriptions limited to the behavior of the current v2.0.0 alpha implementation.

The finished documentation will explain:

1. The common contract supplied by `BaseClassInterface` and `BaseClassPlugin`.
2. The contract of every registered GeoIPS class-based plugin interface.
3. How each interface participates in a processing workflow, including its inputs, outputs, metadata behavior, arguments, argument conduits, and deprecations.
4. How these *Specifications* relate to the existing architecture, developer guides, tutorials, API documentation, and interface pages.
5. Where the current alpha implementation differs from the v2.0.0 contract and what must change before release.
6. Which existing or newly identified behaviors are deprecated, how users migrate away from them, and when each stage of deprecation occurs.

When implementation begins, use this file to choose the next small unit of work, record decisions, and prevent the work from drifting beyond the agreed scope.

## 2. Desired Outcomes

- A developer can distinguish the responsibilities of an interface, an interface-level base plugin class, and a concrete plugin.
- A plugin author can identify every required attribute and method and understand the behavior inherited from the base classes.
- A workflow author can determine what must precede an interface step, what arguments can reach it, and what data and metadata it produces.
- The v2.0.0 target contract is stated clearly and independently of conformance gaps.
- Current alpha behavior is compared with that contract, and every material difference is tracked as conforming, missing, divergent, ambiguous, or intentionally deferred.
- Every factual claim is traceable to code, tests, an existing document, or an explicitly recorded design decision.
- The new pages are discoverable from the appropriate existing documentation indexes and are cross-linked without duplicating tutorial or API-reference material unnecessarily.
- Existing deprecations and deprecations discovered during specification work are collected in one register with rationale, migration guidance, milestones, and owners.
- Future-facing plugin signatures use a standardized argument vocabulary; noncanonical legacy arguments are isolated in compatibility conduits/adapters and placed on an explicit deprecation path.

## 3. Scope

### 3.1. In Scope

- A base class-based plugin *Specification* covering:
  - `BaseClassInterface`
  - `BaseClassPlugin`
  - required and inherited attributes
  - public and lifecycle methods
  - subclass implementation requirements
  - validation and plugin registration behavior
  - pre-call and post-call behavior
  - native-data/DataTree conversion behavior
  - Order-Based Processing (OBP) integration and argument conduits
- One *Specification* page for each registered class-based interface.
- Useful, tested examples selected from real core or plugin-package implementations.
- Links to relevant concepts, architecture, tutorials, migration guidance, API reference, DataTree *Specifications*, OBP documentation, and plugin registry documentation.
- Links from existing documentation into the new *Specifications* where they improve discoverability or resolve ambiguity.
- Conformance-gap issues covering every confirmed difference between the current v2.0.0 alpha implementation and the approved v2.0.0 *Specifications*, aggregated through a v2.0.0 milestone or project.
- A deprecation register and an overall deprecation policy/strategy covering both pre-existing deprecations and deprecations discovered or proposed during this work.
- Changes to `docs/source/devguide/datatree-spec.md` where it conflicts with, omits, or duplicates decisions recorded here, tracked in [`datatree_spec_reconciliation.md`](datatree_spec_reconciliation.md).
- Documentation build, link, spelling, and example validation appropriate to the files changed.

### 3.2. Out of Scope Unless Added by a Later Decision

- Changing plugin runtime behavior or public APIs.
- Implementing runtime fixes or deprecation machinery. This documentation task will identify and track required changes; implementation work should be scheduled separately unless explicitly brought into scope later.
- Rewriting tutorials, generated API reference, or YAML-based interface *Specifications*.
- Treating `geoips/interfaces/class_based/workflow.py` as a plugin interface unless the inventory phase establishes that it is registered as one. It currently appears to be workflow runtime machinery rather than an interface.
- Documenting historical module-based plugin behavior except where needed for migration or compatibility context.

## 4. Requirement Language

The key words **MUST**, **MUST NOT**, **REQUIRED**, **SHALL**, **SHALL NOT**, **SHOULD**, **SHOULD NOT**, **RECOMMENDED**, **NOT RECOMMENDED**, **MAY**, and **OPTIONAL** in this document and the resulting *Specification* documents are to be interpreted as described in BCP 14, [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) and [RFC 8174](https://www.rfc-editor.org/rfc/rfc8174), when, and only when, they appear in all capitals.

Use these terms sparingly and only for normative v2.0.0 contract requirements:

- **MUST** and **MUST NOT** identify absolute requirements and prohibitions.
- **SHOULD** and **SHOULD NOT** identify recommended behavior for which a valid exception can exist. Each *Specification* MUST explain the consequences of an exception or link to that explanation.
- **MAY** identifies behavior that is genuinely optional. Each *Specification* MUST define any interoperability expectations between implementations that include the option and those that do not.

Lowercase words such as "must," "should," "required," and "may" have their ordinary English meanings and no BCP 14 force. Planning steps, research instructions, examples, observations about the current alpha implementation, and future work outside v2.0.0 use ordinary language. Do not use **SHALL** or **SHALL NOT** in new GeoIPS *Specifications*; prefer **MUST** or **MUST NOT** so equivalent requirement levels use one vocabulary.

Every normative keyword must identify its subject and observable behavior. Avoid using a keyword merely to emphasize a fact, implementation preference, or task-management step.

## 5. Records This Work Maintains

The work will maintain four related but distinct records:

1. **Normative v2.0.0 Specifications** describe what released GeoIPS v2.0.0 MUST provide. They use the requirement language defined in [Requirement Language](#4-requirement-language).
2. **Conformance-gap issues** record confirmed differences between the normative *Specifications* and the behavior of the current alpha implementation. A current limitation MUST NOT silently weaken the target contract.
3. **Deprecation register and strategy** records compatibility behavior that exists now or is newly selected for deprecation. It defines the migration path and lifecycle from announcement through warning, removal, and post-removal cleanup.
4. **Datatree spec reconciliation** records changes this effort will make to `docs/source/devguide/datatree-spec.md`.

### 5.1. Normative v2.0.0 Specifications

Specification pages MUST describe the v2.0.0 contract directly. Short compatibility notes can identify behavior still accepted during transition, but detailed remediation belongs in conformance-gap issues and the deprecation registry so temporary alpha behavior is not mistaken for the intended API.

### 5.2. Conformance-Gap Issues

A conformance gap is a confirmed difference between a normative v2.0.0 requirement and the behavior of the current alpha implementation or its tests. Gaps are found while drafting *Specifications*, when each requirement is compared against code and tests.

Recording a gap never adjusts the contract to match the implementation. Where the target requirement is correct, the gap describes work the implementation owes. Where the requirement itself proves wrong or unworkable, that is a *Specification* change requiring its own approval — not a silent weakening of the target.

Each gap is recorded using the [Conformance-Gap Issue Template](#201-conformance-gap-issue-template), carries the `v2-spec-gap` label, and is classified as release-blocking or not. The v2.0.0 milestone or project provides the aggregate readiness view. A gap leaves the open state only by being resolved or explicitly waived by the responsible release authority; the effort is not complete while a release-blocking gap remains neither. The issue template, label set, milestone workflow, and release-blocking criteria are not yet defined; see the corresponding Phase 0 item.

### 5.3. Deprecation Register and Strategy

The target design MUST use a central, machine-readable deprecation registry within the GeoIPS core package as the authoritative inventory. Compatibility implementations—such as argument normalization, conduit bindings, and warning trigger points—remain near the code they adapt, but each MUST reference a stable entry in the central registry. Published deprecation tables and planning reports SHOULD be generated from the registry. When generation is unavailable, they MAY be maintained manually only if automated validation against the registry prevents the inventories from drifting.

The registry will use typed Python records in a core module or package, validated with pydantic to match the project's existing model conventions and to keep the inventory machine-readable. A central `warn_deprecated(deprecation_id, ...)` helper will resolve stable IDs, issue consistent warnings, and prevent distributed warning sites from duplicating messages or schedule logic. External packages MUST NOT mutate or extend the core registry.

### 5.4. Datatree Spec Reconciliation

Several decisions recorded here require corresponding changes to
`docs/source/devguide/datatree-spec.md`. Those are tracked in
[`datatree_spec_reconciliation.md`](datatree_spec_reconciliation.md), which records
requirements the datatree spec needs to carry, places where it is wrong or ambiguous, and
material it should cross-reference rather than restate.

The datatree spec is normative for DataTree structure. This document is normative for the
class-based plugin contract. Where the two conflict, this document governs and the datatree
spec is updated to match — a conflict is never resolved by weakening a decision recorded
here.

## 6. Specification Model

### 6.1. Requirements For Specification Pages

#### 6.1.1. CF Compliance

Datasets produced by GeoIPS are CF compliant. Coordinates, variable metadata, and dataset structure follow CF conventions, and where CF defines a mechanism for something GeoIPS needs, GeoIPS uses that mechanism rather than inventing an alternative.

This governs decisions throughout these *Specifications*. Where a choice exists between a CF mechanism and a GeoIPS-specific one, the CF mechanism is preferred unless a reason to diverge is recorded alongside the decision. Conventions layered on CF, such as ACDD for discovery metadata, are preferred over GeoIPS-specific alternatives on the same basis, though they are not themselves CF requirements.

> [!WARNING]
> **Known divergences at v2.0.0.** Two exist and are recorded rather than hidden.
> Variable-level metadata is optional where CF would require it, and temporal extent uses
> GeoIPS attribute names rather than the ACDD equivalents. Both are transitional; neither
> is a decision that CF compliance does not apply.

#### 6.1.2. Metadata Requirements

Two kinds of *Specification* page carry metadata requirements, and they divide the work by what the metadata describes.

- The **base *Specification*** defines universal provenance: the metadata every step carries regardless of interface, because it describes execution rather than data.
- **Interface *Specifications*** define dataset identity metadata: the metadata that distinguishes one dataset from another, which differs by what the interface produces.

Universal provenance MUST cover:

- plugin identity
- execution timing
- arguments and token information
- upstream step references
- retention decisions

No universal scientific metadata schema is imposed on every dataset. An interface that requires particular scientific metadata states that requirement on its own page; nothing obliges an unrelated interface to carry it.

#### 6.1.3. Workflow Root and Dataset Nodes

The root workflow DataTree is a container, not a data-bearing node. It MUST NOT contain datasets or DataArrays and MUST contain only:

- child DataTrees representing workflow steps, and
- workflow-level metadata in root attributes.

Every data-bearing step result MUST contain:

- the step metadata required by the applicable *Specifications*, and
- one or more dataset nodes, with one `xarray.Dataset` for each coordinate-compatible group of variables.

A **coordinate-compatible variable group** contains variables whose shared dimensions use the same coordinates. Variables in the same group can have different dimensions or different subsets of dimensions, but whenever two variables share a dimension, the coordinate associated with that dimension MUST agree. Variables that require conflicting coordinates for a shared dimension belong in different dataset nodes.

A class-based operation can change the dataset grouping. For example, an interpolator may accept a step DataTree containing several datasets on different grids and return a new step DataTree containing one dataset on the target grid. The resulting `dataset_id` MUST describe the output dataset according to the naming rules established for that interface or operation; it is not required to preserve an input dataset ID.

#### 6.1.4. Step Classification

The v2.0.0 *Specifications* classify steps by their returned DataTree content, independently of whether their plugins are implemented in Python or YAML:

- A **data-bearing step** returns one or more scientific or processing datasets plus metadata. Data-bearing steps are implemented by class-based plugins.
- A **non-data-bearing step** returns metadata but no scientific or processing datasets. Non-data-bearing steps may be implemented by class-based or YAML-based plugins.
- YAML-based plugins are always non-data-bearing. They configure class-based plugin behavior and return metadata-only DataTrees.

Each class-based interface *Specification* MUST declare whether its steps are data-bearing or non-data-bearing based on the interface's semantic result. Incidental serialization of a scalar, string, dictionary, or compatibility object into an `xarray.Dataset` does not by itself make the result data-bearing.

> [!NOTE]
> **Reminder, pending the output formatters *Specification*.** Output formatter steps are
> non-data-bearing. They perform their declared output side effects and record
> output-product metadata (such as written filenames and checksums) in step-level attrs,
> but do not add or return scientific or processing data. Their step nodes contain only
> attrs describing what was written, consistent with datatree spec §6.5.
>
> This is a single interface's classification sitting among general rules. It belongs on
> the output formatters page once that page exists, and should move there rather than
> remain here.

#### 6.1.5. Dataset Identity and Scientific Compatibility

Dataset metadata such as `start_datetime`, `end_datetime`, source, platform, and projection help users and plugins identify otherwise similar datasets. For example, two reader steps may both produce an ABI dataset with the same `dataset_id` and coordinates but represent different observation times; their distinct `step_id` paths and temporal metadata keep them distinguishable before an explicit join.

GeoIPS infrastructure is responsible for preserving and exposing specified identity and provenance metadata, not for determining whether data are scientifically appropriate to combine. Workflow and plugin authors remain responsible for decisions such as combining different processing levels, calibration states, or scientific products. Operators MUST validate the structural requirements needed to perform their declared operation. Except for behavior expressly permitted by an interface *Specification*, such as optional checks for conflicting declared units, operators MUST NOT impose a generic scientific-compatibility policy.

Join operators MUST validate dimension and coordinate compatibility for the requested join operation. A join *Specification* MUST define the applicable checks and the error raised when dimensions or coordinates cannot be joined as requested. Join operators MAY also check for conflicting declared units when unit information is available. Optional unit checking MUST document whether a conflict produces a warning or error. This does not require universal unit metadata, scientific-level inference, or automatic unit conversion in v2.0.0; users remain responsible for the scientific validity of the requested join.

Data collection or valid time is recorded as `start_datetime` and `end_datetime` on dataset nodes. Every dataset node MUST carry both.

#### 6.1.6. Provenance and Retention

Execution timing is recorded as `execution_start_time` and `execution_end_time`. These names are deliberately distinct from `start_datetime` and `end_datetime`, which record data collection or valid time; the two describe unrelated things and earlier names differing by one word proved confusable.

Retention provenance distinguishes the requested policy from the resulting state:

- workflow-level retention policy
- explicit step retention request
- current data-retention state
- retention decision reason

Use a small, extensible reason vocabulary initially: `explicit_keep`, `policy_keep_all`, `pending_consumer`, `unreferenced`, `workflow_output`, and `no_data`. The implementation can represent a retention decision as a structured result rather than reducing it to a Boolean. Retention MUST operate on the target `/<step_id>/<dataset_id>` hierarchy; current step-root-only garbage collection requires conformance review.

#### 6.1.7. Units

Unit metadata is stored in variable attributes as `units`, with UDUNITS-2 notation preferred. The storage location is stated here rather than only referenced, so that each interface *Specification* names it and a plugin author reading one page does not have to find it elsewhere.

For v2.0.0 a variable MAY carry unit metadata. GeoIPS neither requires nor validates it at this release, so a plugin that consumes unit metadata handles its absence and does not assume it is present. This is expected to become a requirement in a later release, once GeoIPS unit handling is developed enough for one to be meetable.

Interface *Specifications* state where their variables carry unit metadata, whether their plugins require, preserve, convert, or ignore it, and any unit-related arguments. Where the answer is "none," they say so — GeoIPS unit handling is currently limited, and recording that plainly is more useful than omitting the question.

`long_name` and `standard_name` are likewise optional for v2.0.0, on the same grounds: GeoIPS neither populates nor validates them consistently. All three are intended to become requirements once it does.

Shared unit vocabulary, validation, and general automatic conversion are deferred to v2.1 or later. They are not v2.0.0 requirements, and their absence MUST NOT create v2.0.0 conformance-gap issues.

#### 6.1.8. Dimensions and Composition

No dimension, including `latitude`, `longitude`, or `time`, is universally mandatory. Datasets contain only the dimensions naturally represented by their variables, subject to interface-specific requirements. Scalar acquisition information may remain metadata when no axis exists, and GeoIPS does not add artificial length-one dimensions merely to anticipate future composition.

Temporal extent and temporal coordinates are distinct. `start_datetime` and `end_datetime` record the span a dataset covers and are dataset attributes. A `time` coordinate, where present, records the time of each element and is read from the source data; it may be scalar, per-scanline, or otherwise structured. Neither is derived from the other by rule, and a dataset may carry either, both, or only the extent.

A join or other composition operator creates a new dimension when combining inputs along time, height, ensemble member, source, or another declared axis. It defines how metadata become coordinate values, and rejects inputs missing information structurally required for that operation. For example, a join may use the `start_datetime` and `end_datetime` attributes from two ABI reader outputs to build a three-dimensional dataset with a new `time` dimension, taking `start_datetime` as each coordinate value and the pair as its bounds — which is why an input need not carry a `time` axis when that value is scalar before composition.

### 6.2. Canonical DataTree Location Notation

Specifications will use absolute, descriptive paths with the following hierarchy:

```text
workflow root -> step DataTree -> dataset node -> variables and coordinates
```

> [!IMPORTANT]
> **This hierarchy differs from the datatree spec.** Datatree spec §5.1 places `data`,
> `coords`, and `attrs` directly on the step node with no dataset level between a step and
> its variables. This works for some examples, but becomes problematic for others, such as
> the `read_abi` example. The datatree spec is ambiguous here about whether data should be
> stored directly on the step DataTree or on a contained dataset.
>
> This plan resolves this ambiguity in favor of always requiring one dataset to represent
> each coordinate-incompatible group of variables. This is true whether there is only one
> group or many. The [reconciliation document](datatree_spec_reconciliation.md)
> records which datatree spec sections this changes.

The canonical forms are:

| Component          | Notation                                          |
| ------------------ | ------------------------------------------------- |
| Workflow root      | `/`                                               |
| Workflow attribute | `/.attrs["workflow_name"]`                        |
| Step DataTree      | `/<step_id>`                                      |
| Step attribute     | `/<step_id>.attrs["plugin_name"]`                 |
| Dataset node       | `/<step_id>/<dataset_id>`                         |
| Dataset attribute  | `/<step_id>/<dataset_id>.attrs["source_name"]`    |
| Data variable      | `/<step_id>/<dataset_id>.data_vars["wind_speed"]` |
| Coordinate         | `/<step_id>/<dataset_id>.coords["latitude"]`      |
| Branch step        | `/<split_id>/<branch>/<step_id>`                  |

A `step_id` is the arbitrary, case-sensitive identifier assigned to a step by a workflow. A `dataset_id` identifies one coordinate-compatible variable group stored as a distinct dataset within a step DataTree. Dataset identity may describe a resolution, projection, shape, operation result, or another meaningful characteristic or combination of characteristics that distinguishes the dataset from its siblings. For example, a reader step may contain `resolution_500m`, `resolution_1km`, and `resolution_2km` dataset nodes, while an interpolator may consolidate those inputs into one appropriately named target- grid dataset node.

Both `step_id` and `dataset_id` MUST be valid Python identifiers. Names that begin with a digit, such as `5424x5424`, are invalid; a name such as `shape_5424x5424` is valid. The *Specifications* should reference the project's shared Python-identifier validation rules rather than defining a competing validator.

Paths begin with `/`, names are case-sensitive, quoted bracket notation identifies component keys, and angle brackets denote placeholders. The notation is descriptive and is not itself promised to be an executable Python expression. For example:

```text
/read_abi/resolution_2km.data_vars["brightness_temperature"]
```

corresponds conceptually to:

```python
tree["/read_abi/resolution_2km"].ds["brightness_temperature"]
```

**Token format.** *Specification* pages and examples use the `blake2b:` prefix for example token values.

### 6.3. v2.0.0 User-Facing Backward-Compatibility Constraint

GeoIPS v2.0.0 MUST continue to support legacy Products, legacy run scripts, and existing procflow CLI calls. Three invocations MUST be distinguished: bare `geoips run` runs Order-Based Processing; `geoips run <procflow>` and `geoips run --procflow <procflow>` reproduce the named legacy procflow's behavior, the latter through the older flag form. Their arguments MUST remain unchanged; the mimicry is entirely under the hood, driven by those same arguments and the Product plugins they name. The promise covers these user-facing entry points and their supported processing outcomes. It does not make the internal APIs of the existing procflows permanent contracts, nor Products and procflow-call forms permanent public APIs.

**Products.** Legacy Products are deprecated and MUST continue to work. When a Product runs under OBP, GeoIPS MUST convert it into a Workflow at runtime; users are not required to rewrite the Product first. The generated Workflow MUST preserve the Product's supported processing intent and user-visible results, subject to explicitly documented deprecations.

**Permanent conversion.** GeoIPS MUST provide a conversion script as the migration path. It performs the same semantic conversion as the runtime path, but materializes the Workflow so it can replace the Product. Runtime conversion and the script MUST share one canonical conversion engine or be proven behaviorally identical: given the same Product and configuration they MUST produce equivalent Workflows, with no divergence in conversion rules, validation, warnings, or deprecation handling.

**Procflows.** The procflows interface MUST be removed, and OBP MUST become the only way GeoIPS runs. OBP is the execution model rather than a procflow, so `order_based` ceases to exist as a registered procflow along with the rest of the interface. No legacy procflow implementation is retained. All procflow behavior MUST be reproduced through the runtime conversion above: a Product is converted into a Workflow whose shape is determined by the Product's family, and OBP runs that Workflow to produce what the corresponding legacy procflow would have produced. That reproduction MUST be evidenced by the integration tests in [v2.0.0 Legacy Compatibility Test Baseline](#65-v200-legacy-compatibility-test-baseline). The conversion is transitional and MUST be removed with the legacy entry points it serves rather than becoming an accidental permanent API.

This constraint guides both the target *Specifications* and deprecation strategy:

- The *Specifications* MUST identify behavior required by legacy Products and run scripts, separately from the internal legacy-procflow behavior being removed.
- The procflows MUST be removed, and all of their behavior MUST be reproduced by internal conversion to Workflows. Their removal MUST NOT break the supported user-facing compatibility boundary.
- Removing a legacy procflow implementation, and later removing the CLI argument mapping that temporarily accepted its calls, are gated on the conditions in [Legacy Implementation and Converter Removal Gates](#64-legacy-implementation-and-converter-removal-gates). A compatibility adapter MUST NOT become an accidental permanent API.
- Any proposed change that could alter accepted Product definitions, run-script inputs, CLI behavior, processing results, metadata, outputs, or failure behavior MUST be identified as a compatibility risk and reviewed explicitly.

### 6.4. Legacy Implementation and Converter Removal Gates

Existing legacy procflows MUST NOT be removed until all of the following conditions are satisfied:

- legacy procflow calls execute through OBP, by CLI argument mapping and Product conversion
- every supported legacy call form and argument is mapped or produces a deliberate, documented migration error
- all core and official-package compatibility tests pass through the converted OBP path
- scientific results, required metadata, expected artifact contents, filenames, exit behavior, and other contractual outputs are equivalent
- actionable warnings and migration instructions are available

Support for CLI calls will raise deprecation warnings but will continue to operate through runtime conversion as described in other sections. These are different mechanisms: the Product converter is a conversion routine the CLI calls, while procflow-call support is argument mapping that translates `geoips run --procflow ...` arguments into their OBP equivalents. Later removal of the Product converter and the legacy CLI argument mapping requires:

- official repositories contain no legacy Products or procflow calls except deliberate compatibility/removal fixtures
- conversion tooling has been available for the approved migration period
- the legacy entry points' own deprecation windows have elapsed
- compatibility tests have moved from verifying successful conversion to verifying the documented post-removal behavior

### 6.5. v2.0.0 Legacy Compatibility Test Baseline

The compatibility matrix includes every current integration test from the core `geoips` package and every official GeoIPS plugin package, including `data_fusion`, `geoips_clavrx`, and all other packages identified by the official package inventory. Do not use a hand-selected subset merely because some packages duplicate interfaces or procflows exercised elsewhere.

The inventory phase will discover and record the complete official package set, all legacy run scripts and Products exercised by their integration tests, required test datasets, entry procflows, expected artifacts, comparison outputs, and runtime conversion paths. Tests passing when the baseline is established MUST be treated as release-blocking compatibility cases unless an explicit deprecation or approved compatibility decision removes them from the v2.0.0 contract. Missing infrastructure or unavailable test data must be tracked rather than silently excluding an official package.

The baseline MUST cover every legacy CLI invocation form with its full argument set — `geoips run <procflow>`, `geoips run --procflow <procflow>`, the `run_procflow` and `data_fusion_procflow` executables, and the `ob` and `obp` aliases — because the compatibility constraint freezes arguments rather than only call forms.

`run_procflow` and `data_fusion_procflow` MUST become thin wrappers around `geoips run` that raise a deprecation warning. Test scripts MUST NOT invoke them; scripts that do MUST be migrated to `geoips run`, leaving those two forms verified by dedicated compatibility cases rather than by the integration suite at large.

### 6.6. Argument Standardization and Conduits

For planning purposes, a conduit is a compatibility-oriented argument-wiring adapter, not simply another spelling for an argument. The current conduit registry maps an upstream plugin kind to:

1. the downstream keyword expected by existing plugins, and
2. an extractor that obtains or transforms that value from the upstream DataTree node.

This lets a DataTree/OBP execution model call plugins whose established signatures use bespoke arguments such as `xarray_obj`, `area_def`, `mpl_colors_info`, or `output_filenames`. Additional compatibility layers may then translate a conduit keyword to a legacy call signature. Current examples include positional-name aliases from `data`, `input_xarray`, and `xobj` to `xarray_obj`, and an output-formatter translation from `output_filenames` to `output_fnames`.

The target *Specifications* should distinguish four concepts for every argument:

- the standardized semantic argument and meaning
- the canonical v2.0.0 public name
- conduit source, extraction, and precedence behavior
- accepted legacy aliases or interface-specific translations

Conduits and aliases are related, but they MUST NOT be documented as synonymous. The deprecation strategy MUST retire individual legacy names or adapters only when their user-facing compatibility role has a validated replacement. DataTree-native plugins may not require conduit entries, so the registry may shrink as migration proceeds without requiring the standardized semantic contract to change.

Conduits are core-only implementation machinery. External packages MUST NOT mutate, replace, or register entries in the conduit registry. The registry and its entry structure will be documented for GeoIPS core contributors so they can diagnose and correct bindings, but that documentation does not make it an external extension API. Observable binding behavior remains the public developer contract; registry location, helper names, and internal invocation mechanics remain private.

Every argument a plugin accepts MUST be suppliable explicitly. Conduits are a convenience that derives a value from an upstream step when the caller does not provide one; no argument is reachable only through a conduit.

A plugin accepts the same inputs regardless of how it is invoked. Where an interface defines a conversion from a supplied type to the type its plugins implement, that conversion applies whether the value arrives from a workflow step, a conduit, or a direct call.

An explicitly supplied canonical argument takes precedence over a conduit-derived value, and each derived argument has exactly one authorized upstream plugin kind. The remaining `depends_on`, implicit conduit-selection, missing-source, and unused-result semantics are not approved; see [Tabled Design Topic: `depends_on` and Conduit Resolution](#8-tabled-design-topic-depends_on-and-conduit-resolution).

The intended direction is:

1. Define one canonical argument name and semantic contract for each standardized value.
2. Use the canonical names in new plugin APIs, workflow schemas, examples, and documentation.
3. Keep differing legacy names out of future-facing signatures where practical; accept them through conduits, aliases, normalization hooks, or other compatibility adapters.
4. Register every noncanonical accepted name as a deprecation, including its affected plugins, compatibility mechanism, replacement, warning behavior, and removal criteria.
5. Remove a legacy name only after legacy products and run scripts can be translated to the canonical contract and the approved deprecation window has elapsed.

Standardization MUST cover meaning, cardinality, type, units, default behavior, and precedence in addition to spelling. Two arguments with similar names MUST NOT be merged unless they represent the same semantic value. Likewise, aliases MUST NOT silently accept ambiguous combinations: the *Specification* MUST define conflict detection and which input, if any, takes precedence during the compatibility period.

Argument inventory and grouping MUST also identify the upstream plugin kind from which a derived value may be collected. Each derived canonical argument has exactly one authorized upstream plugin kind. If the same argument appears to be derivable from multiple plugin kinds, the semantic grouping or plugin model MUST be reconsidered rather than adding cross-kind precedence.

Canonicalization MUST avoid unnecessary compatibility churn. Established GeoIPS abbreviations can remain canonical when they are understood, unambiguous, and semantically consistent. Do not create a deprecation solely to expand an abbreviation or modernize a longstanding spelling. A rename should correct a substantive inconsistency, ambiguity, semantic mismatch, or incompatibility with the standardized contract, and its benefit MUST justify the migration cost.

Canonical names are uniform across interfaces and families whenever they represent the same semantic value. Legacy signature differences alone do not justify different canonical names. Select the canonical form using current usage, clarity, and migration cost; the selected form may be an established abbreviation. Different canonical names are permitted only when the values differ substantively in semantics, units, cardinality, lifecycle, or authorized upstream kind, and the distinction MUST be recorded in the canonical argument matrix.

Argument compatibility uses the canonical contract as an internal pivot with three stages:

1. **Ingress normalization:** deprecated caller names from scripts, workflows, Products, CLI conversion, or other user-facing inputs are translated to canonical names and emit their registered deprecation warning.
2. **Canonical resolution and validation:** explicit values and conduit-derived values are resolved and validated using only canonical argument names.
3. **Legacy invocation adaptation:** immediately before calling an unmigrated plugin, a core/interface adapter translates canonical arguments into the legacy parameter names that plugin still implements.

Legacy-to-canonical and canonical-to-legacy translations MUST share one compatibility mapping so their relationships cannot drift. The behavior is intentionally asymmetric: legacy caller input warns, while a user supplying the canonical name does not receive a warning merely because an internal adapter must invoke a legacy plugin. Plugin migration status may instead produce a developer-facing warning or conformance-gap issue.

Migrated plugins receive canonical arguments. Unmigrated plugins receive legacy parameters only at the final invocation boundary. Workflows, conduits, validation, scripting state, and documentation remain canonical. If canonical and deprecated caller forms are supplied together, normalization raises a conflict error rather than choosing silently. Output and DataTree conversion remain separate from argument-name translation.

## 7. Preliminary Interface Inventory

The current source tree contains the following apparent registered class-based interfaces. This list must be verified against runtime interface discovery and the plugin registry before it is considered final.

- Algorithms
- Colormappers
- Coverage checkers
- Databases
- Filename formatters
- Interpolators
- Output checkers
- Output formatters
- Procflows
- Readers
- Sector adjusters
- Sector metadata generators
- Sector spec generators
- Title formatters
- Validators

The inventory phase must also record interfaces that are deprecated, transitional, internal-only, or intentionally excluded.

### 7.1. Target v2.0.0 Interfaces Not Yet in the Current Inventory

The v2.0.0 *Specification* set will also define two new class-based interfaces:

- `SplitOperators`
- `JoinOperators`

Neither is implemented today. In the current code, `split` and `join` are reserved scaffolding kinds: `SCAFFOLD_KINDS` in `geoips/pydantic_models/v1/workflows.py` accepts them during schema validation and defers them to workflow orchestration rather than resolving them through the plugin registry. Promoting them to registered class-based interfaces is therefore a change in kind — from orchestration scaffolding to resolved plugins — and brings with it plugin resolution, argument models, registry entries, and kind naming under the shared Lexeme rules. The *Specifications* must state that transition explicitly rather than describing these interfaces as though they already exist.

Their exact class names, registry names, argument contracts, and DataTree semantics must be established during specification work. Both produce data-bearing steps because they reorganize or combine processing datasets. They must be included in the coverage matrix, with missing or partial runtime implementations tracked in conformance-gap issues.

When a join combines datasets along time, the new `time` coordinate takes each input's `start_datetime` as its value, and a `time_bnds` bounds variable carries each input's `start_datetime` and `end_datetime` pair. This follows the CF bounds convention, so the interval each observation covers survives the join rather than collapsing to an instant — a geostationary full-disk scan spans minutes, and that span is not recoverable once discarded. The joined dataset's own `start_datetime` and `end_datetime` are the minimum and maximum across its inputs.

Two cases are deliberately left to the JoinOperators *Specification*. Inputs that already carry a `time` coordinate make the operation a concatenation along an existing dimension rather than construction of a new one, with different validation; a mixed set where only some inputs carry one likely warrants rejection. Inputs with overlapping extents are legitimate — an ABI mesoscale sector overlapping a full disk, or two platforms viewing concurrently — but produce a non-monotonic `time` coordinate, which silently breaks selection and interpolation in xarray. Neither is resolved here.

At the planning level, split operators reorganize data into declared branches or groups, while join operators combine selected inputs and may construct new dimensions. Both use the standard step/dataset hierarchy, preserve provenance, identify contributing steps, and define structural requirements without assuming scientific compatibility. Join operators MUST validate dimensions and coordinates and MAY check conflicting declared units. Final registry/class names, the migration path from the current scaffolding kinds, canonical arguments, branch semantics, dataset naming, metadata propagation, errors, retention, and compatibility behavior are explicit deliverables of their interface *Specifications* rather than prerequisites for this plan.

## 8. Tabled Design Topic: `depends_on` and Conduit Resolution

The larger GeoIPS team will decide this behavior separately. Do not treat the candidate behavior as normative or begin implementation work from it. When the team returns a decision, complete this investigation as needed:

1. Trace scripting calls from script-tree initialization through `BaseClassPlugin` conduit extraction and result attachment.
2. Construct scripting examples with repeated data-bearing, sector, and filename-formatter steps and identify exactly which prior result supplies each conduit.
3. Test whether scripting selects the most recent matching kind, how explicit arguments interact with that selection, and what happens when a required kind is missing.
4. Compare those results with OBP workflow validation, implicit `depends_on` injection, topological ordering, upstream collection, and conduit extraction.
5. Evaluate a DAG model where omitted dependencies create implicit edges to the most recent step required for each conduit, while explicit `depends_on` entries replace only automatically selected sources of the same kind.
6. Determine how required conduits are declared so the DAG can be composed before runtime.
7. Define unused-result warnings and missing-required-conduit errors.
8. Create conformance-gap issues for confirmed current/target discrepancies and update the normative *Specifications* from the approved team decision.

Known evidence retained for that discussion: current OBP defaults a missing `depends_on` to the immediately previous step and collects only resolved dependency nodes. The focused two-sector check produced `second` for implicit dependency and `first` for `depends_on: ["first"]`; this does not establish the broader per-conduit behavior.

**New direction under active discussion:** The team is exploring a formulation in which a container object — accessible by all steps — holds the root DataTree, provides methods for interacting with its contents, and is visible to every plugin when it is called so the plugin can attach its own output. Under this model, explicit `depends_on` declarations may become optional or take on a different role: steps would query the container for upstream results rather than receiving a pre-collected subtree. This has unresolved implications for topological ordering, conduit resolution, unused-result detection, DAG composability before runtime, and the relationship between scripting and OBP execution. Investigation items 1–8 above should be revisited once the container model is more fully defined and the team has decided its effect on dependency semantics.

This discussion also governs the workflow terminology question. Two distinct things currently share the name:

- `workflows`, a registered **YAML-based** plugin interface whose plugins are *Specification* artifacts defining an ordered series of steps. This is what exists today.
- A possible internal workflow **container object** as described above, which would be runtime machinery rather than a plugin.

The datatree spec conflates these in its §4.1, §4.7, and §15.2. Do not resolve the conflation, rename either concept, or specify the container object until the team finalizes this discussion. Until then, *Specification* pages MUST refer to the YAML-based `workflows` interface when they mean the registered plugin interface, and MUST NOT describe an internal container object as though it were a registered class-based interface.

## 9. Tabled Design Topic: Data Time Attribute Naming

Execution timing has been disambiguated to `execution_start_time` and `execution_end_time`. Whether the data side should be renamed to match — `data_start_time` and `data_end_time` — is left to the group.

**The case for renaming.** The pair would be symmetric, and neither name would be the unqualified default that a reader has to learn a convention to interpret. `data_start_time` teaches itself; `start_datetime` does not.

**The case against.** `start_datetime` and `end_datetime` are an established GeoIPS convention with roughly 409 usages in core, plus every official plugin package that touches reader attributes. Once `start_time` no longer competes with it, `start_datetime` is unambiguous — which is exactly the situation the canonical-argument guidance describes when it says established names can remain canonical, and that a rename must justify its migration cost.

**Scope, if approved.** The keys do not appear in YAML plugins, so no user-authored configuration breaks. Affected surfaces are internal Python attributes, filename formatter modules, and test fixtures. A rename would be a deprecation-register entry requiring a migration path, alias acceptance during the compatibility window, and a removal schedule — not a mechanical edit.

**A third option.** `time_coverage_start` and `time_coverage_end` are the ACDD names for exactly this concept. Unlike the other two candidates they are not a GeoIPS invention, and GeoIPS already touches them on both ends: `geoips/interfaces/class_based/bases/readers.py:247` reads them from GOES and ABI files alongside other ACDD attributes before storing the values under GeoIPS names, and `windspeed_awips2_formatter.py:307` declares `Conventions: CF-1.6` on output. Adopting them would remove an existing translation rather than add one, and follows the CF-compliance principle in the requirements for *Specification* pages. Against that: the migration cost matches `data_start_time`, the names are longer, and they sit awkwardly beside `execution_start_time`. Only one reader family has been confirmed to supply them; whether other source formats do is unchecked.

**Scope beyond the code.** A rename is not only a code migration. These attribute names are now written into the *Specifications* themselves — the dataset-level requirement in the reconciliation section, the dimensions and composition example, and the join operator's temporal construction rule all name them explicitly. Whichever way this is decided, those *Specification* passages change with the code, and any interface pages drafted before the decision will need revisiting.

**Nothing is decided here.** `start_datetime` and `end_datetime` remain canonical for data collection and valid time. They are the established convention, roughly 409 usages in core plus external packages, and changing them requires a deprecation with a migration path and warning window rather than an edit. That cost is the reason to decide deliberately rather than quickly, not a reason to avoid deciding.

## 10. Tabled Design Topic: Dynamic Sector Interface Consolidation

Three Plugin interfaces cover dynamic sectors today, and they are three sequential stages of
one operation: parse a source, build a sector from it, adjust the result.

| Interface | Signature | Stage |
| --- | --- | --- |
| `sector_metadata_generators` | `call(trackfile_name, allowed_aid_types=None)` | Parse a trackfile into storm metadata |
| `sector_spec_generators` | `call(area_id, long_description, clat, clon, projection, pixel_width, pixel_height, num_samples, num_lines)` | Build an `AreaDefinition` from a center and shape |
| `sector_adjusters` | — | Adjust an existing sector |

The proposal is to consolidate them into a `DynamicSectors` Plugin interface with an
associated `DynamicSectorConfigs` interface. **Nothing here is decided.** The interfaces are
not yet well enough understood to commit to a shape.

**What was established while scoping it.** Five plugins implement these interfaces in core:
four metadata generators (families `tc` and `volc`) and one spec generator (family
`area_definition`). `sector_adjusters` has no implementations at all — none in core, and none
in `recenter_tc` or `data_fusion`. It is referenced from the legacy procflows and from CLI
help text, but nothing implements it. Whether it is vestigial should be confirmed against
plugin packages beyond those two before any consolidation is designed.

**The difficulty is in the callers, not the plugins.** Five plugins is a small surface, but
the call sites live in `single_source.py`, `config_based.py`, and `sector_utils/` — the legacy
procflows being retired in favour of OBP. Consolidating before that retirement means
rewriting code scheduled for deletion.

**One shape worth considering when this is taken up:** a `DynamicSectors` Plugin per source
type, where `call()` runs the whole pipeline and `DynamicSectorConfigs` supplies the
parameters — which trackfile, which projection, resolution, shape, and any adjustment. That
matches how the interfaces are used, since a caller wants a sector for a storm rather than
three coordinated calls. It would also collapse the families: `tc` and `volc` become plugin
names, and `area_definition` disappears because building the area definition becomes an
internal step.

Until this is decided, the three interfaces keep their current names and are excluded from
the Plugin and PluginConfig renaming.

## 11. Tabled Governance Topic: Deprecation Approval and Timing

The group will decide minimum warning windows and removal timing separately using its established responsibility and approval processes. Do not assume that removal waits for v3.0.0; GeoIPS may remove deprecated behavior within the v2 release series after the approved warning window, migration readiness criteria, and user-facing compatibility requirements are satisfied. Existing deprecations without an approved schedule remain tracked as schedule pending.

## 12. Documentation Location and Format

The *Specifications* will be developed separately from the existing user-facing interface documentation under the following developer-guide hierarchy:

```text
docs/source/devguide/
├── deprecations.md
└── plugin-specifications/
    ├── index.md
    └── class-based/
        ├── index.md
        ├── base-classes.md
        └── interfaces/
            ├── algorithms.md
            ├── readers.md
            └── ...
```

All new documents in this effort will use MyST Markdown (`.md`). More broadly, MyST is the preferred format for new GeoIPS documentation because the project intends to migrate its documentation to MyST over time. This task does not include mechanically converting unrelated existing reStructuredText pages.

During *Specification* development, the existing pages under `docs/source/functionality/interfaces/class_based/` remain separate. As part of v2.0.0 release preparation, the approved developer *Specifications* will be distilled into user-facing documentation that replaces or substantially revises those existing pages.

## 13. Required Content for Every Interface Specification

Each interface page must answer the following questions explicitly, even when the answer is "none," "not applicable," or "not yet defined":

1. What `kind` token does a workflow step use to invoke this interface, and how does that token resolve to the interface? Plugin kinds are the singular form of the registered interface name, resolved through the project's shared Lexeme pluralization rules; the page MUST state its kind token and MUST NOT define a competing naming rule.
2. Does the interface produce data-bearing or non-data-bearing steps, and what semantic result establishes that classification? Does the current DataTree representation conform to the target classification?
3. Which data-bearing steps, data nodes, or metadata must exist before this step runs?
4. What output data and metadata does the step add to, replace in, or remove from the returned data tree? How are variables grouped into coordinate-compatible datasets, how are output `dataset_id` values determined, and does the operation preserve, split, merge, or replace its input dataset groups? What units are required, accepted, preserved, converted, or produced for variables and coordinates?
5. What positional or other non-data arguments are accepted?
6. What keyword arguments are accepted, including defaults and required/optional status? Which form is canonical for future-facing plugins, and which accepted forms are deprecated compatibility inputs?
7. What argument conduits exist for the interface, where do their values originate, and how are collisions, missing values, and overrides handled? Which name is canonical, and which names are conduit bindings, legacy aliases, or interface-specific translations?
8. What deprecated positional arguments or keyword arguments remain accepted?
9. For each deprecated argument, what is the current warning/compatibility behavior and the target deprecation schedule and migration strategy?
10. Where do this interface's plugins sit on the family/`data_tree` migration axis, and which plugins remain unmigrated? In the current implementation the presence of a `family` attribute is the legacy marker and `data_tree=False` selects the unwrap/rewrap conversion path, while `data_tree=True` with no `family` is the DataTree-native target state. Because families are deprecated in v2.0.0 and retained only for legacy support, each remaining family-bearing plugin is a conformance gap and a deprecation-register entry, not a future-facing contract feature.
11. Does the current alpha implementation conform to this part of the v2.0.0 contract? If not, what conformance-gap issue tracks the difference?
12. Which parts of the contract are required to keep legacy products and run scripts working, and how do they bridge to workflows, CLI calls, and the OBP-native contract?
13. Does the interface's output diverge from CF conventions?
14. What dataset identity metadata does the interface produce?
15. What dimensions do its datasets carry?
16. What retention behavior applies to its data?

Each page should additionally document, where relevant:

- purpose and common use cases
- families still accepted for legacy support, their call signatures, and their deprecation status; families are not part of the future-facing v2.0.0 contract
- base plugin class and inheritance relationship, distinguishing interface-level base classes from family/legacy scaffolding and from shared implementation helpers
- input and output types outside the DataTree wrapper
- input/output unit contracts and unit metadata behavior
- lifecycle hooks and interface-specific conversions
- required attributes and plugin registration requirements
- exceptions, validation rules, and failure modes
- interaction with legacy procflows versus OBP
- user-facing compatibility requirements for legacy products and run scripts
- a minimal example and links to representative production plugins
- known limitations, open design questions, and compatibility notes

## 14. Standard Page Outline

Use the following starting outline for the base-class page and adapt it only when a section is genuinely not applicable:

1. Overview and audience
2. Normative language
3. Class hierarchy and division of responsibilities
4. `BaseClassInterface` contract
   - attributes
   - methods
   - discovery and validation
5. `BaseClassPlugin` contract
   - required attributes
   - inherited attributes
   - required subclass methods
   - inherited public methods
   - lifecycle hooks and invocation sequence
6. DataTree and native-data conversion
7. OBP integration and argument conduits
8. Plugin registration and lookup
9. Minimal implementation example
10. Validation and failure modes
11. Compatibility and deprecations
12. See also
13. Reference links

Use the following starting outline for each interface page:

1. Overview
2. Normative language
3. Plugin kind and registration identity
4. Step classification
5. Prerequisites and upstream data
6. Returned data-tree changes
   - data
   - metadata
   - replacement or retention behavior
7. Canonical argument contract
8. Non-data positional and keyword arguments
9. Conduits, legacy aliases, and compatibility translations
10. Lifecycle and conversion behavior
11. Family and `data_tree` migration status
    - DataTree-native target contract
    - families retained for legacy support and their deprecation status
12. Required plugin implementation
13. Examples
14. Deprecated arguments, migration strategy, and schedule
15. Current implementation status and conformance-issue links
16. Errors, validation, and edge cases
17. See also
18. Reference links

The `Reference links` section belongs at the bottom of every draft from its first commit. It should initially contain the code, tests, existing documentation, issues/design records, and representative plugins expected to support the page. Links may be refined as drafting proceeds, but unsupported claims must not be added simply to fill a heading.

## 15. Deprecation Specification Outline

The first *Specification* drafted will be `docs/source/devguide/deprecations.md`. Its initial outline will be:

1. Purpose, scope, and normative language
2. Deprecation principles and compatibility constraints
3. Lifecycle states
4. Typed central registry
   - package/module layout
   - `DeprecationRecord` contract
   - stable ID format
   - immutability and core ownership
5. Required record fields
6. `warn_deprecated()` API
   - warning category and message construction
   - stack level and call-site reporting
   - repeated-warning behavior
7. Distributed compatibility adapters and normalization
8. Schedule and migration requirements
9. Existing versus newly proposed deprecations
10. Validation and test requirements
11. Documentation generation and reporting
12. Pending governance decisions
13. Examples
14. Reference links

As with every *Specification*, create only this outline and its bottom reference-links section first, then fill it incrementally. Approval authority and minimum warning windows may remain clearly marked pending group decisions; they do not prevent specifying the registry and warning mechanics.

## 16. Per-Document Working Method

Every *Specification* document will be developed as a small, reviewable unit:

1. **Create the skeleton.** Add the agreed outline and a bottom-of-page reference-links section. Do not fill the full page during this step.
2. **Build an evidence map.** For every planned section, identify relevant source classes, tests, runtime registry information, existing docs, and representative plugins.
3. **Resolve contract questions.** Record ambiguities in the applicable *Specification* or tabled-topic section instead of presenting inferred behavior as settled fact. Decide the desired v2.0.0 behavior; do not simply copy accidental alpha behavior into the contract.
4. **Draft one coherent section group.** Prefer a small group such as step inputs/outputs or arguments/conduits rather than filling all headings at once.
5. **Add or verify examples.** Prefer concise examples based on real plugins. Test code where practical and state when an example is illustrative rather than executable.
6. **Review terminology and links.** Reuse canonical terms and cross-reference existing explanations instead of recreating them.
7. **Reconcile implementation.** Compare every normative requirement with current code and tests, then create or update gap and deprecation entries for differences.
8. **Validate the page.** Run the validation commands recorded in Phase 0, then run any focused tests or introspection needed to verify signatures and examples.
9. **Update this plan.** Mark progress, record decisions, and select the next small unit.

## 17. Example Source Policy

Use example sources in this order:

1. implementations and tests in the core `geoips` repository
2. purpose-built examples in `geoips_plugin_example`
3. templates in `template_basic_plugin`
4. other officially maintained GeoIPS plugin packages only when the preferred sources do not demonstrate the required behavior

Normative requirements and minimal examples must remain understandable within the *Specification* itself. External packages provide supplemental realistic examples and must not be the sole evidence for required behavior. When exact source matters, use a versioned tag or commit link. If no durable example exists, prefer adding a small tested example to `geoips_plugin_example` during later implementation work.

External examples must support the relevant GeoIPS v2 behavior, have applicable tests or other verification, use public or understandable synthetic inputs, and demonstrate the target contract rather than behavior being deprecated. Do not make eligibility depend on identified package maintainers or archived/experimental/retirement metadata: GeoIPS does not currently maintain those classifications. Private/internal packages and incidental local workspace copies are not acceptable published references.

## 18. Evidence and Accuracy Rules

- The approved v2.0.0 design is authoritative for the *Specification*. Treat executable code and focused tests as evidence of current alpha behavior and conformance, not as the automatic definition of the contract.
- If desired v2.0.0 behavior is not yet approved, record it as an open design decision; do not describe either the current behavior or a preferred alternative as normative.
- Use runtime introspection to supplement source reading, especially for inherited signatures and registry discovery.
- Trace GeoIPS subclasses into `pluginify` when behavior is inherited; do not attribute inherited behavior to GeoIPS without qualification.
- Distinguish public contract from implementation detail. Internal helpers should appear only when plugin or interface authors must understand their effects.
- Do not infer a deprecation deadline from a comment or warning alone. Record the current behavior, first-known announcement, source of the proposal, compatibility impact, replacement, migration steps, milestones, owner, and approval status.
- New deprecation candidates discovered during research must enter the same review process as existing deprecations and must not be presented as approved merely because the current API is inconvenient or inconsistent.
- When code, tests, and existing docs disagree, record the conflict before choosing which behavior to specify.
- Use stable Sphinx/MyST cross-references for internal documentation and source links only when source-level detail materially helps the reader.

## 19. Definition of Done for One Specification Page

A page is complete when:

- [ ] Its audience and scope are clear.
- [ ] It includes the BCP 14 notice and uses uppercase requirement keywords only for normative contract requirements.
- [ ] Every **SHOULD** or **SHOULD NOT** requirement explains the consequences of an exception, and every **MAY** requirement defines relevant interoperability behavior.
- [ ] Every standard heading is completed or explicitly marked not applicable.
- [ ] Every required interface question is answered.
- [ ] Common and family-specific behavior are distinguishable.
- [ ] Arguments include names, meanings, types where useful, defaults, required status, and value sources.
- [ ] Canonical arguments are recorded in the shared matrix and use consistent semantics across applicable interfaces and families.
- [ ] Every noncanonical accepted argument is isolated to a compatibility boundary, absent from future-facing examples, and linked to a deprecation entry.
- [ ] Canonical/deprecated argument conflicts and precedence are specified and tested or tracked in conformance-gap issues.
- [ ] Data-tree inputs and outputs identify paths and metadata keys precisely where the v2.0.0 contract defines them.
- [ ] The interface's `kind` token is stated and matches the shared kind-to-interface resolution rule.
- [ ] The interface's position on the family/`data_tree` migration axis is stated, families retained for legacy support are marked deprecated rather than presented as contract features, and each unmigrated plugin has a conformance-gap issue and a deprecation-register entry.
- [ ] The interface's data-bearing or non-data-bearing classification is stated and justified by its semantic result rather than its implementation format.
- [ ] Output variables are assigned to coordinate-compatible dataset groups, and the interface defines how output `dataset_id` values are selected.
- [ ] Existing interface-specific unit locations, accepted inputs, outputs, and behavior are described where applicable without establishing new shared v2.0.0 handling.
- [ ] Shared unit handling and automatic conversion are identified as v2.1-or-later work, not v2.0.0 conformance requirements.
- [ ] Any preservation, splitting, merging, replacement, or removal of input dataset groups is documented.
- [ ] Output formatter *Specifications* document the non-data-bearing classification, identify what metadata is recorded in step attrs (written paths, checksums, mime types), and include a minimal example.
- [ ] No requirement or example places a data variable on the workflow root; root content is limited to step children and workflow-level attributes.
- [ ] Conduits explain source, binding, precedence, missing-value behavior, and examples.
- [ ] Any CF divergence is stated with its reason, or the page confirms there is none.
- [ ] Dataset identity metadata is stated or marked not applicable.
- [ ] Dimension behavior is stated or marked not applicable.
- [ ] Retention behavior is stated or marked not applicable.
- [ ] Deprecations distinguish current support from proposed removal.
- [ ] At least one useful example or a justified statement that no example is appropriate is present.
- [ ] Claims are backed by the reference-links section or an approved design decision.
- [ ] Normative statements describe the v2.0.0 target rather than merely restating alpha behavior.
- [ ] Current implementation conformance has been checked and all confirmed differences have conformance-gap issues, dispositions, and release-blocking classifications.
- [ ] Existing and newly discovered deprecations appear in the deprecation register with migration guidance and approved or clearly proposed schedules.
- [ ] Internal cross-references resolve and external links are appropriate.
- [ ] Relevant documentation checks pass.
- [ ] Progress and decisions are updated in this plan.

## 20. Tracking Record Templates

Use these fields so discoveries are recorded consistently. Confirmed conformance gaps live in GitHub; deprecations live in the typed core registry.

### 20.1. Conformance-Gap Issue Template

Conformance gaps are filed using the repository issue template at
`.github/ISSUE_TEMPLATE/v2-spec-gap.md`, which is the single source of truth for the
required fields. It applies the `v2-spec-gap` label automatically.

The template carries only fields GitHub has no native equivalent for. Ownership, schedule,
open/closed state, and release-blocking status are recorded using GitHub's own assignee,
milestone, issue-state, and label features rather than as prose in the issue body, because
body text duplicating those fields drifts out of date the first time one of them changes
without a matching edit.

### 20.2. Deprecation Entry

| Field | Meaning |
| --- | --- |
| Deprecation ID | Stable identifier, for example `CBP-DEP-001` |
| API/behavior | Argument, keyword, family, interface, method, or compatibility behavior |
| Discovery class | Existing/previously announced or newly discovered/proposed |
| Scope | Affected interfaces, families, plugins, and users |
| Rationale | Why continued support is undesirable |
| Replacement | Target API or behavior |
| Migration strategy | Concrete user/plugin-author steps and supporting documentation |
| Compatibility behavior | What remains accepted and how it is interpreted |
| Warning strategy | Warning category, message, trigger point, and test coverage |
| Schedule | Announcement, warning, removal, and cleanup versions or milestones |
| Earliest known notice | Release note, warning, issue, or other evidence |
| Owner and approval | Responsible party, decision authority, and approval state |
| Dependencies/risks | Plugin ecosystem impact and prerequisites for removal |
| Migration readiness | Product-to-workflow and script-to-CLI replacement status and exit criteria |
| Related bridge lifecycle | Transitional converter/adapter introduction, support, and retirement criteria |
| Argument role | Semantic argument, canonical name, conduit binding, alias, or translation |
| Authorized upstream kind | The one plugin kind permitted to provide a derived value |
| Canonical replacement | Standardized name and full semantic contract |
| Ingress translation | Deprecated caller name to canonical name, including warning ID |
| Invocation translation | Canonical name to an unmigrated plugin's legacy parameter |
| Conflict behavior | Result when canonical and deprecated names are supplied together |
| Status | Candidate, proposed, approved, warning, removed, withdrawn, or complete |

No schedule is approved merely by being entered in the register. Conversely, an existing runtime warning without a recorded migration path and schedule is an incomplete deprecation that must be resolved before the documentation effort is complete.

## 21. Execution Phases

### 21.1. Phase 0: Confirm Documentation Architecture

- [x] Decide the final location and naming convention for the *Specification* pages.
- [x] Decide whether the base-class contract is one page or separate interface/plugin pages with a shared landing page.
- [x] Decide whether existing interface pages will be expanded in place or whether new *Specification* pages will be linked from them.
- [x] Select MyST Markdown as the format for all new *Specification* documents.
- [ ] Establish canonical terms for "data-bearing step," "non-data-bearing step," "argument conduit," "returned data tree," and "family."
- [ ] Record the `kind`-to-interface resolution rule so every interface page states its kind token consistently. Plugin kinds are the singular form of a registered interface name and span both class-based and YAML-based interfaces; `split` and `join` are currently reserved scaffolding kinds that bypass plugin resolution entirely.
- [ ] Define the classification rule for intermediate classes under `geoips/interfaces/class_based/bases/`. Each is either family/legacy scaffolding, documented only as deprecated compatibility and registered in the deprecation register, or shared implementation reuse that is explicitly out of *Specification* scope. Record the rule so per-interface pages do not decide this ad hoc.
- [ ] Record how family deprecation and the `data_tree` migration relate, so pages treat them as one migration axis rather than two independent topics.
- [ ] Define the standardized argument vocabulary and distinguish semantic argument names, canonical public names, conduit bindings, legacy aliases, and translations.
- [ ] Define a canonical argument matrix covering name, meaning, type, cardinality, units, default, required status, valid values, precedence, and applicable interfaces/families, plus the single authorized upstream plugin kind for derived values.
- [ ] Define rules preventing new plugins and examples from introducing noncanonical argument names without an approved *Specification* change.
- [x] Establish BCP 14 requirement-language conventions and rules for distinguishing normative requirements from rationale, examples, compatibility notes, and conformance-gap issues.
- [ ] Define the `v2-spec-gap` GitHub issue template, labels, milestone/project workflow, and criteria that make a gap release-blocking for v2.0.0.
- [ ] Define the deprecation lifecycle, minimum notice periods or release milestones, approval authority, warning requirements, migration-documentation requirements, and exceptions process.
- [ ] Design the central core deprecation registry, stable deprecation IDs, lookup/warning helpers, and validation linking distributed compatibility code to registry entries.
- [ ] Define measurable readiness criteria for removing direct legacy-procflow support, including legacy-product-to-workflow conversion, run-script-to-CLI conversion, OBP feature parity, validation, ecosystem adoption, and an agreed compatibility window.
- [ ] Record documentation ownership/audience boundaries among functionality docs, developer guide, architecture docs, tutorials, and API reference. Extend the existing `docs/source/architecture/documentation/where-to-put.rst` guidance rather than creating a parallel rule set.
- [ ] Record the exact validation commands every page runs, so all pages are checked identically. Starting candidates: `./docs/build_docs.sh . geoips` for the documentation build, `geoips lint` for linting, and the repository's cspell configuration for spelling. Confirm the real invocations and any required options.
- [ ] Adopt MyST style conventions for new pages, chosen so they remain valid as the remaining reStructuredText documentation migrates: - `(label)=` targets immediately before headings, with a page-level target matching the filename stem - the `{ref}` role for internal cross-references and plain Markdown links only for external URLs, because `{ref}` is what `:ref:` converts to and is the only form that resolves while reStructuredText and MyST pages coexist - colon-fenced directives (`:::{note}`) for prose-bearing directives and backtick-fenced directives for content-bearing ones such as `{mermaid}` and `{contents}` - ATX headings only, one H1 per page, sentence case, no skipped levels - GitHub-flavored pipe tables - semantic line breaks (one sentence or clause per line) rather than a fixed column, so requirement-level changes produce reviewable diffs

**Exit criterion:** page architecture and terminology are agreed before *Specification* content is drafted.

### 21.2. Phase 1: Draft the Deprecation Specification

- [ ] Create `docs/source/devguide/deprecations.md` in MyST.
- [ ] Add only the approved outline and initial reference links.
- [ ] Inventory existing warning helpers, warning categories, deprecation modules, compatibility adapters, release notes, and tests.
- [ ] Specify a lightweight typed `DeprecationRecord` and immutable core registry.
- [ ] Specify stable IDs and the `warn_deprecated()` helper contract.
- [ ] Specify how distributed warning and normalization sites reference registry entries.
- [ ] Define validation, testing, and documentation-generation requirements.
- [ ] Mark approval authority and warning-window policy as pending group decisions.
- [ ] Compare the *Specification* with current implementation, create confirmed conformance-gap issues, and seed deprecation tracking without implementing runtime changes in this documentation task.
- [ ] Review and validate the completed *Specification*.

**Exit criterion:** later interface *Specifications* can register and describe deprecations consistently without inventing page-specific tracking or warning behavior.

### 21.3. Phase 2: Build and Verify the Interface Inventory

- [ ] Query runtime interface discovery and the plugin registry.
- [ ] Reconcile runtime results with `geoips/interfaces/class_based/` and its `bases/` directory.
- [ ] Add the target `SplitOperators` and `JoinOperators` interfaces to the coverage matrix and record their missing or partial implementations as v2.0.0 gaps.
- [ ] Identify interface families and representative plugins in GeoIPS and maintained plugin packages.
- [ ] Discover the complete set of official GeoIPS plugin packages and inventory every current integration test, explicitly including `data_fusion` and `geoips_clavrx`.
- [ ] Build the legacy compatibility matrix from core and all official-package integration tests, recording run scripts, Products, procflows, test data, expected artifacts, comparison outputs, conversion paths, and release-blocking status.
- [ ] Mark deprecated, transitional, internal, or incomplete interfaces.
- [ ] Classify each class-based interface as data-bearing or non-data-bearing from its semantic result, compare that target with its current DataTree representation, and identify the YAML metadata-only dependencies that configure it.
- [ ] Inventory all existing deprecation warnings, compatibility shims, deprecated arguments/kwargs, deprecated families, and deprecated interfaces in code, tests, release notes, and documentation.
- [ ] Document the current and target runtime path for converting legacy Products into OBP Workflows.
- [ ] Register legacy Products and Product-to-Workflow runtime conversion as related but distinct deprecations with coordinated migration and removal criteria.
- [ ] Specify the automated Product-to-Workflow conversion script, its inputs, generated Workflow output, validation, overwrite/idempotency behavior, diagnostics, and tests.
- [ ] Require the conversion script and runtime conversion to use the same canonical conversion engine and add equivalence tests for representative Products.
- [ ] Inventory legacy procflow call forms and the OBP arguments each one maps to.
- [ ] Register legacy procflow calls and automatic procflow-to-Workflow conversion as related but distinct deprecations with coordinated migration and removal criteria.
- [ ] Inventory conduit bindings, positional alias mappings, interface hook translations, explicit-argument precedence, and fallback/default behavior.
- [ ] Compare direct-dependency collection with candidate latest-relevant-step semantics and create conformance-gap issues only after the target behavior is approved.
- [ ] Trace class-based plugin calls in scripting mode and determine how they find the most recent step satisfying each conduit.
- [ ] Compare scripting and OBP behavior for omitted, partial, and complete `depends_on` declarations.
- [ ] Record the team's decision about implicit per-conduit edges, explicit dependency behavior, and missing-source errors; then specify the approved semantics.
- [ ] Verify that each conduit has exactly one authorized upstream plugin kind; treat any collisions as design problems rather than establishing cross-kind precedence.
- [ ] Specify unused-result warnings and track their implementation separately. Results deliberately retained as workflow outputs are not unused.
- [ ] Map every currently accepted argument to a canonical argument, a justified interface-specific argument, or a deprecation candidate.
- [ ] Group derived arguments by their authorized upstream plugin kind and flag any argument that appears satisfiable by multiple kinds as a design conflict.
- [ ] Inventory both ingress legacy-to-canonical normalization and canonical-to-legacy plugin invocation adapters, ensuring they share one compatibility mapping.
- [ ] Specify conflict errors for simultaneous canonical and deprecated caller forms and asymmetric warning behavior for users versus internal legacy-plugin adaptation.
- [ ] Seed the deprecation register, distinguishing already-announced deprecations from new candidates discovered during this work.
- [ ] Create a coverage matrix mapping each interface to source, tests, existing docs, examples, and an intended *Specification* page.

**Exit criterion:** every registered class-based interface appears exactly once in the coverage matrix, with exclusions explained.

### 21.4. Phase 3: Specify the Common Base Classes

- [ ] Create only the base *Specification* outline and its initial reference links.
- [ ] Map inherited behavior from `pluginify` separately from GeoIPS-defined behavior.
- [ ] Inventory attributes and methods on `BaseClassInterface` and `BaseClassPlugin`.
- [ ] Classify each item as required, optional, inherited, internal, overrideable, or prohibited from override.
- [ ] Document the invocation sequence and pre/post-call hooks.
- [ ] Document DataTree/native conversion, metadata propagation, scripting behavior, and OBP conduit handling.
- [ ] Specify universal workflow/step provenance separately from interface-specific dataset identity metadata.
- [ ] Specify retention policy, explicit request, current state, and decision reason using a compact reason vocabulary.
- [ ] Compare current garbage collection with dataset-child storage under `/<step_id>/<dataset_id>` and create confirmed conformance-gap issues.
- [ ] Add a minimal plugin example and verify it against current registration rules.
- [ ] Compare every base-class requirement against current alpha behavior and create conformance-gap issues without weakening the target *Specification*.
- [ ] Verify that the base-class target contract preserves behavior required by legacy products and run scripts while clearly separating internal procflow compatibility from the OBP-native contract.
- [ ] Cross-link existing authoring and migration documentation.
- [ ] Validate and review the completed base *Specification*.

**Exit criterion:** the common contract is stable enough that interface pages can link to it without restating inherited behavior.

### 21.5. Phase 4: Pilot One Interface Specification

- [ ] Select one representative interface with meaningful data flow, families, conduits, and existing tests. Algorithms or readers are likely candidates; choose only after the inventory is complete.
- [ ] Create the outline and initial reference links only.
- [ ] Complete the evidence map.
- [ ] Fill the page incrementally using the standard outline.
- [ ] Review whether the template adequately distinguishes family-specific behavior.
- [ ] Revise the standard outline and validation checklist based on the pilot.

**Exit criterion:** one accepted interface page establishes the pattern for the remaining pages.

### 21.6. Phase 5: Specify Remaining Interfaces in Small Batches

Work in reviewable batches based on related data flow, while completing and validating one page at a time. The exact grouping is a planning aid, not a required publishing structure.

- [ ] Data ingestion and transformation: readers, algorithms, interpolators.
- [ ] Data composition and branching: split operators and join operators.
- [ ] For split/join pages, begin with outlines and evidence maps before deciding registry names, families, relationship to built-in workflow kinds, or detailed semantics.
- [ ] Specify mandatory join dimension/coordinate validation and its errors, plus any optional declared-unit checks and their warning/error behavior.
- [ ] Sector construction and adjustment: sector metadata generators, sector spec generators, sector adjusters.
- [ ] Visualization and output: colormappers, output formatters, filename formatters, title formatters.
- [ ] Decisions and validation: coverage checkers, validators, output checkers.
- [ ] Services and orchestration: databases and procflows.

For every page in a batch:

- [ ] Create outline and initial reference links.
- [ ] Complete all required interface questions.
- [ ] Separate common behavior from family-specific behavior.
- [ ] Verify arguments and conduits from code and tests.
- [ ] Add or update the canonical argument matrix and record each noncanonical accepted name in the deprecation register.
- [ ] Include appropriate examples.
- [ ] Record deprecations and label unapproved schedules as proposals.
- [ ] Record every confirmed target/current mismatch in a conformance-gap issue.
- [ ] Verify legacy product and run-script compatibility and record any regression risk; do not require preservation of internal procflow APIs unless user-facing support currently depends on them and no replacement exists yet.
- [ ] Validate documentation and links.
- [ ] Update the coverage matrix and progress tracker.
- [ ] Add one release note per pull request under `docs/source/releases/latest/`. Release notes are per-PR, not per-page, so a batch that ships as a single PR needs a single note covering the pages it contains.

**Exit criterion:** every verified interface has a complete, validated *Specification* or an explicitly approved exclusion.

### 21.7. Phase 6: Integrate the Documentation

- [ ] Link the base *Specification* and interface *Specifications* into the interfaces landing page.
- [ ] Add links from the class-based plugins overview and writing guide.
- [ ] Add targeted links from architecture, DataTree, OBP, migration, registry, tutorial, and API-reference pages where useful.
- [ ] Check for conflicting or obsolete statements in existing pages and resolve them in scope rather than silently leaving contradictions.
- [ ] Ensure compatibility notes link to the deprecation registry and implementation discrepancies link to their conformance-gap issues where appropriate.
- [ ] Check navigation labels, anchors, backlinks, and orphan pages.
- [ ] Work the changes recorded in [`datatree_spec_reconciliation.md`](datatree_spec_reconciliation.md) into `docs/source/devguide/datatree-spec.md`: the propagations, the corrections, and the cross-references it should carry rather than restate.

**Exit criterion:** intended audiences can reach the *Specifications* from the places they are most likely to begin, and the datatree spec no longer conflicts with the decisions recorded here.

### 21.8. Phase 7: Final Consistency and Quality Review

- [ ] Run the full documentation build with warnings treated appropriately.
- [ ] Run link and spelling checks supported by the project.
- [ ] Verify public names, signatures, families, and defaults against the current code.
- [ ] Verify every normative requirement has a conformance result and every confirmed mismatch has a conformance-gap issue.
- [ ] Verify all examples and representative-plugin links.
- [ ] Search for required interface questions missing from any page.
- [ ] Review terminology, deprecation language, and data-tree path notation across pages.
- [ ] Obtain maintainer approval for the v2.0.0 contract, release-blocking gap decisions, deprecation schedules, migration strategy, and unresolved design claims.
- [ ] Confirm every release-blocking conformance-gap issue has been resolved or explicitly waived by the responsible release authority before declaring the effort complete.
- [ ] Confirm every pull request in the effort carried its release note under `docs/source/releases/latest/`.

**Exit criterion:** documentation is internally consistent and builds successfully; the v2.0.0 contract is approved; deprecations have approved schedules and migration paths; and all release-blocking gaps are resolved or explicitly waived.

## 22. Progress Tracker

| Deliverable | Status | Notes |
| --- | --- | --- |
| Planning document | Complete | Initial shared plan; specification work not started |
| Documentation architecture | Not started | Phase 0 |
| Deprecation *Specification* | Not started | `docs/source/devguide/deprecations.md`; Phase 1 |
| Verified interface inventory and coverage matrix | Not started | Phase 2 |
| Conformance-gap tracking | Not started | Issue process defined in Phase 0 |
| Deprecation register and strategy | Not started | Specified in Phase 1; populated throughout |
| Datatree spec reconciliation | Drafting | `datatree_spec_reconciliation.md`; worked during Phase 6 |
| Canonical argument matrix | Not started | Defined in Phase 0; populated per interface |
| Base interface/plugin *Specification* | Not started | Phase 3 |
| Pilot interface *Specification* | Not started | Phase 4 |
| Remaining interface *Specifications* | Not started | Phase 5 |
| Cross-document integration | Not started | Phase 6 |
| Final consistency review | Not started | Phase 7 |

Use only these status values: `Not started`, `Outline`, `Researching`, `Drafting`, `Reviewing`, `Blocked`, and `Complete`.

## 23. Initial Planning References

These are starting points for the task. Each future page will maintain its own narrower reference-links section.

- `geoips/interfaces/base.py` — GeoIPS `BaseClassInterface` and interface validation integration.
- `geoips/interfaces/class_based_plugin.py` — `BaseClassPlugin`, lifecycle hooks, DataTree conversion, scripting behavior, and conduit integration.
- `geoips/interfaces/class_based/` — registered interface objects.
- `geoips/interfaces/class_based/bases/` — interface-level base plugin classes and family behavior.
- `geoips/utils/types/obp_conduits.py` — conduit bindings and extraction behavior.
- `geoips/utils/types/script_datatree.py` — scripting DataTree call/result behavior.
- `docs/source/devguide/datatree-spec.md` — current DataTree *Specification*.
- [`datatree_spec_reconciliation.md`](datatree_spec_reconciliation.md) — changes this effort will make to the datatree spec.
- `.github/ISSUE_TEMPLATE/v2-spec-gap.md` — the conformance-gap issue template.
- `docs/dev/spec_plans/check_consistency.py` — internal consistency check for these planning documents.
- `docs/source/functionality/interfaces/index.rst` — interface documentation navigation.
- `docs/source/functionality/interfaces/writing-class-based-plugins.md` — class-based plugin authoring guidance.
- `docs/source/functionality/interfaces/class_based/` — existing per-interface pages.
- `docs/source/functionality/plugins/class-based/index.rst` — class-based plugin overview.
- `docs/source/devguide/converting-module-to-class.md` — migration guidance.
- `docs/source/architecture/plugin-registry.md` and `docs/source/functionality/plugin-registries.md` — registry architecture and usage.
- `tests/` — focused unit, integration, and interface tests supporting current contracts.
- [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) — requirement-level key words.
- [RFC 8174](https://www.rfc-editor.org/rfc/rfc8174) — clarification that BCP 14 key words are normative only when written in uppercase.
