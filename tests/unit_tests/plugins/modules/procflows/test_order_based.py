"""pytest test-suite for Order Based Procflow."""

import pytest

from geoips.plugins.modules.procflows.order_based import (
    validate_workflow_file_inputs,
)


def _make_workflow_plugin(steps):
    """Build a minimal workflow plugin dict with the given steps."""
    return {"spec": {"steps": steps}}


def test_valid_fnames_no_error(tmp_path):
    """Test that existing command-line fnames pass without error."""
    valid_file = tmp_path / "data.nc"
    valid_file.touch()

    workflow_plugin = _make_workflow_plugin({})
    validate_workflow_file_inputs(workflow_plugin, [str(valid_file)])


def test_missing_fnames_raises(tmp_path):
    """CLI fnames that don't exist raise FileNotFoundError via reader override."""
    missing_path = str(tmp_path / "nonexistent.nc")

    # reader step must exist so CLI fnames override kicks in
    steps = {
        "read_data": {
            "kind": "reader",
            "arguments": {"fnames": ["/placeholder/ignored.nc"]},
        },
    }
    # match on something that actually appears in the message:
    # either the step_id, the kind, or the missing path itself
    with pytest.raises(FileNotFoundError, match="nonexistent.nc"):
        validate_workflow_file_inputs(_make_workflow_plugin(steps), [missing_path])


def test_valid_reader_step_fnames(tmp_path):
    """Test that existing fnames in a reader step pass without error."""
    valid_file = tmp_path / "reader_input.nc"
    valid_file.touch()

    steps = {
        "read_data": {
            "kind": "reader",
            "arguments": {"fnames": [str(valid_file)]},
        },
    }
    validate_workflow_file_inputs(_make_workflow_plugin(steps), [])


def test_missing_reader_step_fnames_raises(tmp_path):
    """Test that missing fnames in a reader step raise FileNotFoundError."""
    steps = {
        "read_data": {
            "kind": "reader",
            "arguments": {"fnames": ["/no/such/file.nc"]},
        },
    }
    with pytest.raises(FileNotFoundError, match="read_data.*reader"):
        validate_workflow_file_inputs(_make_workflow_plugin(steps), [])


def test_valid_compare_path(tmp_path):
    """Test that an existing compare_path in an output_checker step passes."""
    compare_dir = tmp_path / "compare"
    compare_dir.mkdir()

    steps = {
        "check_output": {
            "kind": "output_checker",
            "arguments": {"compare_path": str(compare_dir)},
        },
    }
    validate_workflow_file_inputs(_make_workflow_plugin(steps), [])


def test_missing_compare_path_raises(tmp_path):
    """Test that a missing compare_path raises FileNotFoundError."""
    steps = {
        "check_output": {
            "kind": "output_checker",
            "arguments": {"compare_path": "/no/such/path"},
        },
    }
    with pytest.raises(FileNotFoundError, match="check_output.*output_checker"):
        validate_workflow_file_inputs(_make_workflow_plugin(steps), [])


def test_null_compare_path_is_ignored():
    """Test that a null compare_path does not trigger validation."""
    steps = {
        "check_output": {
            "kind": "output_checker",
            "arguments": {"compare_path": None},
        },
    }
    validate_workflow_file_inputs(_make_workflow_plugin(steps), [])


def test_step_with_no_arguments_is_skipped():
    """Test that steps without an arguments key do not cause errors."""
    steps = {
        "some_step": {
            "kind": "algorithm",
        },
    }
    validate_workflow_file_inputs(_make_workflow_plugin(steps), [])


def test_multiple_missing_files_all_reported(tmp_path):
    """CLI fnames override step fnames; override + compare_path are both reported."""
    steps = {
        "read_data": {
            "kind": "reader",
            # These will be overridden by CLI fnames, so they should NOT appear:
            "arguments": {"fnames": ["/missing/a.nc", "/missing/b.nc"]},
        },
        "check_output": {
            "kind": "output_checker",
            "arguments": {"compare_path": "/missing/compare"},
        },
    }
    with pytest.raises(FileNotFoundError) as exc_info:
        validate_workflow_file_inputs(_make_workflow_plugin(steps), ["/missing/c.nc"])

    error_message = str(exc_info.value)
    # Overridden CLI path + compare_path should appear:
    assert "/missing/c.nc" in error_message
    assert "/missing/compare" in error_message
    # Step-level fnames were overridden, so they must NOT appear:
    assert "/missing/a.nc" not in error_message
    assert "/missing/b.nc" not in error_message
