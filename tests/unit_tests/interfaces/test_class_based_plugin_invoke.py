# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Tests for BaseClassPlugin DataTree wrapping via the public ``plugin()`` call.

Calling ``plugin(...)`` routes through ``__call__`` -> ``_invoke``, so these
tests exercise the ``_invoke`` wrapping/conversion behavior through the public
interface rather than calling ``_invoke`` directly.
"""

import inspect

import numpy as np
import pytest
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


class TestDataArgumentRouting:
    """Canonical data is routed without changing the implementation signature."""

    def test_canonical_data_routes_to_legacy_xarray_obj(self):
        """Canonical ``data`` is translated to a legacy data argument."""

        class _XarrayObjPlugin(_FakeLegacyPlugin):
            def call(self, xarray_obj, **kwargs):
                return xarray_obj

        ds = xr.Dataset({"var": ("x", [1, 2, 3])})
        dt = xr.DataTree.from_dict({"/": ds})
        result = _XarrayObjPlugin()(data=dt, _obp_initiated=True)
        assert isinstance(result, xr.DataTree)
        assert "var" in result.ds

    def test_second_position_input_keeps_first_argument(self):
        """A second-position legacy input does not displace its first argument."""

        class _InterpolatorLikePlugin(_FakeNativePlugin):
            def call(self, area_def, input_xarray, method=None):
                assert area_def == "test-area"
                assert method == "nearest"
                return input_xarray

        data = xr.DataTree(xr.Dataset({"var": ("x", [1, 2, 3])}))
        result = _InterpolatorLikePlugin()(
            "test-area",
            data=data,
            method="nearest",
            _obp_initiated=True,
        )
        assert result is data

    def test_direct_legacy_keyword_remains_supported(self):
        """Existing callers may continue using a legacy argument name."""

        class _XobjPlugin(_FakeNativePlugin):
            def call(self, xobj):
                return xobj

        data = xr.DataTree(xr.Dataset({"var": ("x", [1, 2, 3])}))
        assert _XobjPlugin()(xobj=data) is data

    def test_canonical_data_routes_to_remaining_legacy_names(self):
        """Canonical data supports arrays, xarray_dict, and xobj signatures."""

        class _ArraysPlugin(_FakeNativePlugin):
            def call(self, arrays):
                return arrays

        class _XarrayDictPlugin(_FakeNativePlugin):
            def call(self, xarray_dict):
                return xarray_dict

        class _XobjPlugin(_FakeNativePlugin):
            def call(self, xobj):
                return xobj

        data = xr.DataTree(xr.Dataset({"var": ("x", [1, 2, 3])}))
        for plugin_class in (_ArraysPlugin, _XarrayDictPlugin, _XobjPlugin):
            assert plugin_class()(data=data) is data

    def test_canonical_and_legacy_data_collision_raises(self):
        """Supplying both spellings is rejected rather than silently choosing one."""

        class _ArraysPlugin(_FakeNativePlugin):
            def call(self, arrays):
                return arrays

        canonical = xr.DataTree(name="canonical")
        legacy = xr.DataTree(name="legacy")
        with pytest.raises(TypeError, match="both the canonical 'data'"):
            _ArraysPlugin()(data=canonical, arrays=legacy)

    def test_explicit_unusual_data_argument(self):
        """Third-party plugins can declare an input name outside known aliases."""

        class _CustomInputPlugin(_FakeNativePlugin):
            data_argument = "payload"

            def call(self, option, payload):
                assert option == "keep-first"
                return payload

        data = xr.DataTree(name="custom")
        assert _CustomInputPlugin()("keep-first", data=data) is data

    def test_non_data_call_argument_does_not_receive_data(self):
        """Wrapper data is accepted even when ``call`` consumes no input data."""

        class _RangePlugin(_FakeNativePlugin):
            def call(self, data_range=None, **kwargs):
                return xr.Dataset(attrs={"data_range": list(data_range)})

        dt = xr.DataTree(name="multi_input")
        # No "multiple values for argument 'data_range'" error, and the kwarg
        # (not the positional tree) supplies the value. ``data_tree=True`` so the
        # raw Dataset passes through _post_call unchanged.
        result = _RangePlugin()(data=dt, data_range=[0, 100], _obp_initiated=True)
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
        return {
            "DATA": xr.Dataset({"var": ("x", [1, 2, 3])}),
            "METADATA": xr.Dataset(),
        }


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
        injected = xr.DataTree(xr.Dataset({"up": ("x", [9, 9, 9])}), name="multi_input")
        result = plugin(data=injected, fnames=["a.nc"], _obp_initiated=True)
        assert isinstance(result, xr.DataTree)
        assert "var" in result["DATA"].ds
        assert (result["DATA"].ds["var"].values == [1, 2, 3]).all()

    def test_reader_fnames_remains_first_positional_argument(self):
        """Architectural ``data`` never occupies a legacy reader's fnames slot."""

        class _SignatureReader(BaseClassPlugin):
            interface = "readers"
            family = "test"
            name = "signature_reader"
            data_tree = True

            def call(self, fnames, metadata_only=False):
                assert fnames == ["a.nc", "b.nc"]
                assert metadata_only is True
                return xr.Dataset(attrs={"fnames": fnames})

        plugin = _SignatureReader()
        upstream = xr.DataTree(name="upstream")
        result = plugin(
            ["a.nc", "b.nc"],
            data=upstream,
            metadata_only=True,
            _obp_initiated=True,
        )

        assert result.attrs["fnames"] == ["a.nc", "b.nc"]
        assert list(inspect.signature(plugin).parameters) == [
            "fnames",
            "metadata_only",
        ]

    def test_legacy_reader_strips_empty_tree(self):
        """A top-level entry reader handed an empty DataTree still runs cleanly."""
        plugin = _FakeLegacyReader()
        empty = xr.DataTree(name="multi_input")
        result = plugin(data=empty, fnames=["a.nc"], _obp_initiated=True)
        assert isinstance(result, xr.DataTree)
        assert "var" in result["DATA"].ds

    def test_native_reader_keeps_injected_tree(self):
        """A ``data_tree=True`` reader receives the injected tree as data."""
        plugin = _FakeNativeReader()
        injected = xr.DataTree(xr.Dataset({"up": ("x", [9, 9, 9])}), name="multi_input")
        result = plugin(data=injected, fnames=["a.nc"], _obp_initiated=True)
        assert isinstance(result, xr.DataTree)
        assert "up" in result.ds
        assert (result.ds["up"].values == [9, 9, 9]).all()
