"""Unit test module for interpolator interface preprocessing."""

import pytest
import xarray as xr

from geoips.interfaces import interpolators


dt_no_sector = xr.DataTree.from_dict(
    {
        "/": xr.Dataset(coords={"time": [1, 2, 3]}),
        "/ocean": xr.Dataset(
            {
                "temperature": ("time", [4, 5, 6]),
                "salinity": ("time", [7, 8, 9]),
            },
            attrs={"plugin_kind": "reader"},
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
            },
            attrs={"plugin_kind": "reader"},
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


def test_pre_call_interpolator_no_sector():
    """Interpolator pre-call requires a sector dependency under OBP."""
    with pytest.raises(RuntimeError):
        interp_plg._pre_call(dt_no_sector, _obp_initiated=True, area_def="area")


def test_pre_call_interpolator_no_area_def():
    """Interpolator pre-call requires a resolved area definition."""
    with pytest.raises(RuntimeError):
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
    assert kwargs["varlist"] == ["temperature", "salinity", "time"]
