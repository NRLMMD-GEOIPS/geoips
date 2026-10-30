"""Unit test module for interpolator interface preprocessing."""

import numpy as np
import pytest
import xarray as xr

from geoips.interfaces import interpolators

dt_no_sector = xr.DataTree.from_dict(
    {
        "/": xr.Dataset(coords={"obs": [1, 2, 3]}),
        "/ocean": xr.Dataset(
            {
                "temperature": ("obs", [4, 5, 6]),
                "salinity": ("obs", [7, 8, 9]),
                "time": (
                    "obs",
                    np.array(
                        ["2021-01-01", "2021-01-02", "2021-01-03"], dtype="datetime64"
                    ),
                ),
            },
            attrs={"plugin_kind": "reader"},
        ),
        "/atmosphere": xr.Dataset(
            {
                "temperature": ("obs", [2, 3, 4]),
                "humidity": ("obs", [3, 4, 5]),
            }
        ),
    }
)

dt_with_sector = xr.DataTree.from_dict(
    {
        "/": xr.Dataset(coords={"obs": [1, 2, 3]}),
        "/ocean": xr.Dataset(
            {
                "temperature": ("obs", [4, 5, 6]),
                "salinity": ("obs", [7, 8, 9]),
                "time": (
                    "obs",
                    np.array(
                        ["2021-01-01", "2021-01-02", "2021-01-03"], dtype="datetime64"
                    ),
                ),
            },
            attrs={"plugin_kind": "reader"},
        ),
        "/atmosphere": xr.Dataset(
            {
                "temperature": ("obs", [2, 3, 4]),
                "humidity": ("obs", [3, 4, 5]),
            },
            attrs={"plugin_kind": "sector"},
        ),
    }
)

interp_plg = interpolators.get_plugin("interp_nearest")


def test_pre_call_interpolator_accepts_explicit_area_def():
    """Interpolator pre-call accepts an explicitly supplied area definition."""
    data, kwargs = interp_plg._pre_call(
        dt_no_sector, _obp_initiated=True, area_def="area"
    )

    assert data is dt_no_sector
    assert kwargs["area_def"] == "area"
    assert kwargs["input_xarray"].attrs["plugin_kind"] == "reader"
    assert isinstance(kwargs["output_xarray"], xr.Dataset)
    assert kwargs["varlist"] == ["temperature", "salinity", "obs"]


def test_pre_call_interpolator_no_area_def():
    """Interpolator pre-call requires a resolved area definition."""
    with pytest.raises(RuntimeError, match="area definition.*sector"):
        interp_plg._pre_call(dt_with_sector, _obp_initiated=True)


def test_pre_call_interpolator_prepares_legacy_call_kwargs():
    """Interpolator pre-call prepares legacy call kwargs without calling call()."""
    data, kwargs = interp_plg._pre_call(
        dt_with_sector, _obp_initiated=True, area_def="area"
    )

    assert data is dt_with_sector
    assert kwargs["area_def"] == "area"
    assert kwargs["input_xarray"].attrs["plugin_kind"] == "reader"
    assert isinstance(kwargs["output_xarray"], xr.Dataset)
    assert kwargs["varlist"] == ["temperature", "salinity", "obs"]
