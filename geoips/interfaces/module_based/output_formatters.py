# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Output formatters interface module."""

from geoips.interfaces.base import BaseModuleInterface


class OutputFormattersInterface(BaseModuleInterface):
    """Data format for the resulting output product (e.g. netCDF, png)."""

    name = "output_formatters"
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
