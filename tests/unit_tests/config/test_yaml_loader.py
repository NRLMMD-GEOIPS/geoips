# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Tests for geoips.config.yaml_loader."""

import os
import tempfile
from pathlib import Path

import pytest

from geoips.config.yaml_loader import find_project_config, load_project_config


class TestFindProjectConfig:
    """Tests for find_project_config."""

    def test_no_file_returns_none(self, monkeypatch, tmp_path):
        monkeypatch.delenv("GEOIPS_RCFILE", raising=False)
        monkeypatch.chdir(tmp_path)
        result = find_project_config()
        assert result is None

    def test_finds_file_via_rcfile_env(self, monkeypatch, tmp_path):
        config_file = tmp_path / "my_custom_config.yaml"
        config_file.write_text("geoips:\n  version: test-version\n")
        monkeypatch.setenv("GEOIPS_RCFILE", str(config_file))

        result = find_project_config()
        assert result == str(config_file)

    def test_finds_file_in_cwd(self, monkeypatch, tmp_path):
        monkeypatch.delenv("GEOIPS_RCFILE", raising=False)
        config_file = tmp_path / ".geoips.yaml"
        config_file.write_text("geoips:\n  version: test-version\n")
        monkeypatch.chdir(tmp_path)

        result = find_project_config()
        assert result == str(config_file)

    def test_rcfile_takes_priority(self, monkeypatch, tmp_path):
        rcfile = tmp_path / "rc_config.yaml"
        rcfile.write_text("geoips:\n  version: from-rc\n")
        monkeypatch.setenv("GEOIPS_RCFILE", str(rcfile))

        cwd_file = tmp_path / ".geoips.yaml"
        cwd_file.write_text("geoips:\n  version: from-cwd\n")
        monkeypatch.chdir(tmp_path)

        result = find_project_config()
        assert result == str(rcfile)


class TestLoadProjectConfig:
    """Tests for load_project_config."""

    def test_loads_valid_yaml(self, monkeypatch, tmp_path):
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text("geoips:\n  version: loaded-version\n  features:\n    no_color: true\n")
        monkeypatch.setenv("GEOIPS_RCFILE", str(config_file))

        result = load_project_config()
        assert result is not None
        assert result["geoips"]["version"] == "loaded-version"
        assert result["geoips"]["features"]["no_color"] is True

    def test_returns_none_for_invalid_yaml(self, monkeypatch, tmp_path):
        config_file = tmp_path / "bad_config.yaml"
        config_file.write_text("- this is a list not a mapping\n- not valid config\n")
        monkeypatch.setenv("GEOIPS_RCFILE", str(config_file))

        result = load_project_config()
        assert result is None

    def test_returns_none_when_not_found(self, monkeypatch, tmp_path):
        monkeypatch.delenv("GEOIPS_RCFILE", raising=False)
        monkeypatch.chdir(tmp_path)
        result = load_project_config()
        assert result is None
