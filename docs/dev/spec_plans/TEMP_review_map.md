# TEMPORARY — Review map for `class_based_plugins.md`

Delete this file once the review pass is finished. It is a scratch reference, not part of
the plan.

Every passage listed below was written or substantially rewritten by Claude. All of it was
approved at summary level — Jeremy saw a description of what was being added, not the text
itself. None of it has been reviewed line by line.

Some authored content now lives in `datatree_spec_reconciliation.md`; those rows are marked
`recon`. References are section numbers, not line numbers. Sections survive edits that shift lines,
so this map no longer goes stale every time the document changes.

---

## Highest priority

These assert facts about the GeoIPS code or about `docs/source/devguide/datatree-spec.md`.
This is the category where errors have actually occurred, so read these closest.

| Section | Content | What to check |
| --- | --- | --- |
| [§7.1](class_based_plugins.md#71-target-v200-interfaces-not-yet-in-the-current-inventory) | `SCAFFOLD_KINDS` paragraph in the split/join section | Asserts `split` and `join` bypass plugin resolution today. Verify against `geoips/pydantic_models/v1/workflows.py` |
| [§13](class_based_plugins.md#13-required-content-for-every-interface-specification) | Required Content Q10, family/`data_tree` axis | Asserts that the presence of a `family` attribute is the legacy marker, and that `data_tree=True` with no `family` is the DataTree-native target state. Verify that coupling |
| [recon §4.1–4.3](datatree_spec_reconciliation.md#41-the-dataset-level-is-ambiguous) | Datatree spec alignment note, three items | Three factual claims about the datatree spec: the datatree spec §3.2 self-contradiction on dataset nodes, the datatree spec §4.1 claim that `workflows` is class-based, and `kind: sectorizer` in datatree spec §3.1 being placeholder text |
| [recon §4.6](datatree_spec_reconciliation.md#46-token-prefix-contradicts-its-own-examples) | Token format convention | Claims the datatree spec abstract's `dask:` prefix contradicts its own `blake2b:` examples |
| [§8](class_based_plugins.md#8-tabled-design-topic-depends_on-and-conduit-resolution) | Container object and workflow terminology, in the tabled design topic | Contains a MUST/MUST NOT that Claude authored. Confirm that stating a normative constraint here is intended while the design is still open |
| [§6.3](class_based_plugins.md#63-v200-user-facing-backward-compatibility-constraint) | Backward-compatibility constraint, rewritten in full | Asserts the three `geoips run` dispatch forms. Verified against `geoips/commandline/`, but bare `geoips run` is a target, not current behavior — it raises `NotImplementedError` today |

---

## Medium priority

New normative or structural content.

| Section | Content |
| --- | --- |
| [§6.1.4](class_based_plugins.md#614-step-classification) | Output formatter non-data-bearing paragraph |
| [§13](class_based_plugins.md#13-required-content-for-every-interface-specification) | Required Content Q1, `kind` token |
| [§13](class_based_plugins.md#13-required-content-for-every-interface-specification) | Two "additionally document" bullets: families, and base class inheritance |
| [§14](class_based_plugins.md#14-standard-page-outline) | Interface page outline items 3 and 11 |
| [§21.1](class_based_plugins.md#211-phase-0-confirm-documentation-architecture) | Phase 0: `kind`-to-interface resolution rule |
| [§21.1](class_based_plugins.md#211-phase-0-confirm-documentation-architecture) | Phase 0: intermediate class classification |
| [§21.1](class_based_plugins.md#211-phase-0-confirm-documentation-architecture) | Phase 0: family/`data_tree` relationship |
| [§21.1](class_based_plugins.md#211-phase-0-confirm-documentation-architecture) | Phase 0: MyST style conventions — the longest single addition |
| [§19](class_based_plugins.md#19-definition-of-done-for-one-specification-page) | Two Definition of Done items: `kind` token, family/`data_tree` axis |
| [§19](class_based_plugins.md#19-definition-of-done-for-one-specification-page) | Definition of Done item: output formatter |

---

## Low priority

Small edits to text that already existed.

| Section | Content |
| --- | --- |
| [§7.1](class_based_plugins.md#71-target-v200-interfaces-not-yet-in-the-current-inventory) | Removed "families" from the split/join deliverables list |
| [§7.1](class_based_plugins.md#71-target-v200-interfaces-not-yet-in-the-current-inventory) | Reworded to "migration path from the current scaffolding kinds" |
| [§16](class_based_plugins.md#16-per-document-working-method) | Working method step 8 now points at the Phase 0 command list |
| [§21.1](class_based_plugins.md#211-phase-0-confirm-documentation-architecture) | Appended the `where-to-put.rst` sentence to the ownership item |
| [§21.1](class_based_plugins.md#211-phase-0-confirm-documentation-architecture) | Phase 0 validation commands item |
| [§21.6](class_based_plugins.md#216-phase-5-specify-remaining-interfaces-in-small-batches) | Phase 5 release note item |
| [§21.8](class_based_plugins.md#218-phase-7-final-consistency-and-quality-review) | Phase 7 release note confirmation |
| [§5](class_based_plugins.md#5-records-this-work-maintains) | Anchor link to the Requirement Language section, replacing a positional reference |

---

## Structural changes

- **Required Content ([§13](class_based_plugins.md#13-required-content-for-every-interface-specification))** was renumbered from 1–10 to 1–12 when the `kind` and
  family/`data_tree` questions were inserted. The other ten questions are unchanged text
  at shifted numbers.
- **Interface page outline ([§14](class_based_plugins.md#14-standard-page-outline))** was renumbered from 1–17 to 1–18 for the same
  reason.

A search for numeric cross-references to either list found none, but that is worth
confirming independently.

---

## Reorganizations applied

Line numbers are deliberately omitted here — the current structure is visible in the
document itself, and embedding positions in a change log only makes it go stale.

**2026-09-04**

1. **Three-records framing separated from Requirement Language.** The records list and the
   deprecation registry material had been absorbed into `### Requirement Language`, which
   now contains only BCP 14 content.
2. **Data-Bearing section restructured** into `### DataTree Content Model` with seven
   subsections: Step Classification, Workflow Root and Dataset Nodes, Dataset Identity and
   Scientific Compatibility, Provenance and Retention, Units, Dimensions and Composition,
   and Interface Classification in the Inventory. Headings only; no content moved.
3. **Removal Gates relocated** out of `## Scope` to sit beside the Backward-Compatibility
   Constraint, which covers the same subject.
4. **Deprecations outline separated** into its own section, leaving `## Standard Page
   Outline` holding only the two reusable templates.
5. **Records block given its own heading**, with the registry material nested beneath it
   rather than made a peer of Requirement Language.

**2026-09-05 — reordering into bands**

Sections were regrouped so that material describing how to read and use the document is no
longer interleaved with material describing the target state. Five bands, in order:

1. **Orientation** — Purpose, Desired Outcomes, Scope, Requirement Language, Records This
   Work Maintains
2. **Target state** — Specification Model, Preliminary Interface Inventory, and both
   Tabled Topics
3. **How to produce it** — Documentation Location and Format, Required Content, Standard
   Page Outline, Deprecation Specification Outline, Per-Document Working Method, Example
   Source Policy, Evidence and Accuracy Rules, Definition of Done, Tracking Record
   Templates
4. **Schedule and status** — Execution Phases, Progress Tracker
5. **References** — Initial Planning References

The bands are conceptual groupings expressed through ordering; no band headings were added
to the document.

Three sections were lifted out of their previous parents as part of this:
`Records This Work Maintains` out of `Specification Model`, and both `Example Source
Policy` and `v2.0.0 Legacy Compatibility Test Baseline` out of `Scope`. The Test Baseline
moved into `Specification Model` beside the other two compatibility sections rather than
becoming top-level. `Scope` now holds only In Scope and Out of Scope.

Verification: the reordering pass was checked by comparing the sorted line multiset before
and after, which was identical — proving every line survived and only order changed. The
extraction pass was checked the same way with heading markers stripped.

---

## Identified but not applied

Raised during the structural review and deliberately left alone:

- **Argument compatibility pivot ([§6.5](class_based_plugins.md#65-v200-legacy-compatibility-test-baseline)).** The three-stage ingress-normalization /
  canonical-resolution / legacy-invocation-adaptation model is implementation detail
  sitting in a plan, the same category as the registry paragraphs. Candidate to move to
  the base-classes specification. Still outstanding.
- **Example Source Policy** duplicates guidance in `## Per-Document Working Method` step 5,
  which states a compressed version of the same rule. The misfiling under `## Scope` was
  resolved by the band reordering, but the content duplication remains.

Resolved by the band reordering, recorded so they are not re-raised:

- Example Source Policy is no longer filed under `## Scope`; it is now a top-level section
  in the production band.
- `## Evidence and Accuracy Rules` and `## Per-Document Working Method` are no longer
  separated by the Execution Phases block. Both now sit in the production band with only
  Example Source Policy between them.

---

## Known corrections already applied

Recorded so they are not re-litigated during the read:

- The datatree spec alignment note originally said the spec should be updated "to match
  the code and this plan." Corrected to "this plan" only — the code is not an authority
  for a target-state document.
- An earlier version of the intermediate-class analysis described a four-tier class
  hierarchy. That framing was wrong and was replaced with the classification rule now in [§20.1](class_based_plugins.md#201-conformance-gap-issue-template).
- A proposal to define a `CBP-READERS-014` style requirement-ID scheme was dropped. The
  Conformance-Gap issue template already permits "Link or requirement identifier," and
  anchors provide stable link targets.
