import subprocess
import pytest


@pytest.mark.lint
@pytest.mark.bandit
def test_bandit(lint_path):
    result = subprocess.run(
        ["bandit", "-ll", "-r", lint_path],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stdout + result.stderr)
        pytest.fail(f"bandit failed with exit code {result.returncode}")
