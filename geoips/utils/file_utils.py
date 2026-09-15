# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Filesystem path helpers used across GeoIPS."""

# Python Standard Libraries
from pathlib import Path


def path_exists(path: str | Path) -> bool:
    """Return True if a filesystem path exists.

    Parameters
    ----------
    file_path : str
        File or Directory path to evaluate. This could be a file, directory, or other
         filesystem object.

    Returns
    -------
    bool
        True if `path` exists on the filesystem, otherwise False.
    """
    return Path(path).exists()
