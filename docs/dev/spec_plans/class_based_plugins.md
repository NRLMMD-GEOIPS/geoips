# GeoIPS Class-Based Plugin Specifications: Task Plan

## Purpose

This document is the shared source of truth for planning and tracking the development
of GeoIPS class-based plugin specification documentation. It is intentionally a plan,
not the specifications themselves. The specifications will be **normative target-state
documents for the GeoIPS v2.0.0 release**, not descriptions limited to the behavior of
the current v2.0.0 alpha implementation.

The finished documentation will explain:

1. The common contract supplied by `BaseClassInterface` and `BaseClassPlugin`.
2. The contract of every registered GeoIPS class-based plugin interface.
3. How each interface participates in a processing workflow, including its inputs,
   outputs, metadata behavior, arguments, argument conduits, and deprecations.
4. How these specifications relate to the existing architecture, developer guides,
   tutorials, API documentation, and interface pages.
5. Where the current alpha implementation differs from the v2.0.0 contract and what must
   change before release.
6. Which existing or newly identified behaviors are deprecated, how users migrate away
   from them, and when each stage of deprecation occurs.

When implementation begins, use this file to choose the next small unit of work, record
decisions, and prevent the work from drifting beyond the agreed scope.

## Desired Outcomes

- A developer can distinguish the responsibilities of an interface, an interface-level
  base plugin class, and a concrete plugin.
- A plugin author can identify every required attribute and method and understand the
  behavior inherited from the base classes.
- A workflow author can determine what must precede an interface step, what arguments
  can reach it, and what data and metadata it produces.
- The v2.0.0 target contract is stated clearly and independently of conformance gaps.
- Current alpha behavior is compared with that contract, and every material difference is
  tracked as conforming, missing, divergent, ambiguous, or intentionally deferred.
- Every factual claim is traceable to code, tests, an existing document, or an explicitly
  recorded design decision.
- The new pages are discoverable from the appropriate existing documentation indexes and
  are cross-linked without duplicating tutorial or API-reference material unnecessarily.
- Existing deprecations and deprecations discovered during specification work are
  collected in one register with rationale, migration guidance, milestones, and owners.
- Future-facing plugin signatures use a standardized argument vocabulary; noncanonical
  legacy arguments are isolated in compatibility conduits/adapters and placed on an
  explicit deprecation path.

## Documentation Location and Format

The specifications will be developed separately from the existing user-facing interface
documentation under the following developer-guide hierarchy:

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

All new documents in this effort will use MyST Markdown (`.md`). More broadly, MyST is the
preferred format for new GeoIPS documentation because the project intends to migrate its
documentation to MyST over time. This task does not include mechanically converting
unrelated existing reStructuredText pages.

During specification development, the existing pages under
`docs/source/functionality/interfaces/class_based/` remain separate. As part of v2.0.0
release preparation, the approved developer specifications will be distilled into
user-facing documentation that replaces or substantially revises those existing pages.

## Specification Model

### Requirement Language

