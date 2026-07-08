"""Unit test module for interpolator code in class_based_plugin.py."""

import numpy as np
import pytest
import xarray as xr
from unittest.mock import MagicMock

from geoips.interfaces.class_based_plugin import _collect_interp_kwargs
from geoips.interfaces import interpolators


class DummyData:
    """Dummy class representing an xarray.Dataset."""

    variables = {
        "B01BT": np.ndarray(shape=(2000, 2000)),
        "B13BT": np.ndarray(shape=(2000, 2000)),
        "B14BT": np.ndarray(shape=(2000, 2000)),
    }


dt_no_sector = xr.DataTree.from_dict(
    {
        "/": xr.Dataset(coords={"time": [1, 2, 3]}),
        "/ocean": xr.Dataset(
            {
                "temperature": ("time", [4, 5, 6]),
                "salinity": ("time", [7, 8, 9]),
            }
        ),
        "/atmosphere": xr.Dataset(
            {
                "temperature": ("time", [2, 3, 4]),
                "humidity": ("time", [3, 4, 5]),
            }
        ),
    }
)

dt_with_sector = xr.DataTree.from_dict(
    {
        "/": xr.Dataset(coords={"time": [1, 2, 3]}),
        "/ocean": xr.Dataset(
            {
                "temperature": ("time", [4, 5, 6]),
                "salinity": ("time", [7, 8, 9]),
            }
        ),
        "/atmosphere": xr.Dataset(
            {
                "temperature": ("time", [2, 3, 4]),
                "humidity": ("time", [3, 4, 5]),
            },
            attrs={"plugin_kind": "sector"},
        ),
    }
)

interp_plg = interpolators.get_plugin("interp_nearest")


@pytest.mark.parametrize(
    ["data", "collect_varlist"], [[DummyData(), False], [DummyData, True]]
)
def test_collect_interp_kwargs(data, collect_varlist):
    """Test class_based_plugin._collect_interp_kwargs."""
    kwargs = _collect_interp_kwargs(data, collect_varlist=collect_varlist)
    expected_kwargs = ["input_xarray", "output_xarray"]
    if collect_varlist:
        expected_kwargs += ["varlist"]

    for kwarg in expected_kwargs:
        assert kwarg in kwargs


def test_call_interpolator_invalid_data():
    """Execute class_based_plugin.call_interpolator using invalid data."""
    with pytest.raises(RuntimeError):
        interp_plg._call_interpolator(xr.DataTree(), kwargs={})


def test_call_interpolator_no_sector():
    """Execute class_based_plugin.call_interpolator providing no sector."""
    with pytest.raises(RuntimeError):
        interp_plg._call_interpolator(dt_no_sector, kwargs={})


def test_call_interpolator_no_area_def():
    """Execute class_based_plugin.call_interpolator providing no area definition."""
    with pytest.raises(RuntimeError):
        interp_plg._call_interpolator(dt_with_sector, kwargs={})
