## Abstract

v2.0.0 of GeoIPS is anticipated to require a large number of deprecations amidst the changes required for full implementation of the Order-Based Procflow and DataTree-native plugins, allowing a period of backwards compatibility for old behavior while providing a migration path to the corresponding new functionality. To streamline and organize such deprecations, this Specification describes a standardized approach consisting of three primary components: a form-based reference issue, a YAML-formatted information string, and a set pattern of helper function use. This standardization, combined with the underlying helper utilities, will ensure consistent warning messages, docstrings, and rendering in documentation, as well as aid tracking and management of deprecations through their lifecycle from creation to removal.

:::{important}
**Provisional Draft**: This document, in its present state, is a provisional/early draft, intended to lay out essential elements for developers implementing deprecations, so as to not hold back development requiring such while other components of the deprecation effort are finalized. Future versions of this document are expected to contain such expanded details.
:::

---

## Table of Contents

[toc]

## 1. Scope

### 1.1 Goals

- Define a structured approach to deprecations for all expected varieties of deprecated "things" in GeoIPS v2.0.0 and future versions.
- Describe the balance of deprecation approaches between PEP 702 and (wrapped) PyDeprecate.
- Define the set of fields/attributes that every deprecation MUST, SHOULD, or MAY list.
- Outline what GeoIPS deprecation utilities do with the developer-provided components (warning formatting, documentation listings, docstrings, etc.)

### 1.2 Non-Goals

