# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""pytest test-suite for `geoips.utils.file_utils.py`."""

from geoips.utils.file_utils import path_exists


def test_path_exists_returns_true_for_existing_file(tmp_path):
    """Existing files return True."""
    existing_file = tmp_path / "exists.nc"
    existing_file.touch()
    assert path_exists(str(existing_file))


def test_path_exists_returns_false_for_missing_path(tmp_path):
    """Missing paths return False."""
    missing_file = str(tmp_path / "does_not_exist.nc")
    assert not path_exists(missing_file)
