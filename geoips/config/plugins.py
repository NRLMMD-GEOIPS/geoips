# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Plugin-contributed configuration support for GeoIPS.

External plugin packages can register their own configuration settings with
GeoIPS by exposing a :class:`ConfigPlugin` via the ``geoips.config_plugins``
entry-point group::

    # in my_pkg/config.py
    from pydantic import BaseModel, Field
    from geoips.config import ConfigPlugin


    class MyPkgSettings(BaseModel):
        max_workers: int = Field(4, description="Max parallel workers.")
        tile_cache: str | None = None


    CONFIG_PLUGIN = ConfigPlugin(name="my_pkg", settings_model=MyPkgSettings)

    # in pyproject.toml
    [project.entry-points."geoips.config_plugins"]
    my_pkg = "my_pkg.config:CONFIG_PLUGIN"

The settings are then available as ``config.plugins.my_pkg.max_workers``, may
be set in ``.geoips.yaml`` under ``geoips.plugins.my_pkg``, and are overridable
via auto-generated environment variables of the form
``GEOIPS_PLUGIN_<PKG>_<FIELD>`` (e.g. ``GEOIPS_PLUGIN_MY_PKG_MAX_WORKERS``).

Discovery and per-plugin validation are lazy: plugin modules are only imported
when ``config.plugins`` is first accessed, and each plugin's settings are only
validated on first access, so a misconfigured plugin cannot break importing
``geoips.config`` for everyone.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from importlib import metadata
from typing import Any, Mapping

from pydantic import BaseModel, ValidationError
from pydantic_core import PydanticUndefined

from geoips.errors import ConfigError

LOG = logging.getLogger(__name__)

#: Entry-point group external packages use to register configuration.
CONFIG_PLUGIN_GROUP = "geoips.config_plugins"

#: Prefix for auto-generated plugin environment variables.
ENV_VAR_PREFIX = "GEOIPS_PLUGIN"


@dataclass(frozen=True)
class ConfigPlugin:
    """Describes the configuration a plugin package contributes to GeoIPS.

    Parameters
    ----------
    name : str
        The plugin namespace key. Settings are exposed as
        ``config.plugins.<name>`` and live under ``geoips.plugins.<name>`` in
        the YAML config file. Must match the entry-point name.
    settings_model : type[pydantic.BaseModel]
        A pydantic model describing the plugin's settings. Fields should
        provide defaults (or be ``Optional``) so that importing GeoIPS never
        fails when the plugin is installed but unconfigured.
    env_overrides : Mapping[str, str], optional
        Optional explicit environment-variable aliases mapping a full env var
        name to a model-relative dotted field path (e.g.
        ``{"MY_LEGACY_VAR": "max_workers"}``). Auto-generated variables are
        always available in addition to these.
    """

    name: str
    settings_model: type[BaseModel]
    env_overrides: Mapping[str, str] = field(default_factory=dict)


def _sanitize(text: str) -> str:
    """Uppercase *text* and collapse non-alphanumerics into single underscores."""
    return re.sub(r"[^A-Z0-9]+", "_", text.upper()).strip("_")


def env_var_for(pkg: str, dotted_field: str) -> str:
    """Return the auto-generated env var name for a plugin field.

    Parameters
    ----------
    pkg : str
        The plugin name.
    dotted_field : str
        The model-relative dotted field path (e.g. ``"cache.tile_dir"``).

    Returns
    -------
    str
        The environment variable name (e.g. ``GEOIPS_PLUGIN_MY_PKG_CACHE_TILE_DIR``).
    """
    return f"{ENV_VAR_PREFIX}_{_sanitize(pkg)}_{_sanitize(dotted_field)}"


def is_nested_model(annotation: Any) -> type[BaseModel] | None:
    """Return the nested pydantic model for an annotation, or None."""
    return annotation if getattr(annotation, "model_fields", None) else None


def _field_leaf_paths(name: str, field_info: Any, prefix: str) -> frozenset[str]:
    """Return the dotted leaf paths contributed by a single field."""
    nested = is_nested_model(field_info.annotation)
    if nested is None:
        return frozenset({f"{prefix}{name}"})
    return leaf_field_paths(nested, f"{prefix}{name}.")


def leaf_field_paths(model_cls: type[BaseModel], prefix: str = "") -> frozenset[str]:
    """Return the set of dotted leaf field paths for a pydantic model tree."""
    return frozenset().union(
        *(
            _field_leaf_paths(name, field_info, prefix)
            for name, field_info in model_cls.model_fields.items()
        )
    )


