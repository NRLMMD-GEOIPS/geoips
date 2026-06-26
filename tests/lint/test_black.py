"""Black code formatting check via subprocess."""

import subprocess
import os
import pytest


@pytest.mark.lint
@pytest.mark.black
def test_black(lint_path, geoips_root):
    """Check that code is formatted according to black.

    Parameters
    ----------
    lint_path : str
        Path to the source tree to lint.
    geoips_root : str
        Path to the geoips repository root (for .config/black).
    """
    config_path = os.path.join(geoips_root, ".config", "black")
    result = subprocess.run(
        ["black", "--check", "--diff", "--config", config_path, lint_path],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stdout + result.stderr)
        pytest.fail(f"black failed with exit code {result.returncode}")
