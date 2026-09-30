# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Tests for plugin-aware ``geoips config`` CLI helpers."""

from types import SimpleNamespace

import pytest
import yaml
from pydantic import BaseModel, Field

from geoips.commandline import geoips_config as cli
from geoips.config import plugins as plugins_mod
from geoips.config.plugins import ConfigPlugin


class SampleSettings(BaseModel):
    """Sample plugin settings used for CLI rendering tests."""

    max_workers: int = Field(4, description="Max parallel workers.")
    enabled: bool = False


def _fake_entry_point(name, obj, dist_name=None):
    """Build a stand-in importlib.metadata EntryPoint."""
    dist = SimpleNamespace(name=dist_name) if dist_name else None
    return SimpleNamespace(name=name, load=lambda: obj, dist=dist)


@pytest.fixture
def register_plugins(monkeypatch):
    """Register fake config plugins for CLI helper tests."""

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


class TestBuildNestedConfig:
    """_build_nested_config nests plugin env vars correctly."""

    def test_plugin_env_var_nests(self, register_plugins):
        """Verify a plugin env var is nested under plugins.<pkg>.<field>."""
        register_plugins(
            _fake_entry_point(
                "sample", ConfigPlugin(name="sample", settings_model=SampleSettings)
            )
        )
        nested = cli._build_nested_config({"GEOIPS_PLUGIN_SAMPLE_MAX_WORKERS": "8"})
        assert nested == {"plugins": {"sample": {"max_workers": "8"}}}


class TestRenderConfig:
    """_render_config emits annotated plugin blocks."""

    def test_render_includes_header_and_comments(self, register_plugins):
        """Verify plugin block has a header comment and per-field defaults."""
        plugin = ConfigPlugin(name="sample", settings_model=SampleSettings)
        register_plugins(_fake_entry_point("sample", plugin, dist_name="sample-dist"))
        plugins = plugins_mod.discover_config_plugins()
        plugin_values = {"sample": {"max_workers": 4, "enabled": False}}

        content = cli._render_config({"outdirs": "/data"}, plugin_values, plugins)

        assert "# Plugin: sample (sample-dist)" in content
        assert "# Max parallel workers. (default: 4)" in content
        # The rendered document round-trips and the plugin model validates.
        loaded = yaml.safe_load(content)
        assert loaded["geoips"]["outdirs"] == "/data"
        SampleSettings.model_validate(loaded["geoips"]["plugins"]["sample"])

    def test_core_render_comments_and_valid_roundtrip(self, register_plugins):
        """Verify a resolved core dump renders comments and reloads validly."""
        from geoips.config.config import GeoIPSConfig
        from geoips.config.schema import GeoSettings

        register_plugins()
        resolved = GeoIPSConfig().model_dump()
        content = cli._render_config(resolved, {}, {})

        # Comments are present on core fields.
        assert "# Base directory for all GeoIPS output." in content
        # No breaking nulls: the resolved dump reloads without error, and
        # cache_dir stays populated (the bug wrote null and broke reloading).
        loaded = yaml.safe_load(content)
        GeoSettings.model_validate(loaded["geoips"])
        assert loaded["geoips"]["cache"]["cache_dir"] is not None


class TestValidatePluginsSection:
    """_validate_config_file validates plugin sections and warns on unknowns."""

    def _write(self, tmp_path, data):
        path = tmp_path / ".geoips.yaml"
        path.write_text(yaml.safe_dump(data))
        return path

    def test_unknown_key_warns(self, tmp_path, register_plugins):
        """Verify unknown top-level and plugin keys produce warnings, not errors."""
        register_plugins()
        path = self._write(
            tmp_path,
            {"geoips": {"outdirs": "/x", "bogus": 1, "plugins": {"nope": {"a": 1}}}},
        )
        errors, warnings = cli._validate_config_file(path)
        assert errors == []
        assert any("bogus" in w for w in warnings)
        assert any("nope" in w for w in warnings)

    def test_bad_plugin_value_errors(self, tmp_path, register_plugins):
        """Verify an invalid plugin field value is reported as an error."""
        register_plugins(
            _fake_entry_point(
                "sample", ConfigPlugin(name="sample", settings_model=SampleSettings)
            )
        )
        path = self._write(
            tmp_path,
            {
                "geoips": {
                    "outdirs": "/x",
                    "plugins": {"sample": {"max_workers": "abc"}},
                }
            },
        )
        errors, _ = cli._validate_config_file(path)
        assert any("geoips.plugins.sample.max_workers" in e for e in errors)

    def test_valid_plugin_section(self, tmp_path, register_plugins):
        """Verify a valid plugin section produces no errors."""
        register_plugins(
            _fake_entry_point(
                "sample", ConfigPlugin(name="sample", settings_model=SampleSettings)
            )
        )
        path = self._write(
            tmp_path,
            {"geoips": {"outdirs": "/x", "plugins": {"sample": {"max_workers": 8}}}},
        )
        errors, warnings = cli._validate_config_file(path)
        assert errors == []
        assert warnings == []