def _annotation_at(model_cls: type[BaseModel], dotted: str) -> Any:
    """Return the type annotation for a dotted field path, or None if absent."""
    current: Any = model_cls
    for part in dotted.split("."):
        fields = getattr(current, "model_fields", None)
        if not fields or part not in fields:
            return None
        current = fields[part].annotation
    return current


def _model_defaults(model_cls: type[BaseModel]) -> dict[str, Any]:
    """Return a nested dict of a model's default values.

    Fields without a default (required fields) are omitted; nested models are
    recursed into.
    """
    defaults: dict[str, Any] = {}
    for name, field_info in model_cls.model_fields.items():
        nested = is_nested_model(field_info.annotation)
        if nested is not None:
            defaults[name] = _model_defaults(nested)
        elif field_info.default is not PydanticUndefined:
            defaults[name] = field_info.default
        elif field_info.default_factory is not None:
            defaults[name] = field_info.default_factory()  # type: ignore[call-arg]
    return defaults


def full_model_defaults(model_cls: type[BaseModel]) -> dict[str, Any]:
    """Return a full default dump of a model when instantiable, else partial.

    Uses ``model_dump()`` when the model has no required fields; otherwise
    falls back to :func:`_model_defaults`, which omits required fields.
    """
    try:
        return model_cls().model_dump()
    except ValidationError:
        return _model_defaults(model_cls)


def field_comment(model_cls: type[BaseModel], name: str) -> str:
    """Return a human-readable comment for a field.

    Prefers the field's ``description``; appends ``(default: ...)`` for scalar
    fields with a simple default. Nested-model and factory defaults are not
    expanded (their contents render as their own YAML lines).
    """
    field_info = model_cls.model_fields.get(name)
    if field_info is None:
        return ""
    parts: list[str] = []
    if field_info.description:
        parts.append(field_info.description)
    if field_info.default is not PydanticUndefined:
        parts.append(f"(default: {field_info.default!r})")
    elif not field_info.description and field_info.default_factory is None:
        parts.append("(required)")
    return " ".join(parts)


def _cast_env_value(annotation: Any, raw: str) -> Any:
    """Cast a raw env string toward a field annotation.

    Handles booleans, ``none``/``null``, and space-separated lists; other
    values are returned as strings and coerced by pydantic during validation.
    """
    lower = raw.lower()
    if lower == "true":
        return True
    if lower == "false":
        return False
    if lower in ("none", "null"):
        return None
    origin = getattr(annotation, "__origin__", None)
    if annotation in (list, tuple, set) or origin in (list, tuple, set):
        return raw.split()
    return raw


def plugin_field_env_map(plugin: ConfigPlugin) -> dict[str, str]:
    """Return a mapping of env var name to model-relative dotted field path."""
    mapping = {
        env_var_for(plugin.name, dotted): dotted
        for dotted in leaf_field_paths(plugin.settings_model)
    }
    mapping.update(plugin.env_overrides)
    return mapping


def build_plugin_env_map(
    plugins: Mapping[str, ConfigPlugin] | None = None,
) -> dict[str, str]:
    """Return the combined env var -> ``plugins.<pkg>.<field>`` map.

    Raises
    ------
    ConfigError
        If a plugin env var collides with a core GeoIPS env var or with
        another plugin's env var.
    """
    from geoips.config.schema import GEOIPS_ENV_MAP

    if plugins is None:
        plugins = discover_config_plugins()

    env_map: dict[str, str] = {}
    for pkg, plugin in plugins.items():
        for env_var, rel_path in plugin_field_env_map(plugin).items():
            target = f"plugins.{pkg}.{rel_path}"
            if env_var in GEOIPS_ENV_MAP:
                raise ConfigError(
                    f"Plugin {pkg!r} env var {env_var!r} collides with a core "
                    f"GeoIPS env var. Use ConfigPlugin.env_overrides to rename it."
                )
            if env_var in env_map and env_map[env_var] != target:
                raise ConfigError(
                    f"Plugin {pkg!r} env var {env_var!r} collides with another "
                    f"plugin setting ({env_map[env_var]!r})."
                )
            env_map[env_var] = target
    return env_map


def cast_plugin_target(target: str, raw: str) -> Any:
    """Cast a raw env value for a ``plugins.<pkg>.<field>`` target path."""
    _, pkg, dotted = target.split(".", 2)
    plugins = discover_config_plugins()
    plugin = plugins.get(pkg)
    annotation = _annotation_at(plugin.settings_model, dotted) if plugin else None
    return _cast_env_value(annotation, raw)


