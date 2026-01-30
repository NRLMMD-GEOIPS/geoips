# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Sector adjusters interface class."""

from geoips.interfaces.base import BaseClassInterface


class SectorAdjustersInterface(BaseClassInterface):
    """Interface for adjusting a sector based on additional information.

    Ie, pass in data and the area definition, and modify the area_definition based
    on the data itself.
    """

    name = "sector_adjusters"
    required_args = {
        "list_xarray_list_variables_to_area_def_out_fnames": [
            "xobjs",
            "area_def",
            "variables",
        ]
    }
    required_kwargs = {
        "list_xarray_list_variables_to_area_def_out_fnames": ["recenter_variables"]
    }


sector_adjusters = SectorAdjustersInterface()
