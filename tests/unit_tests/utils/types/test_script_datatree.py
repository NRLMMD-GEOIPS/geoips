# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Unit tests for OBP-style script DataTree helpers."""

from datetime import datetime

import pytest
import xarray as xr

from geoips.utils.types.script_datatree import (
    RETENTION_POLICIES,
    RetentionPolicy,
    SCRIPT_EXECUTION_MODE,
    _valid_script_plugin_kinds,
    apply_script_retention,
    attach_plugin_result,
    initialize_script_tree,
    validate_retention_policy,
)


class TestInitializeScriptTree:
    """Test script DataTree initialization."""

    @pytest.mark.parametrize("retention_policy", sorted(RETENTION_POLICIES))
    def test_sets_standard_script_attrs(self, retention_policy):
        """Test initializing a script tree stamps standard metadata."""
        tree = initialize_script_tree("test_script", retention_policy)

        assert isinstance(tree, xr.DataTree)
        assert tree.name == "test_script"
        assert tree.attrs["execution_mode"] == SCRIPT_EXECUTION_MODE
        assert tree.attrs["retention_policy"] == retention_policy.value
        assert "start_time" in tree.attrs
        datetime.fromisoformat(tree.attrs["start_time"])

    def test_accepts_string_retention_policy(self):
        """Test initializing a script tree accepts retention policy strings."""
        tree = initialize_script_tree("test_script", "metadata_only")

        assert tree.attrs["retention_policy"] == "metadata_only"

    def test_preserves_additional_attrs(self):
        """Test initializing a script tree preserves extra root metadata."""
        tree = initialize_script_tree(
            "test_script",
            "keep_all",
            source_name="abi",
            platform_name="goes-16",
        )

        assert tree.attrs["source_name"] == "abi"
        assert tree.attrs["platform_name"] == "goes-16"

    def test_rejects_invalid_retention_policy(self):
        """Test initializing a script tree rejects unknown retention policies."""
        with pytest.raises(ValueError, match="Invalid retention policy"):
            initialize_script_tree("test_script", "keep_some")

    @pytest.mark.parametrize(
        "reserved_attr", ["execution_mode", "start_time", "end_time"]
    )
    def test_rejects_reserved_attrs(self, reserved_attr):
        """Test initializing a script tree rejects reserved attrs."""
        with pytest.raises(ValueError, match="reserved"):
            initialize_script_tree("test_script", "keep_all", **{reserved_attr: "bad"})


class TestRetentionPolicy:
    """Test retention policy enum values."""

    def test_retention_policies_contains_policy_members(self):
        """Test public retention policies are enum values, not raw strings."""
        assert all(isinstance(policy, RetentionPolicy) for policy in RETENTION_POLICIES)

    def test_policy_values_are_string_like(self):
        """Test retention policy enum values behave like strings."""
        assert RetentionPolicy.metadata_only == "metadata_only"
        assert str(RetentionPolicy.metadata_only) == "metadata_only"

    @pytest.mark.parametrize("retention_policy", RETENTION_POLICIES)
    def test_policy_values_have_descriptions(self, retention_policy):
        """Test retention policy values include interactive descriptions."""
        assert retention_policy.description
        assert retention_policy.__doc__ == retention_policy.description


class TestValidateRetentionPolicy:
    """Test retention policy validation."""

    @pytest.mark.parametrize("retention_policy", sorted(RETENTION_POLICIES))
    def test_accepts_valid_policies(self, retention_policy):
        """Test retention policy validation accepts supported policies."""
        validate_retention_policy(retention_policy)

    @pytest.mark.parametrize(
        "retention_policy", [policy.value for policy in RetentionPolicy]
    )
    def test_accepts_valid_policy_strings(self, retention_policy):
        """Test retention policy validation accepts supported policy strings."""
        validate_retention_policy(retention_policy)

    def test_rejects_invalid_policy(self):
        """Test retention policy validation rejects unsupported policies."""
        with pytest.raises(ValueError, match="Expected one of"):
            validate_retention_policy("keep_recent")


