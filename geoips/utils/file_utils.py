# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Filesystem path helpers used across GeoIPS."""

from pathlib import Path


def path_exists(file_path: str) -> bool:
    """Return True if `path` exists on the filesystem.

    Parameters
    ----------
    file_path : str
        Path to the file to evaluate.

    Returns
    -------
    bool
        True if `path` exists, otherwise False.
    """
    return Path(file_path).exists()
