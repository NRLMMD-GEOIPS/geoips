# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Sector interface module."""

from geoips.interfaces.base import BaseYamlPlugin, BaseYamlInterface
from geoips.pydantic.sectors import SectorPluginModel

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
        from pyresample import load_area
        from importlib.resources import files

        if self.family.startswith("area_definition"):
            abspath = str(files(self.package) / self.relpath)
            ad = load_area(abspath, "spec")
        # elif self.family.startswith("center"):
        #     ad = center_to_area_definition(self)
        # elif self.family.startswith("corners"):
        #     ad = corners_to_area_definition(self)
        return ad

    def create_test_plot(self, fname, return_fig_ax_map=False):
        """Create a test PNG image for this sector."""
        from geoips.image_utils.mpl_utils import create_figure_and_main_ax_and_mapobj
        from cartopy import feature as cfeature

        fig, ax, mapobj = create_figure_and_main_ax_and_mapobj(
            self.area_definition.shape[1],
            self.area_definition.shape[0],
            self.area_definition,
            noborder=True,
        )
        ax.add_feature(cfeature.COASTLINE)
        ax.add_feature(cfeature.BORDERS)
        if fname is not None:
            fig.savefig(fname)
        if return_fig_ax_map:
            return fig, ax, mapobj


class SectorsInterface(BaseYamlInterface):
    """Interface for sector plugins."""

    name = "sectors"
    plugin_class = SectorPluginBase
    # validator = SectorPluginModel


sectors = SectorsInterface()