class TestAttachPluginResult:
    """Test attaching plugin results to script DataTrees."""

    def test_attaches_result_under_step_id(self):
        """Test attaching a plugin result under an explicit step id."""
        tree = initialize_script_tree("test_script", RetentionPolicy.keep_all)
        result = xr.Dataset({"data": ("x", [1, 2, 3])})

        updated = attach_plugin_result(
            tree,
            result,
            step_id="read_data",
            plugin_kind="reader",
            plugin_name="abi_netcdf",
        )

        assert updated is tree
        assert "read_data" in tree.children
        assert "data" in tree["read_data"].ds.data_vars

    def test_uses_plugin_name_when_step_id_missing(self):
        """Test attaching a plugin result falls back to plugin name."""
        tree = initialize_script_tree("test_script", RetentionPolicy.keep_all)
        result = xr.Dataset({"data": ("x", [1, 2, 3])})

        attach_plugin_result(
            tree,
            result,
            plugin_kind="algorithm",
            plugin_name="single_channel",
        )

        assert "single_channel" in tree.children

    def test_allows_manual_plugin_kind(self):
        """Test attaching manually created data can use manual plugin kind."""
        tree = initialize_script_tree("test_script", RetentionPolicy.keep_all)
        result = xr.Dataset({"data": ("x", [1, 2, 3])})

        attach_plugin_result(
            tree,
            result,
            step_id="custom_step",
            plugin_kind="manual",
            plugin_name="user_script",
        )

        assert tree["custom_step"].attrs["plugin_kind"] == "manual"

    def test_manual_plugin_kind_does_not_require_plugin_name(self):
        """Test manually created data does not require plugin name."""
        tree = initialize_script_tree("test_script", RetentionPolicy.keep_all)
        result = xr.Dataset({"data": ("x", [1, 2, 3])})

        attach_plugin_result(
            tree,
            result,
            step_id="custom_step",
            plugin_kind="manual",
            plugin_name=None,
        )

        assert tree["custom_step"].attrs["plugin_kind"] == "manual"
        assert tree["custom_step"].attrs["plugin_name"] == "manual"

    def test_manual_plugin_kind_allows_omitting_plugin_name(self):
        """Test manually created data can omit plugin_name entirely."""
        tree = initialize_script_tree("test_script", RetentionPolicy.keep_all)
        result = xr.Dataset({"data": ("x", [1, 2, 3])})

        attach_plugin_result(
            tree,
            result,
            step_id="custom_step",
            plugin_kind="manual",
        )

        assert tree["custom_step"].attrs["plugin_kind"] == "manual"
        assert tree["custom_step"].attrs["plugin_name"] == "manual"

    def test_manual_plugin_kind_defaults_times_to_none(self):
        """Test manually created data does not receive automatic timestamps."""
        tree = initialize_script_tree("test_script", RetentionPolicy.keep_all)
        result = xr.Dataset({"data": ("x", [1, 2, 3])})

        attach_plugin_result(
            tree,
            result,
            step_id="custom_step",
            plugin_kind="manual",
        )

        assert tree["custom_step"].attrs["start_time"] is None
        assert tree["custom_step"].attrs["end_time"] is None

    def test_manual_plugin_kind_preserves_explicit_times(self):
        """Test manually created data preserves explicitly supplied timestamps."""
        tree = initialize_script_tree("test_script", RetentionPolicy.keep_all)
        result = xr.Dataset({"data": ("x", [1, 2, 3])})

        attach_plugin_result(
            tree,
            result,
            step_id="custom_step",
            plugin_kind="manual",
            start_time="2026-07-15T00:00:00+00:00",
            end_time="2026-07-15T00:00:01+00:00",
        )

        assert tree["custom_step"].attrs["start_time"] == "2026-07-15T00:00:00+00:00"
        assert tree["custom_step"].attrs["end_time"] == "2026-07-15T00:00:01+00:00"

    def test_valid_plugin_kinds_are_cached(self):
        """Test valid script plugin kind discovery is cached."""
        _valid_script_plugin_kinds.cache_clear()
        valid_kinds = _valid_script_plugin_kinds()
        cache_info = _valid_script_plugin_kinds.cache_info()

        assert "reader" in valid_kinds
        assert "manual" in valid_kinds
        assert "product" not in valid_kinds
        assert "workflow" not in valid_kinds
        assert cache_info.misses == 1

        assert _valid_script_plugin_kinds() is valid_kinds
        assert _valid_script_plugin_kinds.cache_info().hits == 1

    def test_rejects_duplicate_step_name(self):
        """Test attaching a plugin result rejects duplicate step names."""
        tree = initialize_script_tree("test_script", RetentionPolicy.keep_all)
        result = xr.Dataset({"data": ("x", [1, 2, 3])})

        attach_plugin_result(
            tree,
            result,
            step_id="read_data",
            plugin_kind="reader",
            plugin_name="abi_netcdf",
        )

        with pytest.raises(ValueError, match="unique step_id"):
            attach_plugin_result(
                tree,
                result,
                step_id="read_data",
                plugin_kind="reader",
                plugin_name="abi_netcdf",
            )


