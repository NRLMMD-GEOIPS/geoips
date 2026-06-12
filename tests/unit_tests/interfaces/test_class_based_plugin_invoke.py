# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Tests for ``_invoke()`` DataTree wrapping in BaseClassPlugin."""

import numpy as np
import xarray as xr

from geoips.interfaces.class_based_plugin import BaseClassPlugin


class _FakeLegacyPlugin(BaseClassPlugin):
    """Simulates a legacy plugin with ``data_tree=False``."""

    interface = "algorithms"
    family = "test"
    name = "fake_legacy"
    data_tree = False

    def call(self, data=None, **kwargs):
        return data

    def _invoke(self, data=None, *args, **kwargs):
        return BaseClassPlugin._invoke(self, data=data, *args, **kwargs)


class _FakeNativePlugin(BaseClassPlugin):
    """Simulates a DataTree-native plugin with ``data_tree=True``."""

    interface = "algorithms"
    family = "test"
    name = "fake_dt"
    data_tree = True

    def call(self, data=None, **kwargs):
        return data

    def _invoke(self, data=None, *args, **kwargs):
        return BaseClassPlugin._invoke(self, data=data, *args, **kwargs)


class TestInvokeWrapping:
    """Tests for _invoke() DataTree conversion."""

    def test_reader_path_no_wrapping(self):
        """Verify data=None path calls call with just args."""
        plugin = _FakeLegacyPlugin()
        result = plugin._invoke(data=None)
        assert result is None

    def test_legacy_unwraps_datatree_to_dataset(self):
        """Verify ``data_tree=False`` unwraps DataTree input to native object."""
        ds = xr.Dataset({"var": ("x", [1, 2, 3])})
        dt = xr.DataTree.from_dict({"/": ds})

        plugin = _FakeLegacyPlugin()
        result = plugin._invoke(data=dt, _obp_initiated=True)
        assert isinstance(result, xr.DataTree)
        assert result.ds is not None
        assert "var" in result.ds
        assert (result.ds["var"].values == [1, 2, 3]).all()

    def test_legacy_rewraps_output(self):
        """Verify ``data_tree=False`` rewraps non-DataTree output."""

        class _ProducesDataset(_FakeLegacyPlugin):
            def call(self, data, **kwargs):
                return xr.Dataset({"out": ("x", [10, 20])})

        plugin = _ProducesDataset()
        result = plugin._invoke(data=xr.DataTree(), _obp_initiated=True)
        assert isinstance(result, xr.DataTree)
        assert result.ds is not None
        assert "out" in result.ds
        assert (result.ds["out"].values == [10, 20]).all()

    def test_datatree_native_skips_conversion(self):
        """Verify ``data_tree=True`` DataTree passes through unchanged."""
        from geoips.utils.types.datatree_ditto import DataTreeDitto

        ds = xr.Dataset({"var": ("x", [1, 2])})
        dt = DataTreeDitto(ds)

        plugin = _FakeNativePlugin()
        result = plugin._invoke(data=dt)
        assert isinstance(result, xr.DataTree)
        assert result.ds is not None
        assert "var" in result.ds
        assert (result.ds["var"].values == [1, 2]).all()

    def test_datatree_ditto_roundtrip(self):
        """Verify DataTreeDitto round-trips numpy through legacy plugin."""
        from geoips.utils.types.datatree_ditto import DataTreeDitto

        arr = np.array([[1.0, 2.0], [3.0, 4.0]])
        dt = DataTreeDitto(arr)

        class _NumpyAlgPlugin(_FakeLegacyPlugin):
            def call(self, data, **kwargs):
                assert isinstance(data, np.ndarray)
                return data * 2

        plugin = _NumpyAlgPlugin()
        result = plugin._invoke(data=dt, _obp_initiated=True)
        assert isinstance(result, xr.DataTree)
        assert result.ds is not None
        assert (result.ds["data"].values == np.array([[2.0, 4.0], [6.0, 8.0]])).all()
