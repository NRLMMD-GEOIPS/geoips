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


import pytest
import xarray
import numpy as np
from geoips.commandline.log_setup import setup_logging
from geoips.xarray_utils import xr_to_dtree

LOG = setup_logging()


@pytest.fixture
def load_testfiles():
    """Generate test xarrays for testing."""
    # only want a small sample for testing
    xarray_dict = {
        "test_{}".format(k): xarray.Dataset(
            data_vars=dict(temp=(["x", "y"], np.empty((2, 2)))),
            coords=dict(lon=(["x", "y"], np.empty((2, 2)))),
        )
        for k in range(0, 4)
    }
    xarray_dict["METADATA"] = xarray.Dataset(
        attrs={"units": "test", "dataset": "synthetic"}
    )
    return xarray_dict


def test_xarray_to_datatree(load_testfiles):
    """Test conversion a xarray dictionary to a datatree.

    Parameters
    ----------
    load_testfiles : dict(xarrays)
        Dictionary of xarrays

    Returns
    -------
    None
    """
    xarray_datatree = xr_to_dtree.xarray_to_datatree(load_testfiles)
    assert xarray_datatree == load_testfiles
    assert xarray_datatree.keys() == load_testfiles.keys()
