# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Tests for ``geoips.config.config`` — GeoIPSConfig loading and overrides."""

import os

import pytest

from geoips.config.config import GeoIPSConfig, _cast_env_value


class TestCastEnvValue:
    """Tests for _cast_env_value string-to-type casting."""

    def test_true(self):
        """Verify "true"/"True"/"TRUE" all cast to True."""
        assert _cast_env_value("true", "features.no_color") is True
        assert _cast_env_value("True", "features.no_color") is True
        assert _cast_env_value("TRUE", "features.no_color") is True

    def test_false(self):
        """Verify "false" and "False" cast to False."""
        assert _cast_env_value("false", "features.no_color") is False
        assert _cast_env_value("False", "features.no_color") is False

    def test_none(self):
        """Verify "none" and "null" cast to None."""
        assert _cast_env_value("none", "default_queue") is None
        assert _cast_env_value("null", "default_queue") is None

    def test_list_split(self):
        """Verify space-separated string is split into a list."""
        result = _cast_env_value("A B C", "replace_output_paths")
        assert result == ["A", "B", "C"]

    def test_float_threshold(self):
        """Verify numeric string is cast to float for threshold field."""
        result = _cast_env_value("0.03", "test.output_checker_threshold_image")
        assert result == 0.03
        assert isinstance(result, float)

    def test_plain_string(self):
        """Verify non-special strings are returned as-is."""
        assert _cast_env_value("info", "logging.level") == "info"


class TestGeoIPSConfig:
    """Tests for GeoIPSConfig class."""

    def test_creates_with_env_outdirs(self, monkeypatch):
        """Verify outdirs is read from GEOIPS_OUTDIRS env var."""
        monkeypatch.setenv("GEOIPS_OUTDIRS", "/test/outdirs")
        cfg = GeoIPSConfig()
        assert cfg.outdirs == "/test/outdirs"

    def test_falls_back_to_home(self, monkeypatch, tmp_path):
        """Verify outdirs falls back to $HOME/geoips_outdirs when unset."""
        home = tmp_path / "home"
        home.mkdir()

        monkeypatch.chdir(tmp_path)
        for var in ("GEOIPS_OUTDIRS", "GEOIPS_LOGGING_LEVEL", "GEOIPS_RCFILE"):
            monkeypatch.delenv(var, raising=False)
        monkeypatch.setenv("HOME", str(home))

        cfg = GeoIPSConfig()

        assert cfg.outdirs == str(home / "geoips_outdirs")

    def test_uses_explicit_project_config_path(self, monkeypatch, tmp_path):
        """Verify GeoIPSConfig applies an explicitly supplied project config path."""
        config_file = tmp_path / "explicit.yaml"
        config_file.write_text("geoips:\n  outdirs: /explicit/outdirs\n")

        cwd_file = tmp_path / ".geoips.yaml"
        cwd_file.write_text("geoips:\n  outdirs: /cwd/outdirs\n")
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv("GEOIPS_OUTDIRS", raising=False)

        cfg = GeoIPSConfig(project_config_path=str(config_file))

        assert cfg.outdirs == "/explicit/outdirs"

    def test_missing_explicit_project_config_path_raises(self, tmp_path):
        """Verify GeoIPSConfig raises for a missing explicit project config path."""
        missing_file = tmp_path / "missing.yaml"

        with pytest.raises(FileNotFoundError):
            GeoIPSConfig(project_config_path=str(missing_file))

    def test_auto_resolves_base_path(self, monkeypatch):
        """Verify base_path is auto-resolved to the geoips package directory."""
        monkeypatch.setenv("GEOIPS_OUTDIRS", "/test/out")
        cfg = GeoIPSConfig()
        assert cfg.base_path is not None
        assert os.path.isabs(cfg.base_path)
        assert os.path.isdir(cfg.base_path)

    def test_auto_resolves_packages_dir(self, monkeypatch):
        """Verify packages_dir is auto-resolved."""
        monkeypatch.setenv("GEOIPS_OUTDIRS", "/test/out")
        cfg = GeoIPSConfig()
        assert cfg.packages_dir is not None
        assert os.path.isabs(cfg.packages_dir)

    def test_auto_resolves_basedir(self, monkeypatch):
        """Verify basedir is auto-resolved."""
        monkeypatch.setenv("GEOIPS_OUTDIRS", "/test/out")
        cfg = GeoIPSConfig()
        assert cfg.basedir is not None
        assert os.path.isabs(cfg.basedir)

    def test_boxname(self, monkeypatch):
        """Verify boxname is resolved to the hostname."""
        monkeypatch.setenv("GEOIPS_OUTDIRS", "/test/out")
        cfg = GeoIPSConfig()
        assert cfg.boxname is not None
        assert isinstance(cfg.boxname, str)
        assert len(cfg.boxname) > 0

    def test_dot_attr_access(self, monkeypatch):
        """Verify dot-attribute access works for nested settings."""
        monkeypatch.setenv("GEOIPS_OUTDIRS", "/test/out")
        cfg = GeoIPSConfig()
        assert cfg.features.no_color is False
        assert cfg.features.rebuild_registries is True
        assert cfg.logging.level == "interactive"
        assert cfg.test.output_checker_threshold_image == 0.05
        assert cfg.version == "0.0.0"

    def test_dot_attr_missing_raises(self, monkeypatch):
        """Verify accessing a nonexistent attribute raises AttributeError."""
        monkeypatch.setenv("GEOIPS_OUTDIRS", "/test/out")
        cfg = GeoIPSConfig()
        with pytest.raises(AttributeError):
            cfg.nonexistent_field


