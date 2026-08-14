"""Unit tests for geoips.utils.types.obp_conduits."""

import xarray as xr

from geoips.interfaces.class_based_plugin import BaseClassPlugin
from geoips.utils.types.obp_conduits import OBP_CONDUITS, kwarg_name_for_kind


class TestObpConduits:
    """Test geoips.utils.types.obp_conduits."""

    def test_title_formatter_kwarg_name(self):
        """Ensure that title formatter conduit kwarg is named correctly."""
        assert OBP_CONDUITS["title_formatter"]["kwarg"] == "preformatted_title_str"
        assert kwarg_name_for_kind("title_formatter") == "preformatted_title_str"

    def test_title_formatter_conduit_injection(self):
        """Ensure that title formatter kwargs get passed along correctly."""
        sentinel = "My Cool Title"
        ds = xr.Dataset(
            attrs={
                "plugin_kind": "title_formatter",
                "value": sentinel,
            }
        )
        dt = xr.DataTree(children={"title": ds})
        kwargs_dict = BaseClassPlugin._extract_child_kwargs(dt, {})
        assert kwargs_dict["preformatted_title_str"] == sentinel

    def test_title_formatter_does_not_discard_manual_override(self):
        """Ensure that a user-specified title string isn't discarded."""
        sentinel = "User-Defined, Even Cooler Title"
        ds = xr.Dataset(
            attrs={
                "plugin_kind": "title_formatter",
                # Set the value differently to the sentinel
                "value": "My Cool Title",
            }
        )
        dt = xr.DataTree(children={"title": ds})
        non_empty_kwargs_dict = {
            "preformatted_title_str": sentinel,
        }
        result_kwargs_dict = BaseClassPlugin._extract_child_kwargs(
            dt,
            non_empty_kwargs_dict,
        )
        assert result_kwargs_dict["preformatted_title_str"] == sentinel

    def test_absent_title_formatter_adds_no_defaults(self):
        """Ensure that an absent title_formatter adds no default values."""
        ds = xr.Dataset(
            attrs={
                "plugin_kind": "colormapper",
                "mpl_colors_info": None,
            }
        )
        dt = xr.DataTree(children={"title": ds})
        kwargs_dict = BaseClassPlugin._extract_child_kwargs(dt, {})
        assert "preformatted_title_str" not in kwargs_dict
