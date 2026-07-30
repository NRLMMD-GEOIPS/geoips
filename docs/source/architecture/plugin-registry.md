<!--
# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.
-->

(plugin-registry)=

# The plugin registry (pluginify)

GeoIPS does not implement its own plugin-management machinery. Instead it uses
[**pluginify**](https://nrlmmd-geoips.github.io/pluginify/), a standalone package that
registers YAML and Python (class- or module-based) plugins into a single, queryable
`PluginRegistry`. Pluginify holds no plugins of its own — it provides the machinery to
register, retrieve, and create plugin objects — so GeoIPS and its plugin packages share
one consistent plugin system.

## How GeoIPS uses it

**Plugin packages advertise themselves.** A GeoIPS plugin package (including `geoips`
itself) registers under the `geoips.plugin_packages` entry-point group in its
`pyproject.toml`:

```toml
[project.entry-points."geoips.plugin_packages"]
my_package = "my_package"
```

**Pluginify builds the registry.** Pluginify scans every registered package for plugins —
YAML files under `plugins/yaml/`, class-based plugins under `plugins/classes/`, and any
remaining module-based plugins — and writes registry files that map each plugin's
interface/name to its location. You (re)build the registry after installing or updating
plugins:

```bash
geoips config create-registries    # wraps pluginify's registry build
geoips config delete-registries    # removes the registry files
```

Under the hood these commands drive
[`pluginify`](https://nrlmmd-geoips.github.io/pluginify/)'s `PluginRegistry` (equivalently,
`pluginify create` / `pluginify delete`). You should not edit the generated registry files
by hand.

**GeoIPS interfaces resolve plugins through it.** The GeoIPS interface classes extend
pluginify's interface base classes, so looking up a plugin by name resolves it from the
registry:

```python
from geoips import interfaces

reader = interfaces.readers.get_plugin("abi_netcdf")
```

The same registry powers the discovery commands `geoips list <interface>` and
`geoips describe <interface> <name>`.

## More information

For the registry internals — the `PluginRegistry` API, the `pluginify` CLI, and how
plugins are validated and stored — see the
[pluginify documentation](https://nrlmmd-geoips.github.io/pluginify/).

## See also

- {ref}`extend GeoIPS with plugins <plugin-extend>` — the plugin model (interfaces, families, YAML vs class-based).
- {ref}`writing-class-based-plugins` — authoring a Python plugin.
- {ref}`geoips config create-registries <geoips_config_create-registries>` — the CLI command.
