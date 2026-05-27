# Review Remediation — `obp-meets-datatree` DataTree Implementation

## Summary

Addresses a comprehensive code review (31 findings) of the DataTree-spec implementation on the `obp-meets-datatree` branch. The changes span 15 files (−479 / +373 LOC net) and target three themes:

1. **Correctness**: fixing mutable frozen models, bare exception swallowing, inconsistent error paths, and tests that don't actually test
2. **OOP/DRY/KISS**: breaking unnecessary inheritance, simplifying topological sort, deduplicating boilerplate, extracting magic strings
3. **Hardening**: narrowing exception clauses, rejecting unimplemented fields at validation time, making converter round-trips fail-loud

## Changes by File

### Production Code

| File | Δ | Key Change |
|---|---|---|
| `geoips/pydantic_models/v1/workflows.py` | +129 / −38 | Split `_resolve_defaults` (after, mutation) → `_inject_defaults` (before) + `_validate_dependencies` (after, read-only). Add `SCAFFOLD_KINDS`, `DEFAULT_RETENTION` constants. Hoist `_PLUGIN_ARGUMENTS_MODELS` to module scope (no duplicate key). Add `_reject_scope`/`_reject_when` validators. Iterative DFS replaces recursive. |
| `geoips/interfaces/class_based/workflow.py` | +77 / −67 | `Workflow` → plain class (no `BaseClassPlugin` inheritance). `name` → `workflow_name`. Remove runtime cycle check (trusts pydantic). `_topological_order`: `deque` + one-pass indegree. `_record_provenance`: 7 manual attrs → `dataclasses.asdict(prov)`. `_gc_step_data`: re-stamps provenance via fresh `StepProvenance`. `_resolve_plugin`: flattened (no AttributeError→re-wrap). `_collect_upstream_data`: unified single/multi-dep path. Delete dead split/join branch in call loop. `command_line_args` removed from call signature. |
| `geoips/interfaces/class_based_plugin.py` | +8 / −1 | Add `import logging` + `LOG`. `_unwrap`: bare `except Exception: pass` → `except (TypeError, ValueError, RuntimeError) as exc: LOG.debug`. `_wrap`: `_convert_datatree_to_ditto` → `from_datatree`. |
| `geoips/plugins/modules/procflows/order_based.py` | +16 / −15 | Delete module-level `_call = OrderBased().call`. Flatten nested `if/elif`. Remove `command_line_args` parameter. |
| `geoips/commandline/geoips_run.py` | +1 / −1 | Drop `command_line_args=args` from procflow call |
| `geoips/utils/types/datatree_converters.py` | +13 / −3 | `_dict_to_dataset`: log warning on lossy stringify. `_ds_to_da`: raise `ValueError` on missing `_ditto_da_name` with multi-var. |
| `geoips/utils/types/datatree_ditto.py` | +26 / −6 | Promote `_convert_datatree_to_ditto` → public `classmethod from_datatree`. Old method kept as deprecated delegate. |
| `geoips/utils/types/tokenization.py` | +10 / −4 | Add `_UNTOKENIZABLE_PREFIX`. `compute_arguments_hash` shares same `untokenizable:` fallback. Narrow `except` to `(TypeError, ValueError)`. Remove redundant manual sort in `compute_arguments_hash`. |
| `geoips/utils/types/__init__.py` | +9 / −1 | Document import side-effect triggering converter registration |

### Test Code

| File | Δ | Key Change |
|---|---|---|
| `tests/unit_tests/plugins/modules/procflows/test_order_based.py` | −96 | Delete 4 dead tests (3x `assert is not None`, 1x `try/except: pass`). Keep only `test_class_has_correct_attrs`. |
| `tests/integration_tests/test_obp_datatree.py` | +100 / −106 | Delete `_run_one_reader_workflow` (95-line fork of `Workflow.call`). Rewrite all tests to call real `Workflow.call()`. `test_cycle_raises_at_runtime` → `test_cycle_raises_at_validation`. Retention test now checks `gc_status`. |
| `tests/integration_tests/conftest.py` | +87 / −0 | Replace dead `abstract=True` fixtures with `autouse` monkeypatch for `Workflow._resolve_plugin` → synthetic doubles. Synthetic plugins are fully concrete (no `abstract=True`). |
| `tests/unit_tests/interfaces/test_class_based_plugin_invoke.py` | +15 / −0 | Add value assertions (content verification) to all 4 wrapper tests. Remove redundant `isinstance` guard. |
| `tests/unit_tests/interfaces/class_based/test_workflow.py` | +3 / −3 | `Workflow(spec, name=…)` → `Workflow(spec, workflow_name=…)` |
| `tests/unit_tests/pydantic_models/v1/test_workflow_spec_model.py` | +2 / −15 | `test_scope_field_accepts_string` → `test_scope_field_rejected` (scope now rejected at validation) |

## Findings Addressed

| Crit (🔴) | Moderate (🟠) | Style (🟡) |
|---|---|---|
| C1: Dead smoke tests | M1: Workflow composition | S1: indegree loop → one-pass |
| C2: Forked `_run_one_reader_workflow` | M2: Private DTD method → public | S2: unified upstream data |
| C3: Module-level `OrderBased()` instantiation | M3: Double-wrapped PluginResolutionError | S3: nested if/elif → flat |
| C4: Bare `except: pass` in `_unwrap` | M4: Dead split/join branch | S4: `name` → `workflow_name` |
| C5: Inconsistent token fallback | M5: Redundant cycle check | S5: reject scope/when at validation |
| C6: `object.__setattr__` on FrozenModel | M6: gc_status re-stamp | S6: documented import side-effect |
| C7: Duplicate dict key | M7: manual attrs → `asdict` | S7: log level consistency |
| C8: missing `super().__init__()` | M8: magic constants extracted | S9: recursive DFS → iterative |
| — | M9: dead `command_line_args` | S11: `abstract=True` misuse |
| — | M10: lossy dict converter | 7.2: invoke test value assertions |
| — | M11: silent wrong-name fallback | — |
| — | M12: redundant manual sort | — |

## Test Results

```
55 passed, 0 failed, 7 warnings
```

All warnings are pre-existing Pydantic 2.x deprecations (`@model_validator` on classmethods).

## Verification

```bash
GEOIPS_TESTDATA_DIR=/tmp GEOIPS_PACKAGES_DIR=. uv run pytest \
  tests/unit_tests/interfaces/class_based/test_workflow.py \
  tests/unit_tests/pydantic_models/v1/test_workflow_spec_model.py \
  tests/unit_tests/interfaces/test_class_based_plugin_invoke.py \
  tests/unit_tests/utils/types/test_tokenization.py \
  tests/integration_tests/test_obp_datatree.py \
  tests/unit_tests/plugins/modules/procflows/test_order_based.py
```

## Deferred

| Issue | Tracking |
|---|---|
| `data_tree` boolean → strategy object | Separate v2 design issue |
| Ported `_FROM_XARRAY` test files (3,082 LOC) | Separate vendor-test hygiene PR |
| Pre-existing test cruft (`test_partial_lexeme.py`, empty test class) | Separate general cleanup PR |
