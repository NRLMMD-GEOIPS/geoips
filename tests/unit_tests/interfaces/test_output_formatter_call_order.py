# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Tests for output formatter call-signature normalization."""

import inspect

import pytest
import xarray as xr

from geoips.errors import BoundaryIOError
from geoips.interfaces.class_based.output_formatters import BaseOutputFormatterPlugin


class _AreaDef:
    """Small duck-typed area definition for formatter routing tests."""

    area_extent = (0, 0, 1, 1)


def _legacy_area_first_formatter_class():
    """Build a legacy formatter while capturing its deprecation warning."""
    with pytest.warns(DeprecationWarning, match="legacy 'area_def' before"):

        class _LegacyAreaFirstFormatter(BaseOutputFormatterPlugin):
            interface = "output_formatters"
            family = "image"
            name = "legacy_area_first_formatter"
            data_tree = False

            def call(self, area_def, xarray_obj, product_name, output_fnames):
                return xr.Dataset(
                    attrs={
                        "area_def_id": id(area_def),
                        "xarray_obj_marker": xarray_obj.attrs["marker"],
                        "product_name": product_name,
                        "output_fnames": tuple(output_fnames),
                    }
                )

    return _LegacyAreaFirstFormatter


def test_legacy_area_first_formatter_exposes_data_first_signature():
    """Legacy area-first formatter classes expose normalized data-first calls."""
    formatter_cls = _legacy_area_first_formatter_class()

    assert list(inspect.signature(formatter_cls.call).parameters) == [
        "self",
        "xarray_obj",
        "area_def",
        "product_name",
        "output_fnames",
    ]
    assert list(inspect.signature(formatter_cls()).parameters) == [
        "xarray_obj",
        "area_def",
        "product_name",
        "output_fnames",
    ]


def test_legacy_area_first_formatter_invokes_original_order_from_obp_kwargs():
    """Data-first OBP arguments are mapped back to the legacy implementation."""
    formatter = _legacy_area_first_formatter_class()()
    area_def = _AreaDef()
    xarray_obj = xr.Dataset({"test": ("x", [1, 2])})
    xarray_obj.attrs["marker"] = "expected-input"
    multi_input = xr.DataTree(name="multi_input")
    multi_input["algorithm"] = xr.DataTree(xr.Dataset(), name="algorithm")
    multi_input["sector"] = xr.DataTree(xr.Dataset(), name="sector")

    result = formatter(
        data=multi_input,
        _obp_initiated=True,
        xarray_obj=xarray_obj,
        area_def=area_def,
        product_name="test_product",
        output_fnames=["out.png"],
    )

    assert result.ds.attrs["area_def_id"] == id(area_def)
    assert result.ds.attrs["xarray_obj_marker"] == "expected-input"
    assert result.ds.attrs["product_name"] == "test_product"
    assert result.ds.attrs["output_fnames"] == ("out.png",)


def test_legacy_area_first_formatter_accepts_old_direct_call_order():
    """Direct legacy area-first calls still reach the original implementation."""
    formatter = _legacy_area_first_formatter_class()()
    area_def = _AreaDef()
    xarray_obj = xr.Dataset({"test": ("x", [1, 2])})
    xarray_obj.attrs["marker"] = "expected-input"

    result = formatter(area_def, xarray_obj, "test_product", ["out.png"])

    assert result.attrs["area_def_id"] == id(area_def)
    assert result.attrs["xarray_obj_marker"] == "expected-input"


def test_legacy_area_first_formatter_accepts_legacy_mixed_call_order():
    """Legacy procflows pass area_def positionally and xarray_obj by keyword."""
    formatter = _legacy_area_first_formatter_class()()
    area_def = _AreaDef()
    xarray_obj = xr.Dataset({"test": ("x", [1, 2])})
    xarray_obj.attrs["marker"] = "expected-input"

    result = formatter(
        area_def,
        xarray_obj=xarray_obj,
        product_name="test_product",
        output_fnames=["out.png"],
    )

    assert result.attrs["area_def_id"] == id(area_def)
    assert result.attrs["xarray_obj_marker"] == "expected-input"


def test_output_formatter_list_result_has_semantic_output_attrs():
    """OBP formatter list results expose semantic output product attrs."""
    formatter = _legacy_area_first_formatter_class()()

    result = formatter._post_call(["out.png"], _obp_initiated=True)

    assert result.ds.attrs["output_products"] == ["out.png"]
    assert result.ds.attrs["_ditto_list_value"] == ["out.png"]


def test_output_formatter_empty_list_result_raises_boundary_error():
    """OBP formatter list results must include at least one output product."""
    formatter = _legacy_area_first_formatter_class()()

    with pytest.raises(BoundaryIOError, match="did not produce any output products"):
        formatter._post_call([], _obp_initiated=True)
