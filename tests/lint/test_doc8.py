"""Doc8 documentation style check via subprocess."""

import subprocess
import os
import pytest


@pytest.mark.lint
@pytest.mark.doc8
def test_doc8(lint_path):
    """Check documentation style with doc8.

    Parameters
    ----------
    lint_path : str
        Path to the source tree.  Looks for docs/source under this path.
    """
    docs_source = os.path.join(lint_path, "docs", "source")
    if not os.path.isdir(docs_source):
        pytest.skip(f"No docs/source directory in {lint_path}")
    result = subprocess.run(
        ["doc8", "--max-line-length=120", docs_source],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stdout + result.stderr)
        pytest.fail(f"doc8 failed with exit code {result.returncode}")