The key words **MUST**, **MUST NOT**, **REQUIRED**, **SHALL**, **SHALL NOT**,
**SHOULD**, **SHOULD NOT**, **RECOMMENDED**, **NOT RECOMMENDED**, **MAY**, and
**OPTIONAL** in this document and the resulting specification documents are to be
interpreted as described in BCP 14, [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119)
and [RFC 8174](https://www.rfc-editor.org/rfc/rfc8174), when, and only when, they appear
in all capitals.

Use these terms sparingly and only for normative v2.0.0 contract requirements:

- **MUST** and **MUST NOT** identify absolute requirements and prohibitions.
- **SHOULD** and **SHOULD NOT** identify recommended behavior for which a valid exception
  can exist. Each specification MUST explain the consequences of an exception or link to
  that explanation.
- **MAY** identifies behavior that is genuinely optional. Each specification MUST define
  any interoperability expectations between implementations that include the option and
  those that do not.

Lowercase words such as "must," "should," "required," and "may" have their ordinary
English meanings and no BCP 14 force. Planning steps, research instructions, examples,
observations about the current alpha implementation, and future work outside v2.0.0 use
ordinary language. Do not use **SHALL** or **SHALL NOT** in new GeoIPS specifications;
prefer **MUST** or **MUST NOT** so equivalent requirement levels use one vocabulary.

Every normative keyword must identify its subject and observable behavior. Avoid using a
keyword merely to emphasize a fact, implementation preference, or task-management step.

The work will maintain three related but distinct records:

1. **Normative v2.0.0 specifications** describe what released GeoIPS v2.0.0 MUST provide.
   They use the requirement language defined above.
2. **GitHub conformance-gap issues** compare the current v2.0.0 alpha code and tests with
   the normative specifications. A current limitation MUST NOT silently weaken the target
   contract. Each confirmed gap is tracked in a GitHub issue with its impact, evidence,
   acceptance criteria, related requirement, and release-blocking status. The v2.0.0
   milestone or project provides the aggregate readiness view.
3. **Deprecation register and strategy** records compatibility behavior that exists now or
   is newly selected for deprecation. It defines the migration path and lifecycle from
   announcement through warning, removal, and post-removal cleanup.

The target design MUST use a central, machine-readable deprecation registry within the
GeoIPS core package as the authoritative inventory. Compatibility implementations—such as
argument normalization, conduit bindings, and warning trigger points—remain near the code
they adapt, but each MUST reference a stable entry in the central registry. Published
deprecation tables and planning reports SHOULD be generated from the registry. When
generation is unavailable, they MAY be maintained manually only if automated validation
against the registry prevents the inventories from drifting.

The registry will use typed Python records in a lightweight, dependency-free core module
or package. A central `warn_deprecated(deprecation_id, ...)` helper will resolve stable IDs,
issue consistent warnings, and prevent distributed warning sites from duplicating messages
or schedule logic. External packages MUST NOT mutate or extend the core registry.

Specification pages MUST describe the v2.0.0 contract directly. Short compatibility
notes can identify behavior still accepted during transition, but detailed remediation
belongs in GitHub conformance-gap issues and the deprecation registry so temporary alpha
behavior is not mistaken for the intended API.

### Data-Bearing and Non-Data-Bearing Steps

The v2.0.0 specifications classify steps by their returned DataTree content, independently
of whether their plugins are implemented in Python or YAML:

- A **data-bearing step** returns one or more scientific or processing datasets plus
  metadata. Data-bearing steps are implemented by class-based plugins.
- A **non-data-bearing step** returns metadata but no scientific or processing datasets.
  Non-data-bearing steps may be implemented by class-based or YAML-based plugins.
- YAML-based plugins are always non-data-bearing. They configure class-based plugin
  behavior and return metadata-only DataTrees.

Each class-based interface specification MUST declare whether its steps are data-bearing
or non-data-bearing based on the interface's semantic result. Incidental serialization of
a scalar, string, dictionary, or compatibility object into an `xarray.Dataset` does not by
itself make the result data-bearing.

The root workflow DataTree is a container, not a data-bearing node. It MUST contain only:

- child DataTrees representing workflow steps, and
- workflow-level metadata in root attributes.

The root MUST NOT contain data variables. Processing data belongs within data-bearing step
DataTrees below the root. Consequently, specifications MUST identify data and metadata
locations relative to a step node rather than implying that scientific data may be stored
on the workflow root.

Every data-bearing step result MUST contain:

- the step metadata required by the applicable specifications, and
- one or more dataset nodes, with one `xarray.Dataset` for each coordinate-compatible
  group of variables.

A **coordinate-compatible variable group** contains variables whose shared dimensions
use the same coordinates. Variables in the same group can have different dimensions or
different subsets of dimensions, but whenever two variables share a dimension, the
coordinate associated with that dimension MUST agree. Variables that require conflicting
coordinates for a shared dimension belong in different dataset nodes.

A class-based operation can change the dataset grouping. For example, an interpolator may
accept a step DataTree containing several datasets on different grids and return a new
step DataTree containing one dataset on the target grid. The resulting `dataset_id` MUST
describe the output dataset according to the naming rules established for that interface
or operation; it is not required to preserve an input dataset ID.

Output formatter steps are non-data-bearing. They perform their declared output side
effects and record output-product metadata (such as written filenames and checksums) in
step-level attrs, but do not add or return scientific or processing data. Their step nodes
contain only attrs describing what was written, consistent with the datatree spec §6.5.

Dataset and step metadata such as `start_datetime`, `end_datetime`, source, platform, and
projection help users and plugins identify otherwise similar datasets. For example, two
reader steps may both produce an ABI dataset with the same `dataset_id` and coordinates
but represent different observation times; their distinct `step_id` paths and temporal
metadata keep them distinguishable before an explicit join.

GeoIPS infrastructure is responsible for preserving and exposing specified identity and
provenance metadata, not for determining whether data are scientifically appropriate to
combine. Workflow and plugin authors remain responsible for decisions such as combining
different processing levels, calibration states, or scientific products. Operators MUST
validate the structural requirements needed to perform their declared operation. Except
for behavior expressly permitted by an interface specification, such as optional checks
for conflicting declared units, operators MUST NOT impose a generic
scientific-compatibility policy.

Join operators MUST validate dimension and coordinate compatibility for the requested join
operation. A join specification MUST define the applicable checks and the error raised when
dimensions or coordinates cannot be joined as requested. Join operators MAY also check for
conflicting declared units when unit information is available. Optional unit checking MUST
document whether a conflict produces a warning or error. This does not require universal
unit metadata, scientific-level inference, or automatic unit conversion in v2.0.0; users
remain responsible for the scientific validity of the requested join.

The base specification defines universal workflow/step execution provenance. Individual
interface specifications define dataset identity metadata required for their data. No
universal scientific metadata schema is imposed on every dataset. Universal provenance
MUST cover plugin identity, execution timing, arguments/token information, upstream step
references, and retention decisions.

Retention provenance distinguishes the requested policy from the resulting state:

- workflow-level retention policy
- explicit step retention request
- current data-retention state
- retention decision reason

Use a small, extensible reason vocabulary initially: `explicit_keep`, `policy_keep_all`,
`pending_consumer`, `unreferenced`, `workflow_output`, and `no_data`. The implementation
can represent a retention decision as a structured result rather than reducing it to a
Boolean. Retention MUST operate on the target `/<step_id>/<dataset_id>` hierarchy; current
step-root-only garbage collection requires conformance review.

Units are relevant descriptive information for conversion and interoperability, not a
general scientific-compatibility judgment. The v2.0.0 interface specifications MUST
document existing or interface-specific expectations, where applicable:

- where variable and coordinate units are currently stored
- unit notation currently encountered or required
- required input units and accepted alternatives
- output units and whether they are fixed, configurable, inherited, or derived
- whether the plugin currently preserves, validates, converts, or ignores unit metadata
- unit-related arguments and their canonical names
- how conversions are recorded in output metadata and provenance

Shared unit-storage rules, canonical unit vocabulary, validation, handling, and general
automatic conversion are deferred to v2.1 or later. They are not v2.0.0 requirements and
their absence MUST NOT create v2.0.0 conformance-gap issues. Existing interface-specific
unit behavior needed for backward compatibility remains documented. Future automatic
conversion should be dimensionally valid, explicitly attributable in provenance, and must
not guess when units are missing or ambiguous.

For example, a join may use temporal metadata from two ABI reader outputs to create a
three-dimensional dataset with a new `time` dimension. This avoids requiring every input
dataset to contain dimensions such as `time` or `height` when those values are scalar
before composition.

No dimension, including `time`, is universally mandatory. Datasets contain only the
dimensions naturally represented by their variables, subject to interface-specific
requirements. Scalar acquisition information may remain metadata when no axis exists. A
join or other composition operator creates a new dimension when combining inputs along
time, height, ensemble member, source, or another declared axis; it defines how metadata
become coordinate values and rejects inputs missing information structurally required for
that operation. GeoIPS does not add artificial length-one dimensions merely to anticipate
future composition.

The inventory must classify every interface by semantic result and compare its current
DataTree representation with that classification. Incidental data variables used only to
transport metadata or compatibility objects are representation gaps, not evidence that an
interface is data-bearing. A YAML-based step that carries processing data is likewise a
conformance gap.

### Canonical DataTree Location Notation

Specifications will use absolute, descriptive paths with the following hierarchy:

```text
workflow root -> step DataTree -> dataset node -> variables and coordinates
```

The canonical forms are:

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
| Branch step | `/<split_id>/<branch>/<step_id>` |

A `step_id` is the arbitrary, case-sensitive identifier assigned to a step by a workflow.
A `dataset_id` identifies one coordinate-compatible variable group stored as a distinct
dataset within a step DataTree. Dataset identity may describe a resolution, projection,
shape, operation result, or another meaningful characteristic or combination of
characteristics that distinguishes the dataset from its siblings. For example, a reader
step may contain `resolution_500m`, `resolution_1km`, and `resolution_2km` dataset nodes,
while an interpolator may consolidate those inputs into one appropriately named target-
grid dataset node.

Both `step_id` and `dataset_id` MUST be valid Python identifiers. Names that begin with a
digit, such as `5424x5424`, are invalid; a name such as `shape_5424x5424` is valid. The
specifications should reference the project's shared Python-identifier validation rules
rather than defining a competing validator.

Paths begin with `/`, names are case-sensitive, quoted bracket notation identifies
component keys, and angle brackets denote placeholders. The notation is descriptive and
is not itself promised to be an executable Python expression. For example:

```text
/read_abi/resolution_2km.data_vars["brightness_temperature"]
```

corresponds conceptually to:

```python
tree["/read_abi/resolution_2km"].ds["brightness_temperature"]
```

**Datatree spec alignment note:** Several points in the existing datatree spec need
updating to match this plan. Track them during Phase 6 integration.

- The datatree spec is internally inconsistent about whether a dataset level exists
  between a step node and its variables. Its §3.2 worked example uses both structures: the
  `/read_abi` step contains a `B14BT(xr.Dataset)` dataset node holding a `B14BT` variable,
  while the `/single_channel` step places `B14BT_clipped` directly on the step node as a
  data variable. §5.1, §5.7, §10.4, and §11.1 all read as the flat form. This plan resolves
  the ambiguity in favor of the two-level `/<step_id>/<dataset_id>` hierarchy, which is
  required to represent coordinate-incompatible variable groups such as multi-resolution
  reader output. The datatree spec should be updated to state that hierarchy normatively
  and to correct the sections that assume the flat form.
- §4.1 states that "the `workflows` interface is class-based." It is registered as a
  YAML-based interface in `geoips/interfaces/__init__.py`. Relatedly, §4.7 places
  `Workflow(Plugin)` in the class-based plugin hierarchy and §15.2 documents it as a class
  at `geoips/interfaces/class_based/workflow.py`. These conflate the registered YAML-based
  `workflows` plugin interface with possible internal workflow runtime machinery; see the
  tabled design topic below before revising them.
- §3.1's example uses `kind: sectorizer`, which is not a registered interface and appears
  to be placeholder text. The registered sector-related interfaces are `sectors`
  (YAML-based), `sector_adjusters`, `sector_metadata_generators`, and
  `sector_spec_generators`. The `kind: sector` usage in §4.6 is valid and resolves to the
  YAML-based `sectors` interface.

**Token format convention:** Specification pages and examples will use the `blake2b:`
prefix for example token values, consistent with the datatree spec §3.2 and §10.7
examples. The datatree spec abstract's mention of a `dask:` prefix is inconsistent with
its own examples; `blake2b:` is the adopted convention here.

### v2.0.0 User-Facing Backward-Compatibility Constraint

GeoIPS v2.0.0 MUST continue to support legacy product definitions and run scripts. The
backward-compatibility promise applies to these user-facing entry points and their
supported processing outcomes; it does not make the internal APIs or implementations of
the existing procflows permanent public contracts. This v2.0.0 compatibility requirement
also does not make legacy Products or procflow-call forms permanent APIs; both are intended
for deprecation and eventual removal under an approved schedule.

OBP is the intended replacement for the existing procflows. In the near term, GeoIPS is
expected to gain conversion paths from legacy products to workflows and from legacy run
scripts to CLI calls. Those converters or adapters MUST preserve user-facing behavior
while allowing the underlying execution to move to OBP.

When a legacy Product is run as part of OBP, GeoIPS will convert that Product into an OBP
Workflow at runtime. The conversion is part of the supported runtime compatibility path;
users are not required to manually rewrite the Product before it can participate in OBP.
The generated Workflow MUST preserve the Product's supported processing intent and
user-visible results, subject to explicitly documented deprecations or gaps.

Legacy Products and Product-to-Workflow runtime conversion are transitional. GeoIPS will
deprecate legacy Products and provide an automated conversion script as the migration
path. The script performs the same semantic conversion as runtime Product-to-Workflow
conversion, but writes or otherwise materializes the resulting Workflow so it can replace
the legacy Product. GeoIPS will eventually stop accepting Products and performing their
automatic runtime conversion.

Runtime conversion and the migration script MUST share one canonical conversion engine
or otherwise be proven behaviorally identical. Given the same Product and applicable
configuration, they MUST produce equivalent Workflow specifications. Conversion rules,
validation, warnings, and deprecation handling MUST NOT diverge between the two paths.

GeoIPS will also eventually provide automatic runtime conversion from calls to legacy
procflows into OBP Workflow execution. That conversion is planned but does not authorize
immediate removal of the legacy procflows. Their existing implementations will remain
available for the time being while conversion behavior, compatibility coverage, migration
readiness, and deprecation schedules are developed and validated.

Automatic procflow-call-to-Workflow conversion is likewise transitional. After callers
have had an approved migration period to adopt Workflows and supported CLI calls, GeoIPS
will eventually stop accepting legacy procflow calls and remove their automatic runtime
conversion path.

This constraint guides both the target specifications and deprecation strategy:

- The specifications MUST identify behavior required by legacy products and run scripts,
  separately from internal legacy-procflow behavior that may be retired.
- A v2.0.0 implementation MAY use existing procflows, OBP, or compatibility adapters, as
  long as supported legacy products and run scripts continue to work as specified.
- OBP execution of a legacy Product performs runtime Product-to-Workflow conversion.
- Until automatic procflow-call conversion is available and validated, calls that require
  legacy procflows continue to use the retained legacy implementations.
- Internal procflow APIs MAY be deprecated without promising indefinite direct support,
  but removal MUST NOT break the supported user-facing compatibility boundary.
- Removal of an internal procflow path depends on a working replacement for the affected
  products and run scripts, migration tooling and documentation, adequate validation, and
  the applicable compatibility window.
- Runtime converters MUST have their own retirement criteria. Removing a legacy entry
  point ultimately includes removing the converter that temporarily accepted it; a
  compatibility adapter MUST NOT become an accidental permanent API.
- Any proposed change that could alter accepted product definitions, run-script inputs,
  CLI-equivalent behavior, processing results, metadata, outputs, or failure behavior MUST
  be identified as a compatibility risk and reviewed explicitly.

### Argument Standardization and Conduits

For planning purposes, a conduit is a compatibility-oriented argument-wiring adapter,
not simply another spelling for an argument. The current conduit registry maps an
upstream plugin kind to:

1. the downstream keyword expected by existing plugins, and
2. an extractor that obtains or transforms that value from the upstream DataTree node.

This lets a DataTree/OBP execution model call plugins whose established signatures use
bespoke arguments such as `xarray_obj`, `area_def`, `mpl_colors_info`, or
`output_filenames`. Additional compatibility layers may then translate a conduit keyword
to a legacy call signature. Current examples include positional-name aliases from
`data`, `input_xarray`, and `xobj` to `xarray_obj`, and an output-formatter translation
from `output_filenames` to `output_fnames`.

The target specifications should distinguish four concepts for every argument:

- the standardized semantic argument and meaning
- the canonical v2.0.0 public name
- conduit source, extraction, and precedence behavior
- accepted legacy aliases or interface-specific translations

Conduits and aliases are related, but they MUST NOT be documented as synonymous. The
deprecation strategy MUST retire individual legacy names or adapters only when their
user-facing compatibility role has a validated replacement. DataTree-native plugins may
not require conduit entries, so the registry may shrink as migration proceeds without
requiring the standardized semantic contract to change.

Conduits are core-only implementation machinery. External packages MUST NOT mutate,
replace, or register entries in the conduit registry. The registry and its entry structure
will be documented for GeoIPS core contributors so they can diagnose and correct bindings,
but that documentation does not make it an external extension API. Observable binding
behavior remains the public developer contract; registry location, helper names, and
internal invocation mechanics remain private.

An explicitly supplied canonical argument takes precedence over a conduit-derived value,
and each derived argument has exactly one authorized upstream plugin kind. The remaining
`depends_on`, implicit conduit-selection, missing-source, and unused-result semantics are
not approved; see [Tabled Design Topic: `depends_on` and Conduit Resolution](#tabled-design-topic-depends_on-and-conduit-resolution).

The intended direction is:

1. Define one canonical argument name and semantic contract for each standardized value.
2. Use the canonical names in new plugin APIs, workflow schemas, examples, and
   documentation.
3. Keep differing legacy names out of future-facing signatures where practical; accept
   them through conduits, aliases, normalization hooks, or other compatibility adapters.
4. Register every noncanonical accepted name as a deprecation, including its affected
   plugins, compatibility mechanism, replacement, warning behavior, and removal criteria.
5. Remove a legacy name only after legacy products and run scripts can be translated to
   the canonical contract and the approved deprecation window has elapsed.

Standardization MUST cover meaning, cardinality, type, units, default behavior, and
precedence in addition to spelling. Two arguments with similar names MUST NOT be merged
unless they represent the same semantic value. Likewise, aliases MUST NOT silently accept
ambiguous combinations: the specification MUST define conflict detection and which input,
if any, takes precedence during the compatibility period.

Argument inventory and grouping MUST also identify the upstream plugin kind from which a
derived value may be collected. Each derived canonical argument has exactly one authorized
upstream plugin kind. If the same argument appears to be derivable from multiple plugin
kinds, the semantic grouping or plugin model MUST be reconsidered rather than adding
cross-kind precedence.

Canonicalization MUST avoid unnecessary compatibility churn. Established GeoIPS
abbreviations can remain canonical when they are understood, unambiguous, and semantically
consistent. Do not create a deprecation solely to expand an abbreviation or modernize a
longstanding spelling. A rename should correct a substantive inconsistency, ambiguity,
semantic mismatch, or incompatibility with the standardized contract, and its benefit
MUST justify the migration cost.

Canonical names are uniform across interfaces and families whenever they represent the
same semantic value. Legacy signature differences alone do not justify different canonical
names. Select the canonical form using current usage, clarity, and migration cost; the
selected form may be an established abbreviation. Different canonical names are permitted
only when the values differ substantively in semantics, units, cardinality, lifecycle, or
authorized upstream kind, and the distinction MUST be recorded in the canonical argument
matrix.

Argument compatibility uses the canonical contract as an internal pivot with three
stages:

1. **Ingress normalization:** deprecated caller names from scripts, workflows, Products,
   CLI conversion, or other user-facing inputs are translated to canonical names and emit
   their registered deprecation warning.
2. **Canonical resolution and validation:** explicit values and conduit-derived values are
   resolved and validated using only canonical argument names.
3. **Legacy invocation adaptation:** immediately before calling an unmigrated plugin, a
   core/interface adapter translates canonical arguments into the legacy parameter names
   that plugin still implements.

Legacy-to-canonical and canonical-to-legacy translations MUST share one compatibility
mapping so their relationships cannot drift. The behavior is intentionally asymmetric:
legacy caller input warns, while a user supplying the canonical name does not receive a
warning merely because an internal adapter must invoke a legacy plugin. Plugin migration
status may instead produce a developer-facing warning or GitHub conformance issue.

Migrated plugins receive canonical arguments. Unmigrated plugins receive legacy parameters
only at the final invocation boundary. Workflows, conduits, validation, scripting state,
and documentation remain canonical. If canonical and deprecated caller forms are supplied
together, normalization raises a conflict error rather than choosing silently. Output and
DataTree conversion remain separate from argument-name translation.

## Scope

### In Scope

- A base class-based plugin specification covering:
  - `BaseClassInterface`
  - `BaseClassPlugin`
  - required and inherited attributes
  - public and lifecycle methods
  - subclass implementation requirements
  - validation and plugin registration behavior
  - pre-call and post-call behavior
  - native-data/DataTree conversion behavior
  - Order-Based Processing (OBP) integration and argument conduits
- One specification page for each registered class-based interface.
- Useful, tested examples selected from real core or plugin-package implementations.
- Links to relevant concepts, architecture, tutorials, migration guidance, API reference,
  DataTree specifications, OBP documentation, and plugin registry documentation.
- Links from existing documentation into the new specifications where they improve
  discoverability or resolve ambiguity.
- GitHub conformance-gap issues covering every confirmed difference between the current
  v2.0.0 alpha implementation and the approved v2.0.0 specifications, aggregated through
  a v2.0.0 milestone or project.
- A deprecation register and an overall deprecation policy/strategy covering both
  pre-existing deprecations and deprecations discovered or proposed during this work.
- Documentation build, link, spelling, and example validation appropriate to the files
  changed.

### Example Source Policy

Use example sources in this order:

1. implementations and tests in the core `geoips` repository
2. purpose-built examples in `geoips_plugin_example`
3. templates in `template_basic_plugin`
4. other officially maintained GeoIPS plugin packages only when the preferred sources do
   not demonstrate the required behavior

Normative requirements and minimal examples must remain understandable within the
specification itself. External packages provide supplemental realistic examples and must
not be the sole evidence for required behavior. When exact source matters, use a versioned
tag or commit link. If no durable example exists, prefer adding a small tested example to
`geoips_plugin_example` during later implementation work.

External examples must support the relevant GeoIPS v2 behavior, have applicable tests or
other verification, use public or understandable synthetic inputs, and demonstrate the
target contract rather than behavior being deprecated. Do not make eligibility depend on
identified package maintainers or archived/experimental/retirement metadata: GeoIPS does
not currently maintain those classifications. Private/internal packages and incidental
local workspace copies are not acceptable published references.

### v2.0.0 Legacy Compatibility Test Baseline

The compatibility matrix includes every current integration test from the core `geoips`
package and every official GeoIPS plugin package, including `data_fusion`,
`geoips_clavrx`, and all other packages identified by the official package inventory. Do
not use a hand-selected subset merely because some packages duplicate interfaces or
procflows exercised elsewhere.

The inventory phase will discover and record the complete official package set, all legacy
run scripts and Products exercised by their integration tests, required test datasets,
entry procflows, expected artifacts, comparison outputs, and runtime conversion paths.
Tests passing when the baseline is established are release-blocking compatibility cases
unless an explicit deprecation or approved compatibility decision removes them from the
v2.0.0 contract. Missing infrastructure or unavailable test data must be tracked rather
than silently excluding an official package.

### Legacy Implementation and Converter Removal Gates

Existing legacy procflow implementations MUST NOT be removed until all of the following
conditions are satisfied:

- automatic legacy-procflow-call-to-Workflow conversion is implemented
- every supported legacy call form and argument is mapped or produces a deliberate,
  documented migration error
- all core and official-package compatibility tests pass through the converted OBP path
- scientific results, required metadata, expected artifact contents, filenames, exit
  behavior, and other contractual outputs are equivalent
- Product runtime conversion and the persistent Product conversion script produce
  equivalent Workflows through the shared canonical conversion behavior
- official-package coverage has corresponding Workflow and CLI tests
- actionable warnings and migration instructions are available
- the group-approved warning window has elapsed
- every retained behavior has an OBP equivalent
- known differences are fixed or approved as changes to the v2.0.0 contract
- conversion failures provide sufficient diagnostics and an approved recovery path

Removing a legacy procflow implementation does not automatically remove its runtime
compatibility converter. Later removal of Product and procflow-call converters requires:

- official repositories contain no legacy Products or procflow calls except deliberate
  compatibility/removal fixtures
- conversion tooling has been available for the approved migration period
- the legacy entry points' own deprecation windows have elapsed
- compatibility tests have moved from verifying successful conversion to verifying the
  documented post-removal behavior

### Out of Scope Unless Added by a Later Decision

- Changing plugin runtime behavior or public APIs.
- Implementing runtime fixes or deprecation machinery. This documentation task will
  identify and track required changes; implementation work should be scheduled separately
  unless explicitly brought into scope later.
- Rewriting tutorials, generated API reference, or YAML-based interface specifications.
- Treating `geoips/interfaces/class_based/workflow.py` as a plugin interface unless the
  inventory phase establishes that it is registered as one. It currently appears to be
  workflow runtime machinery rather than an interface.
- Documenting historical module-based plugin behavior except where needed for migration
  or compatibility context.

## Preliminary Interface Inventory

The current source tree contains the following apparent registered class-based
interfaces. This list must be verified against runtime interface discovery and the
plugin registry before it is considered final.

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
- Sector specification generators
- Title formatters
- Validators

The inventory phase must also record interfaces that are deprecated, transitional,
internal-only, or intentionally excluded.

### Target v2.0.0 Interfaces Not Yet in the Current Inventory

The v2.0.0 specification set will also define two new class-based interfaces:

- `SplitOperators`
- `JoinOperators`

Neither is implemented today. In the current code, `split` and `join` are reserved
scaffolding kinds: `SCAFFOLD_KINDS` in `geoips/pydantic_models/v1/workflows.py` accepts
them during schema validation and defers them to workflow orchestration rather than
resolving them through the plugin registry. Promoting them to registered class-based
interfaces is therefore a change in kind — from orchestration scaffolding to resolved
plugins — and brings with it plugin resolution, argument models, registry entries, and
kind naming under the shared Lexeme rules. The specifications must state that transition
explicitly rather than describing these interfaces as though they already exist.

Their exact class names, registry names, argument contracts, and DataTree semantics must
be established during specification work. Both produce data-bearing steps because they
reorganize or combine processing datasets. They must be included in the coverage matrix,
with missing or partial runtime implementations tracked in GitHub conformance-gap issues.

At the planning level, split operators reorganize data into declared branches or groups,
while join operators combine selected inputs and may construct new dimensions. Both use
the standard step/dataset hierarchy, preserve provenance, identify contributing steps,
and define structural requirements without assuming scientific compatibility. Join
operators MUST validate dimensions and coordinates and MAY check conflicting declared
units. Final registry/class names, the migration path from the current scaffolding kinds,
canonical arguments, branch semantics, dataset naming, metadata propagation, errors,
retention, and compatibility behavior are explicit deliverables of their interface
specifications rather than prerequisites for this plan.

## Required Content for Every Interface Specification

Each interface page must answer the following questions explicitly, even when the answer
is "none," "not applicable," or "not yet defined":

1. What `kind` token does a workflow step use to invoke this interface, and how does that
   token resolve to the interface? Plugin kinds are the singular form of the registered
   interface name, resolved through the project's shared Lexeme pluralization rules; the
   page MUST state its kind token and MUST NOT define a competing naming rule.
2. Does the interface produce data-bearing or non-data-bearing steps, and what semantic
   result establishes that classification? Does the current DataTree representation
   conform to the target classification?
3. Which data-bearing steps, data nodes, or metadata must exist before this step runs?
4. What output data and metadata does the step add to, replace in, or remove from the
   returned data tree?
   How are variables grouped into coordinate-compatible datasets, how are output
   `dataset_id` values determined, and does the operation preserve, split, merge, or
   replace its input dataset groups?
   What units are required, accepted, preserved, converted, or produced for variables and
   coordinates?
5. What positional or other non-data arguments are accepted?
6. What keyword arguments are accepted, including defaults and required/optional status?
   Which form is canonical for future-facing plugins, and which accepted forms are
   deprecated compatibility inputs?
7. What argument conduits exist for the interface, where do their values originate, and
   how are collisions, missing values, and overrides handled?
   Which name is canonical, and which names are conduit bindings, legacy aliases, or
   interface-specific translations?
8. What deprecated positional arguments or keyword arguments remain accepted?
9. For each deprecated argument, what is the current warning/compatibility behavior and
   the target deprecation schedule and migration strategy?
10. Where do this interface's plugins sit on the family/`data_tree` migration axis, and
    which plugins remain unmigrated? In the current implementation the presence of a
    `family` attribute is the legacy marker and `data_tree=False` selects the
    unwrap/rewrap conversion path, while `data_tree=True` with no `family` is the
    DataTree-native target state. Because families are deprecated in v2.0.0 and retained
    only for legacy support, each remaining family-bearing plugin is a conformance gap and
    a deprecation-register entry, not a future-facing contract feature.
11. Does the current alpha implementation conform to this part of the v2.0.0 contract? If
    not, what GitHub conformance-gap issue tracks the difference?
12. Which parts of the contract are required to keep legacy products and run scripts
    working, and how do they bridge to workflows, CLI calls, and the OBP-native contract?

Each page should additionally document, where relevant:

- purpose and common use cases
- families still accepted for legacy support, their call signatures, and their deprecation
  status; families are not part of the future-facing v2.0.0 contract
- base plugin class and inheritance relationship, distinguishing interface-level base
  classes from family/legacy scaffolding and from shared implementation helpers
- input and output types outside the DataTree wrapper
- input/output unit contracts and unit metadata behavior
- lifecycle hooks and interface-specific conversions
- required attributes and plugin registration requirements
- exceptions, validation rules, and failure modes
- interaction with legacy procflows versus OBP
- user-facing compatibility requirements for legacy products and run scripts
- a minimal example and links to representative production plugins
- known limitations, open design questions, and compatibility notes

## Standard Page Outline

The first specification drafted will be
`docs/source/devguide/deprecations.md`. Its initial outline will be:

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

As with every specification, create only this outline and its bottom reference-links
section first, then fill it incrementally. Approval authority and minimum warning windows
may remain clearly marked pending group decisions; they do not prevent specifying the
registry and warning mechanics.

Use the following starting outline for the base-class page and adapt it only when a
section is genuinely not applicable:

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

The `Reference links` section belongs at the bottom of every draft from its first commit.
It should initially contain the code, tests, existing documentation, issues/design
records, and representative plugins expected to support the page. Links may be refined
as drafting proceeds, but unsupported claims must not be added simply to fill a heading.

## Per-Document Working Method

Every specification document will be developed as a small, reviewable unit:

1. **Create the skeleton.** Add the agreed outline and a bottom-of-page reference-links
   section. Do not fill the full page during this step.
2. **Build an evidence map.** For every planned section, identify relevant source classes,
   tests, runtime registry information, existing docs, and representative plugins.
3. **Resolve contract questions.** Record ambiguities in the applicable specification or
   tabled-topic section instead of presenting inferred behavior as settled fact. Decide
   the desired v2.0.0 behavior; do not simply copy accidental alpha behavior into the
   contract.
4. **Draft one coherent section group.** Prefer a small group such as step inputs/outputs
   or arguments/conduits rather than filling all headings at once.
5. **Add or verify examples.** Prefer concise examples based on real plugins. Test code
   where practical and state when an example is illustrative rather than executable.
6. **Review terminology and links.** Reuse canonical terms and cross-reference existing
   explanations instead of recreating them.
7. **Reconcile implementation.** Compare every normative requirement with current code
   and tests, then create or update gap and deprecation entries for differences.
8. **Validate the page.** Run the validation commands recorded in Phase 0, then run any
   focused tests or introspection needed to verify signatures and examples.
9. **Update this plan.** Mark progress, record decisions, and select the next small unit.

## Execution Phases

### Phase 0: Confirm Documentation Architecture

- [x] Decide the final location and naming convention for the specification pages.
- [x] Decide whether the base-class contract is one page or separate interface/plugin
      pages with a shared landing page.
- [x] Decide whether existing interface pages will be expanded in place or whether new
      specification pages will be linked from them.
- [x] Select MyST Markdown as the format for all new specification documents.
- [ ] Establish canonical terms for "data-bearing step," "non-data-bearing step,"
      "argument conduit," "returned data tree," and "family."
- [ ] Record the `kind`-to-interface resolution rule so every interface page states its
      kind token consistently. Plugin kinds are the singular form of a registered
      interface name and span both class-based and YAML-based interfaces; `split` and
      `join` are currently reserved scaffolding kinds that bypass plugin resolution
      entirely.
- [ ] Define the classification rule for intermediate classes under
      `geoips/interfaces/class_based/bases/`. Each is either family/legacy scaffolding,
      documented only as deprecated compatibility and registered in the deprecation
      register, or shared implementation reuse that is explicitly out of specification
      scope. Record the rule so per-interface pages do not decide this ad hoc.
- [ ] Record how family deprecation and the `data_tree` migration relate, so pages treat
      them as one migration axis rather than two independent topics.
- [ ] Define the standardized argument vocabulary and distinguish semantic argument
      names, canonical public names, conduit bindings, legacy aliases, and translations.
- [ ] Define a canonical argument matrix covering name, meaning, type, cardinality,
      units, default, required status, valid values, precedence, and applicable
      interfaces/families, plus the single authorized upstream plugin kind for derived
      values.
- [ ] Define rules preventing new plugins and examples from introducing noncanonical
      argument names without an approved specification change.
- [x] Establish BCP 14 requirement-language conventions and rules for distinguishing normative
      requirements from rationale, examples, compatibility notes, and conformance issues.
- [ ] Define the `v2-spec-gap` GitHub issue template, labels, milestone/project workflow,
      and criteria that make a gap release-blocking for v2.0.0.
- [ ] Define the deprecation lifecycle, minimum notice periods or release milestones,
      approval authority, warning requirements, migration-documentation requirements,
      and exceptions process.
- [ ] Design the central core deprecation registry, stable deprecation IDs, lookup/warning
      helpers, and validation linking distributed compatibility code to registry entries.
- [ ] Define measurable readiness criteria for removing direct legacy-procflow support,
      including legacy-product-to-workflow conversion, run-script-to-CLI conversion, OBP
      feature parity, validation, ecosystem adoption, and an agreed compatibility window.
- [ ] Record documentation ownership/audience boundaries among functionality docs,
      developer guide, architecture docs, tutorials, and API reference. Extend the
      existing `docs/source/architecture/documentation/where-to-put.rst` guidance rather
      than creating a parallel rule set.
- [ ] Record the exact validation commands every page runs, so all pages are checked
      identically. Starting candidates: `./docs/build_docs.sh . geoips` for the
      documentation build, `geoips lint` for linting, and the repository's cspell
      configuration for spelling. Confirm the real invocations and any required options.
- [ ] Adopt MyST style conventions for new pages, chosen so they remain valid as the
      remaining reStructuredText documentation migrates:
      - `(label)=` targets immediately before headings, with a page-level target matching
        the filename stem
      - the `{ref}` role for internal cross-references and plain Markdown links only for
        external URLs, because `{ref}` is what `:ref:` converts to and is the only form
        that resolves while reStructuredText and MyST pages coexist
      - colon-fenced directives (`:::{note}`) for prose-bearing directives and
        backtick-fenced directives for content-bearing ones such as `{mermaid}` and
        `{contents}`
      - ATX headings only, one H1 per page, sentence case, no skipped levels
      - GitHub-flavored pipe tables
      - semantic line breaks (one sentence or clause per line) rather than a fixed column,
        so requirement-level changes produce reviewable diffs

**Exit criterion:** page architecture and terminology are agreed before specification
content is drafted.

### Phase 1: Draft the Deprecation Specification

- [ ] Create `docs/source/devguide/deprecations.md` in MyST.
- [ ] Add only the approved outline and initial reference links.
- [ ] Inventory existing warning helpers, warning categories, deprecation modules,
      compatibility adapters, release notes, and tests.
- [ ] Specify a lightweight typed `DeprecationRecord` and immutable core registry.
- [ ] Specify stable IDs and the `warn_deprecated()` helper contract.
- [ ] Specify how distributed warning and normalization sites reference registry entries.
- [ ] Define validation, testing, and documentation-generation requirements.
- [ ] Mark approval authority and warning-window policy as pending group decisions.
- [ ] Compare the specification with current implementation, create confirmed GitHub
      conformance-gap issues, and seed deprecation tracking without implementing runtime
      changes in this documentation task.
- [ ] Review and validate the completed specification.

**Exit criterion:** later interface specifications can register and describe deprecations
consistently without inventing page-specific tracking or warning behavior.

### Phase 2: Build and Verify the Interface Inventory

- [ ] Query runtime interface discovery and the plugin registry.
- [ ] Reconcile runtime results with `geoips/interfaces/class_based/` and its `bases/`
      directory.
- [ ] Add the target `SplitOperators` and `JoinOperators` interfaces to the coverage
      matrix and record their missing or partial implementations as v2.0.0 gaps.
- [ ] Identify interface families and representative plugins in GeoIPS and maintained
      plugin packages.
- [ ] Discover the complete set of official GeoIPS plugin packages and inventory every
      current integration test, explicitly including `data_fusion` and `geoips_clavrx`.
- [ ] Build the legacy compatibility matrix from core and all official-package integration
      tests, recording run scripts, Products, procflows, test data, expected artifacts,
      comparison outputs, conversion paths, and release-blocking status.
- [ ] Mark deprecated, transitional, internal, or incomplete interfaces.
- [ ] Classify each class-based interface as data-bearing or non-data-bearing from its
      semantic result, compare that target with its current DataTree representation, and
      identify the YAML metadata-only dependencies that configure it.
- [ ] Inventory all existing deprecation warnings, compatibility shims, deprecated
      arguments/kwargs, deprecated families, and deprecated interfaces in code, tests,
      release notes, and documentation.
- [ ] Document the current and target runtime path for converting legacy Products into
      OBP Workflows.
- [ ] Register legacy Products and Product-to-Workflow runtime conversion as related but
      distinct deprecations with coordinated migration and removal criteria.
- [ ] Specify the automated Product-to-Workflow conversion script, its inputs, generated
      Workflow output, validation, overwrite/idempotency behavior, diagnostics, and tests.
- [ ] Require the conversion script and runtime conversion to use the same canonical
      conversion engine and add equivalence tests for representative Products.
- [ ] Inventory legacy procflow call forms that the planned runtime procflow-to-Workflow
      converter must accept while existing procflows remain available.
- [ ] Register legacy procflow calls and automatic procflow-to-Workflow conversion as
      related but distinct deprecations with coordinated migration and removal criteria.
- [ ] Inventory conduit bindings, positional alias mappings, interface hook translations,
      explicit-argument precedence, and fallback/default behavior.
- [ ] Compare direct-dependency collection with candidate latest-relevant-step semantics
      and create GitHub conformance-gap issues only after the target behavior is approved.
- [ ] Trace class-based plugin calls in scripting mode and determine how they find the
      most recent step satisfying each conduit.
- [ ] Compare scripting and OBP behavior for omitted, partial, and complete `depends_on`
      declarations.
- [ ] Record the team's decision about implicit per-conduit edges, explicit dependency
      behavior, and missing-source errors; then specify the approved semantics.
- [ ] Verify that each conduit has exactly one authorized upstream plugin kind; treat any
      collisions as design problems rather than establishing cross-kind precedence.
- [ ] Specify unused-result warnings and track their implementation separately. Results
      deliberately retained as workflow outputs are not unused.
- [ ] Map every currently accepted argument to a canonical argument, a justified
      interface-specific argument, or a deprecation candidate.
- [ ] Group derived arguments by their authorized upstream plugin kind and flag any
      argument that appears satisfiable by multiple kinds as a design conflict.
- [ ] Inventory both ingress legacy-to-canonical normalization and canonical-to-legacy
      plugin invocation adapters, ensuring they share one compatibility mapping.
- [ ] Specify conflict errors for simultaneous canonical and deprecated caller forms and
      asymmetric warning behavior for users versus internal legacy-plugin adaptation.
- [ ] Seed the deprecation register, distinguishing already-announced deprecations from
      new candidates discovered during this work.
- [ ] Create a coverage matrix mapping each interface to source, tests, existing docs,
      examples, and an intended specification page.

**Exit criterion:** every registered class-based interface appears exactly once in the
coverage matrix, with exclusions explained.

### Phase 3: Specify the Common Base Classes

- [ ] Create only the base specification outline and its initial reference links.
- [ ] Map inherited behavior from `pluginify` separately from GeoIPS-defined behavior.
- [ ] Inventory attributes and methods on `BaseClassInterface` and `BaseClassPlugin`.
- [ ] Classify each item as required, optional, inherited, internal, overrideable, or
      prohibited from override.
- [ ] Document the invocation sequence and pre/post-call hooks.
- [ ] Document DataTree/native conversion, metadata propagation, scripting behavior, and
      OBP conduit handling.
- [ ] Specify universal workflow/step provenance separately from interface-specific
      dataset identity metadata.
- [ ] Specify retention policy, explicit request, current state, and decision reason using
      a compact reason vocabulary.
- [ ] Compare current garbage collection with dataset-child storage under
      `/<step_id>/<dataset_id>` and create confirmed GitHub conformance-gap issues.
- [ ] Add a minimal plugin example and verify it against current registration rules.
- [ ] Compare every base-class requirement against current alpha behavior and create
      GitHub conformance-gap issues without weakening the target specification.
- [ ] Verify that the base-class target contract preserves behavior required by legacy
      products and run scripts while clearly separating internal procflow compatibility
      from the OBP-native contract.
- [ ] Cross-link existing authoring and migration documentation.
- [ ] Validate and review the completed base specification.

**Exit criterion:** the common contract is stable enough that interface pages can link to
it without restating inherited behavior.

### Phase 4: Pilot One Interface Specification

- [ ] Select one representative interface with meaningful data flow, families, conduits,
      and existing tests. Algorithms or readers are likely candidates; choose only after
      the inventory is complete.
- [ ] Create the outline and initial reference links only.
- [ ] Complete the evidence map.
- [ ] Fill the page incrementally using the standard outline.
- [ ] Review whether the template adequately distinguishes family-specific behavior.
- [ ] Revise the standard outline and validation checklist based on the pilot.

**Exit criterion:** one accepted interface page establishes the pattern for the remaining
pages.

### Phase 5: Specify Remaining Interfaces in Small Batches

Work in reviewable batches based on related data flow, while completing and validating
one page at a time. The exact grouping is a planning aid, not a required publishing
structure.

- [ ] Data ingestion and transformation: readers, algorithms, interpolators.
- [ ] Data composition and branching: split operators and join operators.
- [ ] For split/join pages, begin with outlines and evidence maps before deciding registry
      names, families, relationship to built-in workflow kinds, or detailed semantics.
- [ ] Specify mandatory join dimension/coordinate validation and its errors, plus any
      optional declared-unit checks and their warning/error behavior.
- [ ] Sector construction and adjustment: sector metadata generators, sector
      specification generators, sector adjusters.
- [ ] Visualization and output: colormappers, output formatters, filename formatters,
      title formatters.
- [ ] Decisions and validation: coverage checkers, validators, output checkers.
- [ ] Services and orchestration: databases and procflows.

For every page in a batch:

- [ ] Create outline and initial reference links.
- [ ] Complete all required interface questions.
- [ ] Separate common behavior from family-specific behavior.
- [ ] Verify arguments and conduits from code and tests.
- [ ] Add or update the canonical argument matrix and record each noncanonical accepted
      name in the deprecation register.
- [ ] Include appropriate examples.
- [ ] Record deprecations and label unapproved schedules as proposals.
- [ ] Record every confirmed target/current mismatch in a GitHub conformance-gap issue.
- [ ] Verify legacy product and run-script compatibility and record any regression risk;
      do not require preservation of internal procflow APIs unless user-facing support
      currently depends on them and no replacement exists yet.
- [ ] Validate documentation and links.
- [ ] Update the coverage matrix and progress tracker.
- [ ] Add one release note per pull request under `docs/source/releases/latest/`. Release
      notes are per-PR, not per-page, so a batch that ships as a single PR needs a single
      note covering the pages it contains.

**Exit criterion:** every verified interface has a complete, validated specification or
an explicitly approved exclusion.

### Phase 6: Integrate the Documentation

- [ ] Link the base specification and interface specifications into the interfaces
      landing page.
- [ ] Add links from the class-based plugins overview and writing guide.
- [ ] Add targeted links from architecture, DataTree, OBP, migration, registry, tutorial,
      and API-reference pages where useful.
- [ ] Check for conflicting or obsolete statements in existing pages and resolve them in
      scope rather than silently leaving contradictions.
- [ ] Ensure compatibility notes link to the deprecation registry and implementation
      discrepancies link to their GitHub conformance-gap issues where appropriate.
- [ ] Check navigation labels, anchors, backlinks, and orphan pages.

**Exit criterion:** intended audiences can reach the specifications from the places they
are most likely to begin.

### Phase 7: Final Consistency and Quality Review

- [ ] Run the full documentation build with warnings treated appropriately.
- [ ] Run link and spelling checks supported by the project.
- [ ] Verify public names, signatures, families, and defaults against the current code.
- [ ] Verify every normative requirement has a conformance result and every confirmed
      mismatch has a GitHub conformance-gap issue.
- [ ] Verify all examples and representative-plugin links.
- [ ] Search for required interface questions missing from any page.
- [ ] Review terminology, deprecation language, and data-tree path notation across pages.
- [ ] Obtain maintainer approval for the v2.0.0 contract, release-blocking gap decisions,
      deprecation schedules, migration strategy, and unresolved design claims.
- [ ] Confirm every release-blocking conformance-gap issue has been resolved or explicitly
      waived by the responsible release authority before declaring the effort complete.
- [ ] Confirm every pull request in the effort carried its release note under
      `docs/source/releases/latest/`.

**Exit criterion:** documentation is internally consistent and builds successfully; the
v2.0.0 contract is approved; deprecations have approved schedules and migration paths;
and all release-blocking gaps are resolved or explicitly waived.

## Evidence and Accuracy Rules

- The approved v2.0.0 design is authoritative for the specification. Treat executable
  code and focused tests as evidence of current alpha behavior and conformance, not as the
  automatic definition of the contract.
- If desired v2.0.0 behavior is not yet approved, record it as an open design decision;
  do not describe either the current behavior or a preferred alternative as normative.
- Use runtime introspection to supplement source reading, especially for inherited
  signatures and registry discovery.
- Trace GeoIPS subclasses into `pluginify` when behavior is inherited; do not attribute
  inherited behavior to GeoIPS without qualification.
- Distinguish public contract from implementation detail. Internal helpers should appear
  only when plugin or interface authors must understand their effects.
- Do not infer a deprecation deadline from a comment or warning alone. Record the current
  behavior, first-known announcement, source of the proposal, compatibility impact,
  replacement, migration steps, milestones, owner, and approval status.
- New deprecation candidates discovered during research must enter the same review process
  as existing deprecations and must not be presented as approved merely because the
  current API is inconvenient or inconsistent.
- When code, tests, and existing docs disagree, record the conflict before choosing which
  behavior to specify.
- Use stable Sphinx/MyST cross-references for internal documentation and source links only
  when source-level detail materially helps the reader.

## Definition of Done for One Specification Page

A page is complete when:

- [ ] Its audience and scope are clear.
- [ ] It includes the BCP 14 notice and uses uppercase requirement keywords only for
      normative contract requirements.
- [ ] Every **SHOULD** or **SHOULD NOT** requirement explains the consequences of an
      exception, and every **MAY** requirement defines relevant interoperability behavior.
- [ ] Every standard heading is completed or explicitly marked not applicable.
- [ ] Every required interface question is answered.
- [ ] Common and family-specific behavior are distinguishable.
- [ ] Arguments include names, meanings, types where useful, defaults, required status,
      and value sources.
- [ ] Canonical arguments are recorded in the shared matrix and use consistent semantics
      across applicable interfaces and families.
- [ ] Every noncanonical accepted argument is isolated to a compatibility boundary,
      absent from future-facing examples, and linked to a deprecation entry.
- [ ] Canonical/deprecated argument conflicts and precedence are specified and tested or
      tracked in GitHub conformance-gap issues.
- [ ] Data-tree inputs and outputs identify paths and metadata keys precisely where the
      v2.0.0 contract defines them.
- [ ] The interface's `kind` token is stated and matches the shared kind-to-interface
      resolution rule.
- [ ] The interface's position on the family/`data_tree` migration axis is stated, families
      retained for legacy support are marked deprecated rather than presented as contract
      features, and each unmigrated plugin has a conformance-gap issue and a
      deprecation-register entry.
- [ ] The interface's data-bearing or non-data-bearing classification is stated and
      justified by its semantic result rather than its implementation format.
- [ ] Output variables are assigned to coordinate-compatible dataset groups, and the
      interface defines how output `dataset_id` values are selected.
- [ ] Existing interface-specific unit locations, accepted inputs, outputs, and behavior
      are described where applicable without establishing new shared v2.0.0 handling.
- [ ] Shared unit handling and automatic conversion are identified as v2.1-or-later work,
      not v2.0.0 conformance requirements.
- [ ] Any preservation, splitting, merging, replacement, or removal of input dataset
      groups is documented.
- [ ] Output formatter specifications document the non-data-bearing classification,
      identify what metadata is recorded in step attrs (written paths, checksums, mime
      types), and include a minimal example.
- [ ] No requirement or example places a data variable on the workflow root; root content
      is limited to step children and workflow-level attributes.
- [ ] Conduits explain source, binding, precedence, missing-value behavior, and examples.
- [ ] Deprecations distinguish current support from proposed removal.
- [ ] At least one useful example or a justified statement that no example is appropriate
      is present.
- [ ] Claims are backed by the reference-links section or an approved design decision.
- [ ] Normative statements describe the v2.0.0 target rather than merely restating alpha
      behavior.
- [ ] Current implementation conformance has been checked and all confirmed differences
      have GitHub issues, dispositions, and release-blocking classifications.
- [ ] Existing and newly discovered deprecations appear in the deprecation register with
      migration guidance and approved or clearly proposed schedules.
- [ ] Internal cross-references resolve and external links are appropriate.
- [ ] Relevant documentation checks pass.
- [ ] Progress and decisions are updated in this plan.

## Tracking Record Templates

Use these fields so discoveries are recorded consistently. Confirmed conformance gaps live
in GitHub; deprecations live in the typed core registry.

### Conformance-Gap GitHub Issue

| Field | Meaning |
| --- | --- |
| Issue | GitHub issue number and `v2-spec-gap` label |
| Specification requirement | Link or requirement identifier for the v2.0.0 target |
| Interface/family | Affected contract scope |
| Alpha behavior | What the current implementation and tests do |
| Gap type | Missing, divergent, ambiguous, obsolete, or test/documentation-only |
| Evidence | Source, test, runtime result, issue, or design record |
| User/release impact | Consequence of shipping the gap |
| Legacy entry-point impact | Products, run scripts, outputs, or users that could regress |
| Resolution | Required code, test, or documentation change |
| Owner and milestone | Responsible party and intended completion point |
| Release blocking | Yes, no, or pending decision, with rationale |
| Status | Open, in progress, resolved, waived, or deferred through GitHub workflow |

### Deprecation Entry

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

No schedule is approved merely by being entered in the register. Conversely, an existing
runtime warning without a recorded migration path and schedule is an incomplete
deprecation that must be resolved before the documentation effort is complete.

## Progress Tracker

| Deliverable | Status | Notes |
| --- | --- | --- |
| Planning document | Complete | Initial shared plan; specification work not started |
| Documentation architecture | Not started | Phase 0 |
| Deprecation specification | Not started | `docs/source/devguide/deprecations.md`; Phase 1 |
| Verified interface inventory and coverage matrix | Not started | Phase 2 |
| GitHub conformance-gap tracking | Not started | Issue process defined in Phase 0 |
| Deprecation register and strategy | Not started | Specified in Phase 1; populated throughout |
| Canonical argument matrix | Not started | Defined in Phase 0; populated per interface |
| Base interface/plugin specification | Not started | Phase 3 |
| Pilot interface specification | Not started | Phase 4 |
| Remaining interface specifications | Not started | Phase 5 |
| Cross-document integration | Not started | Phase 6 |
| Final consistency review | Not started | Phase 7 |

Use only these status values: `Not started`, `Outline`, `Researching`, `Drafting`,
`Reviewing`, `Blocked`, and `Complete`.

## Tabled Design Topic: `depends_on` and Conduit Resolution

The larger GeoIPS team will decide this behavior separately. Do not treat the candidate
behavior as normative or begin implementation work from it. When the team returns a
decision, complete this investigation as needed:

1. Trace scripting calls from script-tree initialization through `BaseClassPlugin` conduit
   extraction and result attachment.
2. Construct scripting examples with repeated data-bearing, sector, and filename-formatter
   steps and identify exactly which prior result supplies each conduit.
3. Test whether scripting selects the most recent matching kind, how explicit arguments
   interact with that selection, and what happens when a required kind is missing.
4. Compare those results with OBP workflow validation, implicit `depends_on` injection,
   topological ordering, upstream collection, and conduit extraction.
5. Evaluate a DAG model where omitted dependencies create implicit edges to the most
   recent step required for each conduit, while explicit `depends_on` entries replace only
   automatically selected sources of the same kind.
6. Determine how required conduits are declared so the DAG can be composed before runtime.
7. Define unused-result warnings and missing-required-conduit errors.
8. Create GitHub conformance-gap issues for confirmed current/target discrepancies and
   update the normative specifications from the approved team decision.

Known evidence retained for that discussion: current OBP defaults a missing `depends_on`
to the immediately previous step and collects only resolved dependency nodes. The focused
two-sector check produced `second` for implicit dependency and `first` for
`depends_on: ["first"]`; this does not establish the broader per-conduit behavior.

**New direction under active discussion:** The team is exploring a formulation in which a
container object — accessible by all steps — holds the root DataTree, provides methods for
interacting with its contents, and is visible to every plugin when it is called so the
plugin can attach its own output. Under this model, explicit `depends_on` declarations may
become optional or take on a different role: steps would query the container for upstream
results rather than receiving a pre-collected subtree. This has unresolved implications
for topological ordering, conduit resolution, unused-result detection, DAG composability
before runtime, and the relationship between scripting and OBP execution. Investigation
items 1–8 above should be revisited once the container model is more fully defined and the
team has decided its effect on dependency semantics.

This discussion also governs the workflow terminology question. Two distinct things
currently share the name:

- `workflows`, a registered **YAML-based** plugin interface whose plugins are specification
  artifacts defining an ordered series of steps. This is what exists today.
- A possible internal workflow **container object** as described above, which would be
  runtime machinery rather than a plugin.

The datatree spec conflates these in §4.1, §4.7, and §15.2. Do not resolve the conflation,
rename either concept, or specify the container object until the team finalizes this
discussion. Until then, specification pages MUST refer to the YAML-based `workflows`
interface when they mean the registered plugin interface, and MUST NOT describe an
internal container object as though it were a registered class-based interface.

## Tabled Governance Topic: Deprecation Approval and Timing

The group will decide minimum warning windows and removal timing separately using its
established responsibility and approval processes. Do not assume that removal waits for
v3.0.0; GeoIPS may remove deprecated behavior within the v2 release series after the
approved warning window, migration readiness criteria, and user-facing compatibility
requirements are satisfied. Existing deprecations without an approved schedule remain
tracked as schedule pending.

## Initial Planning References

These are starting points for the task. Each future page will maintain its own narrower
reference-links section.

- `geoips/interfaces/base.py` — GeoIPS `BaseClassInterface` and interface validation
  integration.
- `geoips/interfaces/class_based_plugin.py` — `BaseClassPlugin`, lifecycle hooks,
  DataTree conversion, scripting behavior, and conduit integration.
- `geoips/interfaces/class_based/` — registered interface objects.
- `geoips/interfaces/class_based/bases/` — interface-level base plugin classes and family
  behavior.
- `geoips/utils/types/obp_conduits.py` — conduit bindings and extraction behavior.
- `geoips/utils/types/script_datatree.py` — scripting DataTree call/result behavior.
- `docs/source/devguide/datatree-spec.md` — current DataTree specification.
- `docs/source/functionality/interfaces/index.rst` — interface documentation navigation.
- `docs/source/functionality/interfaces/writing-class-based-plugins.md` — class-based
  plugin authoring guidance.
- `docs/source/functionality/interfaces/class_based/` — existing per-interface pages.
- `docs/source/functionality/plugins/class-based/index.rst` — class-based plugin overview.
- `docs/source/devguide/converting-module-to-class.md` — migration guidance.
- `docs/source/architecture/plugin-registry.md` and
  `docs/source/functionality/plugin-registries.md` — registry architecture and usage.
- `tests/` — focused unit, integration, and interface tests supporting current contracts.
- [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) — requirement-level key words.
- [RFC 8174](https://www.rfc-editor.org/rfc/rfc8174) — clarification that BCP 14 key
  words are normative only when written in uppercase.
