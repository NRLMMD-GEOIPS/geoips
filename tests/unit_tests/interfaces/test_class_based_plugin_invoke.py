# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Tests for BaseClassPlugin DataTree wrapping via the public ``plugin()`` call.

Calling ``plugin(...)`` routes through ``__call__`` -> ``_invoke``, so these
tests exercise the ``_invoke`` wrapping/conversion behavior through the public
interface rather than calling ``_invoke`` directly.
"""

import numpy as np
import xarray as xr

from geoips.interfaces.class_based_plugin import BaseClassPlugin
from geoips.interfaces.class_based.readers import BaseReaderPlugin


class _FakeLegacyPlugin(BaseClassPlugin):
    """Simulates a legacy plugin with ``data_tree=False``."""

    interface = "algorithms"
    family = "test"
    name = "fake_legacy"
    data_tree = False

    def call(self, data=None, **kwargs):
        return data


class _FakeNativePlugin(BaseClassPlugin):
    """Simulates a DataTree-native plugin with ``data_tree=True``."""

    interface = "algorithms"
    family = "test"
    name = "fake_dt"
    data_tree = True

    def call(self, data=None, **kwargs):
        return data


class TestInvokeWrapping:
    """Tests for DataTree conversion when calling ``plugin()``."""

    def test_reader_path_no_wrapping(self):
        """Verify data=None path calls call with just args."""
        plugin = _FakeLegacyPlugin()
        result = plugin(data=None)
        assert result is None

    def test_legacy_unwraps_datatree_to_dataset(self):
        """Verify ``data_tree=False`` unwraps DataTree input to native object."""
        ds = xr.Dataset({"var": ("x", [1, 2, 3])})
        dt = xr.DataTree.from_dict({"/": ds})

        plugin = _FakeLegacyPlugin()
        result = plugin(data=dt, _obp_initiated=True)
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
        result = plugin(data=xr.DataTree(), _obp_initiated=True)
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
        result = plugin(data=dt)
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
        result = plugin(data=dt, _obp_initiated=True)
        assert isinstance(result, xr.DataTree)
        assert result.ds is not None
        assert (result.ds["data"].values == np.array([[2.0, 4.0], [6.0, 8.0]])).all()


class TestPositionalDataRouting:
    """`_invoke` only drops positional data when it collides with a kwarg."""

    def test_leading_non_data_positional_still_receives_data(self):
        """A plugin whose first param is not ``data`` still gets it positionally."""

        class _XarrayObjPlugin(_FakeLegacyPlugin):
            def call(self, xarray_obj, **kwargs):
                # No ``xarray_obj`` kwarg is supplied, so the injected data must
                # arrive here positionally.
                return xarray_obj

        ds = xr.Dataset({"var": ("x", [1, 2, 3])})
        dt = xr.DataTree.from_dict({"/": ds})
        result = _XarrayObjPlugin()(data=dt, _obp_initiated=True)
        assert isinstance(result, xr.DataTree)
        assert "var" in result.ds

    def test_leading_positional_collision_drops_data(self):
        """When the first param is already a kwarg, positional data is dropped."""

        class _RangePlugin(_FakeNativePlugin):
            def call(self, data_range=None, **kwargs):
                return xr.Dataset(attrs={"data_range": list(data_range)})

        dt = xr.DataTree(name="multi_input")
        # No "multiple values for argument 'data_range'" error, and the kwarg
        # (not the positional tree) supplies the value. ``data_tree=True`` so the
        # raw Dataset passes through _post_call unchanged.
        result = _RangePlugin()(
            data=dt, data_range=[0, 100], _obp_initiated=True
        )
        assert result.attrs["data_range"] == [0, 100]

    def test_keyword_only_leading_signature_drops_data(self):
        """A keyword-only-leading ``call`` never receives positional data."""

        class _KwOnlyPlugin(_FakeNativePlugin):
            def call(self, *, fnames=None, **kwargs):
                return xr.Dataset(attrs={"fnames": list(fnames or [])})

        dt = xr.DataTree(name="multi_input")
        # Would raise "takes 0 positional arguments" if data were passed
        # positionally; instead it is dropped and fnames arrives by keyword.
        result = _KwOnlyPlugin()(data=dt, fnames=["a.nc"], _obp_initiated=True)
        assert result.attrs["fnames"] == ["a.nc"]


class _FakeLegacyReader(BaseReaderPlugin):
    """A legacy (``data_tree=False``) reader whose ``call`` rejects ``data``."""

    interface = "readers"
    family = "test"
    name = "fake_legacy_reader"
    data_tree = False

    def call(self, fnames=None, **kwargs):
        # Legacy readers read solely from fnames; the injected tree must have
        # been stripped in _pre_call so it never arrives as `data`.
        assert "data" not in kwargs
        return {"DATA": xr.Dataset({"var": ("x", [1, 2, 3])})}


class _FakeNativeReader(BaseReaderPlugin):
    """A DataTree-native (``data_tree=True``) reader that keeps injected data."""

    interface = "readers"
    family = "test"
    name = "fake_native_reader"
    data_tree = True

    def call(self, data=None, fnames=None, **kwargs):
        return data


class TestReaderDataStripping:
    """OBP reader input handling based on the ``data_tree`` capability flag."""

    def test_legacy_reader_strips_injected_tree(self):
        """A ``data_tree=False`` reader drops the injected tree and reads fnames."""
        plugin = _FakeLegacyReader()
        injected = xr.DataTree(
            xr.Dataset({"up": ("x", [9, 9, 9])}), name="multi_input"
        )
        result = plugin(data=injected, fnames=["a.nc"], _obp_initiated=True)
        assert isinstance(result, xr.DataTree)
        assert "var" in result.ds
        assert (result.ds["var"].values == [1, 2, 3]).all()

    def test_legacy_reader_strips_empty_tree(self):
        """A top-level entry reader handed an empty DataTree still runs cleanly."""
        plugin = _FakeLegacyReader()
        empty = xr.DataTree(name="multi_input")
        result = plugin(data=empty, fnames=["a.nc"], _obp_initiated=True)
        assert isinstance(result, xr.DataTree)
        assert "var" in result.ds

    def test_native_reader_keeps_injected_tree(self):
        """A ``data_tree=True`` reader receives the injected tree as data."""
        plugin = _FakeNativeReader()
        injected = xr.DataTree(
            xr.Dataset({"up": ("x", [9, 9, 9])}), name="multi_input"
        )
        result = plugin(data=injected, fnames=["a.nc"], _obp_initiated=True)
        assert isinstance(result, xr.DataTree)
        assert "up" in result.ds
        assert (result.ds["up"].values == [9, 9, 9]).all()
