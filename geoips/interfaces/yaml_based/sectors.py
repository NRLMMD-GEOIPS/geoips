# # # This source code is subject to the license referenced at
# # # https://github.com/NRLMMD-GEOIPS.

"""Sector interface module."""

from cartopy import feature as cfeature
import numpy as np
from pyresample import kd_tree

from geoips.interfaces.base import BaseYamlPlugin, BaseYamlInterface
from geoips.image_utils.mpl_utils import create_figure_and_main_ax_and_mapobj
from geoips.pydantic.sectors import SectorPluginModel

# Commenting these out for PR #260
# Will work on this again after the 2023 workshop
#
# def center_to_area_definition(sector):
#     """Return a pyresample AreaDefinition for the input sector.
#
#     The input sector must supply location information in the center format.
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

    def create_test_plot(self, fname, return_fig_ax_map=False, overlay=False):
        """Create a test PNG image for this sector.

        Parameters
        ----------
        fname: str
            - The full path to the output image.
        return_fix_ax_map: bool, default=False
            - Whether or not we should save the image to disk or return the figure,
              axes, and mapobj variables in memory
        overlay: bool, default=False
            - If true, overlay this sector on the global grid and make it slightly
              transparent. Useful for projecting tiny sectors on the global grid to get
              a sense of where they'll end up and what they'll look like.

        """
        if overlay:
            global_sector = sectors.get_plugin("global_cylindrical")
            global_area_def = global_sector.area_definition
            fig, ax, mapobj = create_figure_and_main_ax_and_mapobj(
                global_area_def.shape[1],
                global_area_def.shape[0],
                global_area_def,
                noborder=True,
            )

            # Create a dummy 2D numpy array of data for self.area_definition
            data_overlay = np.ones(self.area_definition.shape) * 10  # or real data

            # Reproject data_overlay to the global grid
            resampled_data = kd_tree.resample_nearest(
                self.area_definition,
                data_overlay,
                global_area_def,
                radius_of_influence=14000,  # Not sure what to set here. I chose 14km
                fill_value=np.nan,
            )

            # Normalize to 0–1 range; this additionally masks out pixels we don't want
            # to color.
            norm = np.nan_to_num(resampled_data)
            norm = (norm - norm.min()) / (norm.max() - norm.min() + 1e-6)

            data_overlay = np.zeros(resampled_data.shape + (4,), dtype=np.float32)
            # This produces a Vivid Green Color
            data_overlay[..., 0] = 0.282
            data_overlay[..., 1] = 1.0
            data_overlay[..., 2] = 0
            data_overlay[..., 3] = norm * 0.5

            # Plot overlay data (with transparency) on the global grid
            ax.imshow(
                data_overlay,
                transform=mapobj,
                extent=(
                    global_area_def.area_extent[0],
                    global_area_def.area_extent[2],
                    global_area_def.area_extent[1],
                    global_area_def.area_extent[3],
                ),
                origin="upper",
            )

        else:
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
    validator = SectorPluginModel


sectors = SectorsInterface()
