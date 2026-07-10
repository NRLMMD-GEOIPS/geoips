# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Unit tests for geoips.utils.yaml_utils."""

import os
import pytest
import geoips.utils.yaml_utils as yaml
from geoips.errors import DuplicateKeyError, MissingEnvironmentVariableError

FLAT_UNIQUE = "key1: 1\nkey2: 2"

NESTED_UNIQUE = (
    "key1:\n"
    "  subkey1: 1\n"
    "  subkey2: 2\n"
    "key2:\n"
    "  subkey1: 1\n"
    "  subkey2: 2\n"
)

FLAT_DUPLICATE = "key1: 1\nkey1: 2"

NESTED_DUPLICATE = "key1:\n  subkey1: 1\n  subkey1: 2"

# Single !ENV string, no default.
# For tests where the env var IS set.
SINGLE_ENV = "geoips_var: !ENV ${TEST_VAR_ABC}"

# Single !ENV string with a default.
# For tests where the env var is UNSET
SINGLE_ENV_DEFAULT = "geoips_var: !ENV ${TEST_VAR_ABC:primrose}"

# Two env vars in one string
MULTI_ENV = "geoips_multi: !ENV '${TEST_VAR_ABC}:${TEST_VAR_XYZ}'"

# Two env vars in one string, both with defaults
MULTI_ENV_DEFAULTS = "geoips_multi: !ENV '${TEST_VAR_ABC:seed}<${TEST_VAR_XYZ:flax}>'"

# Mix of !ENV and plain strings
MIXED_ENV = "key1: quintuple\n" "key2: !ENV ${TEST_VAR_ABC}\n" "key3: hedgehog\n"

# Duplicate !ENV keys
ENV_DUPLICATE = "key1: !ENV ${TEST_VAR_ABC}\n" "key1: !ENV ${TEST_VAR_XYZ}\n"

# Single !ENV with no default, var unset
SINGLE_ENV_MISSING = "geoips_var: !ENV ${TEST_VAR_NEVER_SET}"


# ------------------
# Testing safe_load
# ------------------


def test_safe_load_flat_unique_keys():
    """safe_load succeeds on flat YAML with no duplicate keys."""
    assert yaml.safe_load(FLAT_UNIQUE) == {"key1": 1, "key2": 2}


def test_safe_load_nested_unique_keys():
    """safe_load succeeds when same subkey names appear under different parent keys."""
    result = yaml.safe_load(NESTED_UNIQUE)
    assert result == {
        "key1": {"subkey1": 1, "subkey2": 2},
        "key2": {"subkey1": 1, "subkey2": 2},
    }


def test_safe_load_flat_duplicate_key_raises():
    """safe_load raises DuplicateKeyError on a top-level duplicate key."""
    with pytest.raises(DuplicateKeyError):
        yaml.safe_load(FLAT_DUPLICATE)


def test_safe_load_nested_duplicate_key_raises():
    """safe_load raises DuplicateKeyError on a duplicate key within a nested mapping."""
    with pytest.raises(DuplicateKeyError):
        yaml.safe_load(NESTED_DUPLICATE)


# --------------------------------------
# Testing EnvVarLoader -- Parameterized
# --------------------------------------