class TestApplyScriptRetention:
    """Test script DataTree retention policies."""

    def _build_tree(self, retention_policy=RetentionPolicy.keep_all):
        """Build a script tree with multiple attached results."""
        tree = initialize_script_tree("test_script", retention_policy)
        first = xr.Dataset(
            {"data": ("x", [1, 2, 3])},
            coords={"latitude": ("x", [10, 20, 30])},
            attrs={"first_attr": "preserved"},
        )
        second = xr.Dataset(
            {"data": ("x", [4, 5, 6])},
            coords={"latitude": ("x", [40, 50, 60])},
            attrs={"second_attr": "preserved"},
        )

        attach_plugin_result(
            tree,
            first,
            step_id="read_data",
            plugin_kind="reader",
            plugin_name="abi_netcdf",
        )
        attach_plugin_result(
            tree,
            second,
            step_id="apply_algorithm",
            plugin_kind="algorithm",
            plugin_name="single_channel",
        )
        return tree

    def test_keep_all_preserves_all_step_data(self):
        """Test keep_all leaves all step nodes intact."""
        tree = self._build_tree(RetentionPolicy.keep_all)

        updated = apply_script_retention(tree, "apply_algorithm")

        assert updated is tree
        assert "read_data" in tree.children
        assert "apply_algorithm" in tree.children
        assert "data" in tree["read_data"].ds.data_vars
        assert "latitude" in tree["read_data"].ds.coords
        assert "data" in tree["apply_algorithm"].ds.data_vars

    def test_metadata_only_reduces_older_steps_to_attrs(self):
        """Test metadata_only removes older step data while preserving attrs."""
        tree = self._build_tree(RetentionPolicy.metadata_only)

        apply_script_retention(tree, "apply_algorithm")

        assert "read_data" in tree.children
        assert "apply_algorithm" in tree.children
        assert tree["read_data"].attrs["first_attr"] == "preserved"
        assert tree["read_data"].attrs["plugin_kind"] == "reader"
        assert not tree["read_data"].ds.data_vars
        assert not tree["read_data"].ds.coords
        assert "data" in tree["apply_algorithm"].ds.data_vars

    def test_current_only_removes_older_steps(self):
        """Test current_only removes older step nodes."""
        tree = self._build_tree(RetentionPolicy.current_only)

        apply_script_retention(tree, "apply_algorithm")

        assert "read_data" not in tree.children
        assert "apply_algorithm" in tree.children
        assert "data" in tree["apply_algorithm"].ds.data_vars

    def test_explicit_retention_policy_overrides_root_policy(self):
        """Test explicit retention policy overrides root retention policy."""
        tree = self._build_tree(RetentionPolicy.keep_all)

        apply_script_retention(
            tree,
            "apply_algorithm",
            retention_policy=RetentionPolicy.current_only,
        )

        assert "read_data" not in tree.children
        assert "apply_algorithm" in tree.children

    def test_accepts_retention_policy_string(self):
        """Test script retention accepts string policy values."""
        tree = self._build_tree(RetentionPolicy.keep_all)

        apply_script_retention(
            tree, "apply_algorithm", retention_policy="metadata_only"
        )

        assert "read_data" in tree.children
        assert not tree["read_data"].ds.data_vars
        assert not tree["read_data"].ds.coords

    def test_rejects_invalid_retention_policy(self):
        """Test script retention rejects invalid retention policies."""
        tree = self._build_tree(RetentionPolicy.keep_all)

        with pytest.raises(ValueError, match="Invalid retention policy"):
            apply_script_retention(
                tree,
                "apply_algorithm",
                retention_policy="keep_recent",
            )

    def test_rejects_unknown_current_step(self):
        """Test script retention rejects unknown current step ids."""
        tree = self._build_tree(RetentionPolicy.keep_all)

        with pytest.raises(ValueError, match="unknown step"):
            apply_script_retention(tree, "missing_step")

    def test_rejects_non_script_root(self):
        """Test script retention rejects non-script DataTrees."""
        tree = xr.DataTree(name="plain")

        with pytest.raises(ValueError, match="initialize_script_tree"):
            apply_script_retention(tree, "apply_algorithm")

    def test_rejects_invalid_plugin_kind(self):
        """Test attaching a plugin result rejects unknown plugin kinds."""
        tree = initialize_script_tree("test_script", RetentionPolicy.keep_all)
        result = xr.Dataset({"data": ("x", [1, 2, 3])})

        with pytest.raises(ValueError, match="Invalid script plugin kind"):
            attach_plugin_result(
                tree,
                result,
                step_id="read_data",
                plugin_kind="not_a_kind",
                plugin_name="abi_netcdf",
            )

    def test_rejects_empty_plugin_name(self):
        """Test registered plugin kinds reject empty plugin names."""
        tree = initialize_script_tree("test_script", RetentionPolicy.keep_all)
        result = xr.Dataset({"data": ("x", [1, 2, 3])})

        with pytest.raises(ValueError, match="plugin_name"):
            attach_plugin_result(
                tree,
                result,
                step_id="read_data",
                plugin_kind="reader",
                plugin_name="",
            )

    def test_rejects_invalid_step_id(self):
        """Test attaching a plugin result rejects invalid step ids."""
        tree = initialize_script_tree("test_script", RetentionPolicy.keep_all)
        result = xr.Dataset({"data": ("x", [1, 2, 3])})

        with pytest.raises(ValueError, match="valid Python identifiers"):
            attach_plugin_result(
                tree,
                result,
                step_id="read-data",
                plugin_kind="reader",
                plugin_name="abi_netcdf",
            )

    def test_rejects_unconvertible_step_data_with_script_context(self):
        """Test attaching unsupported data gives a script-specific error."""
        tree = initialize_script_tree("test_script", RetentionPolicy.keep_all)

        with pytest.raises(TypeError, match="script step 'mytest'") as excinfo:
            attach_plugin_result(
                tree,
                0,
                step_id="mytest",
                plugin_kind="manual",
                plugin_name="manual",
            )

        assert "builtins.int" in str(excinfo.value)
        assert "wrap it in a Dataset, DataArray, or dict" in str(excinfo.value)
        assert isinstance(excinfo.value.__cause__, TypeError)

    def test_stamps_step_attrs(self):
        """Test attaching a plugin result stamps step metadata attrs."""
        tree = initialize_script_tree("test_script", RetentionPolicy.keep_all)
        result = xr.Dataset({"data": ("x", [1, 2, 3])})

        attach_plugin_result(
            tree,
            result,
            step_id="apply_algorithm",
            plugin_kind="algorithm",
            plugin_name="single_channel",
            start_time="2026-07-15T00:00:00+00:00",
            end_time="2026-07-15T00:00:01+00:00",
            retention_policy=RetentionPolicy.metadata_only,
        )

        attrs = tree["apply_algorithm"].attrs
        assert attrs["step_id"] == "apply_algorithm"
        assert attrs["plugin_kind"] == "algorithm"
        assert attrs["plugin_name"] == "single_channel"
        assert attrs["start_time"] == "2026-07-15T00:00:00+00:00"
        assert attrs["end_time"] == "2026-07-15T00:00:01+00:00"
        assert attrs["retention_policy"] == "metadata_only"

    def test_registered_plugin_kind_defaults_times_to_current_time(self):
        """Test registered plugin data receives automatic timestamps."""
        tree = initialize_script_tree("test_script", RetentionPolicy.keep_all)
        result = xr.Dataset({"data": ("x", [1, 2, 3])})

        attach_plugin_result(
            tree,
            result,
            step_id="apply_algorithm",
            plugin_kind="algorithm",
            plugin_name="single_channel",
        )

        datetime.fromisoformat(tree["apply_algorithm"].attrs["start_time"])
        datetime.fromisoformat(tree["apply_algorithm"].attrs["end_time"])

    def test_inherits_root_retention_policy(self):
        """Test attaching a plugin result inherits the root retention policy."""
        tree = initialize_script_tree("test_script", RetentionPolicy.current_only)
        result = xr.Dataset({"data": ("x", [1, 2, 3])})

        attach_plugin_result(
            tree,
            result,
            step_id="read_data",
            plugin_kind="reader",
            plugin_name="abi_netcdf",
        )

        assert tree["read_data"].attrs["retention_policy"] == "current_only"

    def test_rejects_non_script_root(self):
        """Test attaching a plugin result rejects non-script DataTrees."""
        tree = xr.DataTree(name="plain")
        result = xr.Dataset({"data": ("x", [1, 2, 3])})

        with pytest.raises(ValueError, match="initialize_script_tree"):
            attach_plugin_result(
                tree,
                result,
                step_id="read_data",
                plugin_kind="reader",
                plugin_name="abi_netcdf",
            )
