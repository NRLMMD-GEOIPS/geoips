# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Integration test fixtures for the DataTree spec integration suite."""

import numpy as np
import pytest
import xarray as xr

from geoips.interfaces.class_based.readers import BaseReaderPlugin
from geoips.interfaces.class_based.coverage_checkers import BaseCoverageCheckerPlugin
from geoips.utils.types.datatree_ditto import DataTreeDitto


class _SyntheticReader(BaseReaderPlugin, abstract=True):
    """A test-only reader that returns a deterministic xr.Dataset.

    Does not read from disk.  Used in integration tests so that
    workflow execution exercises the full pipeline without needing
    real test data files.
    """

    interface = "readers"
    family = "test"
    name = "synthetic_reader"
    data_tree = False

    def call(self, *args, fnames=None, **kwargs):
        """Return a small deterministic dataset with synthetic data."""
        ds = xr.Dataset(
            {
                "B14BT": (["y", "x"], np.arange(6, dtype=np.float64).reshape(2, 3)),
                "lat": (["y", "x"], np.zeros((2, 3))),
                "lon": (["y", "x"], np.zeros((2, 3))),
            },
            attrs={
                "start_datetime": "2024-01-01T00:00:00",
                "end_datetime": "2024-01-01T01:00:00",
                "source_name": "abi",
                "platform_name": "goes-16",
                "data_provider": "test",
                "interpolation_radius_of_influence": 3000,
            },
        )
        return DataTreeDitto(ds, name="reader_output")


class _SyntheticCoverageChecker(BaseCoverageCheckerPlugin, abstract=True):
    """A test-only coverage checker that passes data through unchanged.

    Actual coverage checkers would filter data; this one is a no-op
    that preserves the upstream dataset.
    """

    interface = "coverage_checkers"
    family = "test"
    name = "synthetic_coverage"
    data_tree = False

    def call(self, data, **kwargs):
        return data


@pytest.fixture(scope="session")
def synthetic_reader():
    """Return an instance of _SyntheticReader."""
    return _SyntheticReader()


@pytest.fixture(scope="session")
def synthetic_coverage_checker():
    """Return an instance of _SyntheticCoverageChecker."""
    return _SyntheticCoverageChecker()
