# PLAN.md — Addressing Review Comments on PR #1338

> **STATUS: COMPLETE.** All review-comment items (A, B, C, D, E, F, G, H, I, J,
> K, M, N) plus bug-found items (O, P) are implemented. L is documented-only (no
> code, by request). A follow-up hardening pass (items Q–T + call-style, see the
> "Follow-up hardening" section below) consolidated the converter functions into
> one canonical module, fixed a MaskedArray-converter crash, made dict-origin
> dittos honor the full mapping read protocol, and restored test isolation of the
> shared converter registry. Verified: zero test regressions vs. the base branch
> (identical 121 pre-existing unit failures, empty diff; +37 new passing tests)
> and zero new flake8 findings in the changed files.
> Tests were run with the project `.venv`. The single-source end-to-end script
> (`abi.static.dmw.imagery_windbarbs_high.sh`, item A) could not be executed
> locally because no real ABI test data is available (an empty
> `$GEOIPS_TESTDATA_DIR` was pointed at `/tmp`); the fix is covered by new unit
> tests and matches the reported traceback exactly.
>
> **Additional bug fix found while attempting to run the OBP end-to-end
> (item O, below).** While running `tests/scripts/obp.datatree_conversion_test.sh`
> (which needs only the repo clone), the CLI failed immediately because
> `geoips_run.py` invoked the order-based procflow with `obp(workflow=...)` while
> `OrderBased.call` expects `workflow_spec`. Fixed the kwarg name and gave
> `OrderBased.call` a `command_line_args` param for parity with the module-level
> entry point. This unblocks the CLI; the same workflow then hits a *pre-existing*
> conduit issue (`call() got an unexpected keyword argument 'xarray_obj'`) that
> reproduces on the base branch and is outside this PR's review-comment scope.

### P. [bug found during testing] OBP conduit kwarg leaks into legacy plugin ``call``

After fixing item O, `geoips run order_based test_datatree_conversions` failed with
``call() got an unexpected keyword argument 'xarray_obj'`` on the ``single_channel``
(family ``list_numpy_to_numpy``) step. Root cause: ``_extract_child_kwargs`` wires an
upstream ``reader`` output to the ``xarray_obj`` conduit kwarg, but for legacy families
the same data is separately converted by ``_pre_call`` into the first positional
argument (``arrays``). The leftover ``xarray_obj`` kwarg is then passed to a ``call``
that does not accept it. Confirmed pre-existing on the base branch (was masked by the
item-O bug, which aborted earlier).

**Fix** (`geoips/interfaces/class_based_plugin.py`):
- Added ``_call_kwargs`` and, under OBP, filter the kwargs forwarded to ``self.call``
  to only those the signature accepts (applied in both the positional-unpacking and
  positional-``data`` branches of ``_invoke``). ``_post_call`` still receives the full
  ``new_kwargs``.
- Made ``_obp_filter_kwargs`` ``**kwargs``-aware so plugins with a ``VAR_KEYWORD``
  parameter keep all keys.

Dropping unaccepted kwargs can only prevent ``TypeError``s, never cause them.
`test_datatree_conversions` now runs to completion; all 28 OBP integration tests pass.

**Follow-on to item B (name-override log):** the ``_attach_step_node`` name-override
message was downgraded from ``warning`` to ``debug``. In practice every step renames a
plugin's generically-named output node (e.g. ``single_channel`` → ``algorithm``), so
warning fired on every step and was pure noise — exactly the risk flagged in the plan.

### O. [bug found during testing] OBP CLI ``workflow_spec`` kwarg mismatch

`geoips/commandline/geoips_run.py` called
``obp(workflow=workflow, ...)`` but ``OrderBased.call`` (and the module-level
``call``) name the parameter ``workflow_spec``; because the plugin invoke chain
leaves ``data=None``, ``workflow`` landed in ``**kwargs`` and ``workflow_spec``
was reported missing. Renamed the call-site kwarg to ``workflow_spec`` and added
a ``command_line_args=None`` parameter to ``OrderBased.call`` for parity with the
module-level entry point (accepted, not consumed). Verified no regressions in the
commandline test suite (identical 86 failed / 1551 passed to baseline).

---

## Follow-up hardening (post-review continuation)

> These items were found and fixed after the A–P review-comment work, while
> hardening the converter layer and the dict-origin ditto behavior. Same
> constraints apply: code + tests only; no GitHub issue creation. Verified
> against the same baseline (121 pre-existing unit failures, empty diff).

