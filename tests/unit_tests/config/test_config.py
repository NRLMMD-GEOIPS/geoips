# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Tests for geoips.config.config — GeoIPSConfig loading and overrides."""

import os
from unittest import mock

import pytest

from geoips.config.config import GeoIPSConfig, _cast_env_value, get_config
from geoips.config.schema import GeoSettings


class TestCastEnvValue:
    """Tests for _cast_env_value string-to-type casting."""

    def test_true(self):
        assert _cast_env_value("true", "features.no_color") is True
        assert _cast_env_value("True", "features.no_color") is True
        assert _cast_env_value("TRUE", "features.no_color") is True

    def test_false(self):
        assert _cast_env_value("false", "features.no_color") is False
        assert _cast_env_value("False", "features.no_color") is False

    def test_none(self):
        assert _cast_env_value("none", "default_queue") is None
        assert _cast_env_value("null", "default_queue") is None

    def test_list_split(self):
        result = _cast_env_value("A B C", "replace_output_paths")
        assert result == ["A", "B", "C"]

    def test_float_threshold(self):
        result = _cast_env_value("0.03", "test.output_checker_threshold_image")
        assert result == 0.03
        assert isinstance(result, float)

    def test_plain_string(self):
        assert _cast_env_value("info", "logging.level") == "info"


class TestGeoIPSConfig:
    """Tests for GeoIPSConfig class."""

    def test_creates_with_env_outdirs(self, monkeypatch):
        monkeypatch.setenv("GEOIPS_OUTDIRS", "/test/outdirs")
        cfg = GeoIPSConfig()
        assert cfg.outdirs == "/test/outdirs"

    def test_falls_back_to_home(self, monkeypatch):
        for var in ("GEOIPS_OUTDIRS", "GEOIPS_LOGGING_LEVEL"):
            monkeypatch.delenv(var, raising=False)
        monkeypatch.setenv("HOME", "/home/testuser")
        cfg = GeoIPSConfig()
        assert cfg.outdirs == "/home/testuser/geoips_outdirs"

    def test_auto_resolves_base_path(self, monkeypatch):
        monkeypatch.setenv("GEOIPS_OUTDIRS", "/test/out")
        cfg = GeoIPSConfig()
        assert cfg.base_path is not None
        assert os.path.isabs(cfg.base_path)
        assert os.path.isdir(cfg.base_path)

    def test_auto_resolves_packages_dir(self, monkeypatch):
        monkeypatch.setenv("GEOIPS_OUTDIRS", "/test/out")
        cfg = GeoIPSConfig()
        assert cfg.packages_dir is not None
        assert os.path.isabs(cfg.packages_dir)

    def test_auto_resolves_basedir(self, monkeypatch):
        monkeypatch.setenv("GEOIPS_OUTDIRS", "/test/out")
        cfg = GeoIPSConfig()
        assert cfg.basedir is not None
        assert os.path.isabs(cfg.basedir)

    def test_boxname(self, monkeypatch):
        monkeypatch.setenv("GEOIPS_OUTDIRS", "/test/out")
        cfg = GeoIPSConfig()
        assert cfg.boxname is not None
        assert isinstance(cfg.boxname, str)
        assert len(cfg.boxname) > 0

    def test_dot_attr_access(self, monkeypatch):
        monkeypatch.setenv("GEOIPS_OUTDIRS", "/test/out")
        cfg = GeoIPSConfig()
        assert cfg.features.no_color is False
        assert cfg.features.rebuild_registries is True
        assert cfg.logging.level == "interactive"
        assert cfg.test.output_checker_threshold_image == 0.05
        assert cfg.version == "0.0.0"

    def test_dot_attr_missing_raises(self, monkeypatch):
        monkeypatch.setenv("GEOIPS_OUTDIRS", "/test/out")
        cfg = GeoIPSConfig()
        with pytest.raises(AttributeError):
            cfg.nonexistent_field


class TestLegacyDict:
    """Tests for the backward-compatible legacy dict interface."""

    def test_to_legacy_dict_has_required_keys(self, monkeypatch):
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
        monkeypatch.setenv("GEOIPS_OUTDIRS", "/test/out")
        cfg = GeoIPSConfig()
        d = cfg.to_legacy_dict()

        assert "GEOIPS_DATA_CACHE_DIR" in d
        assert "SATPY_DATA_CACHE_DIR" in d
        assert "GEOIPS_GEOLOCATION_CACHE_BACKEND" in d

    def test_dict_access_via_getitem(self, monkeypatch):
        monkeypatch.setenv("GEOIPS_OUTDIRS", "/test/out")
        cfg = GeoIPSConfig()
        assert cfg["GEOIPS_OUTDIRS"] == "/test/out"
        assert cfg["NO_COLOR"] is False

    def test_get_method(self, monkeypatch):
        monkeypatch.setenv("GEOIPS_OUTDIRS", "/test/out")
        cfg = GeoIPSConfig()
        assert cfg.get("GEOIPS_OUTDIRS") == "/test/out"
        assert cfg.get("NONEXISTENT_KEY") is None
        assert cfg.get("NONEXISTENT_KEY", "fallback") == "fallback"


class TestEnvOverrides:
    """Tests for environment variable override priority."""

    def test_env_overrides_feature_toggle(self, monkeypatch):
        monkeypatch.setenv("GEOIPS_OUTDIRS", "/test/out")
        monkeypatch.setenv("GEOIPS_USE_PYDANTIC", "true")
        cfg = GeoIPSConfig()
        assert cfg.features.use_pydantic is True

    def test_env_overrides_logging_level(self, monkeypatch):
        monkeypatch.setenv("GEOIPS_OUTDIRS", "/test/out")
        monkeypatch.setenv("GEOIPS_LOGGING_LEVEL", "debug")
        cfg = GeoIPSConfig()
        assert cfg.logging.level == "debug"

    def test_env_overrides_no_color_unprefixed(self, monkeypatch):
        monkeypatch.setenv("GEOIPS_OUTDIRS", "/test/out")
        monkeypatch.setenv("NO_COLOR", "true")
        cfg = GeoIPSConfig()
        assert cfg.features.no_color is True

    def test_env_overrides_cache_setting(self, monkeypatch):
        monkeypatch.setenv("GEOIPS_OUTDIRS", "/test/out")
        monkeypatch.setenv("GEOIPS_GEOLOCATION_CACHE_BACKEND", "zarr")
        cfg = GeoIPSConfig()
        assert cfg.cache.geolocation_cache_backend == "zarr"

    def test_env_overrides_output_path(self, monkeypatch):
        monkeypatch.setenv("GEOIPS_OUTDIRS", "/test/out")
        monkeypatch.setenv("ANNOTATED_IMAGERY_PATH", "/custom/annotated")
        cfg = GeoIPSConfig()
        assert cfg.output_paths.annotated_imagery == "/custom/annotated"
