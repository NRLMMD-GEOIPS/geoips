# <Interface name>

<!--
Copy this file to start a new interface Specification page. Fill every section.
Where something genuinely does not apply, write "None." or "Not applicable." and say why
in one sentence -- silence is indistinguishable from an unanswered question, and
check_consistency.py treats an empty section as a failure.

Delete these comments as you fill each section in.
-->

## Overview

<!-- What the interface is for, and the common cases a plugin author would write one for. -->

## Plugin kind

<!-- The value provided to `kind` in a workflow step to invoke a plugin from this
     interface. The singular form of the registered interface name. One word. -->

## Step classification

<!-- Data-bearing or non-data-bearing, and the semantic result that makes it so. -->

## Prerequisites

<!-- What must already exist in the tree before a step of this kind runs: which upstream
     steps, data nodes, or metadata. -->

## Data produced

<!-- What the step adds to, replaces in, or removes from its step node. How variables are
     grouped into coordinate-compatible datasets, and how output `dataset_id` values are
     chosen. -->

## Dataset identity metadata

<!-- The metadata that distinguishes one of this interface's datasets from another. -->

## Dimensions

<!-- Which dimensions this interface's datasets carry, and which it creates or removes. -->

## Units

<!-- Required input units, output units, and whether plugins preserve, convert, or ignore
     unit metadata. "None" is a valid answer -- unit handling is optional for v2.0.0. -->

## CF conformance

<!-- Any divergence from CF conventions, with the reason. State "None." if there is none. -->

## Retention

<!-- What retention behavior applies to this interface's data. -->

## Arguments

<!-- Positional and keyword arguments, with defaults and required/optional status. Mark the
     canonical name for each. -->

## Conduits and aliases

<!-- Argument conduits for this interface: where each value originates, and how collisions,
     missing values, and overrides are handled. Legacy aliases and interface-specific
     translations, each marked as deprecated. -->

## Family and `data_tree` status

<!-- Where this interface's plugins sit on the migration axis: which are DataTree-native
     (`data_tree=True`, no `family`) and which still carry a `family`. Each unmigrated
     plugin needs a conformance-gap issue and a deprecation-register entry. -->

## Lifecycle and conversion

<!-- Lifecycle hooks this interface defines or overrides, and any interface-specific
     conversion applied before or after `call()`. -->

## Required plugin implementation

<!-- What a plugin author must implement: required attributes, required methods, the base
     class to inherit from, and registration requirements. -->

## Errors and validation

<!-- Exceptions raised, validation performed, and failure modes. -->

## Deprecations

<!-- Deprecated arguments or behavior still accepted, each with its current warning
     behavior, replacement, and migration path. Link each to its deprecation-register
     entry. -->

## Legacy compatibility

<!-- What this contract must preserve for legacy Products and run scripts to keep working,
     and how that bridges to workflows and CLI calls. -->

## Conformance status

<!-- Where the current implementation diverges from what this page requires. Link each
     confirmed difference to its conformance-gap issue. -->

## Examples

<!-- At least one worked example, or a statement of why none is appropriate. -->

## See also

<!-- Related Specification pages and documentation. -->

## Reference links

<!-- The code, tests, existing documentation, issues, and representative plugins that
     support the claims on this page. Add these from the first commit, not at the end. -->