### Q. Consolidate all converter functions into one canonical module

Converter *functions* were split between ``converters.py`` and inline defs in
``datatree_converters.py`` (``_dict_to_dataset``, ``_dataset_to_dict``,
``_da_to_ds``, ``_ds_to_da``), inviting drift. Moved all four into the single
canonical module ``geoips/utils/types/converters.py`` with public names
(``dict_to_dataset``, ``dataset_to_dict``, ``dataarray_to_dataset``,
``dataset_to_dataarray``). ``datatree_converters.py`` is now **pure wiring** —
it imports every converter from ``converters.py`` and only calls
``register_converter``; a module-docstring note states this so the two cannot
drift again. ``converter_registry.py`` (dispatch) is a separate concern and was
left as-is.

### R. [bug] MaskedArray converter crashes on non-float dtypes

``masked_array_to_dataset`` filled masked entries with ``np.nan`` and cast
``fill_value`` via ``float()``. This raised ``TypeError: Cannot convert
fill_value nan to dtype int64`` for any integer/uint/string MaskedArray with an
active mask. Fixed to store the underlying data via ``np.ma.getdata(obj)``
(preserves exact dtype, no NaN fill) and the ``fill_value`` as a native scalar
via ``.item()``; ``dataset_to_masked_array`` restores the recorded original
dtype and sets ``fill_value`` defensively. All dtypes (int64, uint8, float64,
2-D int, string) now round-trip losslessly with the mask preserved. +5
regression tests (``TestMaskedArrayConverter``) in
``tests/unit_tests/utils/types/test_datatree_converters.py``.

### S. Dict-origin ditto: consistent mapping (read) protocol

Item A fixed ``__getitem__`` for dict-origin dittos, but ``"k" in d``,
``d.get("k")``, and iteration still ignored the wrapped dict. Extended the
protocol so a dict-origin ``DataTreeDitto`` (``_ditto_original_type ==
builtins.dict``) behaves like the dict it wraps across ``__getitem__``,
``__contains__``, ``get``, ``__iter__``, ``keys``, ``values``, ``items`` — so
``dict(d)``, ``**d`` and ``d.get(k, default)`` all work.

**Recursion pitfall (fixed):** xarray's tree traversal calls ``node.get(part)``;
routing ``get``/``__getitem__`` through each other caused infinite recursion. The
fix gates all dict behavior behind a single ``_as_original_dict()`` helper that
returns ``None`` for every non-dict-origin node (so overrides fall straight
through to standard ``DataTree`` behavior), and ``get`` calls ``super().get``
directly rather than routing through ``__getitem__``. +11 tests
(``TestDictOriginMapping``) covering both dict-origin and tree behavior.

### T. Test-hygiene: restore the shared converter registry

Three teardowns in ``test_datatree_ditto.py`` registered converters via
``DataTreeDitto.register_converter`` (which populates **both** the per-class
``_converters`` dict and the shared ``converter_registry``) but only cleaned the
former. Leaked ``str``/``list``/``MaskedArray`` converters polluted the shared
registry and made ``test_datatree_ditto_FROM_XARRAY.py::test_create_with_data``
fail depending on collection order. Fixed by snapshotting and restoring **both**
registries in all three teardowns (chosen over adding a public ``unregister``
API). The full unit suite is now order-independent.

### Call-style: use the public ``plugin(...)`` everywhere

Replaced ``plugin._invoke(...)`` prescriptions in ``docs/dev/datatree-spec.md``
with the public call form ``plugin(...)`` and added "never call ``_invoke()``
directly" notes.



**PR:** NRLMMD-GEOIPS/geoips#1338 — "Obp meets datatree and callable yaml"
**Head branch:** `obp-meets-datatree` → **Base:** `datatree-ditto`
**Related PR:** #1319 (the `docs/dev/datatree-spec.md` spec PR — establishes conventions this PR must conform to)
**Scope of this plan:** Code changes only (no GitHub issue creation; no comment-reply drafting).
**Reviewers referenced:** `jsolbrig`, `mindyls`, `evrose54`, `srikanth-kumar`; author `biosafetylvl5`.

---

## 0. Context & Conventions (from PR #1319)

These decisions from the spec PR constrain the work here:

