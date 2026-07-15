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

    @pytest.mark.parametrize("retention_policy", [policy.value for policy in RetentionPolicy])
    def test_accepts_valid_policy_strings(self, retention_policy):
        """Test retention policy validation accepts supported policy strings."""
        validate_retention_policy(retention_policy)

    def test_rejects_invalid_policy(self):
        """Test retention policy validation rejects unsupported policies."""
        with pytest.raises(ValueError, match="Expected one of"):
            validate_retention_policy("keep_recent")
