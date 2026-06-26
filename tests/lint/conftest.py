import os
import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--lint-path",
        default=None,
        help="Path to lint (defaults to current directory)",
    )
    parser.addoption(
        "--flake8-docstring-only",
        action="store_true",
        default=False,
        help="Only check RST/D docstrings with flake8",
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "black: Black code formatting check")
    config.addinivalue_line("markers", "flake8: Flake8 linting check")
    config.addinivalue_line("markers", "bandit: Bandit security check")
    config.addinivalue_line("markers", "doc8: Doc8 documentation check")


@pytest.fixture
def lint_path(request):
    return request.config.getoption("--lint-path") or os.getcwd()


@pytest.fixture
def geoips_root():
    return os.path.realpath(os.path.join(os.path.dirname(__file__), "..", ".."))
