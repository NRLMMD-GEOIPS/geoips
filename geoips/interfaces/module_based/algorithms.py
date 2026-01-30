# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Algorithms interface module."""

from geoips.interfaces.base import BaseClassInterface


class AlgorithmsInterface(BaseClassInterface):
    """Data manipulations to apply to the dataset."""

    name = "algorithms"

    required_args = {
        "scalar_to_scalar": [],
        "single_channel": ["arrays"],
        "channel_combination": ["arrays"],
        "list_numpy_to_numpy": ["arrays"],
        "xarray_to_numpy": ["xobj"],
        "xarray_to_xarray": ["xobj", "variables"],  # product_name optional
        "rgb": ["arrays"],
        "xarray_dict_to_xarray": ["xarray_dict"],
        "xarray_dict_dict_to_xarray": ["xarray_dict_dict"],
        "xarray_dict_to_xarray_dict": ["xarray_dict"],
        "xarray_dict_area_def_to_numpy": ["xarray_dict", "area_def"],
    }

    required_kwargs = {
        "scalar_to_scalar": ["value"],
        "single_channel": [],
        "channel_combination": [],
        "xarray_to_numpy": [],
        "xarray_to_xarray": [],
        "list_numpy_to_numpy": [],
        "rgb": [],
        "xarray_dict_to_xarray": [],
        "xarray_dict_dict_to_xarray": [],
        "xarray_dict_to_xarray_dict": [],
        "xarray_dict_area_def_to_numpy": [],
    }


algorithms = AlgorithmsInterface()