class TestLegacyDict:
    """Tests for the backward-compatible legacy dict interface."""

    def test_to_legacy_dict_has_required_keys(self, monkeypatch):
        """Verify to_legacy_dict contains all expected legacy keys."""
        monkeypatch.setenv("GEOIPS_OUTDIRS", "/test/out")
        cfg = GeoIPSConfig()
        d = cfg.to_legacy_dict()

        assert "GEOIPS_OUTDIRS" in d
        assert d["GEOIPS_OUTDIRS"] == "/test/out"
        assert "GEOIPS_PACKAGES_DIR" in d
        assert "GEOIPS_BASEDIR" in d
        assert "NO_COLOR" in d
        assert "GEOIPS_VERSION" in d
        assert "GEOIPS_COPYRIGHT" in d
        assert "BASE_PATH" in d
        assert "BOXNAME" in d
        assert "HOME" in d

    def test_to_legacy_dict_output_paths(self, monkeypatch):
        """Verify output paths in legacy dict are absolute."""
        monkeypatch.setenv("GEOIPS_OUTDIRS", "/test/out")
        cfg = GeoIPSConfig()
        d = cfg.to_legacy_dict()

        assert "PRESECTORED_DATA_PATH" in d
        assert d["PRESECTORED_DATA_PATH"].startswith("/test/out")
        assert "ANNOTATED_IMAGERY_PATH" in d
        assert "GEOTIFF_IMAGERY_PATH" in d
        assert "TCWWW" in d
        assert "TCWWW_URL" in d

    def test_to_legacy_dict_cache_paths(self, monkeypatch):
        """Verify cache paths are present in legacy dict."""
        monkeypatch.setenv("GEOIPS_OUTDIRS", "/test/out")
        cfg = GeoIPSConfig()
        d = cfg.to_legacy_dict()

        assert "GEOIPS_DATA_CACHE_DIR" in d
        assert "SATPY_DATA_CACHE_DIR" in d
        assert "GEOIPS_GEOLOCATION_CACHE_BACKEND" in d

    def test_dict_access_via_getitem(self, monkeypatch):
        """Verify backward-compatible __getitem__ access."""
        monkeypatch.setenv("GEOIPS_OUTDIRS", "/test/out")
        cfg = GeoIPSConfig()
        assert cfg["GEOIPS_OUTDIRS"] == "/test/out"
        assert cfg["NO_COLOR"] is False

    def test_get_method(self, monkeypatch):
        """Verify .get() behaves like dict.get()."""
        monkeypatch.setenv("GEOIPS_OUTDIRS", "/test/out")
        cfg = GeoIPSConfig()
        assert cfg.get("GEOIPS_OUTDIRS") == "/test/out"
        assert cfg.get("NONEXISTENT_KEY") is None
        assert cfg.get("NONEXISTENT_KEY", "fallback") == "fallback"


class TestEnvOverrides:
    """Tests for environment variable override priority."""

    def test_env_overrides_feature_toggle(self, monkeypatch):
        """Verify GEOIPS_USE_PYDANTIC env var overrides the default."""
        monkeypatch.setenv("GEOIPS_OUTDIRS", "/test/out")
        monkeypatch.setenv("GEOIPS_USE_PYDANTIC", "true")
        cfg = GeoIPSConfig()
        assert cfg.features.use_pydantic is True

    def test_env_overrides_logging_level(self, monkeypatch):
        """Verify GEOIPS_LOGGING_LEVEL env var overrides the default."""
        monkeypatch.setenv("GEOIPS_OUTDIRS", "/test/out")
        monkeypatch.setenv("GEOIPS_LOGGING_LEVEL", "debug")
        cfg = GeoIPSConfig()
        assert cfg.logging.level == "debug"

    def test_env_overrides_no_color_unprefixed(self, monkeypatch):
        """Verify unprefixed NO_COLOR env var works."""
        monkeypatch.setenv("GEOIPS_OUTDIRS", "/test/out")
        monkeypatch.setenv("NO_COLOR", "true")
        cfg = GeoIPSConfig()
        assert cfg.features.no_color is True

    def test_env_overrides_cache_setting(self, monkeypatch):
        """Verify GEOIPS_GEOLOCATION_CACHE_BACKEND overrides default."""
        monkeypatch.setenv("GEOIPS_OUTDIRS", "/test/out")
        monkeypatch.setenv("GEOIPS_GEOLOCATION_CACHE_BACKEND", "zarr")
        cfg = GeoIPSConfig()
        assert cfg.cache.geolocation_cache_backend == "zarr"

    def test_env_overrides_output_path(self, monkeypatch):
        """Verify ANNOTATED_IMAGERY_PATH env var overrides the default path."""
        monkeypatch.setenv("GEOIPS_OUTDIRS", "/test/out")
        monkeypatch.setenv("ANNOTATED_IMAGERY_PATH", "/custom/annotated")
        cfg = GeoIPSConfig()
        assert cfg.output_paths.annotated_imagery == "/custom/annotated"


class TestInvalidProjectConfig:
    """A malformed project config raises a clear ConfigError."""

    def test_invalid_config_raises(self, monkeypatch):
        """Verify invalid values raise ConfigError listing the offending fields."""
        import importlib

        from geoips.errors import ConfigError

        config_mod = importlib.import_module("geoips.config.config")

        monkeypatch.setenv("GEOIPS_OUTDIRS", "/test/out")
        monkeypatch.setattr(
            config_mod,
            "load_project_config",
            lambda project_config_path=None: {
                "geoips": {"features": {"no_color": "notabool"}}
            },
        )
        monkeypatch.setattr(
            config_mod,
            "find_project_config",
            lambda project_config_path=None: "bad/.geoips.yaml",
        )

        with pytest.raises(ConfigError) as excinfo:
            GeoIPSConfig()

        message = str(excinfo.value)
        assert "Invalid GeoIPS config file" in message
        assert "geoips.features.no_color" in message
