# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Interpolators interface module."""

from geoips.interfaces.base import BaseModuleInterface


class InterpolatorsInterface(BaseModuleInterface):
    """Interpolation routine to apply when reprojecting data."""

    name = "interpolators"
    required_args = {
        "2d": ["area_def", "input_xarray", "output_xarray", "varlist"],
        "grid": ["area_def", "input_xarray", "output_xarray", "varlist"],
    }

    required_kwargs = {"2d": ["array_num"], "grid": ["array_num"]}


interpolators = InterpolatorsInterface()
