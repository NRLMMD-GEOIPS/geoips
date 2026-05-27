# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Tests for DataTreeDitto converters registered in Phase III."""

import numpy as np
import xarray as xr

from geoips.utils.types.datatree_ditto import DataTreeDitto


class TestNdarrayConverter:
    """ndarray is registered as a built-in converter in DataTreeDitto."""

    def test_roundtrip(self):
        """Round-trip a 2D ndarray through DataTreeDitto."""
        arr = np.array([[1.0, 2.0], [3.0, 4.0]])
        dt = DataTreeDitto(arr)
        result = dt.get_original()
        assert isinstance(result, np.ndarray)
        assert np.allclose(result, arr)

    def test_1d_array(self):
        """Round-trip a 1D ndarray through DataTreeDitto."""
        arr = np.array([1, 2, 3, 4, 5])
        dt = DataTreeDitto(arr)
        result = dt.get_original()
        assert np.allclose(result, arr)


class TestDictConverter:
    """dict converter registered in datatree_converters.py."""

    def test_simple_dict_values(self):
        """Round-trip a dict with mixed scalar values."""
        d = {"a": 1, "b": "hello", "c": 3.14}
        dt = DataTreeDitto(d)
        result = dt.get_original()
        assert result == d

    def test_dict_with_ndarray(self):
        """Round-trip a dict containing an ndarray value."""
        arr = np.array([10.0, 20.0])
        d = {"name": "test", "data": arr}
        dt = DataTreeDitto(d)
        result = dt.get_original()
        assert result["name"] == "test"
        assert np.allclose(result["data"], arr)


class TestDatasetConverter:
    """Dataset identity passthrough."""

    def test_identity_passthrough(self):
        """Pass a Dataset through DataTreeDitto unchanged."""
        ds = xr.Dataset({"var": ("x", [1, 2, 3])})
        dt = DataTreeDitto(ds)
        result = dt.get_original()
        assert isinstance(result, xr.Dataset)
        assert "var" in result


class TestDataArrayConverter:
    """DataArray converter."""

    def test_dataarray_roundtrip(self):
        """Round-trip a DataArray through DataTreeDitto."""
        da = xr.DataArray([1, 2, 3], dims="x", name="myvar")
        dt = DataTreeDitto(da)
        result = dt.get_original()
        assert isinstance(result, xr.DataArray)
        assert np.allclose(result.values, da.values)
        assert result.name == "myvar"
