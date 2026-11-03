# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Unit tests for the class-based reader base classes."""

import pytest

from geoips.plugins.classes.readers.abi_l2_netcdf import AbiL2NetcdfReaderPlugin
from geoips.plugins.classes.readers.abi_netcdf import AbiNetcdfReaderPlugin


@pytest.mark.parametrize("reader", [AbiL2NetcdfReaderPlugin, AbiNetcdfReaderPlugin])
def test_abi_readers_define_dont_autogen_geolocation(reader):
    """ABI readers have the DONT_AUTOGEN_GEOLOCATION get_latitude_longitude reads."""
    assert isinstance(reader.DONT_AUTOGEN_GEOLOCATION, bool)
