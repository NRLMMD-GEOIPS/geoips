# Script DataTree Developer Notes

This document describes how to extend the script DataTree helpers used by
OBP-style plugin calls in scripts.

The public scripting API is exposed from `geoips.scripting`. Implementation
details live in `geoips.utils.types.script_datatree`.

## Public API And Testing Expectations

`geoips.scripting` is the user-facing import surface for script helpers.
Implementation details may live in `geoips.utils.types.script_datatree`, but
normal user scripts should not need to import from that module directly.

Current public scripting helpers and values:

- `add_data_step`
- `attach_plugin_result`
- `get_current_data`
- `get_output_products`
- `initialize_script_tree`
- `RetentionPolicy`
- `RETENTION_POLICIES`

Retention helpers should not be exposed from `geoips.scripting` until there is a
clear user-facing need. For example, `normalize_retention_policy` and
`validate_retention_policy` are implementation helpers and should remain
internal for now.

When adding a new public helper:

1. Add it to `geoips.scripting`.
2. Add it to `geoips.scripting.__all__`.
3. Provide a user-facing docstring.
4. Include an example showing how it interacts with plugin calls when relevant.
5. Add focused tests in `tests/unit_tests/test_scripting.py`.
6. Update `docs/dev/obp_script_plugin_calls.md` if users should know about it.

When adding or changing retention policy behavior:

- Keep `RETENTION_POLICIES` derived from `tuple(RetentionPolicy)` rather than
  maintaining a separate list by hand.
- Accept both `RetentionPolicy` values and equivalent strings when appropriate.
- Store canonical string values in DataTree attrs so attrs remain easy to
  inspect and serialize.
- Apply retention at the attachment boundary so each scripted plugin call
  returns a tree that already reflects the effective policy.
- Add tests for enum values and string values.
- Add tests for interactive descriptions on each policy member.

When adding or changing reserved root attrs:

- Add the reserved name to `_RESERVED_ROOT_ATTRS`.
- Stamp the value from GeoIPS-managed code rather than accepting it through
  arbitrary `**attrs`.
- Add tests proving users cannot override the reserved attr through
  `initialize_script_tree(..., **attrs)`.

## Script Plugin Kind Validation

Script step metadata validates `plugin_kind` against the registered GeoIPS
interface list. The valid kinds are derived from
`geoips.interfaces.list_available_interfaces()`, singularized with `Lexeme`, and
cached for the lifetime of the Python process. The special kind `manual` is also
allowed for user-created script data.
`product` and `workflow` are intentionally excluded for now; workflow support may
be added later once scripted workflow composition is better defined.

Do not replace this with a hard-coded list unless the interface registry is no
longer available. Interface discovery can be expensive, so keep the lookup
cached.

When adding a new GeoIPS interface, script plugin kind validation should pick it
up automatically through `list_available_interfaces()`. Add tests only if the
new interface has special script behavior.

## Script Step Data Conversion

Script step data is normalized through `DataTreeDitto` before it is attached to
the root script tree. Accepted values are:

- `xarray.DataTree`
- `DataTreeDitto`
- `xarray.Dataset`
- `xarray.DataArray`
- other types registered with the `DataTreeDitto` converter registry

The script helper should not silently accept arbitrary scalars. If a user wants
to attach a scalar or simple value, they should wrap it in a supported structure
such as a `dict`, `Dataset`, or `DataArray`.

Keep low-level conversion behavior in `DataTreeDitto` and the converter
registry. Script helpers may catch conversion errors and re-raise them with
script-specific context, such as the step id and the unsupported input type.
When doing so, include the original converter error text in the script-facing
error so users can see whether the problem is the outer object type or the
contents of an otherwise supported container.

## Script Tree And Timestamp Validation

Script helpers should validate root script trees the first time they are seen.
A valid script tree is an `xarray.DataTree` created by `initialize_script_tree()`
with:

- `execution_mode="script"`
- `retention_policy`
- `start_time`
- `end_time`

Do not rely only on `execution_mode="script"`; manually constructed trees with
that attr but without the required metadata should fail with an error that
directs users back to `initialize_script_tree()`.

