# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Tests for plugin-contributed configuration (``geoips.config.plugins``)."""

from types import SimpleNamespace

import pytest
from pydantic import BaseModel, Field

from geoips.config import plugins as plugins_mod
from geoips.config.config import GeoIPSConfig
from geoips.config.plugins import (
    ConfigPlugin,
    build_plugin_env_map,
    cast_plugin_target,
    discover_config_plugins,
    env_var_for,
    leaf_field_paths,
    resolve_plugin_settings,
)
from geoips.errors import ConfigError


class CacheSettings(BaseModel):
    """Nested settings used to exercise dotted field paths."""

    tile_dir: str | None = None
    size: int = 256


class SampleSettings(BaseModel):
    """Sample plugin settings model with a mix of field types."""

    max_workers: int = Field(4, description="Max parallel workers.")
    enabled: bool = False
    tags: list[str] = Field(default_factory=list)
    cache: CacheSettings = Field(default_factory=CacheSettings)


class RequiredSettings(BaseModel):
    """Plugin settings with a required field (no default)."""

    token: str


def _fake_entry_point(name, obj, dist_name=None):
    """Build a stand-in importlib.metadata EntryPoint."""
    dist = SimpleNamespace(name=dist_name) if dist_name else None
    return SimpleNamespace(name=name, load=lambda: obj, dist=dist)


@pytest.fixture
def register_plugins(monkeypatch):
    """Return a function that registers fake config plugins for a test."""

    def _register(*entry_points):
        monkeypatch.setattr(
            plugins_mod.metadata,
            "entry_points",
            lambda group=None: (
                list(entry_points) if group == plugins_mod.CONFIG_PLUGIN_GROUP else []
            ),
        )
        monkeypatch.setattr(plugins_mod, "_CACHE", None)

    return _register


class TestEnvVarNaming:
    """Auto-generated env var naming conventions."""

    def test_env_var_for_simple(self):
        """Verify simple field names produce prefixed uppercase env vars."""
        assert (
            env_var_for("my_pkg", "max_workers") == "GEOIPS_PLUGIN_MY_PKG_MAX_WORKERS"
        )

    def test_env_var_for_nested(self):
        """Verify dotted paths are flattened with underscores."""
        assert (
            env_var_for("my-pkg", "cache.tile_dir")
            == "GEOIPS_PLUGIN_MY_PKG_CACHE_TILE_DIR"
        )

    def test_leaf_field_paths(self):
        """Verify nested models expand to dotted leaf paths."""
        paths = leaf_field_paths(SampleSettings)
        assert paths == frozenset(
            {"max_workers", "enabled", "tags", "cache.tile_dir", "cache.size"}
        )


class TestDiscovery:
    """Config plugin discovery via entry points."""

    def test_discovers_plugin(self, register_plugins):
        """Verify a registered ConfigPlugin is discovered by name."""
        plugin = ConfigPlugin(name="sample", settings_model=SampleSettings)
        register_plugins(_fake_entry_point("sample", plugin))
        assert discover_config_plugins() == {"sample": plugin}

    def test_non_config_plugin_raises(self, register_plugins):
        """Verify entry points that aren't ConfigPlugins raise ConfigError."""
        register_plugins(_fake_entry_point("bad", object()))
        with pytest.raises(ConfigError, match="must .*load a ConfigPlugin"):
            discover_config_plugins()

    def test_name_mismatch_raises(self, register_plugins):
        """Verify a name/entry-point mismatch raises ConfigError."""
        plugin = ConfigPlugin(name="other", settings_model=SampleSettings)
        register_plugins(_fake_entry_point("sample", plugin))
        with pytest.raises(ConfigError, match="does not match"):
            discover_config_plugins()


