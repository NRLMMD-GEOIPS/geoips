# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Fixtures for testing the Order-based procflow's CoverageCheckerArgumentsModel."""

# Third-Party Libraries
import pytest


@pytest.fixture
def valid_coverage_checker_arguments():
    """Fixture providing valid data for CoverageCheckerArgumentsModel tests."""
    return {"variable_name": "infrared", "area_def": "test_string", "radius_km": 300}
