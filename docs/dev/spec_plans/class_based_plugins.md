# GeoIPS Class-Based Plugin Specifications: Plan

## 1. Purpose and Scope

This document plans and tracks the class-based plugin *Specifications*. They are normative target-state documents for GeoIPS v2.0.0, not descriptions of the alpha implementation.

### 1.1. Deliverables

1. A base *Specification* for `BaseClassInterface` and `BaseClassPlugin` ([§8.1](#81-base-class-page)).
2. One page per registered class-based interface, with tested examples from real plugins.
3. A deprecation *Specification* and register ([§11.2](#112-deprecation-entry)).
4. A conformance-gap issue for every confirmed difference between the alpha implementation and the contract, aggregated through a v2.0.0 milestone. Gap types are missing, divergent, ambiguous, obsolete, and test-or-documentation-only. A difference deferred past v2.0.0 is filed the same way and marked not release-blocking.
5. A standardized argument vocabulary. Noncanonical legacy arguments live in conduits or adapters and sit on a deprecation path.
6. The datatree-spec changes in [§13](#13-datatree-spec-reconciliation).
7. Links from indexes and existing pages that do not duplicate tutorial or API-reference material.
8. Build, link, spelling, and example validation.

### 1.2. Out of Scope

Unless a later decision adds them:

- Runtime or public-API changes, and implementing fixes or deprecation machinery. This effort tracks them. Implementation is scheduled separately.
- Rewriting tutorials, generated API reference, or YAML-based *Specifications*.
- Treating `geoips/interfaces/class_based/workflow.py` as an interface unless the inventory finds it registered. It currently appears to be runtime machinery.
- Module-based plugin history beyond migration context.

## 2. Requirement Language

The key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** in this document and the *Specifications* are to be interpreted as described in BCP 14, [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) and [RFC 8174](https://www.rfc-editor.org/rfc/rfc8174), when, and only when, they appear in all capitals.

These words mark normative v2.0.0 requirements only. **MUST** and **MUST NOT** are absolute. **SHOULD** and **SHOULD NOT** permit exceptions, and the *Specification* MUST state or link the consequence of an exception. **MAY** marks optional behavior, and the *Specification* MUST define how implementations that take the option interoperate with those that do not. Do not use **SHALL**, **REQUIRED**, **RECOMMENDED**, or **OPTIONAL**. Lowercase forms carry ordinary meaning. Every keyword names its subject and an observable behavior. A keyword never adds emphasis or marks a task step.

## 3. Records

1. ***Specifications*** state what v2.0.0 MUST provide, directly. A short compatibility note may identify transitional behavior. Remediation belongs in gap issues and the register. A current limitation MUST NOT silently weaken the contract.
2. **Conformance-gap issues** record each confirmed difference between a requirement and the alpha implementation. A wrong requirement changes only by *Specification* approval. Each gap uses the [issue template](#111-conformance-gap-issue), carries the `v2-spec-gap` label, and is classified release-blocking or not. A gap closes only as resolved or as waived by the release authority. Milestone workflow and blocking criteria are Phase 0 work.
3. **Deprecation register.** The target design MUST use a central, machine-readable registry in the core package as the authoritative inventory. The registry holds typed pydantic records, and a `warn_deprecated(deprecation_id, ...)` helper resolves stable IDs and issues consistent warnings. Compatibility code stays near what it adapts but MUST reference a registry entry. Tooling SHOULD generate deprecation tables and reports from the registry. Manual maintenance MAY substitute only under automated validation against the registry. External packages MUST NOT mutate or extend the registry.
4. **Datatree spec reconciliation**, [§13](#13-datatree-spec-reconciliation).

## 4. Specification Model

### 4.1. CF Compliance

GeoIPS datasets are CF compliant in coordinates, variable metadata, and structure. Prefer a CF mechanism, or a convention layered on CF such as ACDD, unless the decision records a reason to diverge. v2.0.0 carries two transitional divergences. Variable-level metadata is optional where CF requires it ([§4.7](#47-units)). Temporal extent uses GeoIPS attribute names rather than ACDD's ([§6.2](#62-data-time-attribute-naming)).

### 4.2. Metadata

The base *Specification* defines universal provenance, which describes execution. Interface *Specifications* define dataset identity metadata. Universal provenance MUST cover plugin identity, execution timing, arguments and token information, upstream step references, and retention decisions. There is no universal scientific metadata schema.

### 4.3. Workflow Root and Dataset Nodes

The root DataTree MUST NOT hold datasets or DataArrays. It MUST hold only step child DataTrees and workflow-level attributes.

Every data-bearing step result MUST hold the step metadata the *Specifications* require and one or more dataset nodes. Each dataset node is one `xarray.Dataset` holding one coordinate-compatible variable group. In such a group, every shared dimension uses the same coordinates. Members may carry different dimensions or subsets of them, but where two members share a dimension its coordinate MUST agree. Variables with conflicting coordinates go in different nodes. An operation may regroup datasets. Each resulting `dataset_id` MUST follow the interface's naming rules and need not preserve an input ID.

### 4.4. Step Classification

A **data-bearing** step returns scientific or processing datasets plus metadata. Only class-based plugins implement data-bearing steps. A **non-data-bearing** step returns metadata only. YAML-based plugins are always non-data-bearing. A nested `kind: workflow` node is a container ([§4.3](#43-workflow-root-and-dataset-nodes)). It is non-data-bearing at its own node even though its descendant steps carry datasets. Each class-based interface *Specification* MUST declare its classification from the interface's semantic result. Incidentally serializing a scalar, string, dictionary, or compatibility object into an `xarray.Dataset` does not make a step data-bearing.

Output formatter steps are non-data-bearing. They perform side effects and record output-product metadata (written paths, checksums, mime types) in step-level attrs, which are their nodes' only contents, per datatree spec §6.5. Move this paragraph to the output formatters page once it exists.

### 4.5. Dataset Identity and Scientific Compatibility

Identity metadata such as `start_datetime`, `end_datetime`, source, platform, and projection distinguishes similar datasets. `step_id` paths keep same-`dataset_id` reader outputs distinct before an explicit join. Every dataset node MUST carry `start_datetime` and `end_datetime`, meaning the data collection or valid time.

Operators MUST validate the structural requirements of their declared operation. They MUST NOT impose a generic scientific-compatibility policy unless an interface *Specification* permits one. Join operators MUST validate dimension and coordinate compatibility, and the join *Specification* MUST define the checks and the error raised. Join operators MAY check conflicting declared units. If they do, the *Specification* MUST say whether a conflict warns or errors.

### 4.6. Provenance and Retention

Execution timing uses `execution_start_time` and `execution_end_time`. Earlier names differed from the data-time pair by one word and proved confusable.

Retention provenance records four things: the workflow-level policy, the explicit step request, the current state, and the decision reason. The initial reason vocabulary is `explicit_keep`, `policy_keep_all`, `pending_consumer`, `unreferenced`, `workflow_output`, and `no_data`. A decision may be structured rather than Boolean. Retention MUST operate on the `/<step_id>/<dataset_id>` hierarchy. Current garbage collection works only at the step root and needs conformance review.

### 4.7. Units

Unit metadata lives in the `units` variable attribute, with UDUNITS-2 notation preferred. In v2.0.0 a variable MAY carry it. GeoIPS neither requires nor validates it, so consumers handle its absence. `long_name` and `standard_name` are likewise optional. All three become requirements once GeoIPS handling can meet them. Shared vocabulary, validation, inference, and automatic conversion are v2.1-or-later work. Their absence MUST NOT create v2.0.0 gaps.

### 4.8. Dimensions

No dimension is universally mandatory, including `latitude`, `longitude`, and `time`. Datasets carry only the dimensions their variables represent. Scalar acquisition information stays metadata, and GeoIPS adds no length-one dimensions in anticipation of composition. `start_datetime` and `end_datetime` record the span a dataset covers. A `time` coordinate, where present, records each element's time as read from the source and may be scalar or per-scanline. Neither is derived from the other.

### 4.9. Family and `data_tree` Migration

`BaseClassPlugin.required_attributes` requires `family` on every non-abstract class-based plugin, so `family` does not mark a plugin as legacy. `data_tree` is the sole runtime discriminator. `False` selects the unwrap/rewrap path and `True` passes the DataTree through. The v2.0.0 target is `data_tree=True` with no `family`, which no plugin can express while `family` is required. Families are deprecated in v2.0.0. Each family-bearing plugin is a gap and a register entry.

### 4.10. DataTree Location Notation

*Specifications* use absolute descriptive paths over the hierarchy `workflow root -> step DataTree -> dataset node -> variables and coordinates`. The dataset level differs from datatree spec §5.1, which places data on the step node ([§13.2](#132-corrections) item 1).

| Component | Notation |
| --- | --- |
| Workflow root | `/` |
| Workflow attribute | `/.attrs["workflow_name"]` |
| Step DataTree | `/<step_id>` |
| Step attribute | `/<step_id>.attrs["plugin_name"]` |
| Dataset node | `/<step_id>/<dataset_id>` |
| Dataset attribute | `/<step_id>/<dataset_id>.attrs["source_name"]` |
| Data variable | `/<step_id>/<dataset_id>.data_vars["wind_speed"]` |
| Coordinate | `/<step_id>/<dataset_id>.coords["latitude"]` |

A `step_id` is the case-sensitive identifier a workflow assigns to a step. A `dataset_id` names one coordinate-compatible group within a step by resolution, projection, shape, operation result, or any distinguishing combination. Both MUST be valid Python identifiers. The *Specifications* MUST reference the project's shared identifier validation and MUST NOT define a competing validator. `_input` is the data-injection dependency token and MUST NOT name a step.

Paths begin with `/`. Bracket notation quotes keys, and angle brackets mark placeholders. The notation is descriptive, not executable. Example tokens use the `blake2b:` prefix. The SplitOperators *Specification* defines notation under split-operator branches.

### 4.11. Backward Compatibility

GeoIPS v2.0.0 MUST continue to support legacy Products, legacy run scripts, and the legacy procflow CLI calls `single_source`, `config_based`, and `data_fusion`. Four invocations MUST be distinguished, with arguments unchanged:

- Bare `geoips run` runs OBP.
- `geoips run order_based`, and its `ob` and `obp` aliases, runs OBP as a superseded spelling.
- `geoips run <procflow>` reproduces the named procflow.
- `run_procflow` and `data_fusion_procflow` accept the older `--procflow <procflow>` form.

Only the third works today. Bare `geoips run` prints usage (`commandline_interface.py:182-187`). `geoips run --procflow` raises `NotImplementedError` (`:194`). `support_legacy_procflows()` rewrites the legacy executables to `geoips run <procflow>` (`:209-222`). File this paragraph as a gap in Phase 2 and delete it here.

`run_procflow` and `data_fusion_procflow` MUST become thin wrappers around `geoips run` that raise a deprecation warning. The promise covers these entry points and their supported outcomes. Procflow internals, Products, and call forms are not permanent public APIs. Preserve an internal procflow API only where user-facing support depends on it and no replacement exists.

**Products** are deprecated and MUST continue to work. GeoIPS MUST convert a Product into a Workflow at runtime. The generated Workflow MUST preserve the Product's supported processing intent and user-visible results, subject to documented deprecations. GeoIPS MUST also provide a conversion script that materializes the same Workflow as the migration path. The script and the runtime conversion MUST share one engine or be proven behaviorally identical, producing equivalent Workflows from the same Product and configuration with no divergence in rules, validation, warnings, or deprecation handling.

**Procflows.** The procflows interface MUST be removed, and OBP MUST become the only way GeoIPS runs. No procflow implementation is retained, and OBP is not itself a registered procflow. All procflow behavior MUST be reproduced through runtime Product conversion, shaped by the Product's family, and MUST be evidenced by the [baseline tests](#413-compatibility-test-baseline). `order_based`, `ob`, and `obp` MUST remain accepted as deprecated aliases for bare `geoips run`. They warn on use and MUST NOT resolve through the plugin registry. Where a legacy name is accepted as the first positional argument, the *Specifications* MUST define how it is disambiguated from a Workflow name.

The runtime conversion and every other compatibility adapter MUST NOT become permanent APIs. The conversion goes away with the entry points it serves. The *Specifications* MUST identify the behavior legacy Products and run scripts require separately from the internal procflow behavior being removed. Any change that could alter accepted Product definitions, run-script inputs, CLI behavior, results, metadata, outputs, or failure behavior MUST be identified as a compatibility risk and reviewed explicitly.

One identified risk concerns generated subcommands. `geoips/commandline/geoips_describe.py` and `geoips_list.py` generate `geoips describe <interface>` and `geoips list <interface>` per entry in `geoips.interfaces.__all__`. Each rename in [§5.1](#51-terminology-and-rename-map) therefore renames two subcommands, and removing `procflows` deletes two. The rename map's deprecation rule covers kinds only. The *Specifications* MUST state, per renamed interface, whether the old subcommand is aliased with a warning or removed, and what `geoips describe procflows` and `geoips list procflows` do afterward.

### 4.12. Removal Gates

Legacy procflows MUST NOT be removed until all of the following hold:

- Legacy calls execute through OBP by argument mapping and Product conversion.
- Every supported call form and argument is mapped or produces a deliberate, documented migration error.
- All core and official-package compatibility tests pass through the converted path.
- Results, required metadata, artifact contents, filenames, and exit behavior are equivalent.
- Actionable migration warnings exist.

Two mechanisms carry the transition. Runtime Product conversion is the routine the CLI invokes. Procflow-call argument mapping translates `run_procflow` and `data_fusion_procflow --procflow ...` arguments into OBP equivalents. Removing either requires all of the following:

- Official repositories hold no legacy Products or procflow calls beyond deliberate fixtures.
- Conversion tooling has been available for the approved migration period.
- The entry points' deprecation windows have elapsed.
- Compatibility tests verify documented post-removal behavior rather than successful conversion.

### 4.13. Compatibility Test Baseline

The matrix includes every current integration test from core `geoips` and from every official plugin package, including `data_fusion`, `geoips_clavrx`, and all others the inventory identifies. Do not subset because packages exercise the same interfaces. The inventory records the package set, the run scripts and Products each test exercises, required datasets, entry procflows, expected artifacts, comparison outputs, and conversion paths. Tests passing at baseline are release-blocking unless a deprecation or an approved decision removes them. The inventory tracks missing infrastructure and unavailable data and never silently excludes a package. Test scripts should invoke `geoips run` and leave the executables to dedicated compatibility cases.

**Recorded conflict.** `docs/source/functionality/command-line/index.rst:587` and `docs/source/getting-started/migrating-to-2.0.md:20, :40` document a `geoips legacy run` wrapper. No such subcommand exists. The top-level commands at `geoips/commandline/commandline_interface.py:38-47` are Config, Describe, Expand, List, Run, Test, Tree, and Validate. Legacy support is `sys.argv` rewriting in `support_legacy_procflows()` (`:157`). The inventory MUST resolve whether the wrapper is planned, abandoned, or a documentation error before the baseline is fixed. Route the correction through Phase 6.

### 4.14. Arguments and Conduits

A conduit is a compatibility argument-wiring adapter. The conduit registry maps an upstream plugin kind to two things: the downstream keyword existing plugins expect, and an extractor that obtains the value from the upstream node. This lets OBP call bespoke signatures such as `xarray_obj`, `area_def`, `mpl_colors_info`, and `output_filenames`. Further layers alias a conduit keyword to a legacy parameter. `data`, `input_xarray`, and `xobj` alias `xarray_obj`, and `output_fnames` aliases `output_filenames`.

Conduits and aliases MUST NOT be documented as synonymous. A legacy name or adapter MUST be retired only when its compatibility role has a validated replacement. Conduits are core-only, so external packages MUST NOT mutate, replace, or register entries. Observable binding behavior is the public contract. Registry location, helper names, and mechanics are private.

Every argument a plugin accepts MUST be suppliable explicitly. A conduit derives a value only when the caller supplies none. A plugin accepts the same inputs however it is invoked. An interface's type conversion applies whether the value arrives from a step, a conduit, or a direct call. An explicit argument takes precedence over a derived one. Each derived argument has exactly one authorized upstream kind. If an argument appears derivable from several kinds, the grouping or plugin model MUST be reconsidered rather than adding cross-kind precedence. `depends_on`, implicit conduit selection, missing-source, and unused-result semantics are not approved ([§6.1](#61-depends_on-and-conduit-resolution)).

**Canonical names.** Each standardized value gets one canonical name and semantic contract, used in new APIs, schemas, examples, and documentation. Legacy names stay out of future-facing signatures. Conduits, aliases, or normalization hooks accept them instead. Every noncanonical accepted name is registered as a deprecation ([§11.2](#112-deprecation-entry)). It is removed only after Products and run scripts can be translated and the approved window has elapsed.

Standardization MUST cover meaning, cardinality, type, units, default, and precedence. Similar names MUST NOT be merged unless they carry the same semantic value. Aliases MUST NOT silently accept ambiguous combinations, and the *Specification* MUST define conflict detection and precedence. Canonicalization MUST avoid churn. Established abbreviations stay canonical when unambiguous. A rename corrects a substantive inconsistency rather than modernizing a spelling, and its benefit MUST justify the migration cost. Different names across interfaces and families are permitted only for values that differ in semantics, units, cardinality, lifecycle, or upstream kind, and the [matrix](#113-canonical-argument-matrix) MUST record the distinction.

Legacy-to-canonical and canonical-to-legacy translations MUST share one mapping. Canonical and deprecated forms supplied together raise a conflict error. Argument-name translation stays separate from output and DataTree conversion. The three-stage pivot that implements this is specified on the base-classes page ([§8.1](#81-base-class-page)).

## 5. Interfaces

### 5.1. Terminology and Rename Map

The terminology is proposed, not yet committed. A **Plugin** is today's class-based plugin: Python that implements behavior. A **PluginConfig** is today's YAML-based plugin: a declaration that configures a Plugin. Every PluginConfig interface maps to exactly one Plugin interface. Several PluginConfig interfaces may share one Plugin interface, and a Plugin needs no PluginConfig. Two choices are committed. The writer config is `WriterConfigs`. `FeatureAnnotators` and `GridlineAnnotators` are retained as `WriterFeatureConfigs` and `WriterGridlineConfigs`, which `WriterConfigs` references rather than absorbs, so one annotator definition serves several writers.

The table covers every registered interface except the three deferred dynamic-sector interfaces ([§6.3](#63-dynamic-sector-consolidation)), plus three proposed PluginConfig interfaces. Verify it against runtime discovery before treating it as final. A step's `kind` is the singular of the interface name ([§8.2](#82-interface-page)).

| # | Current | Type | New | → Plugin | → PluginConfig | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `algorithms` | Plugin | `algorithms` | `Algorithms` | **`AlgorithmConfigs`** | |
| 2 | `colormappers` | Plugin | **`colormaps`** | **`Colormaps`** | **`ColormapConfigs`** | |
| 3 | `coverage_checkers` | Plugin | `coverage_checkers` | `CoverageCheckers` | none | |
| 4 | `databases` | Plugin | **`reporters`** | **`Reporters`** | none | Reports results outward. The database is an implementation detail |
| 5 | `filename_formatters` | Plugin | `filename_formatters` | `FilenameFormatters` | none | |
| 6 | `interpolators` | Plugin | `interpolators` | `Interpolators` | none | |
| 7 | `output_checkers` | Plugin | `output_checkers` | `OutputCheckers` | none | |
| 8 | `output_formatters` | Plugin | **`writers`** | **`Writers`** | **`WriterConfigs`** | |
| 9 | `procflows` | Plugin | none | none | none | Retired for OBP. `procflow` is removed as a kind, not redirected |
| 10 | `readers` | Plugin | `readers` | `Readers` | none | |
| 11 | `title_formatters` | Plugin | `title_formatters` | `TitleFormatters` | none | |
| 12 | `validators` | Plugin | `validators` | `Validators` | none | |
| 13 | `feature_annotators` | PluginConfig | **`writer_feature_configs`** | `Writers` | **`WriterFeatureConfigs`** | Referenced by `WriterConfigs` |
| 14 | `gridline_annotators` | PluginConfig | **`writer_gridline_configs`** | `Writers` | **`WriterGridlineConfigs`** | As row 13 |
| 15 | `product_defaults` | PluginConfig | `product_defaults` | `Workflows` | retained | Deprecated. Converts to a `WorkflowConfig` at runtime. Target Plugin pending row 18 |
| 16 | `products` | PluginConfig | `products` | `Workflows` | retained | As row 15 |
| 17 | `sectors` | PluginConfig | **`sector_configs`** | **new `Sectors`** | **`SectorConfigs`** | Name reassignment. Static sectors only |
| 18 | `workflows` | PluginConfig | deferred | `Workflows` | `WorkflowConfigs` | Deferred per [§6.1](#61-depends_on-and-conduit-resolution). Same shape as row 17 if it proceeds. Names are candidates |
| 19 | none | PluginConfig | **`algorithm_configs`** | `Algorithms` | **`AlgorithmConfigs`** | Declarative algorithms, as the RGB configs in [#1484](https://github.com/NRLMMD-GEOIPS/geoips/pull/1484) |
| 20 | none | PluginConfig | **`colormap_configs`** | `Colormaps` | **`ColormapConfigs`** | |
| 21 | none | PluginConfig | **`writer_configs`** | `Writers` | **`WriterConfigs`** | References rows 13 and 14 |

Rows 17 and 18 reassign a name. `sectors` and `workflows` register PluginConfig interfaces today and would register the new Plugin instead, with the existing interface moving to `sector_configs` or `workflow_configs`. Aliasing the old kind to the new one handles every other rename but not these, because `kind: workflow` would be ambiguous. Row 17 therefore needs a deliberate answer in the register. Row 18 waits on [§6.1](#61-depends_on-and-conduit-resolution) and on the inventory establishing whether `class_based/workflow.py` is registered. The `Workflows` Plugin MUST NOT be specified before then. Products and ProductDefaults reach `Workflows` through conversion and keep their names, because renaming a compatibility surface defeats it.

Current kinds stay accepted and raise a deprecation warning. No rename lands without a register entry carrying old kind, new kind, warning, and schedule. Row 9 gets a removal entry instead.

### 5.2. Split and Join Operators

v2.0.0 adds `SplitOperators` and `JoinOperators`. Neither is implemented. `split` and `join` are reserved scaffolding kinds. `SCAFFOLD_KINDS` (`geoips/pydantic_models/v1/workflows.py:66`) accepts them during validation and defers them to orchestration rather than registry resolution. Registering them as interfaces changes their kind and brings plugin resolution, argument models, registry entries, and Lexeme naming with it. The *Specifications* state that transition. Both produce data-bearing steps and belong in the coverage matrix, and missing implementation is tracked as gaps.

Split operators reorganize data into declared branches. Join operators combine inputs and may construct dimensions. Both follow [§4.2](#42-metadata) through [§4.5](#45-dataset-identity-and-scientific-compatibility). A join creates a new dimension along a declared axis, for example time, height, ensemble member, or source. It defines how metadata become coordinate values and rejects inputs that lack structurally required information. An input need not carry a `time` axis when the value composed from it is scalar. A join along time takes each input's `start_datetime` as the `time` value and carries the `start_datetime` and `end_datetime` pair in a `time_bnds` bounds variable. This follows the CF bounds convention and preserves each observation's interval, since a full-disk scan spans minutes. The joined extent is the minimum and maximum across inputs. Two cases are left to the JoinOperators *Specification*. Inputs that already carry `time` make the operation a concatenation with different validation, and a mixed set likely warrants rejection. Overlapping extents are legitimate, for example a mesoscale sector inside a full disk, but produce a non-monotonic `time` that silently breaks xarray selection. Names, branch semantics, dataset naming, metadata propagation, errors, retention, and migration from the scaffolding kinds are deliverables of their *Specifications*, not prerequisites of this plan.

## 6. Tabled Topics

Nothing here is normative or implementable until the larger team decides it.

### 6.1. `depends_on` and Conduit Resolution

Once decided:

1. Trace scripting calls from script-tree initialization through `BaseClassPlugin` conduit extraction and result attachment.
2. Build scripting examples with repeated data-bearing, sector, and filename-formatter steps. Establish which prior result feeds each conduit, whether the most recent matching kind wins, how explicit arguments interact, and what a missing required kind does.
3. Compare with OBP validation, implicit `depends_on` injection, topological ordering, and upstream collection.
4. Evaluate a DAG model in which omitted dependencies create implicit edges to the most recent step each conduit requires, and explicit `depends_on` replaces only same-kind automatic sources.
5. Determine how required conduits are declared so the DAG composes before runtime.
6. Define unused-result warnings and missing-conduit errors, including whether results retained as workflow outputs count as unused.
7. File gaps and update the *Specifications*.

Evidence so far: OBP defaults a missing `depends_on` to the previous step and collects only resolved nodes. A two-sector check gave `second` implicitly and `first` for `depends_on: ["first"]`. That does not establish per-conduit behavior.

Under discussion: a container object that holds the root DataTree and exposes methods over its contents. Every plugin can see it at call time, so a plugin can attach its own output. `depends_on` may become optional or change role. Effects on ordering, conduit resolution, unused-result detection, pre-runtime composability, and the scripting/OBP relationship are unresolved.

The same discussion governs terminology. `workflows` is the registered **YAML-based** interface. A workflow **container object** would be runtime machinery. The datatree spec conflates them ([§13.2](#132-corrections) item 2). Until the team decides, do not resolve the conflation, rename either concept, or specify the container. *Specification* pages MUST mean the YAML-based `workflows` interface when they name it and MUST NOT describe a container object as a registered class-based interface.

### 6.2. Data Time Attribute Naming

Whether data time attributes should match the `execution_*` pair is undecided. `start_datetime` and `end_datetime` remain canonical. There are three options.

- Keep them. Core has roughly 409 usages, plus every official package touching reader attributes, and the [§4.14](#414-arguments-and-conduits) churn rule favors this.
- Rename to `data_start_time` and `data_end_time`, symmetric with the execution pair.
- Adopt the ACDD names `time_coverage_start` and `time_coverage_end`. This follows [§4.1](#41-cf-compliance) and removes a translation `geoips/interfaces/class_based/readers.py:254` already performs for GOES and ABI files, and `windspeed_awips2_formatter.py:307` declares `Conventions: CF-1.6`. Only one reader family is confirmed to supply them.

Either rename needs a register entry. No YAML plugin carries these keys, so a rename touches Python attributes, filename formatters, fixtures, and *Specification* passages, which means early pages get revisited.

### 6.3. Dynamic Sector Consolidation

Three Plugin interfaces cover dynamic sectors as sequential stages of one operation. The proposal consolidates them into `DynamicSectors` with `DynamicSectorConfigs`. The interfaces are not understood well enough to commit.

| Interface | Signature | Stage |
| --- | --- | --- |
| `sector_metadata_generators` | `call(trackfile_name, allowed_aid_types=None)` | Parse a trackfile into storm metadata |
| `sector_spec_generators` | `call(area_id, long_description, clat, clon, projection, pixel_width, pixel_height, num_samples, num_lines)` | Build an `AreaDefinition` from center and shape |
| `sector_adjusters` | none recorded | Adjust an existing sector |

Against consolidating now: the call sites are in `single_source.py`, `config_based.py`, and `sector_utils/`, which is procflow code scheduled for deletion. One candidate shape is a `DynamicSectors` Plugin per source type whose `call()` runs the whole pipeline, with the config supplying trackfile, projection, resolution, shape, and adjustment. `tc` and `volc` become plugin names and `area_definition` an internal step. Core has four metadata generators (families `tc` and `volc`) and one spec generator (`area_definition`). Nothing in core, `recenter_tc`, or `data_fusion` implements `sector_adjusters`, though procflows and CLI help reference it. Confirm it is vestigial against other packages first.

### 6.4. Deprecation Approval and Timing

The group sets minimum warning windows and removal timing through its established processes. Removal need not wait for v3.0.0. Deprecated behavior may go within the v2 series once the approved window, migration readiness, and compatibility requirements are met. Deprecations without an approved schedule are tracked as schedule pending.

## 7. Documentation Location and Format

The *Specifications* live in the developer guide:

```text
docs/source/devguide/
├── deprecations.md
└── plugin-specifications/
    ├── index.md
    ├── canonical-arguments.md
    └── class-based/
        ├── index.md
        ├── base-classes.md
        └── interfaces/
            ├── algorithms.md
            ├── readers.md
            └── ...
```

New documents use MyST Markdown. Unrelated reStructuredText pages are not converted. The existing user-facing pages under `docs/source/functionality/interfaces/class_based/` stay separate during development. At release, the approved *Specifications* are distilled into user-facing documentation that replaces or revises them.

Style conventions, chosen to survive the reStructuredText migration:

- Put `(label)=` immediately before each heading, with one unique page-level target. A content page uses its filename stem. An index page uses its section, so `plugin-specifications/class-based/index.md` gets `(plugin-specifications-class-based)=`, as in `docs/source/functionality/scripting/index.md:6`.
- Use `{ref}` for internal cross-references and plain Markdown links only for external URLs. `{ref}` alone resolves while the two formats coexist.
- Use colon fences (`:::{note}`) for prose directives and backtick fences for content-bearing ones such as `{mermaid}` and `{contents}`.
- Use ATX headings, one H1 per page, sentence case, and no skipped levels.
- Use pipe tables.
- Use semantic line breaks: one sentence or clause per line.

## 8. Page Outlines

Create each page as its outline plus an empty reference-links section, then fill it incrementally. Answer every heading. Where one does not apply, write "Not applicable" and a one-sentence reason.

### 8.1. Base-Class Page

1. Overview and audience
2. Normative language
3. Class hierarchy and division of responsibilities
4. `BaseClassInterface` contract: attributes, methods, discovery and validation
5. `BaseClassPlugin` contract: required and inherited attributes, required subclass methods, inherited public methods, lifecycle hooks and invocation sequence
6. DataTree and native-data conversion
7. OBP integration and conduits, including the three-stage compatibility pivot (ingress normalization of deprecated caller names, which warns, then canonical resolution and validation, then legacy adaptation at the final invocation boundary only, which does not warn)
8. Registration and lookup
9. Minimal example
10. Validation and failure modes
11. Compatibility and deprecations
12. See also
13. Reference links

### 8.2. Interface Page

1. **Overview.** Purpose, and the cases a plugin author would write one for.
2. **Normative language.** The [§2](#2-requirement-language) notice, verbatim.
3. **Plugin kind.** The `kind` a workflow step gives to invoke this interface, per the [§12.1](#121-phase-0-documentation-architecture) rule. The page MUST state its kind and MUST NOT define a competing naming rule.
4. **Step classification.** Data-bearing or not, the semantic result that makes it so, and whether the current representation conforms.
5. **Prerequisites.** Upstream steps, dataset nodes, and metadata that must exist first.
6. **Data produced.** What the step adds, replaces, or removes. How variables group into datasets and how `dataset_id` values are chosen. Whether input groups are preserved, split, merged, replaced, or removed. Input and output types outside the DataTree wrapper.
7. **Dataset identity metadata.** What distinguishes one of this interface's datasets from another.
8. **Dimensions.** Which dimensions its datasets carry, create, or remove.
9. **Units.** Where variables carry `units`, the required input and output units, whether plugins require, preserve, convert, or ignore unit metadata, and any unit-related arguments.
10. **CF conformance.** Any divergence, with its reason.
11. **Retention.** Retention behavior for this interface's data.
12. **Arguments.** Positional and keyword arguments with defaults and required status. Which name is canonical and which are deprecated compatibility inputs.
13. **Conduits and aliases.** Each conduit's source, binding, precedence, missing-value behavior, and example. Which names are bindings, legacy aliases, or interface-specific translations, each marked deprecated.
14. **Family and `data_tree` status.** Per [§4.9](#49-family-and-data_tree-migration), with each remaining family's call signature.
15. **Lifecycle and conversion.** Hooks defined or overridden, and interface-specific conversion around `call()`.
16. **Required plugin implementation.** Attributes, methods, base class, and registration. Distinguish the interface-level base class from family scaffolding and shared helpers.
17. **Errors and validation.** Exceptions, validation rules, and failure modes.
18. **Deprecations.** Each accepted deprecated argument or behavior, with its warning behavior, replacement, migration path, schedule, and register link.
19. **Legacy compatibility.** What the contract preserves for legacy Products and run scripts, how it bridges to workflows and CLI calls, and how the interface interacts with procflows versus OBP.
20. **Conformance status.** Each alpha divergence linked to its gap. Known limitations and open questions.
21. **Examples.** At least one, or why none is appropriate. Links to representative production plugins.
22. **See also.**
23. **Reference links.** The code, tests, documentation, issues, and plugins that support the page.

### 8.3. Deprecation Page

Draft `docs/source/devguide/deprecations.md` first, with this outline:

1. Purpose, scope, and normative language
2. Principles and compatibility constraints
3. Lifecycle states
4. Typed central registry: module layout, `DeprecationRecord`, stable ID format, immutability and core ownership
5. Required record fields
6. `warn_deprecated()` API: category and message construction, stack level, repeated-warning behavior
7. Distributed adapters and normalization
8. Schedule and migration requirements
9. Existing versus newly proposed deprecations
10. Validation and test requirements
11. Documentation generation and reporting
12. Pending governance decisions
13. Examples
14. Reference links

## 9. Working Method

Per page:

1. Create the skeleton ([§8](#8-page-outlines)).
2. Build an evidence map per section from source classes, tests, registry information, existing docs, and representative plugins.
3. Resolve contract questions. Record ambiguities in the page or a tabled topic rather than presenting inferred behavior as settled.
4. Draft one coherent section group at a time.
5. Add or verify examples from real plugins. Test code where practical, and say when an example is illustrative.
6. Review terminology and links against canonical terms.
7. Reconcile every requirement with code and tests, and create or update gap and deprecation entries.
8. Validate with the Phase 0 commands plus focused tests or introspection.
9. Update this plan.

**Example sources**, in order of preference:

1. Core `geoips`.
2. `geoips_plugin_example`.
3. `template_basic_plugin`.
4. Other official packages, only where the first three fall short.

Requirements and minimal examples stay understandable within the page. External packages supplement a requirement and never serve as its sole evidence. Link a tag or commit where exact source matters. Add a small tested example to `geoips_plugin_example` where no durable one exists. An external example supports the v2 behavior, is verified, uses public or synthetic inputs, and shows the target contract. Maintainer identity and archival status do not affect eligibility. Private packages and local copies are not references.

**Evidence rules.** Code and tests evidence alpha behavior and conformance, not the contract. Unapproved target behavior is an open decision. Supplement source reading with runtime introspection, especially for inherited signatures and registry discovery. Trace inherited behavior into `pluginify`, and do not attribute it to GeoIPS unqualified. Mention internal helpers only where authors must understand their effects. Do not infer a deprecation deadline from a comment or warning. Record a candidate as a [§11.2](#112-deprecation-entry) entry with approval pending, and put it through the same review as existing deprecations. When code, tests, and docs disagree, record the conflict before choosing. Use source links only where source detail helps the reader. Every factual claim traces to code, tests, a document, or a recorded decision.

## 10. Definition of Done

- [ ] Every [§8.2](#82-interface-page) heading is complete or marked not applicable.
- [ ] Common and family-specific behavior are distinguishable.
- [ ] The BCP 14 notice is present. Every **SHOULD** gives the consequence of an exception, and every **MAY** gives its interoperability behavior. Normative statements describe the v2.0.0 target.
- [ ] Canonical arguments are in the [matrix](#113-canonical-argument-matrix) with consistent semantics across interfaces and families.
- [ ] Every noncanonical accepted argument sits at a compatibility boundary, stays out of future-facing examples, and links to a register entry. Conflicts and precedence are specified, and are tested or tracked as a gap.
- [ ] Data-tree paths and metadata keys are named wherever the contract defines them. Nothing places a data variable on the workflow root.
- [ ] The reference-links section or an approved decision backs every claim.
- [ ] Every confirmed difference has a gap with a release-blocking classification. Closed gaps carry their disposition label.
- [ ] Every deprecation is in the register, with current support distinguished from proposed removal, migration guidance, and an approved or clearly proposed schedule.
- [ ] Cross-references resolve, documentation checks pass, and this plan is updated.

## 11. Record Templates

### 11.1. Conformance-Gap Issue

`.github/ISSUE_TEMPLATE/v2-spec-gap.md` is the single source of truth for the fields and applies the `v2-spec-gap` label. It carries only fields GitHub lacks natively. Ownership, schedule, state, and release-blocking status use the assignee, milestone, issue state, and labels, never prose. A closed gap's disposition is a label. `waived` marks a gap the release authority waived. A closed gap without it was resolved.

### 11.2. Deprecation Entry

| Field | Meaning |
| --- | --- |
| Deprecation ID | Stable identifier, for example `CBP-DEP-001` |
| API/behavior | Argument, keyword, family, interface, method, or compatibility behavior |
| Discovery class | Previously announced, or newly discovered or proposed |
| Scope | Affected interfaces, families, plugins, and users |
| Rationale | Why continued support is undesirable |
| Replacement | Target API or behavior |
| Migration strategy | Concrete steps and supporting documentation |
| Compatibility behavior | What remains accepted and how it is interpreted |
| Warning strategy | Category, message, trigger point, and test coverage |
| Schedule | Announcement, warning, removal, and cleanup milestones |
| Earliest known notice | Release note, warning, issue, or other evidence |
| Owner and approval | Responsible party, decision authority, and approval state |
| Dependencies/risks | Ecosystem impact and prerequisites for removal |
| Migration readiness | Product-to-workflow and script-to-CLI replacement status and exit criteria |
| Related bridge lifecycle | Transitional converter or adapter introduction, support, and retirement |
| Argument mapping | For argument deprecations: the role (conduit binding, alias, or translation), the ingress and invocation translations with warning ID, and the conflict behavior when both names are supplied |
| Status | Candidate, proposed, approved, warning, removed, withdrawn, or complete |

A runtime warning with no recorded migration path and schedule is an incomplete deprecation and must be resolved before this effort is complete.

### 11.3. Canonical Argument Matrix

The matrix lives at `docs/source/devguide/plugin-specifications/canonical-arguments.md`, with one row per canonical argument. Columns: name, meaning, type, cardinality (single, sequence, or mapping), units, default, required status, valid values or range, precedence of an explicit value over a derived one, applicable interfaces and families, and authorized upstream kind.

## 12. Execution Phases

Status: this plan is complete, [§13](#13-datatree-spec-reconciliation) is drafting, and no phase has started.

### 12.1. Phase 0: Documentation Architecture

Done: page location and naming, base-page structure, expand-versus-link, and MyST format ([§7](#7-documentation-location-and-format)). BCP 14 conventions ([§2](#2-requirement-language)). The family and `data_tree` axis ([§4.9](#49-family-and-data_tree-migration)). Open:

- [ ] Canonical terms. "Data-bearing," "non-data-bearing," and "argument conduit" are fixed. "Returned data tree" and "family" are not.
- [ ] The `kind` resolution rule (proposed). A kind is the singular of a registered interface name, class-based and YAML-based alike. The reserved kinds `split` and `join` bypass resolution.
- [ ] One rule, set here, classifying the classes under `geoips/interfaces/class_based/bases/` as either family scaffolding (deprecated compatibility, registered) or shared implementation reuse (outside scope).
- [ ] The argument vocabulary and the [matrix](#113-canonical-argument-matrix) (columns proposed in §11.3). A block on new plugins or examples introducing noncanonical names without an approved change.
- [ ] Gap labels, milestone workflow, and release-blocking criteria.
- [ ] The deprecation lifecycle, warning and migration-documentation requirements, and exceptions process. Notice periods, milestones, and approval authority stay pending [§6.4](#64-deprecation-approval-and-timing).
- [ ] The registry design (proposed in [§3](#3-records) item 3).
- [ ] Measurable thresholds for the [§4.12](#412-removal-gates) gates.
- [ ] Documentation ownership boundaries, by extending `docs/source/architecture/documentation/where-to-put.rst`.
- [ ] The validation commands every page runs, confirmed as real invocations. Candidates are `./docs/build_docs.sh . geoips`, `geoips lint`, and the cspell configuration.
- [ ] Adoption of the [§7](#7-documentation-location-and-format) style conventions.

**Exit:** architecture and terminology are agreed before content is drafted.

### 12.2. Phase 1: Deprecation Specification

- [ ] Create the page from [§8.3](#83-deprecation-page).
- [ ] Inventory existing warning helpers, deprecation modules, adapters, release notes, and tests.
- [ ] Specify `DeprecationRecord`, the registry, stable IDs, `warn_deprecated()`, and how distributed sites reference entries. Define validation, testing, and generation requirements.
- [ ] Compare with the implementation, open gaps, and seed the register.

**Exit:** interface pages can register deprecations without inventing page-specific tracking.

### 12.3. Phase 2: Interface Inventory

- [ ] Query runtime discovery and the registry, and reconcile the results with `class_based/` and `bases/`. Mark deprecated, transitional, internal, and excluded interfaces. Add `SplitOperators` and `JoinOperators`.
- [ ] Classify each interface by semantic result and compare with its current representation. Identify the YAML interfaces that configure it, and its families and representative plugins.
- [ ] Discover every official package and its integration tests. Build the [compatibility matrix](#413-compatibility-test-baseline) with release-blocking status per case.
- [ ] Inventory existing deprecation warnings, shims, deprecated arguments, families, and interfaces across code, tests, release notes, and docs.
- [ ] Document the current and target Product-to-Workflow conversion path. Register Product conversion and procflow-call conversion as distinct deprecations with coordinated removal criteria. Specify the conversion script (inputs, output, validation, idempotency, diagnostics, tests) and its equivalence tests.
- [ ] Inventory procflow call forms and their OBP arguments. Inventory conduit bindings, aliases, translations, precedence, and fallbacks. Inventory ingress and invocation adapters and confirm one shared mapping.
- [ ] Run the [§6.1](#61-depends_on-and-conduit-resolution) investigation once the team decides, and specify the approved semantics.
- [ ] Map every accepted argument to a canonical argument, a justified interface-specific one, or a deprecation candidate. Flag any argument derivable from several kinds.
- [ ] Build the coverage matrix: source, tests, docs, examples, and intended page per interface, with a reason for each exclusion.

**Exit:** every registered class-based interface appears exactly once in the coverage matrix.

### 12.4. Phase 3: Base Classes

- [ ] Classify each `BaseClassInterface` and `BaseClassPlugin` attribute and method as required, optional, inherited, internal, overrideable, or prohibited from override.
- [ ] Document the invocation sequence, hooks, conversion, metadata propagation, scripting, and conduit handling. Specify universal provenance and retention per [§4.2](#42-metadata) and [§4.6](#46-provenance-and-retention).
- [ ] Compare garbage collection with `/<step_id>/<dataset_id>` storage and open gaps.
- [ ] Add a minimal example verified against registration rules. Compare every requirement with alpha behavior. Verify that legacy Products and run scripts are preserved and that procflow compatibility is separate from the OBP-native contract.

**Exit:** interface pages link to the common contract without restating it.

### 12.5. Phase 4: Pilot

- [ ] Select one interface with real data flow, families, conduits, and tests. Algorithms or readers are likely candidates. Complete it per [§9](#9-working-method), then revise [§8.2](#82-interface-page) and [§10](#10-definition-of-done) from what it shows.

**Exit:** one accepted page sets the pattern.

### 12.6. Phase 5: Remaining Interfaces

Work in batches by data flow and validate one page at a time:

- [ ] Readers, algorithms, interpolators.
- [ ] Split and join operators. Write outlines and evidence maps before deciding names or semantics. Specify join validation and its errors.
- [ ] The three sector interfaces.
- [ ] Colormappers, output formatters, filename formatters, title formatters.
- [ ] Coverage checkers, validators, output checkers.
- [ ] Databases.

For each page, apply [§9](#9-working-method) and [§10](#10-definition-of-done), and update the coverage matrix. Write one release note per pull request under `docs/source/releases/latest/`.

**Exit:** every interface has a validated page or an approved exclusion.

### 12.7. Phase 6: Integration

- [ ] Link from the interfaces landing page, the class-based overview, and the writing guide. Add targeted links from architecture, DataTree, OBP, migration, registry, tutorial, and API-reference pages.
- [ ] Resolve conflicting or obsolete statements in existing pages. Link compatibility notes to the register and discrepancies to gaps. Check navigation, anchors, backlinks, and orphans.
- [ ] Apply [§13](#13-datatree-spec-reconciliation).

**Exit:** readers reach the pages from where they begin, and the datatree spec no longer conflicts with this plan.

### 12.8. Phase 7: Final Review

- [ ] The full build, link check, and spelling check pass.
- [ ] [§9](#9-working-method) and [§10](#10-definition-of-done) hold for every page.
- [ ] Terminology, deprecation language, and path notation are consistent across pages.
- [ ] Maintainers approve the contract, blocking decisions, schedules, migration strategy, and unresolved claims.
- [ ] The release authority has resolved or waived every blocking gap. Every pull request carried its release note.

**Exit:** the documentation builds and is consistent, the contract is approved, deprecations are scheduled, and blocking gaps are closed.

## 13. Datatree Spec Reconciliation

This section records the changes to `docs/source/devguide/datatree-spec.md`, applied in Phase 6. The datatree spec is normative for DataTree structure. This plan is normative for the plugin contract. Where they conflict, the plan governs and the datatree spec changes, never the reverse. Unprefixed section numbers below are datatree-spec sections.

### 13.1. Propagations

| Plan requirement | Datatree spec sections |
| --- | --- |
| Root holds only step children and workflow attrs ([§4.3](#43-workflow-root-and-dataset-nodes)) | §5.1 |
| One dataset node per coordinate-compatible group ([§4.3](#43-workflow-root-and-dataset-nodes)) | §5.1 shows data on the step node. Define the term in §5 |
| Retention on `/<step_id>/<dataset_id>` ([§4.6](#46-provenance-and-retention)) | §10.4, §10.5 |
| Retention provenance records policy, request, state, and reason ([§4.6](#46-provenance-and-retention)) | §5.4 carries only `gc_status`. §10.7 |
| `start_datetime` and `end_datetime` on every dataset node ([§4.5](#45-dataset-identity-and-scientific-compatibility)) | §5.2 defines them only as a root aggregate. Add a dataset-level statement to §5. The aggregate's fate is open ([§13.4](#134-open-questions)) |
| `execution_start_time` and `execution_end_time` ([§4.6](#46-provenance-and-retention)) | §5.3 `processing_history`, §5.4, and the §3.2 example |
| Join validation contract ([§4.5](#45-dataset-identity-and-scientific-compatibility)) | §4.5, §8.3 |
| `source_name`, `platform_name`, and `data_provider` are dataset-node attributes | §5.2 note (:687), §5.4 `/<step_id>.attrs` (:717-719, :728), and §3.2 note (:268) |
| Interface renames ([§5.1](#51-terminology-and-rename-map)), once committed | Every `kind` token in the examples (`output_formatter` and `colormapper`, about twenty lines) and the §4.4 kind list (:375) |

### 13.2. Corrections

1. **Dataset level ambiguous.** The §3.2 example has `/read_abi` holding a `B14BT(xr.Dataset)` node but `/single_channel` holding `B14BT_clipped` directly. §5.1, §5.7, §10.4, and §11.1 read as flat. State the [§4.3](#43-workflow-root-and-dataset-nodes) hierarchy and correct the flat sections.
2. **`workflows` is YAML-based.** §4.1 (:300) calls it class-based. §4.7 places `Workflow(Plugin)` in the class hierarchy. §15.2 puts it at `class_based/workflow.py`. `geoips/interfaces/__init__.py:53` registers it YAML-based. The §2.2 glossary (:96-97) already separates Workflow (spec) from Workflow (runtime), so build on that. Revise after [§6.1](#61-depends_on-and-conduit-resolution) settles which concept each passage means. Item 12 removes procflows from the same §4.7 block.
3. **`kind: sectorizer` is not registered.** §3.1 (:194) and the §4.4 `kind` row (:375) list `sectorizer` and omit `sector`. The registered sector interfaces are `sectors` (YAML), `sector_adjusters`, `sector_metadata_generators`, and `sector_spec_generators`. §4.6's `kind: sector` is valid. Fix both sites. The :375 list is also partial, with eleven kinds where the Phase 0 rule yields one per registered interface. `test.kinds` keys are plural (`readers:` at :169 and :357) where the adjacent comment and the rule say singular.
4. **Variable metadata relaxed.** §5.5 requires `units`, `long_name`, and `standard_name`. GeoIPS sets them in 18, 1, and 2 reader modules respectively and validates none. Enforcing the requirement would open gaps against every reader. All three are optional in v2.0.0 ([§4.7](#47-units)), with no restore date.
5. **Execution timing keys.** `start_time` and `end_time` sit beside `start_datetime` and `end_datetime` with no stated convention. The §3.2 example lists `start_time` among `source_name` and `wavelength`, where observation time is the natural reading. Rename per [§4.6](#46-provenance-and-retention) in §5.4, the `processing_history` schema, and the example.
6. **Token prefix.** No change. The abstract's status line stays `dask:`, the runtime prefix (`geoips/utils/types/tokenization.py:21`). The §3.2 and §10.7 examples stay `blake2b:` ([§4.10](#410-datatree-location-notation)). Add one sentence distinguishing the two.
7. **`depends_on` and `keep` Model Note stale.** Delete :383. It says neither is a field yet, ordering is positional, and per-step retention is unvalidated. The abstract (:27-28) says the opposite. `WorkflowStepDefinitionModel` (`geoips/pydantic_models/v1/workflows.py:352`) has `depends_on` (:372) and `keep` (:389). `class_based/workflow.py:232-237` orders topologically. `_is_kept` (:137-138, :161) honors `keep`. Add §4.4 to the sections touched.
8. **Workflow-level `outputs:` asserted and denied.** §9.1 (:1002) denies it and the Required/Optional table (:285-292) omits it. Twelve other passages state or depend on it: :28, :75, :102, :125, :235, :296, :465, :534, :1091, :1283, :1316, and :1409. :28 claims it is an implemented pydantic field. [§4.6](#46-provenance-and-retention) keeps `workflow_output` in the retention vocabulary, which presupposes declarable outputs, so correct §9.1 and the table. If the decision becomes `keep: true` alone, record it here and remove `workflow_output` from the plan. `workflows.py:679-713` defines no `outputs` field, and the only one (:1329) is the test-override model. That is a gap, not authority.
9. **Per-step provenance MUST (:662) versus SHOULD (:710).** Raise :710 to MUST per [§4.2](#42-metadata).
10. **Exception roster overstated.** §12.1 (:1224) says nine classes are "All defined in `geoips/errors.py`". `TokenMismatchError` (:1233) and `JoinConflictError` (:1236) exist nowhere. `errors.py` runs from `GeoipsError` (:9) to `BoundaryIOError` (:137). §15.4 (:1430-1443) lists six, keeping `TokenMismatchError` and dropping `CoverageError`, `BoundaryIOError`, and `JoinConflictError`. Qualify :1224, mark the two as not implemented at :1238, and reconcile the two lists into one roster. Either name `JoinConflictError` as the join error or defer the name to the JoinOperators *Specification*.
11. **Colormapper `data_tree` unsettled.** :570 annotates `BaseColormapperPlugin` as `data_tree=True` in a hierarchy otherwise reported as implemented. `colormappers.py:16` sets `False`, and `_post_call` (:18-28) wraps. The colormappers page decides. If `True`, mark :570 target-state and file a gap. If `False`, §2.3 (:123) and §6.1 (:797) stop citing colormapper as pass-through. §2.2 is untouched. Do not flip §2.3 or §6.1 first.
12. **Procflow hierarchy removed** ([§4.11](#411-backward-compatibility)). Delete :572-573, keeping :570, and delete §15.3 (:1412-1428, `OrderBased(BaseProcflowPlugin)`). Revise the abstract (:37), the §2.2 glossary entry (:109), §2.3 step 3 (:119), and the References link (:1451). Point successors at the OBP/Workflow model. Check §4.8 and §15 for remaining `BaseProcflowPlugin` or `procflows` references.
13. **`depends_on` semantics stated as settled.** §4.4 (:378), §6.2 (:802-821), §8.1 (:936), and §8.1.1 (:938-965) specify defaulting to the preceding step, input-tree shape by dependency count, and `_input` behavior as normative. [§6.1](#61-depends_on-and-conduit-resolution) has not approved them. :821 says "the runner MUST only expose parents explicitly listed in `depends_on`", which is the opposite of the container-object direction under discussion. Mark these passages current behavior pending §6.1, and do not revise them before it decides.
14. **Operators "rather than transforming data".** The §2.2 glossary (:100) defines an operator as changing the DAG's shape rather than transforming data. [§5.2](#52-split-and-join-operators) makes split and join data-bearing interfaces, and a join constructs `time` and `time_bnds`. Revise with §5.2.
15. **Two split syntaxes.** The abstract (:31-33) describes an inline body with `scopes:` or `over: sector_list`. §4.5 (:391-421) shows `on:` and `branches:` with sibling steps tagged `scope:`. This is internal to the datatree spec, and the SplitOperators *Specification* resolves it.

### 13.3. Cross-References

The datatree spec should point at the plan rather than restate it in two places. For dimensions, point at [§4.8](#48-dimensions). For identity and join validation, point at [§4.5](#45-dataset-identity-and-scientific-compatibility). §4.5 (:387) and §8.3 (:980) already fix the `split` and `join` argument shape, the `conflict` default (`error`, :444), and `strategy` (:986-992). Keep that text and defer the validation contract to the operator *Specifications* ([§5.2](#52-split-and-join-operators)).

### 13.4. Open Questions

**Root attributes on mixed-grid or multi-source steps.** :678 makes `registered_dataset` a root MUST, with `sample_distance_km` (:675) and `area_definition` (:677) as root SHOULDs. `interpolation_radius_of_influence` (:676), `minimum_coverage` (:679), and `data_attribution` (:680, a root MUST) describe data the same way, and :687's own multi-source rationale makes one root attribution wrong. [§4.3](#43-workflow-root-and-dataset-nodes) permits a step holding datasets on different grids, where one root Boolean cannot be evaluated. Whether these attributes stay workflow-level, become derived, or move to dataset nodes is a plan decision. So is the root `start_datetime` and `end_datetime` aggregate. §13.1 carries no row for any of them until the plan decides.

## 14. Review Notes

This document was drafted with AI assistance and approved at summary level. Claims about code have been wrong before, so read these closest:

- [§5.2](#52-split-and-join-operators): `split` and `join` bypass plugin resolution today. `SCAFFOLD_KINDS` exists at `workflows.py:66`. Verify how it is used.
- [§4.9](#49-family-and-data_tree-migration): `family` is required and `data_tree` is the sole discriminator. Verify that coupling.
- [§6.1](#61-depends_on-and-conduit-resolution) carries a MUST and a MUST NOT while the design is open. Confirm the constraint is intended.

The [§13](#13-datatree-spec-reconciliation) line citations were checked against `datatree-spec.md` and the source at `864712f`. They hold until either changes.

Two things are decided and not to be re-litigated. An earlier four-tier class hierarchy was wrong, and the Phase 0 classification rule replaces it. A `CBP-READERS-014`-style requirement-ID scheme was dropped, because the gap template's requirement field and heading anchors give stable targets.

## 15. References

Starting points. Each page keeps its own reference-links section.

- `geoips/interfaces/base.py`: `BaseClassInterface` and interface validation
- `geoips/interfaces/class_based_plugin.py`: `BaseClassPlugin`, hooks, conversion, scripting, and conduits
- `geoips/interfaces/class_based/` and `bases/`: registered interfaces, interface-level base classes, and family behavior
- `geoips/utils/types/obp_conduits.py` and `script_datatree.py`: conduit bindings and scripting DataTree behavior
- `docs/source/devguide/datatree-spec.md`: the DataTree *Specification*
- `.github/ISSUE_TEMPLATE/v2-spec-gap.md`: the gap issue template
- `docs/source/functionality/interfaces/index.rst`, `writing-class-based-plugins.md`, and `class_based/`: interface navigation, the authoring guide, and existing pages
- `docs/source/functionality/plugins/class-based/index.rst`: the class-based plugin overview
- `docs/source/devguide/converting-module-to-class.md`: migration guidance
- `docs/source/architecture/plugin-registry.md` and `docs/source/functionality/plugin-registries.md`: the registry
- `tests/`: current contracts
- [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) and [RFC 8174](https://www.rfc-editor.org/rfc/rfc8174): BCP 14