- **`/metadata` node removed** — use xarray's built-in `attrs`. Attributes live at the **step-node** level (`/<step_id>`), not a separate metadata tree.
- **Tokens** (from `dask.base.tokenize`) are stored in each step node's `attrs`; used for content-addressable caching and fast regression testing. **Token stamping must not be removed.**
- **Step-id prefixing** (`w0-`, `w1-`, …) for cross-workflow uniqueness — noted as future work, not implemented here.
- **Retention / GC:** `depends_on` governs when a step's `data_vars` are dropped; entries in top-level `outputs:` survive unconditionally; metadata/tokens always survive.
- **Operators:** `split` / `join` are special step kinds that change DAG shape.
- **YAML-based plugins** are first-class "step invocations."
- **`source_name` / `platform_name`** retained by reader steps, retrieved via `get_source_names()`; workflow root carries copies. **Each step (including workflows) has start/end times** → motivates Item M.
- **`data_tree` flag** on plugins discriminates whether a plugin natively consumes/produces a DataTree.

---

## 1. Execution Order (authoritative)

1. **A** — `DataTreeDitto.__getitem__` narrow fix + legible errors *(priority bug)*
2. **J** — replace interface-discovery hack with canonical allowlist
3. **K** — `write_tokens` wiring decision + registry-refresh decision
4. **M** — root-level workflow start/end times
5. **N** — dot-path `depends_on` into sub-workflow steps (deep validation)
6. **E / F / H** — clearer errors; docstring/naming fixes; strengthen converter test
7. **C / D / I** — targeted import hoisting; remove commented debug; reconcile out-of-scope changes
8. **B** — `workflow.py` refactors
9. **G** — confirm step-level attrs conform to #1319
10. **L** — documented-only follow-ups (no code)

Rationale: front-load risky core-behavior items (bug, discovery, token wiring, new features) so the test suite stabilizes early; defer low-risk cleanup.

---

## 2. Detailed Work Items

### A. [PRIORITY BUG] `DataTreeDitto.__getitem__` breaks the single-source procflow

**Source comment:** jsolbrig issue-level comment. Running
`./tests/scripts/abi.static.dmw.imagery_windbarbs_high.sh` crashes with:

```
File ".../geoips/utils/types/datatree_ditto.py", line 424, in __getitem__
    result = super().__getitem__(key)
  ...
KeyError: 'Could not find node at cmap'
```

Triggered by `mpl_colors_info["cmap"]` in
`geoips/plugins/modules/output_formatters/imagery_windbarbs.py:56` (`plot_barbs`).

**Root cause (confirmed):** `DataTreeDitto.__getitem__` (`geoips/utils/types/datatree_ditto.py`, ~lines 391–439) delegates straight to `xr.DataTree.__getitem__`, which interprets the key as a **node path** rather than dict access. Under the single-source procflow, `mpl_colors_info` is a plain dict-origin object, so `"cmap"` should be a dict key lookup, not a tree-node lookup.