class TestEnvMap:
    """Plugin env-map construction and collision detection."""

    def test_build_env_map(self, register_plugins):
        """Verify env vars map to plugins.<pkg>.<field> targets."""
        register_plugins(
            _fake_entry_point(
                "sample", ConfigPlugin(name="sample", settings_model=SampleSettings)
            )
        )
        env_map = build_plugin_env_map()
        assert (
            env_map["GEOIPS_PLUGIN_SAMPLE_MAX_WORKERS"] == "plugins.sample.max_workers"
        )
        assert (
            env_map["GEOIPS_PLUGIN_SAMPLE_CACHE_TILE_DIR"]
            == "plugins.sample.cache.tile_dir"
        )

    def test_core_collision_raises(self, register_plugins):
        """Verify an env_overrides alias colliding with a core var raises."""
        plugin = ConfigPlugin(
            name="sample",
            settings_model=SampleSettings,
            env_overrides={"GEOIPS_OUTDIRS": "max_workers"},
        )
        register_plugins(_fake_entry_point("sample", plugin))
        with pytest.raises(ConfigError, match="collides with a core"):
            build_plugin_env_map()

    def test_plugin_collision_raises(self, register_plugins):
        """Verify two plugins claiming the same env var alias raises."""
        register_plugins(
            _fake_entry_point(
                "a",
                ConfigPlugin(
                    name="a",
                    settings_model=SampleSettings,
                    env_overrides={"SHARED_VAR": "max_workers"},
                ),
            ),
            _fake_entry_point(
                "b",
                ConfigPlugin(
                    name="b",
                    settings_model=SampleSettings,
                    env_overrides={"SHARED_VAR": "max_workers"},
                ),
            ),
        )
        with pytest.raises(ConfigError, match="collides with another plugin"):
            build_plugin_env_map()

    def test_cast_plugin_target(self, register_plugins):
        """Verify casting uses the plugin field's declared type."""
        register_plugins(
            _fake_entry_point(
                "sample", ConfigPlugin(name="sample", settings_model=SampleSettings)
            )
        )
        assert cast_plugin_target("plugins.sample.max_workers", "8") == "8"
        assert cast_plugin_target("plugins.sample.enabled", "true") is True
        assert cast_plugin_target("plugins.sample.tags", "a b c") == ["a", "b", "c"]


class TestResolution:
    """Layered resolution of plugin settings (defaults < yaml < env)."""

    def test_defaults(self):
        """Verify defaults are used when no yaml/env provided."""
        plugin = ConfigPlugin(name="sample", settings_model=SampleSettings)
        settings = resolve_plugin_settings(plugin, None)
        assert settings.max_workers == 4
        assert settings.cache.size == 256

    def test_yaml_overrides_defaults(self):
        """Verify YAML values override defaults."""
        plugin = ConfigPlugin(name="sample", settings_model=SampleSettings)
        settings = resolve_plugin_settings(
            plugin, {"max_workers": 9, "cache": {"size": 1}}
        )
        assert settings.max_workers == 9
        assert settings.cache.size == 1

    def test_env_overrides_yaml(self, monkeypatch):
        """Verify env vars take precedence over YAML."""
        monkeypatch.setenv("GEOIPS_PLUGIN_SAMPLE_MAX_WORKERS", "16")
        monkeypatch.setenv("GEOIPS_PLUGIN_SAMPLE_ENABLED", "true")
        plugin = ConfigPlugin(name="sample", settings_model=SampleSettings)
        settings = resolve_plugin_settings(plugin, {"max_workers": 9})
        assert settings.max_workers == 16
        assert settings.enabled is True

    def test_required_field_missing_raises(self):
        """Verify a missing required field raises a clear ConfigError."""
        plugin = ConfigPlugin(name="req", settings_model=RequiredSettings)
        with pytest.raises(ConfigError, match="Invalid configuration for plugin 'req'"):
            resolve_plugin_settings(plugin, None)


class TestGeoIPSConfigPlugins:
    """Plugin access via the GeoIPSConfig.plugins namespace."""

    def test_attribute_access(self, register_plugins, monkeypatch):
        """Verify config.plugins.<pkg> returns the validated model."""
        monkeypatch.setenv("GEOIPS_OUTDIRS", "/test/out")
        register_plugins(
            _fake_entry_point(
                "sample", ConfigPlugin(name="sample", settings_model=SampleSettings)
            )
        )
        cfg = GeoIPSConfig()
        assert cfg.plugins.sample.max_workers == 4
        assert cfg.plugins["sample"].cache.size == 256
        assert "sample" in list(cfg.plugins)

    def test_unknown_plugin_raises(self, register_plugins, monkeypatch):
        """Verify accessing an unregistered plugin raises AttributeError."""
        monkeypatch.setenv("GEOIPS_OUTDIRS", "/test/out")
        register_plugins()
        cfg = GeoIPSConfig()
        with pytest.raises(AttributeError):
            cfg.plugins.nope
        assert cfg.plugins.get("nope") is None

    def test_lazy_validation_isolates_failure(self, register_plugins, monkeypatch):
        """Verify a broken plugin only fails when that plugin is accessed."""
        monkeypatch.setenv("GEOIPS_OUTDIRS", "/test/out")
        register_plugins(
            _fake_entry_point(
                "ok", ConfigPlugin(name="ok", settings_model=SampleSettings)
            ),
            _fake_entry_point(
                "req", ConfigPlugin(name="req", settings_model=RequiredSettings)
            ),
        )
        cfg = GeoIPSConfig()
        assert cfg.plugins.ok.max_workers == 4
        with pytest.raises(ConfigError):
            cfg.plugins.req
