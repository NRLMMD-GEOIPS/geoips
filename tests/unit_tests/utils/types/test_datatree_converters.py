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


class TestMaskedArrayConverter:
    """MaskedArray converter round-trips, including non-float dtypes.

    Regression coverage for a bug where ``masked_array_to_dataset`` filled
    masked entries with ``np.nan``, which raised ``TypeError`` for integer,
    unsigned and string dtypes (NaN is not representable) and upcast the dtype
    even when it succeeded.
    """

    def _assert_roundtrip(self, arr):
        dt = DataTreeDitto(arr)
        result = dt.get_original()
        assert isinstance(result, np.ma.MaskedArray)
        assert result.dtype == arr.dtype
        assert (np.ma.getmaskarray(result) == np.ma.getmaskarray(arr)).all()
        assert np.ma.allequal(result, arr)
        return result

    def test_int_masked_roundtrip(self):
        """Round-trip an integer MaskedArray with an active mask."""
        self._assert_roundtrip(np.ma.array([1, 2, 3, 4], mask=[0, 1, 0, 1]))

    def test_uint8_masked_roundtrip(self):
        """Round-trip a uint8 MaskedArray with an active mask."""
        self._assert_roundtrip(
            np.ma.array([1, 2, 3], dtype=np.uint8, mask=[0, 1, 0])
        )

    def test_float_masked_roundtrip(self):
        """Round-trip a float MaskedArray with an active mask."""
        self._assert_roundtrip(np.ma.array([1.5, 2.5, 3.5], mask=[0, 1, 0]))

    def test_2d_int_masked_roundtrip(self):
        """Round-trip a 2D integer MaskedArray with an active mask."""
        self._assert_roundtrip(
            np.ma.array([[1, 2], [3, 4]], mask=[[0, 1], [1, 0]])
        )

    def test_string_masked_roundtrip(self):
        """Round-trip a string MaskedArray (non-numeric fill value)."""
        arr = np.ma.array(["x", "y", "z"], mask=[0, 1, 0])
        dt = DataTreeDitto(arr)
        result = dt.get_original()
        assert isinstance(result, np.ma.MaskedArray)
        assert (np.ma.getmaskarray(result) == np.ma.getmaskarray(arr)).all()


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
        """Round-trip a DataArray through DataTreeDitto without any change.

        The round-trip should be lossless: values, dims, name and coords must
        all be preserved (not merely numerically close), and the result must be
        ``identical`` to the input.
        """
        da = xr.DataArray(
            [1, 2, 3],
            dims="x",
            name="myvar",
            coords={"x": [10, 20, 30]},
            attrs={"units": "K"},
        )
        dt = DataTreeDitto(da)
        result = dt.get_original()
        assert isinstance(result, xr.DataArray)
        # dims and name are unchanged
        assert result.dims == da.dims
        assert result.name == da.name
        # fully identical (values, dims, name, coords)
        xr.testing.assert_identical(result, da)