**Fix approach (narrow — per codex review):**
- Preserve normal `DataTree` node lookup as the primary path.
- On `KeyError`, fall back **only for dict-origin nodes** (i.e. when the wrapped original is a dict — check `_ditto_original_type == dict` / the stored original-type attr), returning `self.get_original()[key]`.
- For genuine missing tree nodes (non-dict-origin), re-raise with a **clear** message stating the object is a `DataTreeDitto`, what key was requested, and the available keys/nodes.
- Do **not** add a blanket `.ds`/attrs fallback (would mask legitimate errors and conflict with #1319 tree/attrs semantics).

**Files:**
- `geoips/utils/types/datatree_ditto.py` — `__getitem__` (~424) + error text.
- Verify `get_original()` and the original-type marker attribute name in the same file before editing.

**Verification:**
- `./tests/scripts/abi.static.dmw.imagery_windbarbs_high.sh` runs to completion (or fails later for unrelated reasons).
- Add/extend a unit test in `tests/unit_tests/utils/types/` asserting dict-key access on a dict-origin `DataTreeDitto` works, and that a missing node on a non-dict-origin instance raises a clear, typed error.
- Confirm OBP node-path lookups (e.g. `tree.get("subwf/algo")`) still behave.

**Risk:** Medium — `__getitem__` is on the hot path for both OBP and single-source. Keep the fallback strictly gated on dict-origin.

---

### B. `geoips/interfaces/class_based/workflow.py` refactors (biosafetylvl5)

> Re-locate exact line targets before editing — some references have drifted.

| Comment (orig line) | Action |
|---|---|
| L95 "Refactor this with `in` for brevity" | Simplify the membership/branch check (see `_has_pending_consumers`, ~95–101) using `in`. |
| L51 "store the step definition, make these get callables/convenience functions" | Store the step definition object; expose accessors as convenience callables rather than recomputing. |
| L232 "convert all to DataTreeDitto … don't override the DataTree name" | In `_attach_step_node` (~232–235) use `DataTreeDitto(step_data)` without forcing the node name. |
| L235 "do this for all things; warn on override of DataTree name that's already set" | Apply uniformly; **emit `LOG.warning`** when overriding an already-set DataTree name. |
| L361 "make this an instance attribute cleared at the beginning of the call; make it a list/tuple" | The token-tracking structure (`upstream_tokens` region, ~393) becomes an instance attribute reset at `call()` start, typed as list/tuple. |
| L393 "specify why this may have multiple upstream tokens" | Add an explanatory comment on the multi-upstream-token loop (~394–399). |
| L611 "boo buried imports" | See Item C (evaluate cycle risk before hoisting). |

**Risk:** The "warn on name override" may be noisy if overrides are common in normal operation — verify against existing call patterns before enabling at `WARNING` level (consider `DEBUG` if frequent-and-benign).

---

### C. Buried imports — targeted hoisting (jsolbrig; author agreed)

**Source:** jsolbrig on `filename_formatters.py:73`; author "buried all over … I'm cleaning that up."

**Nuance (codex):** Several local imports (e.g. `from geoips import interfaces` in `workflow.py:611`) are **intentional circular-import guards**. Do **not** blanket-hoist.

**Approach:**
- Grep for function-local `from geoips…import` added in this PR.
- For each: attempt to hoist to module top; if it introduces an import cycle or heavy import-time side effect, **leave it local and add a one-line comment** explaining why.
- Known candidates: `geoips/interfaces/class_based/filename_formatters.py:73`, `geoips/interfaces/class_based/workflow.py:611` (likely must stay), and others surfaced by grep.

**Risk:** Import cycles / import-time side effects. Verify with a clean `python -c "import geoips"` and the unit suite after each move.

---

### D. Remove commented-out debug code (jsolbrig)

- `geoips/plugins/modules/colormappers/visir/Infrared.py` (~95–97) — code jsolbrig commented out "for testing"; logic already in `_post_call()`. Remove; confirm behavior unchanged.
- `geoips/plugins/modules/filename_formatters/geoips_fname.py` (~94–105) — same; remove the commented block already present in `_post_call()`.

**Risk:** Low. Confirm the live `_post_call()` path fully replaces the removed code before deleting.

---

### E. Clearer error messages (jsolbrig; author agreed)

**E1 — `geoips/utils/types/converter_registry.py` (~144–148), `TypeConverterRegistry.convert`:**
Rewrite the `TypeError` to state (a) the failure originates from a `DataTreeDitto` having **no registered converter** for the given type, and (b) how to fix it (register a converter / link to docs). Keep the "registered targets" listing. jsolbrig's example (`DataTreeDitto("abd")`) should produce an actionable message.

**E2 — `geoips/interfaces/class_based_plugin.py` (~306), unhandled-type path:**
Apply the same clarity treatment to the wrapping fallback error.

**Risk:** Low. Keep original exception type; enrich message only.

---

### F. Docs / comments / naming

| Item | File:line | Action |
|---|---|---|
| F1 "What is D4?" (mindyls) — author: "just a note for me" | `geoips/pydantic_models/v1/workflows.py:661` | Remove the internal "decision D4" reference from the docstring (or expand to a real explanation). |
| F2 legacy family conversions (mindyls) | `geoips/utils/types/family_conversions.py` (~35) | Add docstring note: these are **backwards-compatibility (legacy)** family conversions; future plugins are DataTree-native. Clarify the "does not include specific args/kwargs" question. |
| F3 conduit mappings (mindyls) | `geoips/utils/types/obp_conduits.py` (~49) | Clarify these are the **permanent official** mappings; note whether temporary legacy per-family arg/kwarg mappings belong here (credit @srikanth-kumar's origin). |
| F4 "What is MRO ordered?" (mindyls; evrose54 linked docs) | `geoips/utils/types/converter_registry.py` (~100) | Expand "MRO-ordered" with a one-line explanation + link `https://docs.python.org/3/howto/mro.html`. |
| F5 acronym (mindyls; author: "meant SSP … single source procflow") | `tests/integration_tests/test_obp_sectoring.py:4,12` | Rewrite the docstring to reflect **single-source-procflow parity** intent; fix the "SBP"/"static multi-sector" wording. (Author intent overrides the reviewer's "SBP intentional" guess.) |
| F6 test-script header (mindyls) | `tests/scripts/obp.datatree_conversion_test.sh:4` | Correct the header: it does **not** require `$GEOIPS_TESTDATA_DIR`; it requires a full clone. |

**Risk:** Negligible (comments/docstrings only).

---

### G. Attribute grouping — confirm conformance to #1319 (mindyls)

**Comments:** mindyls on `yaml_based/sectors.py`, `colormappers/visir/Infrared.py`, `geoips_fname.py:97` ("why is the filename formatter a DataArray while others become attrs?").

**Resolution (do not re-litigate):** #1319 already decided attrs live at the **step-node** level and `/metadata` is removed. `sectors.py` already writes step-level `ds.attrs`.
- Verify `sectors.py` / `Infrared.py` write step-level attrs consistently.
- Any grouping policy belongs in the **OBP wrappers / conduits** (`obp_conduits.py`, `class_based_plugin.py`), **not** in individual plugins.
- Add a short doc note explaining the intentional DataArray-vs-attrs distinction for `geoips_fname.py:97` (filename output is data; plugin metadata is attrs).

**Risk:** Low; primarily verification + docs.

---

### H. Strengthen converter round-trip test (mindyls; author agreed)

**File:** `tests/unit_tests/utils/types/test_datatree_converters.py` (~72, `TestDataArrayConverter.test_dataarray_roundtrip`).

**Action:** Beyond `np.allclose`, assert the round-tripped `DataArray` is **identical** (values, `dims`, `name`, and coords) — e.g. `xr.testing.assert_identical` or explicit `dims`/`name` checks. If any type-casting is discovered, document it or fix the converter.

**Risk:** Low; may surface a real converter fidelity bug (desirable).

---

### I. Reconcile out-of-scope changes (mindyls / jsolbrig)

- **I1** `geoips/image_utils/maps.py:381` — mindyls "How did these lat/lon type changes end up in this PR?" → Determine provenance; **revert if out of scope** for this PR, otherwise add a justifying comment.
- **I2** `geoips/dev/output_config.py:369` — mindyls still asked "what is this for?" (jsolbrig later "never mind") → Add a clarifying comment or extract if out of scope.

**Risk:** Medium if reverting — confirm nothing in the PR depends on the change first (grep usages).

---

### J. Proper fix for the interface-discovery hack

**Comment:** jsolbrig on `geoips/interfaces/__init__.py:117` — a temporary filter removes `"workflow"` because, once `interfaces.class_based.workflow` is imported, it appears in `list_available_interfaces()` and breaks many unit tests.

**Current state (confirmed):** `geoips/interfaces/__init__.py:116-117` explicitly strips `"workflow"` from discovered interface modules (brittle module-introspection side effect).

**Fix approach (codex suggestion):** Replace the introspection-based filter with an explicit **canonical interface allowlist** (e.g. driven by the known `class_based`/`yaml_based` interface registries) so the non-registerable `Workflow` executor is never mistaken for a registered interface. Investigate why `workflow.py`'s `Workflow` isn't part of `WorkflowPlugin` and whether it should live elsewhere to avoid discovery entirely.

**Verification:** `list_available_interfaces()` output is unchanged (excludes `workflow`); run the full unit suite (this is the item most likely to ripple).

**Risk:** High (touches discovery used across the suite). Do early; gate on full unit-test pass.

---

### K. `write_tokens` wiring + registry-refresh decision

**K1 — `write_tokens` (jsolbrig: "output currently unused"):**
- **Correction:** `write_tokens` lives in `geoips/interfaces/class_based/workflow.py:156,160` (constructor param), **not** `geoips_run.py`. It is currently dead.
- **Decision:** either (a) **wire it through** — thread from CLI/`order_based.py` into `Workflow(..., write_tokens=...)` and use it to gate token *output/emission* — or (b) **remove the dead param**.
- **Constraint:** Token *stamping* into `attrs` (provenance) must remain regardless (core to #1319 caching/regression). `write_tokens` may only control optional emission/export, not stamping.

**K2 — registry auto-refresh (jsolbrig; mindyls caveat):**
- `geoips/commandline/geoips_command.py` (~864–870) has a special-case hack and reads `PATHS["GEOIPS_REBUILD_REGISTRIES"]`.
- **Decision:** whether to auto-refresh a stale registry here; if yes, it **must respect the `rebuild_registries` config** (mindyls: "check the geoips rebuild registries config if you do rebuild registries").

**Risk:** Medium. Do not silently rebuild registries against user config.

---

### M. [NEW] Root-level workflow start/end times

**Motivation:** #1319 — "each step (incl workflows) has start/end times"; the root workflow currently has none.

**Current state:** `Workflow._set_root_attrs` (`geoips/interfaces/class_based/workflow.py:313-327`) stamps `workflow_name`, `outputs`, `retention_policy`, `geoips_version`, `api_version` — **no timing**. Per-step timing exists via `StepProvenance.start_time/end_time` (lines 53-54, set at 373/391).

**Plan:**
- In `Workflow.call` (`workflow.py:329`), capture `wf_start = datetime.now(timezone.utc).isoformat()` before the step loop; stamp via `_set_root_attrs` (add `start_time` param or set `tree.attrs["start_time"]`).
- After the loop, before `return tree` (line 423), stamp `tree.attrs["end_time"] = datetime.now(timezone.utc).isoformat()`.
- Reuse the **same attr keys** (`start_time` / `end_time`) as `StepProvenance` for consistency.
- Recursion is automatic: `kind: workflow` steps (line 383) and split branches (line 484) run nested `Workflow(...).call(...)`, so every sub-workflow root gets its own timing.

**Caveat to handle:** When a sub-workflow tree is attached (`_attach_step_node` → `_record_provenance`, lines 418-419), the step-level provenance `.attrs.update()` overlays the sub-workflow root's own `start_time`/`end_time`. Values are ~identical; confirm step-level timing winning is acceptable and clobbers nothing else. Document the intended precedence.

**Tests:** extend `tests/unit_tests/interfaces/class_based/test_workflow.py` to assert root `tree.attrs["start_time"]`/`["end_time"]` exist, are ISO-8601, and `end >= start`; verify nested sub-workflow roots also carry them.

**Risk:** Low; self-contained.

---

### N. [NEW] Allow `depends_on` to reference sub-workflow steps (dot syntax, deep validation)

**Decisions:** separator = **dot** (`subwf.substep`); validation = **deep** (recurse into sub-spec, error early on missing segments).

**Current state (flat-only):**
- Type `depends_on: List[PythonIdentifier]` (`geoips/pydantic_models/v1/workflows.py:346`); `PythonIdentifier` rejects any non-identifier char (`bases.py:340`, `str.isidentifier`).
- Validation `_validate_dependencies` checks `dep in self.steps` — top-level only (`workflows.py:934`).
- Runtime resolves flat ids: `_topological_order` indegree/edges (`workflow.py:172-186`), `_has_pending_consumers` (95-101), `_collect_upstream_data` `tree.get(dep_id)` (210), token loop (394).
- Sub-workflow/split outputs already nest at `/<sid>/<substep>` and `/<split_id>/<scope>/<substep>` — the **data is addressable**; only the reference machinery is flat.

**Plan:**

1. **Type** — add `StepReference` in `geoips/pydantic_models/v1/bases.py`: `Annotated[str, AfterValidator(step_reference)]` where `step_reference` splits on `.` and validates each segment via `python_identifier`. Change `depends_on` to `List[StepReference]` (`workflows.py:346`). Single-segment (plain id) stays valid. (Leave `StepOutputOverride.depends_on` at `List[str]`, line 1012, or align if desired.)

2. **Deep validation** (`_validate_dependencies`, `workflows.py:918-951`): for `dep` containing `.`:
   - `head = dep.split(".", 1)[0]` must be a defined top-level step of `kind` `workflow` or `split`.
   - Recurse into that step's `spec.steps`, following each subsequent segment; error on the first missing segment, quoting the full dotted path and the valid ids at that level.
   - **Split ambiguity:** require a scope segment for split containers (`split.scope.substep`); reject bare `split.substep` with a clear error.
   - Cycle detection operates on `head`.

3. **Runtime topological order** (`workflow.py:166-188`): compute indegree/edges against `head = dep.split(".", 1)[0]`. Apply the same head-mapping in `_has_pending_consumers` (95-101).

4. **Upstream collection** (`_collect_upstream_data`, `workflow.py:190-213`): resolve nodes via `tree.get(dep.replace(".", "/"))` (xarray path lookup). Use a **`.`→`__` sanitized child key** when inserting into the `multi_input` tree to avoid collisions and illegal node names. Downstream conduits key off `plugin_kind` attrs, not node name — safe.

5. **Token loop** (`workflow.py:393-399`): resolve deps with the same dot→slash conversion; key `upstream_tokens` by the raw dotted path.

6. **Docs** — update the `depends_on` field description (`workflows.py:346`) and the `_collect_upstream_data` / `call` docstrings to document dot syntax and deep validation. (`datatree-spec.md` itself is PR #1319's scope — code + docstrings only here.)

7. **Tests:**
   - Unit (`tests/unit_tests/interfaces/class_based/test_workflow.py` and `tests/unit_tests/pydantic_models/v1/test_workflow_spec_model.py`): valid dot-path accepted; missing nested segment rejected with clear error; split ambiguity rejected; topo order respects head mapping.
   - Integration (`tests/integration_tests/test_obp_datatree.py`): a top-level step with `depends_on: ["subwf.algo"]` receives the nested node's data.

**Risk:** Medium. Split-scope ambiguity and node-name sanitization are the sharp edges; covered by explicit errors + tests.

---

### L. Documented-only follow-ups (no code this pass)

Recorded for future issues (not created here per user's instruction):
- `data_tree=True` as default when a plugin has no family; requires pydantic to allow omitting `family` (`geoips/interfaces/class_based/algorithms.py:18`).
- Move `geoips_run` workflow methods into the `Workflow` class (`geoips/commandline/geoips_run.py:183`).
- A "master list" of legacy call-signature kwargs/args mappings to ease deprecation (`geoips/interfaces/class_based_plugin.py:299`).
- Clean out the `geoips/dev/` directory (`geoips/dev/output_config.py:1`).

---

## 3. Resolved / No-Action Threads (for the record)

- `geoips/commandline/geoips_test.py` debug line — already deleted by author.
- `geoips/interfaces/class_based/coverage_checkers.py:87` — jsolbrig added the requested explanatory comment.
- `geoips/dev/output_config.py:341` — self-resolved ("extra 360 doesn't matter here").
- `the-most-exciting-workflow.yaml` threads — enthusiasm, no action.
- `class_based_plugin.py:271` (DTD deprecation philosophy) — "no action needed at this time."
- `class_based_plugin.py:295` (`__call__` vs specialized `_wrap`) — author justified keeping the specialized function (eases future deprecation).
- `pydantic_models/v1/workflows.py:368` / `:1016` — clarifying Q&A; author confirmed intent; no change.

---

## 4. Global Verification Checklist

Run after each phase (and fully at the end):
- [ ] `python -c "import geoips"` (import-cycle / side-effect check — esp. after C, J)
- [ ] Unit tests: `tests/unit_tests/...` (esp. after A, H, J, M, N)
- [ ] Integration tests: `tests/integration_tests/test_obp_*.py` (esp. after M, N)
- [ ] `./tests/scripts/abi.static.dmw.imagery_windbarbs_high.sh` (Item A)
- [ ] `list_available_interfaces()` excludes `workflow` (Item J)
- [ ] Lint / style per repo config (confirm command — see AGENTS.md / pyproject).
- [ ] No token *stamping* removed (Item K constraint).

> **TODO before starting:** confirm the repo's lint/format/test entry points (e.g. `pytest`, `ruff`, `flake8`, `black`, `check_code.sh`) and record them here so they run consistently.

---

## 5. Risk Summary

| Item | Risk | Mitigation |
|---|---|---|
| A | Med — hot path both modes | Gate fallback strictly on dict-origin; unit tests both modes |
| J | High — discovery-wide | Do early; full unit suite gate; allowlist approach |
| K | Med — config/token semantics | Respect `rebuild_registries`; never drop token stamping |
| N | Med — split-scope ambiguity, node naming | Explicit errors + sanitized keys + tests |
| I | Med — reverting shared changes | Grep usages before revert |
| B (name-warn) | Low/Med — log noise | Verify override frequency; pick WARNING vs DEBUG |
| M, C, D, E, F, G, H | Low | Localized; verify per checklist |
