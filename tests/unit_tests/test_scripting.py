# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Unit tests for the public GeoIPS scripting helpers."""

import geoips.scripting as scripting


def test_initialize_script_tree_public_helper():
    """Test the public scripting initializer creates a script DataTree."""
    tree = scripting.initialize_script_tree("test_script", retention_policy="keep_all")

    assert tree.name == "test_script"
    assert tree.attrs["execution_mode"] == "script"
    assert tree.attrs["retention_policy"] == "keep_all"


def test_initialize_script_tree_docstring_describes_plugin_calls():
    """Test public initializer docstring describes plugin-call usage."""
    assert "data" in scripting.initialize_script_tree.__doc__
    assert "_obp_initiated=True" in scripting.initialize_script_tree.__doc__
    assert "step_id" in scripting.initialize_script_tree.__doc__


def test_retention_policies_public_constant():
    """Test supported retention policies are available from scripting API."""
    assert "RETENTION_POLICIES" in scripting.__all__
    assert scripting.RETENTION_POLICIES == (
        scripting.RetentionPolicy.keep_all,
        scripting.RetentionPolicy.metadata_only,
        scripting.RetentionPolicy.current_only,
    )


def test_retention_policy_enum_public():
    """Test retention policy enum is available from scripting API."""
    assert "RetentionPolicy" in scripting.__all__
    assert scripting.RetentionPolicy.metadata_only == "metadata_only"
    assert "attrs only" in scripting.RetentionPolicy.metadata_only.__doc__


def test_internal_validation_helper_not_public():
    """Test low-level validation helper is not part of public scripting API."""
    assert "validate_retention_policy" not in scripting.__all__
    assert not hasattr(scripting, "validate_retention_policy")
