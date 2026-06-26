import subprocess
import os
import pytest


@pytest.mark.lint
@pytest.mark.black
def test_black(lint_path, geoips_root):
    config_path = os.path.join(geoips_root, ".config", "black")
    result = subprocess.run(
        ["black", "--check", "--diff", "--config", config_path, lint_path],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stdout + result.stderr)
        pytest.fail(f"black failed with exit code {result.returncode}")
