# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Output formatters interface class."""

from geoips.interfaces.class_based_plugin import BaseClassPlugin
from geoips.interfaces.base import BaseClassInterface
from geoips.utils.types.family_conversions import OUTPUT_FORMATTER_FAMILY_CONVERSIONS


class BaseOutputFormatterPlugin(BaseClassPlugin, abstract=True):
    """Base class for GeoIPS output_formatter plugins.

    Plugins with ``data_tree=False`` have their inputs / outputs
    automatically converted according to the family-specific rules
    defined in ``OUTPUT_FORMATTER_FAMILY_CONVERSIONS``.
    """

    data_tree = False
    _family_conversion_map = OUTPUT_FORMATTER_FAMILY_CONVERSIONS

    def _normalize_obp_kwargs(self, kwargs):
        """Rename ``output_filenames`` → ``output_fnames`` for legacy formatters.

        Legacy (family-bearing) output formatter plugins expect
        ``output_fnames`` in their ``call`` signature, but the OBP
        conduit uses ``output_filenames``.  This hook renames the kwarg
        so ``_obp_filter_kwargs`` does not drop it and ``call`` receives
        the expected argument name.

        Datatree-native output formatters (no ``family``) pass through
        unchanged.
        """
        if hasattr(self.__class__, "family") and "output_filenames" in kwargs:
            kwargs["output_fnames"] = kwargs.pop("output_filenames")
        return kwargs


class OutputFormattersInterface(BaseClassInterface):
    """Data format for the resulting output product (e.g. netCDF, png)."""

    name = "output_formatters"
    plugin_class = BaseOutputFormatterPlugin

    required_args = {
        "image": ["area_def", "xarray_obj", "product_name", "output_fnames"],
        "unprojected": ["xarray_obj", "product_name", "output_fnames"],
        "image_overlay": ["area_def", "xarray_obj", "product_name", "output_fnames"],
        "image_multi": [
            "area_def",
            "xarray_obj",
            "product_names",
            "output_fnames",
            "mpl_colors_info",
        ],
        "xrdict_area_varlist_to_outlist": ["xarray_dict", "area_def", "varlist"],
        "xrdict_area_product_outfnames_to_outlist": [
            "xarray_dict",
            "area_def",
            "product_name",
            "output_fnames",
        ],
        "xrdict_area_product_to_outlist": [
            "xarray_dict",
            "area_def",
            "product_name",
        ],
        "xrdict_to_outlist": [
            "xarray_dict",
        ],
        "xrdict_varlist_outfnames_to_outlist": [
            "xarray_dict",
            "varlist",
            "output_fnames",
        ],
        "xarray_data": ["xarray_obj", "product_names", "output_fnames"],
        "standard_metadata": [
            "area_def",
            "xarray_obj",
            "metadata_yaml_filename",
            "product_filename",
        ],
    }
    required_kwargs = {
        "image": ["product_name_title", "mpl_colors_info", "existing_image"],
        "unprojected": ["product_name_title", "mpl_colors_info"],
        "image_overlay": [
            "product_name_title",
            "clean_fname",
            "mpl_colors_info",
            "clean_fname",
            "feature_annotator",
            "gridline_annotator",
            "clean_fname",
            "product_datatype_title",
            "clean_fname",
            "bg_data",
            "bg_mpl_colors_info",
            "clean_fname",
            "bg_xarray",
            "bg_product_name_title",
            "bg_datatype_title",
            "clean_fname",
            "remove_duplicate_minrange",
        ],
        "image_multi": ["product_name_titles"],
        "xarray_dict_data": ["append", "overwrite"],
        "xarray_dict_to_image": [],
        "xarray_data": [],
        "standard_metadata": ["metadata_dir", "basedir", "output_dict"],
        "xrdict_varlist_outfnames_to_outlist": [],
        "xrdict_area_varlist_to_outlist": [],
        "xrdict_area_product_outfnames_to_outlist": [],
        "xrdict_area_product_to_outlist": [],
        "xrdict_to_outlist": [],
    }


output_formatters = OutputFormattersInterface()
