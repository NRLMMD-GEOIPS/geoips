# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Utility functions for the order-based procflow."""

from pathlib import Path
from typing import Optional


def validate_paths(file_path: str) -> Optional[str]:
    """
    Check whether a file path exists.

    Parameters
    ----------
    file_path : str
        Path to the file to evaluate.

    Returns
    -------
    Optional[str]
        The file path if it does not exist.
    """
    if not Path(file_path).is_file():
        return file_path