@pytest.mark.parametrize(
    "env_set, env_unset, yaml_input, expected",
    [
        # === geoips-authored baseline cases ===
        pytest.param(
            {"TEST_VAR_ABC": "abc_sentinel"},
            [],
            SINGLE_ENV,
            {"geoips_var": "abc_sentinel"},
            id="single_var_set",
        ),
        pytest.param(
            {},
            ["TEST_VAR_ABC"],
            SINGLE_ENV_DEFAULT,
            {"geoips_var": "primrose"},
            id="default_fires_when_var_unset",
        ),
        pytest.param(
            {"TEST_VAR_ABC": "host", "TEST_VAR_XYZ": "5432"},
            [],
            MULTI_ENV,
            {"geoips_multi": "host:5432"},
            id="multi_var_both_set",
        ),
        pytest.param(
            {},
            ["TEST_VAR_ABC", "TEST_VAR_XYZ"],
            MULTI_ENV_DEFAULTS,
            {"geoips_multi": "seed<flax>"},
            id="multi_var_defaults_both_fire",
        ),
        pytest.param(
            {"TEST_VAR_ABC": "moustache"},
            [],
            MIXED_ENV,
            {"key1": "quintuple", "key2": "moustache", "key3": "hedgehog"},
            id="mixed_plain_and_env_scalars",
        ),
        # === adapted pyaml-env cases ===
        # All adapted to our fail-fast behavior: bare ${VAR} references that
        # pyaml-env relied on falling back to 'N/A' are given explicit defaults.
        pytest.param(
            {},
            ["TEST_VAR_ABC", "TEST_VAR_XYZ"],
            (
                "test1:\n"
                "    data0: !ENV ${TEST_VAR_ABC:default1}"
                "/somethingelse/${TEST_VAR_XYZ:default2}\n"
                "    data1: !ENV ${TEST_VAR_XYZ:default3}\n"
            ),
            {
                "test1": {
                    "data0": "default1/somethingelse/default2",
                    "data1": "default3",
                }
            },
            id="two_defaults_in_one_scalar",
        ),
        pytest.param(
            {},
            ["TEST_VAR_ABC", "TEST_VAR_XYZ"],
            (
                "test1:\n"
                "    data0: !ENV ${TEST_VAR_ABC:defaul^{t1}"
                "/somethingelse/${TEST_VAR_XYZ:default2}\n"
                "    data1: !ENV ${TEST_VAR_XYZ:default3}\n"
            ),
            {
                "test1": {
                    "data0": "defaul^{t1/somethingelse/default2",
                    "data1": "default3",
                }
            },
            id="defaults_with_extra_surrounding_chars",
        ),
        pytest.param(
            {},
            ["TEST_VAR_ABC", "TEST_VAR_XYZ"],
            (
                "test1:\n"
                "    data0: !ENV ${TEST_VAR_ABC:defaul^{}t1}"
                "/somethingelse/${TEST_VAR_XYZ:default2}\n"
                "    data1: !ENV ${TEST_VAR_XYZ:default3}\n"
            ),
            {
                "test1": {
                    "data0": "defaul^{t1}/somethingelse/default2",
                    "data1": "default3",
                }
            },
            id="default_value_contains_braces",
        ),
        pytest.param(
            {},
            ["TEST_VAR_ABC", "TEST_VAR_XYZ"],
            (
                "test1:\n"
                "    data0: !ENV ${TEST_VAR_ABC:strong_pwd_default}"
                "/somethingelse/${TEST_VAR_XYZ:tail_default}\n"
                "    data1: !ENV ${TEST_VAR_XYZ:0.0.0.0}\n"
            ),
            {
                "test1": {
                    "data0": "strong_pwd_default/somethingelse/tail_default",
                    "data1": "0.0.0.0",
                }
            },
            id="default_alphanumeric_value",
        ),
        pytest.param(
            {},
            ["TEST_VAR_ABC", "TEST_VAR_XYZ"],
            (
                "test1:\n"
                "    data0: !ENV ${TEST_VAR_ABC:35xV*+/\\gPEFGxrg}"
                "/somethingelse/${TEST_VAR_XYZ:tail_default}\n"
                "    data1: !ENV ${TEST_VAR_XYZ:0.0.0.0}\n"
            ),
            {
                "test1": {
                    "data0": "35xV*+/\\gPEFGxrg/somethingelse/tail_default",
                    "data1": "0.0.0.0",
                }
            },
            id="default_contains_backslash",
        ),
        pytest.param(
            {"TEST_VAR_ABC": "test"},
            ["TEST_VAR_XYZ"],
            (
                "test1:\n"
                "    data0: !ENV ${TEST_VAR_ABC:35xV*+/\\gPEFGxrg}"
                "/somethingelse/${TEST_VAR_XYZ:tail_default}\n"
                "    data1: !ENV ${TEST_VAR_XYZ:0.0.0.0}\n"
            ),
            {"test1": {"data0": "test/somethingelse/tail_default", "data1": "0.0.0.0"}},
            id="env_var_overrides_default",
        ),
        pytest.param(
            {"TEST_VAR_ABC": "myWeakPassword"},
            ["TEST_VAR_XYZ"],
            (
                "test1:\n"
                "    data0: !ENV ${TEST_VAR_ABC:strong_pwd_default}"
                "/somethingelse/${TEST_VAR_XYZ:tail_default}\n"
                "    data1: !ENV ${TEST_VAR_XYZ:0.0.0.0}\n"
            ),
            {
                "test1": {
                    "data0": "myWeakPassword/somethingelse/tail_default",
                    "data1": "0.0.0.0",
                }
            },
            id="env_var_overrides_alphanumeric_default",
        ),
        pytest.param(
            {"TEST_VAR_ABC": "1value", "TEST_VAR_XYZ": "2values"},
            [],
            (
                "test1:\n"
                "    data0: !ENV ${TEST_VAR_ABC:strong_pwd_default}"
                "/somethingelse/${TEST_VAR_XYZ}\n"
                "    data1: !ENV ${TEST_VAR_XYZ:0.0.0.0}\n"
            ),
            {"test1": {"data0": "1value/somethingelse/2values", "data1": "2values"}},
            id="two_vars_both_set",
        ),
    ],
)
def test_envvarloader_resolves(monkeypatch, env_set, env_unset, yaml_input, expected):
    """Verify EnvVarLoader resolves !ENV tags across the documented matrix of forms."""
    for name, value in env_set.items():
        monkeypatch.setenv(name, value)
    for name in env_unset:
        monkeypatch.delenv(name, raising=False)
    result = yaml.load(yaml_input, Loader=yaml.EnvVarLoader)
    assert result == expected


