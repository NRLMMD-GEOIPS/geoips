<!--
# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.
-->

<!-- cspell:ignore igration -->
<!-- "igration" is a cspell allowCompoundWords artifact on the correctly-spelled word
     "migration"; it is not a typo. -->

(converting-module-to-class)=

# Converting module-based plugins to class-based

GeoIPS 2.0 converted its Python plugins from **module-based** (a module with a top-level
`call()` function) to **class-based** (a class subclassing an interface base class). This
guide shows how to convert your own plugins. For how class-based plugins work, see
{ref}`writing-class-based-plugins`.

## The mapping

A 1.x module-based plugin looks like this:

```python
# geoips/plugins/modules/algorithms/single_channel.py
interface = "algorithms"
family = "list_numpy_to_numpy"
name = "single_channel"


def call(arrays, output_data_range=None, input_units=None, output_units=None):
    """Apply data range and corrections to a single channel product."""
    ...
    return final_array
```

The 2.0 class-based equivalent:

```python
# geoips/plugins/classes/algorithms/single_channel.py
from geoips.interfaces.class_based.algorithms import BaseAlgorithmPlugin


class SingleChannelAlgorithmPlugin(BaseAlgorithmPlugin):
    """Single Channel algorithm plugin class."""

    interface = "algorithms"
    family = "list_numpy_to_numpy"
    name = "single_channel"

    def call(self, arrays, output_data_range=None, input_units=None,
             output_units=None):
        """Apply data range and corrections to a single channel product."""
        ...
        return final_array


PLUGIN_CLASS = SingleChannelAlgorithmPlugin
```

Step by step:

1. **Move the file** from `.../plugins/modules/<interface>/` to
   `.../plugins/classes/<interface>/` (keep the same filename).
2. **Wrap the module in a class** that subclasses the interface base class
   (`Base<Interface>Plugin` from `geoips.interfaces.class_based.<interface>`). The class
   name convention is `<Name><Interface>Plugin` (e.g. `SingleChannelAlgorithmPlugin`).
3. **Move `interface` / `family` / `name`** from module attributes to class attributes.
4. **Turn `call()` into a method** — add `self` as the first parameter. Its remaining
   signature stays the same.
5. **Replace cross-plugin imports with `self`** — shared helpers moved onto the base
   classes, so where a 1.x plugin imported a helper from a sibling plugin, call it via
   `self.<helper>` instead (or add it to the base class if it is missing).
6. **Add `PLUGIN_CLASS = <YourPluginClass>`** at the bottom of the module so the registry
   knows which class is the plugin.
7. **Rebuild registries** with `geoips config create-registries` and confirm with
   `geoips list <interface>` / `geoips describe <interface> <name>`.

## Data conversion is handled for you

You generally do **not** need to handle DataTree conversion. The interface base class
converts the OBP/scripting `DataTree` into the native input type your `family` expects
before `call()` runs, and wraps your return value afterward. Continue to write `call()` in
terms of the native types (numpy arrays, xarray objects) your family uses.

## Assisted conversion

The repository ships helper scripts under `v2_migration_tools/` that automate much of the
mechanical rewrite:

- `module_to_class.py` — walks a plugin package's registered module-based plugins and
  generates class-based versions.
- `cst_transformer.py` — the libCST-based transformer that rewrites a single file
  (`convert_single_file(input_file, output_file, class_name, base_class, ...)`).

These are developer tools intended to bootstrap a conversion; review and test the
generated classes, and adjust output paths for your environment. Always run the plugin's
tests (and `geoips list`/`describe`) after converting.

## See also

- {ref}`writing-class-based-plugins` — the class-based plugin contract in detail.
- {ref}`migrating-1x-to-2x` — the full 1.x to 2.0 migration overview.