_CACHE: dict[str, ConfigPlugin] | None = None


def discover_config_plugins(*, refresh: bool = False) -> dict[str, ConfigPlugin]:
    """Discover and return all registered config plugins, keyed by name.

    Results are cached after the first call unless *refresh* is True.

    Raises
    ------
    ConfigError
        If an entry point does not load a :class:`ConfigPlugin`, if its
        declared name does not match the entry-point name, or if two plugins
        share a name.
    """
    global _CACHE
    if _CACHE is not None and not refresh:
        return _CACHE

    plugins: dict[str, ConfigPlugin] = {}
    for entry in metadata.entry_points(group=CONFIG_PLUGIN_GROUP):
        obj = entry.load()
        if not isinstance(obj, ConfigPlugin):
            raise ConfigError(
                f"Entry point {entry.name!r} in {CONFIG_PLUGIN_GROUP!r} must "
                f"load a ConfigPlugin, got {type(obj).__name__}."
            )
        if obj.name != entry.name:
            raise ConfigError(
                f"ConfigPlugin name {obj.name!r} does not match its entry-point "
                f"name {entry.name!r}."
            )
        if obj.name in plugins:
            raise ConfigError(f"Duplicate config plugin name {obj.name!r}.")
        plugins[obj.name] = obj

    _CACHE = plugins
    return plugins


def _deep_update(base: dict, override: Mapping) -> None:
    """Recursively merge *override* into *base* in-place."""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_update(base[key], value)
        else:
            base[key] = value


def _read_plugin_env(plugin: ConfigPlugin) -> dict[str, Any]:
    """Return nested env overrides (relative to the model) for a plugin."""
    overrides: dict[str, Any] = {}
    for env_var, rel_path in plugin_field_env_map(plugin).items():
        raw = os.getenv(env_var)
        if raw is None:
            continue
        annotation = _annotation_at(plugin.settings_model, rel_path)
        cast = _cast_env_value(annotation, raw)
        parts = rel_path.split(".")
        node = overrides
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = cast
    return overrides


def resolve_plugin_settings(
    plugin: ConfigPlugin, yaml_values: Mapping[str, Any] | None
) -> BaseModel:
    """Resolve a plugin's settings with defaults < YAML < env precedence.

    Parameters
    ----------
    plugin : ConfigPlugin
        The plugin to resolve.
    yaml_values : Mapping or None
        The ``geoips.plugins.<pkg>`` sub-mapping from the project config, if any.

    Returns
    -------
    pydantic.BaseModel
        A validated instance of the plugin's settings model.

    Raises
    ------
    ConfigError
        If the merged values fail validation against the plugin's model.
    """
    merged = _model_defaults(plugin.settings_model)
    if yaml_values:
        _deep_update(merged, dict(yaml_values))
    _deep_update(merged, _read_plugin_env(plugin))
    try:
        return plugin.settings_model.model_validate(merged)
    except ValidationError as exc:
        raise ConfigError(
            f"Invalid configuration for plugin {plugin.name!r}:\n{exc}"
        ) from exc


class PluginSettingsNamespace:
    """Attribute/dict accessor for resolved plugin settings.

    Access a plugin's validated settings via ``config.plugins.<name>`` or
    ``config.plugins["<name>"]``. Iterating yields the registered plugin names.
    """

    def __init__(self, resolver, names) -> None:
        self._resolver = resolver
        self._names = tuple(names)

    def __getattr__(self, name: str) -> BaseModel:
        """Return the resolved settings for plugin *name* via attribute access."""
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            return self._resolver(name)
        except KeyError:
            raise AttributeError(
                f"No config plugin named {name!r} is registered."
            ) from None

    def __getitem__(self, name: str) -> BaseModel:
        """Return the resolved settings for plugin *name* via item access."""
        try:
            return self._resolver(name)
        except KeyError:
            raise KeyError(name) from None

    def get(self, name: str, default: Any = None) -> Any:
        """Return the settings for *name*, or *default* if not registered."""
        try:
            return self._resolver(name)
        except KeyError:
            return default

    def __iter__(self):
        """Iterate over the registered plugin names."""
        return iter(self._names)

    def __contains__(self, name: object) -> bool:
        """Return True if a plugin named *name* is registered."""
        return name in self._names

    def __repr__(self) -> str:
        """Return a debug representation listing the registered plugin names."""
        return f"PluginSettingsNamespace(plugins={list(self._names)!r})"
