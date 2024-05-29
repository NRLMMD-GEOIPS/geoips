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

"""Takes in a dictionary of xarrays and converts to xarray datatree."""


import logging

LOG = logging.getLogger(__name__)
try:
    from datatree import DataTree
except ImportError:
    LOG.info(
        "Failed import DataTree in xarray_utils/xr_to_dtree.py. "
        "If you need it, install it."
    )


def xarray_to_datatree(xarray_dict):
    """Convert a flat (non nested) dictionary of xarrays to DataTree format."""
    tmp_meta = xarray_dict.pop("METADATA")
    xarray_datatree = DataTree(
        name="METADATA", data=tmp_meta, children=DataTree.from_dict(xarray_dict)
    )

    return xarray_datatree
