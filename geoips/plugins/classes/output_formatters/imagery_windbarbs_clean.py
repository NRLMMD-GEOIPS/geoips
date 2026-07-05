# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Matplotlib-based windbarb clean image output (no overlays or backgrounds)."""

from geoips.interfaces.class_based.output_formatters import (
    WindbarbOutputFormatterPlugin,
)

import logging

LOG = logging.getLogger(__name__)


class ImageryWindbarbsCleanOutputFormatterPlugin(WindbarbOutputFormatterPlugin):
    """Imagery Windbarbs Clean Output formatter plugin class."""

    interface = "output_formatters"
    family = "image"
    name = "imagery_windbarbs_clean"

    def call(
        self,
        area_def,
        xarray_obj,
        product_name,
        output_fnames,
        product_name_title=None,
        mpl_colors_info=None,
        existing_image=None,
        remove_duplicate_minrange=None,
        fig=None,
        main_ax=None,
        mapobj=None,
    ):
        """Plot clean windbarb imagery on matplotlib figure."""
        formatted_data_dict = self.format_windbarb_data(xarray_obj, product_name)

        success_outputs = self.output_clean_windbarbs(
            area_def,
            output_fnames,
            mpl_colors_info,
            xarray_obj.start_datetime,
            formatted_data_dict,
            fig,
            main_ax,
            mapobj,
        )

        return success_outputs


PLUGIN_CLASS = ImageryWindbarbsCleanOutputFormatterPlugin
