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

"""Takes in a dictionary of xarrays and converts to xarray datatree"""


import logging
from datatree import DataTree

LOG = logging.getLogger(__name__)


def xarray_to_datatree(xarray_dict):
    """Convert a flat (non nested) dictionary of xarrays to DataTree format"""
    xarray_datatree = DataTree.from_dict(xarray_dict)
    assert xarray_datatree == xarray_dict

    return xarray_datatree