# # # Distribution Statement A. Approved for public release. Distribution unlimited.
# # #
# # # Author:
# # # Naval Research Laboratory, Marine Meteorology Division
# # #
# # # This program is free software: you can redistribute it and/or modify it under
# # # the terms of the NRLMMD License included with this program. This program is
# # # distributed WITHOUT ANY WARRANTY; without even the implied warranty of
# # # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the included license
# # # for more details. If you did not receive the license, for more information see:
# # # https://github.com/U-S-NRL-Marine-Meteorology-Division/

"""Sector adjusters interface module."""

from geoips.interfaces.base import BaseModuleInterface


class SectorAdjustersInterface(BaseModuleInterface):
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
