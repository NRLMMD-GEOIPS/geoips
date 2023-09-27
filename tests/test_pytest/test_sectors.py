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

"""Unit tests for sector plugins."""

import pytest
import pyresample
from geoips import interfaces
from geoips.interfaces.yaml_based.sectors import SectorPluginBase


def test_get_all_sectors():
    """Attempt to load all available sectors."""
    interfaces.sectors.get_plugins()


@pytest.mark.parametrize("sector", interfaces.sectors.get_plugins())
def test_sector(sector):
    """Ensure that a sector has the correct attributes."""
    assert isinstance(sector, SectorPluginBase)
    assert sector.interface == "sectors"
    assert sector.name
    assert sector.family
    assert sector.__doc__
    assert sector.docstring == sector.__doc__
    # Should add this back after completing #301
    # assert isinstance(sector.area_definition, pyresample.AreaDefinition)
