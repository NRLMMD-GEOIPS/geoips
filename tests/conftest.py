# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Pytest configuration for test data validation.

Provides command-line options and fixtures to control test behavior
when required test data files are missing.
"""

import pytest


def pytest_addoption(parser):
    """Add custom command-line options to pytest.

    Parameters
    ----------
    parser : pytest.Parser
        Pytest command-line argument parser.

    Notes
    -----
    Adds --no-fail-on-missing-data flag to skip tests instead of
    failing when test data is unavailable.
    """
    try:
        parser.addoption(
            "--no-fail-on-missing-data",
            action="store_true",
            default=False,
            help="Fail tests if test data is missing",
        )
    except ValueError as resp:
        if "option names {'--no-fail-on-missing-data'} already added" in str(resp):
            pass


@pytest.fixture
def fail_on_missing_data(request):
    """Determine whether to fail tests on missing data.

    Parameters
    ----------
    request : pytest.FixtureRequest
        Pytest fixture request object.

    Returns
    -------
    bool
        True if tests should fail on missing data, False to skip instead.
    """
    return not request.config.getoption("--no-fail-on-missing-data")