# ----------------------------------------------
# Testing EnvVarLoader -- edge / negative cases
# ----------------------------------------------


def test_envvarloader_missing_var_raises_no_default(monkeypatch):
    """Verify EnvVarLoader raises when a ${VAR} is unset and has no default."""
    monkeypatch.delenv("TEST_VAR_NEVER_SET", raising=False)
    with pytest.raises(MissingEnvironmentVariableError):
        yaml.load(SINGLE_ENV_MISSING, Loader=yaml.EnvVarLoader)


def test_envvarloader_does_not_detect_duplicates(monkeypatch):
    """Verify EnvVarLoader silently lets a duplicate key overwrite (2nd value wins)."""
    monkeypatch.setenv("TEST_VAR_ABC", "yogurt")
    monkeypatch.setenv("TEST_VAR_XYZ", "rasp")
    result = yaml.load(ENV_DUPLICATE, Loader=yaml.EnvVarLoader)
    assert result == {"key1": "rasp"}  # second mapping silently wins


def test_envvarloader_resolves_special_chars_in_var_name(monkeypatch):
    """Verify EnvVarLoader handles env var names containing chars outside POSIX names.

    Uses monkeypatch.setattr(os, "environ", ...) rather than monkeypatch.setenv
    because Windows env var APIs do not reliably accept names with metacharacters.
    """
    fake_env = {
        "ENV*)__TAG101sfdarg": "2values",
        "TEST_VAR_XYZ": "1value",
    }
    monkeypatch.setattr(os, "environ", fake_env)
    yaml_input = (
        "test1:\n"
        "    data0: !ENV ${ENV*)__TAG101sfdarg:NoHtnnmEuluGp2boPvGQkGrXqTAtBvIVz"
        ".,hujn+000-!!#9VRmV65}/somethingelse/${TEST_VAR_XYZ}\n"
        "    data1: !ENV ${TEST_VAR_XYZ:0.0.0.0}\n"
    )
    result = yaml.load(yaml_input, Loader=yaml.EnvVarLoader)
    assert result == {
        "test1": {
            "data0": "2values/somethingelse/1value",
            "data1": "1value",
        },
    }


# ---------------------------------
# Testing EnvVarLoaderNoDuplicates
# ---------------------------------


def test_envvarnodup_loader_raises_on_duplicate(monkeypatch):
    """Verify EnvVarLoaderNoDuplicates raises DuplicateKeyError on duplicate keys.

    This occurs even with !ENV resolution available.
    """
    monkeypatch.setenv("TEST_VAR_ABC", "foo")
    monkeypatch.setenv("TEST_VAR_XYZ", "bar")
    with pytest.raises(DuplicateKeyError):
        yaml.load(ENV_DUPLICATE, Loader=yaml.EnvVarLoaderNoDuplicates)


def test_envvarnodup_loader_resolves_env_vars_when_no_duplicates(monkeypatch):
    """Verify EnvVarLoaderNoDuplicates resolves !ENV tags w/o duplicates present."""
    monkeypatch.setenv("TEST_VAR_ABC", "gamma")
    result = yaml.load(SINGLE_ENV, Loader=yaml.EnvVarLoaderNoDuplicates)
    assert result == {"geoips_var": "gamma"}


# ---------------------
# Testing parse_config
# ---------------------


def test_parse_config_resolves_env_var_from_file(tmp_path, monkeypatch):
    """Verify parse_config reads a YAML file from disk and resolves !ENV tags."""
    monkeypatch.setenv("TEST_VAR_ABC", "harpsicord")
    path = tmp_path / "config.yaml"
    path.write_text(SINGLE_ENV)
    result = yaml.parse_config(str(path))
    assert result == {"geoips_var": "harpsicord"}


def test_parse_config_detect_duplicates_default_raises(tmp_path, monkeypatch):
    """Verify parse_config defaults to raising DuplicateKeyError on duplicate keys."""
    monkeypatch.setenv("TEST_VAR_ABC", "foo")
    monkeypatch.setenv("TEST_VAR_XYZ", "bar")
    path = tmp_path / "config.yaml"
    path.write_text(ENV_DUPLICATE)
    with pytest.raises(DuplicateKeyError):
        yaml.parse_config(str(path))


def test_parse_config_detect_duplicates_false_silent(tmp_path, monkeypatch):
    """Verify parse_config(..., detect_duplicates=False) accepts duplicate keys.

    The second value silently wins.
    """
    monkeypatch.setenv("TEST_VAR_ABC", "rhetoric")
    monkeypatch.setenv("TEST_VAR_XYZ", "prose")
    path = tmp_path / "config.yaml"
    path.write_text(ENV_DUPLICATE)
    result = yaml.parse_config(str(path), detect_duplicates=False)
    assert result == {"key1": "prose"}
