# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Interpolators interface class."""

from geoips.base_class_plugins import BaseInterpolatorPlugin
from geoips.interfaces.base import BaseClassInterface


class InterpolatorsInterface(BaseClassInterface):
    """Interpolation routine to apply when reprojecting data."""

    name = "interpolators"
    plugin_class = BaseInterpolatorPlugin

    required_args = {
        "2d": ["area_def", "input_xarray", "output_xarray", "varlist"],
        "grid": ["area_def", "input_xarray", "output_xarray", "varlist"],
    }

    required_kwargs = {"2d": ["array_num"], "grid": ["array_num"]}


interpolators = InterpolatorsInterface()
