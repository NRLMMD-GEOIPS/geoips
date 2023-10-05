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
import pytest
from datatree import DataTree
import glob
from geoips.interfaces import readers

LOG = logging.getLogger(__name__)


@pytest.fixture
def load_testfiles():
    """Preload files for testing."""
    # only want a few files for testing
    fnames = glob.glob('geoips/test_data/test_data_amsr2/data/*.nc')[:2]
    amsr2_reader = readers.get_plugin('amsr2_netcdf')
    xarray_dict = amsr2_reader(fnames)
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
    xarray_datatree = DataTree.from_dict(load_testfiles)
    assert xarray_datatree == load_testfiles
