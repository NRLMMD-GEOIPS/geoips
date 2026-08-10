<!--
# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.
-->

(writing-class-based-plugins)=

# Writing a class-based plugin

In GeoIPS 2.0, most Python plugins — readers, algorithms, interpolators, colormappers,
output formatters, filename formatters, title formatters, coverage checkers, and more —
are **class-based**. Each plugin is a Python class that subclasses the base class for its
interface and implements a `call()` method.

:::{admonition} Coming from 1.x module-based plugins?
:class: note

In GeoIPS 1.x these plugins were *module-based*: a module with a top-level `call()`
function and `interface`/`family`/`name` module attributes. In 2.0 they are true classes.
See the {ref}`module-to-class conversion guide <converting-module-to-class>` to migrate an
existing plugin.
:::

## Anatomy of a plugin

A class-based plugin:

1. Subclasses the interface base class (e.g. `BaseAlgorithmPlugin` from
   `geoips.interfaces.class_based.algorithms`).
2. Sets three required class attributes: `interface`, `family`, and `name`.
3. Implements `call(self, ...)` with the arguments its family expects.
4. Declares `PLUGIN_CLASS = <YourPluginClass>` at the bottom of the module so the plugin
   registry (`pluginify`) knows which class in the file is the plugin.

```python
from geoips.interfaces.class_based.algorithms import BaseAlgorithmPlugin

import logging

LOG = logging.getLogger(__name__)


class SingleChannelAlgorithmPlugin(BaseAlgorithmPlugin):
    """Single Channel algorithm plugin class."""

    interface = "algorithms"
    family = "list_numpy_to_numpy"
    name = "single_channel"

    def call(self, arrays, output_data_range=None, input_units=None,
             output_units=None, min_outbounds="crop", max_outbounds="crop",
             norm=False, inverse=False):
        """Apply data range and requested corrections to a single channel product."""
        ...
        return final_array


# Tells pluginify which class in this module is the plugin to register.
PLUGIN_CLASS = SingleChannelAlgorithmPlugin
```

This example mirrors the real
`geoips/plugins/classes/algorithms/single_channel.py`.

## Required class attributes

`interface`
: The interface the plugin belongs to (e.g. `"algorithms"`, `"readers"`). Must be a known
  class-based interface. Usually the interface base class already implies it, but set it
  explicitly on your plugin.

`family`
: The family name, which determines the plugin's expected call signature and how GeoIPS
  converts data into and out of it.

`name`
: The unique plugin name used to look it up (`algorithms.get_plugin("single_channel")`).

The base class validates that all three are non-empty strings and that `interface` is a
real interface.

## The `call()` method

`call()` holds your plugin's logic. You do **not** call it directly — the base class
exposes it through `__call__` and wraps it with pre/post hooks, so both of these work:

```python
plugin = algorithms.get_plugin("single_channel")
result = plugin(arrays, output_data_range=[-90.0, 30.0])   # module-style call
```

Under {ref}`Order-Based Processing <order-based-processing>` and
{ref}`scripting <scripting-guide>`, plugins are called with the accumulated `data` tree.
The base class handles converting the DataTree into the native input type your `family`
expects (e.g. a list of numpy arrays for `list_numpy_to_numpy`) before `call()` runs, and
wrapping your return value back into the tree afterward. In most cases you only write
`call()` and never touch the `_pre_call` / `_post_call` hooks.

## Where plugins live and how they register

Class-based plugins live under `geoips/plugins/classes/<interface>/<name>.py` (or the
equivalent path in your plugin package). Declare `PLUGIN_CLASS = <YourPluginClass>` at the
bottom of the module so the registry knows which class to register. After adding a plugin,
rebuild the plugin registries so GeoIPS can find it:

```bash
geoips config create-registries
```

Then confirm it is discovered:

```bash
geoips list algorithms
geoips describe alg single_channel
```

## Shared functionality on base classes

In 2.0 common behavior moved onto the interface base classes, so plugins of the same kind
no longer import helpers from one another — access shared functionality via `self`
instead. When adding behavior useful to every plugin of an interface, prefer adding it to
the interface base class.

## See also

- {ref}`converting-module-to-class` — migrate a 1.x module-based plugin.
- {ref}`order-based-processing` — how plugins are composed into workflows.
- The tutorials under {ref}`tutorials` walk through building specific plugin types
  end-to-end.
