import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--no-fail-on-missing-data",
        action="store_true",
        default=False,
        help="Fail tests if test data is missing",
    )


@pytest.fixture
def fail_on_missing_data(request):
    """Fixture to get the 'no_fail_on_missing_data' option value."""
    return not request.config.getoption("--no-fail-on-missing-data")
