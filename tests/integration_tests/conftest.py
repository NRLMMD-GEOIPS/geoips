# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Integration test fixtures for the DataTree spec integration suite.

Provides a ``patch_plugin_registry`` autouse fixture that monkeypatches the
``Workflow._resolve_plugin`` staticmethod so that ``Workflow.call()`` resolves
synthetic reader and coverage-checker plugins at runtime without a real registry.
"""

import logging

import numpy as np
import pytest
import xarray as xr

LOG = logging.getLogger(__name__)


# -- synthetic plugins (fully concrete, NOT abstract) -------------------------


class _TestReader:
    """A test-only reader that returns a deterministic xr.Dataset."""

    interface = "readers"
    family = "test"
    name = "synthetic_reader"
    data_tree = False

    def call(self, fnames=None, **kwargs):
        from geoips.utils.types.datatree_ditto import DataTreeDitto

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

    def __call__(self, fnames=None, **kwargs):
        return self.call(fnames=fnames, **kwargs)


class _TestCoverageChecker:
    """A test-only coverage checker that passes data through unchanged."""

    interface = "coverage_checkers"
    family = "test"
    name = "synthetic_coverage"
    data_tree = False

    def call(self, data, **kwargs):
        return data

    def __call__(self, data=None, **kwargs):
        return self.call(data=data, **kwargs)


class _Passthrough:
    """Returns upstream data unchanged for any non-reader/coverage step."""

    data_tree = True

    def call(self, data=None, **kwargs):
        return data

    def __call__(self, data=None, **kwargs):
        if data is not None:
            return data
        return xr.DataTree(name="empty")


# -- helper for mock resolution -----------------------------------------------


def _mock_resolve_plugin(kind, name):
    """Mock ``Workflow._resolve_plugin`` returning a callable test double."""
    _ = name  # unused
    if kind == "reader":
        return _TestReader()
    if kind == "coverage_checker":
        return _TestCoverageChecker()
    return _Passthrough()


# -- autouse fixture ----------------------------------------------------------


@pytest.fixture(autouse=True)
def patch_plugin_registry(monkeypatch):
    """Redirect plugin resolution to synthetic test doubles.

    Patches ``Workflow._resolve_plugin`` so that every plugin kind resolves
    to a synthetic test double without needing a full GeoIPS plugin registry.
    """
    from geoips.interfaces.class_based.workflow import Workflow

    monkeypatch.setattr(Workflow, "_resolve_plugin",
                        staticmethod(_mock_resolve_plugin))
