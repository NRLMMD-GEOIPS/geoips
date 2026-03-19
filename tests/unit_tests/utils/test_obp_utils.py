# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""pytest test-suite for `geoips.utils.obp_utils`."""

import pytest

from geoips.utils.obp_utils import validate_workflow_file_inputs


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
    """Test that missing command-line fnames raise FileNotFoundError."""
    missing_path = str(tmp_path / "nonexistent.nc")

    workflow_plugin = _make_workflow_plugin({})
    with pytest.raises(FileNotFoundError, match="command_line_args"):
        validate_workflow_file_inputs(workflow_plugin, [missing_path])


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


def test_missing_sector_fnames_raises():
    """Test that missing fnames in a sector step raise FileNotFoundError."""
    steps = {
        "define_sector": {
            "kind": "sector",
            "arguments": {"fnames": ["/no/such/sector_file.yaml"]},
        },
    }
    with pytest.raises(FileNotFoundError, match="define_sector.*sector"):
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
    """Test that all missing files are listed in a single error message."""
    steps = {
        "read_data": {
            "kind": "reader",
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
    assert "/missing/a.nc" in error_message
    assert "/missing/b.nc" in error_message
    assert "/missing/c.nc" in error_message
    assert "/missing/compare" in error_message