- Defining deprecation and/or removal of support for versions of Python or core dependency packages, as is done in [NEP 29](https://numpy.org/neps/nep-0029-deprecation_policy.html), [SPEC 0](https://scientific-python.org/specs/spec-0000/), and the like.
- Enumerating or defining in advance all expected deprecations to occur in v2.0.0
- Fully specify underlying implementation details of deprecation utilities (e.g., how deprecations are rendered in documentation)

### 1.3 Limitations of Current Specification

- With [canonical plugin invocation APIs](https://github.com/NRLMMD-GEOIPS/geoips/issues/1464) unresolved, and the pattern not envisioned to be widely used outside of it, deprecation of function signatures *as* signatures (i.e., using Python `@overload`s) are not handled within the scope of the current version of this *Specification*. Instead, deprecated argument patterns that are currently handled as pathways through Conduits should be treated as general deprecations of functionality (i.e., `@deprecated` decorators on functions encapsulating the deprecated functionality, as described in Section 8.1.7), and deprecated arguments in workflows should be handled in the appropriate Pydantic model (see Section 8.1.1)
- The "Canonical Reference Issue" form (Section 5.2) has not been finalized as of this draft. For new deprecations being implemented before this form is finalized, it is recommended to link instead to an existing issue describing the deprecation, or a new (generic) issue if such does not exist. Do not list the reference issue as "MISSING" in such cases.
- Details on how deprecations are displayed and tracked are not yet included in the current version of this document, given its current focus on usage examples.

---

## 2. Normative Language & Terminology

### 2.1 RFC 2119 Keywords

The keywords **MUST**, **MUST NOT**, **REQUIRED**, **SHOULD**, **SHOULD NOT**, **RECOMMENDED**, **NOT RECOMMENDED**, **MAY**, and **OPTIONAL** in this document are to be interpreted as described in BCP 14, [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) and [RFC 8174](https://www.rfc-editor.org/rfc/rfc8174), when, and only when, they appear in all capitals. **MUST**, **MUST NOT**, and **REQUIRED** are absolute. **SHOULD**, **SHOULD NOT**,**RECOMMENDED**, and **NOT RECOMMENDED** permit exceptions, and this document MUST state or link the consequence of an exception. **MAY** and **OPTIONAL** mark optional behavior, and this document MUST define how implementations that take the option interoperate with those that do not. The keywords **SHALL** and **SHALL NOT** are not used.

The keywords **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** are used in text, naming the respective subject and corresponding observable behavior. The keywords **REQUIRED**, **RECOMMENDED**, **NOT RECOMMENDED**, and **OPTIONAL** are used in tables, referring to usage or inclusion of the particular entry. Lowercase forms carry ordinary meaning. These keywords are not used to add emphasis or mark a task step.

### 2.2 Glossary

:::{note}
A glossary of key terms will be added here in a future version of this document.
:::

---

## 3. Quick Example

The following is an example of a deprecated field in a Pydantic model, demonstrating the YAML-parsable GeoIPS standard deprecation message (see Section 8.1.1 for complete description). Other varieties of "things" (as far as they exist in the Python API) may require different specific approaches (see Section 8.1) to fully implement, but the foundational element is this parsable, standardized string (see Section 5.1).

```python
from typing_extensions import deprecated

from geoips import deprecation

class ReaderArgumentsModel(PermissiveFrozenModel):
    ...
    chans: List[str] = Field(
        None,
        description="List of variables to read",
        deprecated=deprecated("""
            Entity/Behavior: "`chans` argument in Readers"
            Replacement: "Use `variables` instead"
            Component: Readers
            Reference Issue: https://github.com/NRLMMD-GEOIPS/geoips/issues/953
            Deprecated In: 1.19.0
            Removal In: 2.1.0
        """)
    )
    ...
```

(Note that here, and throughout the GeoIPS codebase, a `from typing_extensions import deprecated` import is used for the PEP 702 `@deprecated` decorator. This is because the standard `from warnings import deprecated` is not available for Python versions before 3.13, which GeoIPS is expected to still need to support for the foreseeable future.)

When such a deprecated field is included in validation input, a `GeoipsDeprecationWarning` is issued, with the following reformatted message:

```
`chans` argument in Readers (Component: Readers) is deprecated as of v1.19.0, and will
be removed in v2.1.0. Replacement/Migration Instructions: Use `variables` instead. See
https://github.com/NRLMMD-GEOIPS/geoips/issues/953 for more information.
```

---

## 4. Deprecation Lifecycle and Best Practices

:::{note}
A more complete description of the lifecycle of deprecations and best practices regarding such will be added here in a future version of this document. In the interim, recommendations include:

- Do not omit the "Replacement" field (see [NEP 23](https://numpy.org/neps/nep-0023-backwards-compatibility.html)).
- When a particular version is used (rather than "Conditional (see issue)"), the "Removal In" field should generally be no less than two minor versions after the "Deprecated In" version.
- When deprecating a particular behavior or functionality within a class/function/method that will remain, keep its future removal in mind: encapsulate the to-be-removed code cleanly, rather than as multiple conditional branches within a given function/method, and leave clear comments/issue notes on what clean up steps are required.
- For deprecations related to plugins, implement the deprecation on the applicable base class wherever possible, rather than on every affected subclass in a repeated fashion.
:::

---

## 5. GeoIPS Deprecation Components

Every deprecation in GeoIPS implemented according to this Specification will consist of the following three elements or components:

- a well-formatted, standardized deprecation message string
- a reference issue on GitHub (or GitLab, etc.)
- the particular code implementing the deprecation for the type of thing being deprecated

### 5.1 Deprecation Message String

The central component of a standardized GeoIPS deprecation is the *message string*. It is a YAML-formatted collection of fields/arguments that are then parsed to assemble any warning messages/documentation components. It is a string rather than a collection of Python function arguments to ensure compatibility with PEP 702, which leverages static analysis. Whenever it is used rather than simply output as-is, it is parsed through a Pydantic model, and so validated according to the requirements below:

| Name | Typing/Validation | Inclusion | Use/Reason |  
| ---- | ----------------- | --------- | ---------- |
| Entity/Behavior | `str` of ≤70 chars | Public API: OPTIONAL<br>Internal/Private API: REQUIRED | A nice, human-readable "name" to give this deprecation, for display in docs. Useful when deprecating some functionality whose Python API name may not be helpful to the user or developer encountering the deprecation. |
| Replacement | `str` of ≤90 chars | RECOMMENDED | A short description of what should be used instead of this deprecated functionality. For more complex migrations, a replacement message like 'Consult the migration guide at INSERT-URL-HERE' is recommended. More verbose descriptions of the replacement can occur in the reference issue. |
| Component | `str` of ≤40 chars | REQUIRED | Component of GeoIPS in which this deprecation is located (e.g., CLI, Readers, Products). |
| Reference Issue | `AnyUrl` (RECOMMENDED) or `"MISSING"` (NOT RECOMMENDED) | REQUIRED | Canonical reference issue on GitHub (or GitLab, etc.) for this deprecation, containing all anciliary information relevant for developers (see Section 5.2). |
| Deprecated In | `SemanticVersion` | REQUIRED | Communicates deprecation lifecycle, and can be parsed into PyDeprecate (or equivalent) tooling for lifecycle checks/auditing |
| Removal In | `SemanticVersion` or `"Conditional (see issue)"` | Existing deprecations: RECOMMENDED<br>New deprecations: REQUIRED | Communicates deprecation lifecycle, when a semantic version string, can be parsed into PyDeprecate (or equivalent) tooling for lifecycle checks/auditing. If this is "Conditional (see issue)", the reference issue (not the deprecation message) MUST explanation the conditions/gates/etc to be met before removal can occur. |

**Additional Notes**:
- The key used for "Entity/Behavior" field is implemented with alias choices in Pydantic, such that any of the following are valid (and the implementer of the deprecation can choose whichever is most appropriate): "Entity", "Behavior", or "Entity/Behavior".
- The v2.0 Specification effort is expected to involve renaming and reorganizing a substantial number of GeoIPS "Components" (e.g., "YAML-based Plugins" becoming `PluginConfigs`, what were `OutputFormatters` (or parts thereof) becoming either `OutputFormatters` or `Writers`). Deprecation messages should use the updated name for any of these.
- For existing deprecations re-implemented under this new approach (see [Pull Request 1539](https://github.com/NRLMMD-GEOIPS/geoips/pull/1539)), the "Deprecated In" field should be set to the minor version in which that deprecation was first implemented, if such can be readily identified via `git blame`, otherwise, setting as "2.0.0" is acceptable (so long as the "Removal In" version is not also "2.0.0").
- For "Reference Issue", the string literal `"MISSING"` SHOULD pass Pydantic validation (for cases of existing deprecations prior to reference issue creation) but SHOULD NOT be allowed past review for any new deprecations (the reference issue should be created first).
- "Replacement" is expected to be included in warning messages and documentation in a sentence-like way, either prefaced by something akin to "Replacement/Migration Instructions:" or alone. And so, structure this field as a sentence (e.g., begin with a capitalized imperative verb), but omit final punctuation.
- See Section 4 for recommendations and requirements about the span between "Deprecated In" and "Removal In" versions.
- Some of this information will be duplicated in the contents of the Reference Issue (see Section 5.3.2).
- When not using special characters, the YAML value does not need to be contained in quotes, but does when such are used (particularly backticks, as recommended for code formatting).

### 5.2 Canonical Reference Issue

:::{note}
A description of the components of the "Canonical Reference Issue" (particularly the issue form that will be used to create such) will be included here in a future version of this document. In the interim, generic issues describing the deprecation are sufficient, and can be updated at a later time.
:::

### 5.3 Implementation

Given the differences in support between PEP 702 and PyDeprecate, the actual implementation of any given deprecation in the code will look different, depending on the particular sort of "thing" that is being deprecated. In general, we prefer to rely upon PEP 702 deprecations wherever possible, and use (easy to replace) wrappers of PyDeprecate to fill in (either in part or in whole) where they are insufficient. This works out more or less to the following:

Use PEP 702 style deprecations alone for:
- Pydantic fields
- Private functions/methods

Use GeoIPS `deprecate_THING` style wrappers alone for:
- Modules
- Object instances (e.g., singletons)
- Function arguments

Use both in combination (with the PEP 702 decorator within/below the PyDeprecate wrapper) for:
- Public functions/methods
- Classes

For further details on what this looks like in code, see the Examples > Enumerations of Varieties section (8.1)

---

## 6. Documentation

:::{note}
A description of the automated tabular listing of deprecations as well as docstring updates will be added in a future version of this document. In the interim, just note that *no documentation changes* ought to be needed when implementing a deprecation, as they will be handled behind-the-scenes by the helper utilities (i.e., *do not* add deprecation information to docstrings manually in additional to the other components).
:::

### 6.1 Deprecation Listing

To be added...

### 6.2 Docstrings

To be added...

---

## 7. CI and Audit Tooling

:::{note}
A description of the audit/version tracking tooling that we will be able to leverage using PyDeprecate will be added here in a future version of this document.
:::

---

## 8. Detailed Examples

### 8.1 Enumeration of Varieties

#### 8.1.1 Pydantic Fields

**General Instruction**: Use a PEP 702 `deprecated` as an object argument to the field, either in the type with `Annotated` or in the `Field` value, as described in the [Pydantic documentation](https://pydantic.dev/docs/validation/latest/concepts/fields/#deprecated-fields).

*Example 1*: Deprecating support for a particular type in a union of accepted types for a field

```python
class AreaDefinitionSpec(FrozenModel):
    ...
    shape: Union[
        Tuple[
            Annotated[int, Field(strict=True, gt=0)],
            Annotated[int, Field(strict=True, gt=0)],
        ],
        Annotated[
            SectorShape,
            deprecated("""
                Entity/Behavior: SectorShape in AreaDefinition
                Component: Sectors
                Reference Issue: MISSING
                Deprecated In: 1.17.0
                Removal In: 2.1.0
                Replacement: "Set `shape` as a tuple of positive integers"
            """),
        ],
    ]
    ...
```

*Example 2*: Deprecating a field

```python
class ReaderArgumentsModel(PermissiveFrozenModel):
    ...
    chans: List[str] = Field(
        None,
        description="List of variables to read",
        deprecated=deprecated("""
            Entity/Behavior: "`chans` argument in Readers"
            Component: Readers
            Reference Issue: https://github.com/NRLMMD-GEOIPS/geoips/issues/953
            Deprecated In: 1.19.0
            Removal In: 2.0.0
            Replacement: "Use `variables` instead"
        """),
    )
    ...
```

(Note that this does nothing to alias the old argument to any replacement for backwards compatibility—that must be handled separately in a model validator method. When implementing such, keep in mind that Pydantic will issue a (non-GeoIPS) deprecation warning on access, so it may be helpful to wrap in a catch warnings block.)

#### 8.1.2 Public Function/Method

**General Instruction**: Use PEP 702 decorator (primary) but with category `None`, then PyDeprecate wrapper (for docstring and audit tracking support), used in combination. "Entity/Behavior" field is optional in this case, as the entity name corresponds well with the name of the deprecated thing (the function/method).

```python
@deprecation.deprecate_callable()
@deprecated(
    """
    Replacement: See documentation for migration guide
    Component: Plugins
    Reference Issue: https://github.com/this/is/not/a/real/issue/12345
    Deprecated In: 2.0.0
    Removal In: 2.3.0
    """,
    category=None,
)
def this_function_will_not_be_supported_for_long(...):
    ...
```

:::{attention}
The `category=None` in the PEP 702 decorator is important, as otherwise the deprecation will be issued twice (once by the PEP 702 decorator, through a generic `DeprecationWarning`, then once by the `deprecation.deprecate_callable` decorator, through the `GeoipsDeprecationWarning`)
:::

#### 8.1.3 Public Class

**General Instruction**: Use PEP 702 decorator (primary) but with category `None`, then PyDeprecate wrapper (for docstring and audit tracking support), used in combination. "Entity/Behavior" field is optional in this case, as the entity name corresponds well with the name of the deprecated thing (the class).

```python
@deprecation.deprecate_class()
@deprecated(
    """
    Replacement: See documentation for migration guide
    Component: Plugins
    Reference Issue: https://github.com/this/is/not/a/real/issue/12345
    Deprecated In: 2.0.0
    Removal In: 2.3.0
    """,
    category=None,
)
class ThisPluginWillSoonDisappear(BaseClassPlugin):
    ...
```

:::{attention}
The `category=None` in the PEP 702 decorator is important, as otherwise the deprecation will be issued twice (once by the PEP 702 decorator, through a generic `DeprecationWarning`, then once by the `deprecation.deprecate_class` decorator, through the `GeoipsDeprecationWarning`)
:::

#### 8.1.4 Module

**General Instruction**: Use GeoIPS wrapper, as PEP 702 does not support this use case. "Entity/Behavior" field is optional in this case, as the entity name corresponds well with the name of the deprecated thing (the module).

```python
deprecation.deprecate_module(
    """
    Replacement: Use geoips.config instead
    Component: Config
    Reference Issue: https://github.com/this/is/not/a/real/issue/12345
    Deprecated In: 2.0.0
    """,
    name=__name__,
)
```

#### 8.1.5 Instance
*(e.g., singletons)*

**General Instruction**: Use GeoIPS wrapper, as PEP 702 does not support this use case. "Entity/Behavior" field is optional in this case, as the entity name corresponds well with the name of the deprecated thing (the object).

```python
deprecation.deprecate_instance(
    old_thing,
    """
    Replacement: Use new thing instead
    Component: Config
    Reference Issue: https://github.com/this/is/not/a/real/issue/12345
    Deprecated In: 2.0.0
    """
)
```

#### 8.1.6 Function Argument(s)

**General Instruction**: Use GeoIPS wrapper, as PEP 702 does not support this use case, and pay close attention to the `args_mapping` keyword argument, which is passed along to PyDeprecate to actually perform the argument handling.

*Example 1*: Renaming an argument

```python
@deprecation.deprecate_argument(
    """
    Entity: "`xobj` method argument in `call`"
    Replacement: "Use `data` instead"
    Component: Algorithms
    Reference Issue: https://github.com/this/is/not/a/real/issue/12345
    Deprecated In: 2.0.0
    """,
    args_mapping={"xobj": "data"}
)
def call(self, data, *args, **kwargs):
    ...
```

(Note that the old/deprecated argument *does not* need to be set in the function signature in this case)

*Example 2*: Warning for a provided argument without one-to-one remapping

*(e.g., when no direct replacement is available, or some processing needs to occur)*

```python
@deprecation.deprecate_argument(
    """
    Entity: "`poorly_devised` method argument in `call`"
    Replacement: See migration guide in documentation
    Component: Algorithms
    Reference Issue: https://github.com/this/is/not/a/real/issue/12345
    Deprecated In: 2.0.0
    """,
    args_mapping={"poorly_devised": None}
)
def call(self, data, poorly_devised=0, *args, **kwargs):
    _clean_up_poorly_devised_option(...)
    ...
```

(Note that the old/deprecated argument *does* need to be set in the function signature in this case)

#### 8.1.7 General Behaviors/Other

**General Instruction**: Cleanly encapsulate the deprecated functionality/behavior in a private function/method, require the "Entity/Behavior" field in the deprecation message string, and use PEP 702 decorator alone. Only when not otherwise possible issue a GeoIPS deprecation warning directly with `deprecation.deprecation_warning`.

*Example 1*: Preferred pattern

```python
@deprecated(
    """
    Entity/Behavior: "`create_plugin_registries` command"
    Replacement: "Use `geoips config create-registries`"
    Component: CLI
    Reference Issue: https://github.com/NRLMMD-GEOIPS/geoips/issues/1227
    Deprecated In: 1.16.0
    Removal In: 2.0.0
    """,
    category=deprecation.GeoipsDeprecationWarning,
)
def _deprecated_create_plugin_registries():
    ...
```

:::{attention}
The `category=deprecation.GeoipsDeprecationWarning` in the PEP 702 decorator is important, as otherwise the deprecation issued with a generic `DeprecationWarning`, which does not reformat the message string.
:::

*Example 2*: To-be-avoided fallback

```python
if deprecated_pathway:
    ...
    deprecation.deprecation_warning("""
        Behavior: The old way through the code
        Replacement: Use a data-tree native plugin instead
        Component: Plugins
        Reference Issue: https://github.com/this/is/not/a/real/issue/12345
        Deprecated In: 2.0.0
    """)
```

:::{note}
This pattern is not preferred as it leaves no object in the AST or API to scan for when compiling documentation on all extant deprecations, and would require manual listing in the docs instead.
:::

### 8.2 Single-Use vs. Re-Used Deprecations

Often, a deprecation will be specific to only one thing in the codebase, so there are no concerns about unnecessary repeation or keeping multiple instances consistent when changed. However, this may not always be the case. If a deprecation implementer finds a particular deprecation (i.e., with the same message string) occuring multiple times, the following pattern of reuse is recommended:

Instead of directly decorating a given function/method/class or specifying the argument to a Pydantic field, save the decorator-callable (typically the PEP 702 `deprecated`, but sometimes a `deprecate_argument`) to a variable, and decorate using *it* instead. In practice, this looks something like:

```python
dep_12345 = deprecated("""
    Behavior: The old thing
    Replacement: The new thing
    Component: Workflows
    Reference Issue: https://github.com/this/is/not/a/real/issue/12345
    Deprecated In: 2.0.0
    Removal In: 3.0.0
""")

@dep_12345
def _old_stuff(...):
    ...
```

Given that all deprecations are intended to have a reference issue, and all GitHub issues have issue numbers, it can be helpful to name this variable with the corresponding issue number. In cases where two decorators are required to implement a deprecation, reuse only the one containing the standardized message string.

Note that this approach does not apply to deprecation patterns that do not use decorators (e.g., module and instance deprecations). In such cases, since they do not require PEP 702 static analysis support either, set the *deprecation message string* to a variable instead, and reuse that variable in each deprecation function call.

---

## 9. References

- [PEP 702 (Core Python's `@deprecated` decorator)](https://peps.python.org/pep-0702/)
- [NEP 23 (NumPy's best practices around deprecations)](https://numpy.org/neps/nep-0023-backwards-compatibility.html)
- [PyDeprecate (Selected, at least for now, deprecation utility library)](https://github.com/Borda/pyDeprecate)
