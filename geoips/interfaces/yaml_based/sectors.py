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

"""Sector interface module."""

from geoips.interfaces.base import BaseYamlPlugin, BaseYamlInterface
from pyresample import load_area
from geoips.image_utils.mpl_utils import create_figure_and_main_ax_and_mapobj
from cartopy import feature as cfeature
from pyresample import create_area_def


# Commenting these out for PR #260
# Will work on this again after the 2023 workshop
#
# def center_to_area_definition(sector):
#     """Return a pyresample AreaDefinition for the input sector.
#
#     The input sector must supply location information in the "center" format.
#     """
#     if not sector.family.startswith("center"):
#         raise ValueError("Sector does not supply location as center coordinates.")
#     raise NotImplementedError
#
#
# def corners_to_area_definition(sector):
#     """Return a pyresample AreaDefinition for the input sector.
#
#     The input sector must supply location information in the "corners" format.
#     """
#     if not sector.family.startswith("center"):
#         raise ValueError("Sector does not supply location as corner coordinates.")
#
#     ad_info = {
#         "area_id": sector.name,
#         "projection": {
#             "units": "m",
#             "a": 6371228.0,
#             "proj": sector.spec.projection,
#             "lat_0": sector.spec.center.lat,
#             "lon_0": sector.spec.center.lon,
#         },
#         "width": sector.shape[0],
#         "height": sector.shape[1],
#         "resolution": [sector.resolution, sector.resolution],
#         "center": [0, 0],
#     }
#
#     ad = create_area_def(**ad_info)
#     raise NotImplementedError


class SectorPluginBase(BaseYamlPlugin):
    """The base class for all sector plugins.

    This class provides the functionality specific to sector plugin classes. It should
    not be instantiated directly. To access sector plugins, use
    `geoips.interfaces.sectors`.
    """

    @property
    def area_definition(self):
        """Return the pyresample AreaDefinition for the sector."""
        # if self.family.startswith(("area_definition", "generated")):
        if self.family.startswith("area_definition"):
            ad = load_area(self.abspath, "spec")
        # elif self.family.startswith("center"):
        #     ad = center_to_area_definition(self)
        # elif self.family.startswith("corners"):
        #     ad = corners_to_area_definition(self)
        return ad

    def create_test_plot(self, fname):
        """Create a test PNG image for this sector."""
        fig, ax, mapobj = create_figure_and_main_ax_and_mapobj(
            self.area_definition.shape[1],
            self.area_definition.shape[0],
            self.area_definition,
            noborder=True,
        )
        ax.add_feature(cfeature.COASTLINE)
        ax.add_feature(cfeature.BORDERS)
        fig.savefig(fname)


class SectorsInterface(BaseYamlInterface):
    """Interface for sector plugins."""

    name = "sectors"
    plugin_class = SectorPluginBase


sectors = SectorsInterface()
