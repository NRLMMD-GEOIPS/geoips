# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Unit test module for testing functionality of geoips/xarray_utils/data.py."""

from importlib import resources
import logging
import pytest
from pyresample import load_area

from geoips.interfaces import sectors
from geoips.xarray_utils.data import get_minmax_latlon_from_area_def, point_in_area_def

LOG = logging.getLogger(__name__)


class XarrayDataUtils:
    """Class for testing functions out of xarray_utils/data.py.

    Currently tests get_minmax_latlon_from_area_def and point_in_area_def from the
    aforementioned file.
    """

    def __init__(self):
        """Initialize the XarrayDataUtils Class.

        Instantiate both the plugins to test and the paths to those plugins.
        """
        self._sector_plugins = self.sector_plugins
        self._sector_abspaths = self.sector_abspaths
        self._area_defs = self.area_defs

    @property
    def sector_plugins(self):
        """Available sector plugins for testing."""
        if not hasattr(self, "_sector_plugins"):
            return sectors.plugin_registry.registered_plugins["yaml_based"]["sectors"]
        else:
            return self._sector_plugins

    @property
    def sector_abspaths(self):
        """Absolute paths to the available (static) sector plugins for testing."""
        if not hasattr(self, "_sector_abspaths"):
            self._sector_abspaths = []
            for plg_name in self.sector_plugins:
                plg_family = self.sector_plugins[plg_name]["family"]
                if plg_family == "area_definition_static":
                    self._sector_abspaths.append(
                        str(
                            resources.files(self.sector_plugins[plg_name]["package"])
                            / self.sector_plugins[plg_name]["relpath"]
                        )
                    )
            return sorted(self._sector_abspaths)
        else:
            return self._sector_abspaths

    @property
    def area_defs(self):
        """Available (static) PyResample AreaDefinition()'s for testing."""
        if not hasattr(self, "_area_defs"):
            return [load_area(abspath, "spec") for abspath in self.sector_abspaths]
        else:
            return self._area_defs

    def generate_id(self, area_def):
        """Generate and Return an id for the provided PyResample AreaDefinition()."""
        return f"{area_def.area_id.title()}"


xdu = XarrayDataUtils()


@pytest.mark.parametrize("area_def", xdu.area_defs, ids=xdu.generate_id)
def test_get_minmax_latlon_from_area_def(area_def):
    """Test the function geoips/xarray_utils/data.py:get_minmax_latlon_from_area_def.

    This test will only be applied to static sectors, as dynamic sectors do not have
    enough information in the yamls to create an area definition initially.
    """
    min_lon, min_lat, max_lon, max_lat = get_minmax_latlon_from_area_def(area_def, 0, 0)
    pole = False
    if max_lat == 90:
        pole = True
        assert min_lat == list(area_def.area_extent_ll)[1]
    elif min_lat == -90:
        pole = True
        assert max_lat == list(area_def.area_extent_ll)[3]
    if pole:
        assert min_lon == -180
        assert max_lon == 180
    else:
        assert -180 <= min_lon <= max_lon < 360
        assert -90 <= min_lat <= max_lat <= 90


@pytest.mark.parametrize("area_def", xdu.area_defs, ids=xdu.generate_id)
def test_point_in_area_def(area_def):
    """Test the funciton geoips/xarray_utils/data.py:point_in_area_def.

    This test will only be applied to static sectors, as dynamic sectors do not have
    enough information in the yamls to create an area definition initially.
    """
    if area_def.area_id in ["north_pole", "south_pole"]:
        assert point_in_area_def(area_def, 0, 90) or point_in_area_def(area_def, 0, -90)
    else:
        assert not (
            point_in_area_def(area_def, 0, 90) or point_in_area_def(area_def, 0, -90)
        )
