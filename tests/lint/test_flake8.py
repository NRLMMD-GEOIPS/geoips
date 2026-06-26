import subprocess
import os
import pytest


@pytest.mark.lint
@pytest.mark.flake8
def test_flake8(lint_path, request):
    flake8_args = ["flake8"]
    if request.config.getoption("--flake8-docstring-only"):
        flake8_args += ["--select=RST,D"]
    original_cwd = os.getcwd()
    try:
        os.chdir(lint_path)
        flake8_args.append(lint_path)
        result = subprocess.run(flake8_args, capture_output=True, text=True)
    finally:
        os.chdir(original_cwd)
    if result.returncode != 0:
        print(result.stdout + result.stderr)
        pytest.fail(f"flake8 failed with exit code {result.returncode}")
