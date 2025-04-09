# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Takes in a dictionary of xarrays and converts to xarray datatree."""


import logging
from datatree import DataTree

LOG = logging.getLogger(__name__)


def xarray_to_datatree(xarray_dict):
    """Convert a flat (non nested) dictionary of xarrays to DataTree format."""
    tmp_meta = xarray_dict.pop("METADATA")
    xarray_datatree = DataTree(
        name="METADATA", data=tmp_meta, children=DataTree.from_dict(xarray_dict)
    )

    return xarray_datatree