Root timestamps are managed by GeoIPS. `initialize_script_tree()` should stamp
`start_time` automatically and initialize `end_time` to `None`; users should not
be allowed to provide those values as arbitrary attrs.

Step timestamps should be accepted as `datetime.datetime` instances or `None`,
then stored as ISO strings in DataTree attrs. Timestamp strings should be
rejected at the API boundary so scripts do not mix parsed and unparsed time
metadata. For manual steps, omitted timestamps should remain `None`; registered
plugin steps may receive automatic current UTC timestamps.

## Adding A Retention Policy

Retention policies are defined by the `RetentionPolicy` enum in
`geoips.utils.types.script_datatree`.

To add a new policy:

1. Add a new `RetentionPolicy` member.

   ```python
   class RetentionPolicy(StrEnum):
       keep_all = (
           "keep_all",
           "Keep every plugin result intact...",
       )
       new_policy = (
           "new_policy",
           "Brief user-facing description of what this policy retains.",
       )
   ```

2. Include a useful description.

   Each enum member is string-like, but also carries a `description` and
   member-level `__doc__` value for interactive help. Write this description as
   user-facing documentation.

3. Update retention application logic.

   Policy validation updates automatically because `RETENTION_POLICIES` is
   derived from `tuple(RetentionPolicy)`. The behavior still needs to be
   implemented where script retention is applied.

4. Add tests.

   Add or update tests for:

   - accepting the new policy value
   - accepting the string equivalent
   - applying the policy behavior
   - preserving useful interactive descriptions

5. Update user-facing documentation.

   Update `docs/dev/obp_script_plugin_calls.md` with the new policy, expected
   behavior, and an example if the policy is generally useful.

## Adding Reserved Root Attributes

Reserved root attributes are defined by `_RESERVED_ROOT_ATTRS` in
`geoips.utils.types.script_datatree`.

These attributes are managed by GeoIPS and may not be supplied through
`initialize_script_tree(..., **attrs)`.

Current reserved attributes include:

- `execution_mode`
- `retention_policy`
- `start_time`
- `end_time`

Reserved root attributes should be initialized when the script tree is created.
If the value is not known at initialization time, initialize it to `None`.
For example, `end_time` starts as `None` and can be filled by a later
finalization or execution-lifecycle helper.

To add a new reserved root attribute:

1. Add the name to `_RESERVED_ROOT_ATTRS`.

   ```python
   _RESERVED_ROOT_ATTRS = frozenset(
       ("execution_mode", "retention_policy", "start_time", "end_time", "new_attr")
   )
   ```

2. Set the attribute from GeoIPS-managed code.

   Reserved attributes should be stamped by initialization, finalization,
   attachment, retention, or provenance helpers. Add an initial value during
   script tree initialization, using `None` when the value will be populated
   later. Reserved attributes should not be accepted as arbitrary user-provided
   metadata.

3. Add tests.

   Add tests showing:

   - the helper stamps the attribute when appropriate
   - user attempts to override the attribute through `**attrs` raise an error

4. Update developer or user docs if users need to understand the attribute.

## Reserved Attribute Error Behavior

If a user tries to set a reserved root attribute, initialization raises
`ValueError` and identifies the reserved fields.

For example:

```python
from geoips.scripting import RetentionPolicy, initialize_script_tree

initialize_script_tree(
    "example",
    retention_policy=RetentionPolicy.keep_all,
    execution_mode="custom",
)
```

raises an error like:

```text
ValueError: Script DataTree metadata fields are reserved and may not be
overridden: execution_mode.
```

This prevents user metadata from clobbering fields GeoIPS relies on to identify
script-mode execution, apply retention, and track execution metadata.

## User-Facing Docstrings

Any helper exposed through `geoips.scripting` should have a user-facing
docstring that explains:

- what the helper does
- how it is used with plugin calls
- whether it accepts `RetentionPolicy` values or strings
- what it returns
- what errors users should expect

Lower-level helpers that remain internal should still have docstrings, but they
can focus on implementation behavior rather than tutorial-style usage.
