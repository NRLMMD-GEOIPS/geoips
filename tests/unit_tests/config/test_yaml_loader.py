# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Tests for ``geoips.config.yaml_loader``."""

import pytest

from geoips.config.yaml_loader import find_project_config, load_project_config


class TestFindProjectConfig:
    """Tests for find_project_config."""

    def test_no_file_returns_none(self, monkeypatch, tmp_path):
        """Verify None is returned when no config file exists."""
        monkeypatch.delenv("GEOIPS_RCFILE", raising=False)
        monkeypatch.chdir(tmp_path)
        result = find_project_config()
        assert result is None

    def test_finds_file_via_rcfile_env(self, monkeypatch, tmp_path):
        """Verify the file specified by GEOIPS_RCFILE is found."""
        config_file = tmp_path / "my_custom_config.yaml"
        config_file.write_text("geoips:\n  version: test-version\n")
        monkeypatch.setenv("GEOIPS_RCFILE", str(config_file))

        result = find_project_config()
        assert result == str(config_file)

    def test_finds_file_in_cwd(self, monkeypatch, tmp_path):
        """Verify .geoips.yaml in CWD is found."""
        monkeypatch.delenv("GEOIPS_RCFILE", raising=False)
        config_file = tmp_path / ".geoips.yaml"
        config_file.write_text("geoips:\n  version: test-version\n")
        monkeypatch.chdir(tmp_path)

        result = find_project_config()
        assert result == str(config_file)

    def test_rcfile_takes_priority(self, monkeypatch, tmp_path):
        """Verify GEOIPS_RCFILE takes priority over CWD .geoips.yaml."""
        rcfile = tmp_path / "rc_config.yaml"
        rcfile.write_text("geoips:\n  version: from-rc\n")
        monkeypatch.setenv("GEOIPS_RCFILE", str(rcfile))

        cwd_file = tmp_path / ".geoips.yaml"
        cwd_file.write_text("geoips:\n  version: from-cwd\n")
        monkeypatch.chdir(tmp_path)

        result = find_project_config()
        assert result == str(rcfile)

    def test_explicit_path_is_used(self, monkeypatch, tmp_path):
        """Verify an explicit config path is used instead of default search paths."""
        explicit_file = tmp_path / "explicit.yaml"
        explicit_file.write_text("geoips:\n  version: explicit-version\n")

        cwd_file = tmp_path / ".geoips.yaml"
        cwd_file.write_text("geoips:\n  version: cwd-version\n")
        monkeypatch.chdir(tmp_path)

        result = find_project_config(str(explicit_file))

        assert result == str(explicit_file)

    def test_explicit_missing_path_raises(self, tmp_path):
        """Verify an explicit config path must exist."""
        missing_file = tmp_path / "missing.yaml"

        with pytest.raises(FileNotFoundError):
            find_project_config(str(missing_file))


class TestLoadProjectConfig:
    """Tests for load_project_config."""

    def test_loads_valid_yaml(self, monkeypatch, tmp_path):
        """Verify valid YAML with nested structure is parsed correctly."""
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text(
            "geoips:\n  version: loaded-version\n  features:\n    no_color: true\n"
        )
        monkeypatch.setenv("GEOIPS_RCFILE", str(config_file))

        result = load_project_config()
        assert result is not None
        assert result["geoips"]["version"] == "loaded-version"
        assert result["geoips"]["features"]["no_color"] is True

    def test_loads_explicit_path(self, monkeypatch, tmp_path):
        """Verify an explicit config path is loaded instead of default search paths."""
        explicit_file = tmp_path / "explicit.yaml"
        explicit_file.write_text("geoips:\n  version: explicit-version\n")

        cwd_file = tmp_path / ".geoips.yaml"
        cwd_file.write_text("geoips:\n  version: cwd-version\n")
        monkeypatch.chdir(tmp_path)

        result = load_project_config(str(explicit_file))

        assert result is not None
        assert result["geoips"]["version"] == "explicit-version"

    def test_explicit_missing_path_raises(self, tmp_path):
        """Verify loading an explicit missing config path raises."""
        missing_file = tmp_path / "missing.yaml"

        with pytest.raises(FileNotFoundError):
            load_project_config(str(missing_file))

    def test_returns_none_for_invalid_yaml(self, monkeypatch, tmp_path):
        """Verify None is returned when YAML is not a mapping."""
        config_file = tmp_path / "bad_config.yaml"
        config_file.write_text("- this is a list not a mapping\n- not valid config\n")
        monkeypatch.setenv("GEOIPS_RCFILE", str(config_file))

        result = load_project_config()
        assert result is None

    def test_returns_none_when_not_found(self, monkeypatch, tmp_path):
        """Verify None is returned when no config file exists."""
        monkeypatch.delenv("GEOIPS_RCFILE", raising=False)
        monkeypatch.chdir(tmp_path)
        result = load_project_config()
        assert result is None
