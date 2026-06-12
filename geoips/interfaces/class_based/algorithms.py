# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Algorithms interface class."""

from geoips.interfaces.class_based_plugin import BaseClassPlugin
from geoips.interfaces.base import BaseClassInterface
from geoips.utils.types.family_conversions import ALGORITHM_FAMILY_CONVERSIONS


class BaseAlgorithmPlugin(BaseClassPlugin, abstract=True):
    """Base class for GeoIPS algorithm plugins.

    Plugins with ``data_tree=False`` have their inputs / outputs
    automatically converted according to the family-specific rules
    defined in ``ALGORITHM_FAMILY_CONVERSIONS``.
    """

    data_tree = False
    _family_conversion_map = ALGORITHM_FAMILY_CONVERSIONS


class AlgorithmsInterface(BaseClassInterface):
    """Data manipulations to apply to the dataset."""

    name = "algorithms"
    plugin_class = BaseAlgorithmPlugin

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
