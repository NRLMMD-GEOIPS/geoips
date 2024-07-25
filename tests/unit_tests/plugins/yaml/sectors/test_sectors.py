# # # This source code is protected under the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Unit tests for sector plugins."""

import pytest
from geoips import interfaces
from geoips.interfaces.yaml_based.sectors import SectorPluginBase


def test_get_all_sectors():
    """Attempt to load all available sectors."""
    interfaces.sectors.get_plugins()


def gen_ids(sector_dict):
    """Generate ids from the name key in each sector."""
    return sector_dict["name"]


@pytest.mark.parametrize("sector", interfaces.sectors.get_plugins(), ids=gen_ids)
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
