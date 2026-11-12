## Abstract

...TODO...

<!-- writing notes: ... -->

---

## Table of Contents

[toc]

## 1. Motivation, Goals, and Non-Goals

### 1.1 Problem

...TODO...

<!-- writing notes: ... -->

### 1.2 Goals

- ...TODO...

<!-- writing notes: ... -->

### 1.3 Non-Goals

- Defining deprecation and/or removal of support for versions of Python or core dependency packages, as is done in NEP 29, SPEC 0, and the like (TODO-EXTERNAL-LINK).
- ...TODO...

<!-- writing notes: ... -->

### 1.4 Limitations of Current Specification

- With [canonical plugin invocation APIs](https://github.com/NRLMMD-GEOIPS/geoips/issues/1464) unresolved, functional deprecation of invocation signatures *as* signatures (i.e., using Python `@overload`s) cannot be handled within the scope of this *Specification* as it stands, as it would require an entirely separate refactor of how plugins are invoked first. Instead, deprecated argument patterns/names, which are currently handled as pathways through Conduits, should be treated as general deprecations of functionality (i.e., `@deprecated` decorators on functions encapsulating the deprecated functionality, as described in TODO-LINK-SECTION).

<!-- writing notes: ... -->

---

## 2. Normative Language & Terminology

### 2.1 RFC 2119 Keywords

The keywords **MUST**, **MUST NOT**, **REQUIRED**, **SHOULD**, **SHOULD NOT**, **RECOMMENDED**, **NOT RECOMMENDED**, **MAY**, and **OPTIONAL** in this document are to be interpreted as described in BCP 14, [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) and [RFC 8174](https://www.rfc-editor.org/rfc/rfc8174), when, and only when, they appear in all capitals. **MUST**, **MUST NOT**, and **REQUIRED** are absolute. **SHOULD**, **SHOULD NOT**,**RECOMMENDED**, and **NOT RECOMMENDED** permit exceptions, and this document MUST state or link the consequence of an exception. **MAY** and **OPTIONAL** mark optional behavior, and this document MUST define how implementations that take the option interoperate with those that do not. The keywords **SHALL** and **SHALL NOT** are not used.

For ease of presentation, to parallel the keyword **REQUIRED**, the keyword **PROHIBITED** is also defined, with meaning equivalent to the phrase "MUST NOT be used."

The keywords **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** are used in text, naming the respective subject and corresponding observable behavior. The keywords **REQUIRED**, **PROHIBITED**, **RECOMMENDED**, **NOT RECOMMENDED**, and **OPTIONAL** are used in tables, referring to usage or inclusion of the particular entry. Lowercase forms carry ordinary meaning. These keywords are not used to add emphasis or mark a task step.

### 2.2 Glossary

| Term | Definition |
| --- | --- |
| **...TODO...** | ...TODO... |

<!-- list to define: Conduit, ... -->

---

## 3. Quick Example

The following is an example of a deprecated field in a Pydantic model, demonstrating the YAML-parsable GeoIPS standard deprecation message (see TODO-LINK-SECTION for complete description). Other varieties of "things" (as far as they exist in the Python API) may require different specific approaches (see TODO-LINK-SECTION) to fully implement, but the foundational element is this parsable, standardized string (see TODO-LINK-SECTION).

```python
from typing_extensions import deprecated

class ReaderArgumentsModel(PermissiveFrozenModel):
    ...
    chans: List[str] = Field(
        None,
        description="List of variables to read",
        deprecated=deprecated(
            """
            Name: "`chans` argument in Readers"
            Component: Readers
            Reference Issue: https://github.com/NRLMMD-GEOIPS/geoips/issues/953
            Deprecated In: 1.19.0
            Removal In: 2.0.0
            Replacement: "Use `variables` instead"
            """,
            category=geoips.deprecation.GeoipsDeprecationWarning
        )
    )
    ...
```

(Note that here, and throughout the GeoIPS codebase, a `from typing_extensions import deprecated` import is used for the PEP 702 `@deprecated` decorator. This is because the standard `from warnings import deprecated` is not available for Python versions before 3.13, which GeoIPS is expected to still need to support for the foreseeable future.)

---

## 4. Deprecation Lifecycle and Best Practices

...TODO...

<!-- writing notes: ... -->

---

## 5. GeoIPS Deprecation Components

...TODO...

<!-- writing notes: this is just a pretty short description/clarification of what is meant by "deprecation components"; just introduce the notion that every deprecation has 1. A standardized YAML-formatted message string (for users and developers) 2. a canonical reference issue (for developers) and 3. the code which actually implements the deprecation (and issues the warning, etc.) -->

### 5.1 Deprecation Message String

...TODO...

<!-- writing notes: just describe what it is (YAML formatted multiline string), with the fields as in the following table, and able to be validated by pydantic -->

| Name | Typing/Validation | Inclusion | Use/Reason |  
| ---- | ----------------- | --------- | ---------- |
| Name | `str` of ≤70 chars | Public API: OPTIONAL<br>Internal/Private API: REQUIRED | A nice, human-readable "name" to give this deprecation, for display in docs. Useful when deprecating some functionality whose Python API name may not be helpful to the user or developer encountering the deprecation. |
| Component | `str` of ≤40 chars | REQUIRED | Component of GeoIPS in which this deprecation is located (e.g., CLI, Readers, Products). |
| Reference Issue | `AnyUrl` (RECOMMENDED) or `"MISSING"` (NOT RECOMMENDED) | REQUIRED | Canonical reference issue on GitHub (or GitLab, etc.) for this deprecation, containing all anciliary information relevant for developers (see Section 5.2 (TODO LINK) below). |
| Deprecated In | `SemanticVersion` | REQUIRED | Communicates deprecation lifecycle, and can be parsed into PyDeprecate (or equivalent) tooling for lifecycle checks/auditing |
| Removal In | `SemanticVersion` or `"Conditional (see issue)"` | Existing deprecations: RECOMMENDED<br>New deprecations: REQUIRED | Communicates deprecation lifecycle, when a semantic version string, can be parsed into PyDeprecate (or equivalent) tooling for lifecycle checks/auditing. If this is "Conditional (see issue)", the reference issue (not the deprecation message) MUST explanation the conditions/gates/etc to be met before removal can occur. |
| Replacement | `str` of ≤90 chars | RECOMMENDED | A short description of what should be used instead of this deprecated functionality. For more complex migrations, a replacement message like 'Consult the migration guide at INSERT-URL-HERE' is recommended. More verbose descriptions of the replacement can occur in the reference issue. |

**Additional Notes**:
- The v2.0 Specification effort is expected to involve renaming a substantial number of GeoIPS "Components" (e.g., `OutputFormatters` to `Writers` and "YAML-based Plugins" to `PluginConfigs`). Deprecation messages should use the updated name for any of these.
- For existing deprecations re-implemented under this new approach (see PR TODO), the "Deprecated In" field should be set to the minor version in which that deprecation was first implemented, if such can be readily identified via `git blame`, otherwise, setting as "2.0" is acceptable (so long as the "Removal In" version is not also "2.0").
- For "Reference Issue", the string literal `"MISSING"` SHOULD pass Pydantic validation (for cases of existing deprecations prior to reference issue creation) but SHOULD NOT be allowed past review for any new deprecations (the reference issue should be created first).
- "Replacement" is expected to be included in warning messages and documentation in a sentence-like way, either prefaced by something akin to "Replacement/Migration Instructions:" or alone. And so, structure this field as a sentence (e.g., begin with a capitalized imperative verb), but omit final punctuation.
- See TODO-LINK-SECTION for recommendations and requirements about the span between "Deprecated In" and "Removal In" versions.
- Some of this information will be duplicated in the contents of the Reference Issue (see TODO-LINK-SECTION).

### 5.2 Canonical Reference Issue

...TODO...

<!-- writing notes: still need to work out what the form fields for this will be... -->

### 5.3 Implementation

...TODO...

<!-- writing notes: you are intending this to be purposefully brief, likely with a table or some such, with more details referenced to the later section (right?)  -->

---

## 6. Documentation

...TODO...

<!-- writing notes: brief purpose motivation why sort of thing here -->

### 6.1 Deprecation Listing

...TODO...

<!-- writing notes: describe *what we want* in the docs, not necessarily *how* we plan to accomplish it (yet) (right?) -->

### 6.2 Docstrings

...TODO...

<!-- writing notes: this likely needs some additional consideration, given that I'd really like to not have to pipe *every* callable and class through pydeprecate just to get the docstring updates? but otherwise where else are you getting it?? this is in relation to (what is currently) 5.3 and 8.1 -->

---

## 7. CI and Audit Tooling

...TODO...

<!-- writing notes: not sure entirely what to go in to here, other than just say "hey, this is what pydeprecate gets us, we should probably do something with it, but doing too much is too much of a headache until CI is refactored?? -->

---

## 8. Detailed Examples

### 8.1 Enumeration of Varieties

...TODO...

<!-- writing notes: consult old obsidian notes here! -->

### 8.2 Single-Use vs. Re-Used Deprecations

...TODO...

<!-- writing notes: @deprecated is what gets reused in most cases, not the deprecation.deprecate_THING...but sometimes you might? general rule is only reuse the one with the geoips standardized message in it, and never more than one of the compnents! -->

---

## 9. References

- ...TODO...
