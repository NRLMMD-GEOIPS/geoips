"""Pytest configuration for lint tests.

Provides ``--lint-path`` and ``--flake8-docstring-only`` CLI options,
registers lint-specific markers, and exposes the ``lint_path`` and
``geoips_root`` fixtures.
"""

import os
import pytest


def pytest_addoption(parser):
    """Register --lint-path and --flake8-docstring-only CLI options.

    Parameters
    ----------
    parser : pytest.Parser
        Pytest command-line argument parser.
    """
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
    """Register lint-specific pytest markers.

    Parameters
    ----------
    config : pytest.Config
        Pytest configuration object.
    """
    config.addinivalue_line("markers", "black: Black code formatting check")
    config.addinivalue_line("markers", "flake8: Flake8 linting check")
    config.addinivalue_line("markers", "bandit: Bandit security check")
    config.addinivalue_line("markers", "doc8: Doc8 documentation check")


@pytest.fixture
def lint_path(request):
    """Return the path to lint, from --lint-path or cwd.

    Parameters
    ----------
    request : _pytest.fixtures.FixtureRequest
        Pytest request fixture.
    """
    return request.config.getoption("--lint-path") or os.getcwd()


@pytest.fixture
def geoips_root():
    """Return the absolute path to the geoips repository root."""
    return os.path.realpath(os.path.join(os.path.dirname(__file__), "..", ".."))
